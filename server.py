"""
FastAPI backend — REST + WebSocket interface for the revision agent.

Endpoints
---------
POST   /tasks                Submit a new agent task
GET    /tasks                List all tasks
GET    /tasks/{id}           Get task detail + status
POST   /tasks/{id}/interrupt Respond to human-in-the-loop prompt
WS     /ws/{task_id}         Real-time streaming of agent activity

GET    /ambient/status       Ambient cron status
POST   /ambient/poll         Trigger immediate poll
GET    /ambient/log          Recent ambient activity log
GET    /ambient/manifest     Processed-PDF manifest

GET    /outputs              List files in AgentOutput/
GET    /outputs/{filename}   Serve a specific output file

GET    /                     Web UI (HTMX)
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ambient import Ambient, read_log, MANIFEST_PATH, WATCH_DIR, _read_manifest

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f)
    return {}

_cfg = _load_config()
_server_cfg = _cfg.get("server", {})
HOST = _server_cfg.get("host", "0.0.0.0")
PORT = _server_cfg.get("port", 8080)

OUTPUT_DIR = os.path.abspath(
    _cfg.get("paths", {}).get("agent_output", "./AgentOutput")
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="RevisionAgent", version="2.0")

# Templates
_base = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(_base, "ui", "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(_base, "ui", "static")), name="static")

# ---------------------------------------------------------------------------
# In-memory task store (swap for SQLite later)
# ---------------------------------------------------------------------------

class Task(BaseModel):
    id: str
    message: str
    status: str = "pending"            # pending | running | awaiting_approval | completed | failed
    thread_id: str = ""
    created_at: str = ""
    completed_at: str = ""
    result_summary: str = ""
    interrupt_payload: Optional[dict] = None  # set when status == awaiting_approval
    output_files: list[str] = []
    source: str = "user"               # user | ambient

_tasks: dict[str, Task] = {}
_task_agents: dict[str, tuple] = {}   # task_id -> (agent, config) — reused for follow-ups
_interrupt_events: dict[str, asyncio.Event] = {}
_interrupt_decisions: dict[str, list] = {}
_ws_connections: dict[str, list[WebSocket]] = {}  # task_id -> list of WS


# ---------------------------------------------------------------------------
# WebSocket broadcaster
# ---------------------------------------------------------------------------

async def _broadcast(task_id: str, event: str, data: dict | str):
    """Send a JSON message to all WebSocket clients following a task."""
    payload = json.dumps({"event": event, "data": data})
    conns = _ws_connections.get(task_id, [])
    dead = []
    for ws in conns:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.remove(ws)


# ---------------------------------------------------------------------------
# Agent execution (background)
# ---------------------------------------------------------------------------

async def _run_task(task_id: str):
    """Execute the agent task in the background, streaming progress over WS."""
    from agent_factory import create_agent, reset_tool_counters

    task = _tasks[task_id]
    task.status = "running"
    task.thread_id = f"task-{task_id}"
    await _broadcast(task_id, "status", {"status": "running"})

    try:
        # Reuse existing agent if this is a follow-up message
        cached = _task_agents.get(task_id)
        if cached:
            agent, config = cached
        else:
            agent = await create_agent()
            config = {"configurable": {"thread_id": task.thread_id}}
            _task_agents[task_id] = (agent, config)

        reset_tool_counters()
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": task.message}]},
            config=config,
        )

        # Handle interrupt
        if result.get("__interrupt__"):
            task.status = "awaiting_approval"
            interrupts = result["__interrupt__"][0].value
            task.interrupt_payload = interrupts

            await _broadcast(task_id, "interrupt", {
                "action_requests": interrupts.get("action_requests", []),
                "review_configs": interrupts.get("review_configs", []),
            })

            # Wait for the UI to respond
            evt = asyncio.Event()
            _interrupt_events[task_id] = evt
            await evt.wait()

            decisions = _interrupt_decisions.pop(task_id, [])
            from langgraph.types import Command
            result = await agent.ainvoke(
                Command(resume={"decisions": decisions}),
                config=config,
            )

        # Extract summary from last AI message
        messages = result.get("messages", [])
        summary = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
                summary = msg.content
                break

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.result_summary = summary
        task.interrupt_payload = None

        await _broadcast(task_id, "status", {"status": "completed", "summary": summary})

    except Exception as e:
        task.status = "failed"
        task.result_summary = f"Error: {e}"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        await _broadcast(task_id, "status", {"status": "failed", "error": str(e)})


# ---------------------------------------------------------------------------
# Ambient integration
# ---------------------------------------------------------------------------

_ambient = Ambient()


def _launchd_daemon_running() -> bool:
    """Check if the standalone launchd ambient daemon is already running."""
    import subprocess
    try:
        result = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/com.revisionagent.ambient"],
            capture_output=True, text=True, timeout=5,
        )
        # If the command succeeds and shows a PID, the daemon is running
        return result.returncode == 0 and "pid" in result.stdout.lower()
    except Exception:
        return False


@app.on_event("startup")
async def _startup():
    """Start the ambient cron on server boot — unless the launchd daemon is already handling it."""
    if not _cfg.get("ambient", {}).get("enabled", True):
        return
    if _launchd_daemon_running():
        print("ℹ️  Standalone ambient daemon detected (launchd) — skipping in-process cron")
    else:
        print("🔄 No standalone daemon found — starting in-process ambient cron")
        await _ambient.start()


# ---------------------------------------------------------------------------
# REST: Tasks
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    message: str

@app.post("/tasks")
async def create_task(body: TaskCreate):
    task_id = uuid.uuid4().hex[:12]
    task = Task(
        id=task_id,
        message=body.message,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _tasks[task_id] = task
    asyncio.create_task(_run_task(task_id))
    return {"task_id": task_id, "status": "pending"}


@app.get("/tasks")
async def list_tasks():
    return [t.model_dump() for t in sorted(_tasks.values(), key=lambda t: t.created_at, reverse=True)]


@app.get("/tasks/pending")
async def list_pending_approvals():
    """Return tasks that are awaiting human approval."""
    pending = [
        t.model_dump()
        for t in _tasks.values()
        if t.status == "awaiting_approval"
    ]
    # Sort newest first
    pending.sort(key=lambda t: t["created_at"], reverse=True)
    return pending


@app.get("/tasks/pending/count")
async def pending_approval_count():
    """Return the count of tasks awaiting approval (for sidebar badge)."""
    count = sum(1 for t in _tasks.values() if t.status == "awaiting_approval")
    return {"count": count}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.model_dump()


class InterruptResponse(BaseModel):
    decisions: list[dict]  # e.g. [{"type": "approve"}]

@app.post("/tasks/{task_id}/interrupt")
async def resolve_interrupt(task_id: str, body: InterruptResponse):
    task = _tasks.get(task_id)
    if not task or task.status != "awaiting_approval":
        raise HTTPException(400, "No pending interrupt for this task")

    _interrupt_decisions[task_id] = body.decisions
    evt = _interrupt_events.pop(task_id, None)
    if evt:
        evt.set()

    task.status = "running"
    return {"status": "resumed"}


# ---------------------------------------------------------------------------
# REST: Conversation threading (follow-up messages)
# ---------------------------------------------------------------------------

class FollowUpMessage(BaseModel):
    message: str

@app.post("/tasks/{task_id}/message")
async def send_follow_up(task_id: str, body: FollowUpMessage):
    """Send a follow-up message in the same conversation thread."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status not in ("completed", "failed"):
        raise HTTPException(400, "Task is still running — wait for it to finish")

    # Reset status for the follow-up
    task.status = "running"
    task.message = body.message  # update to latest message for display
    task.result_summary = ""
    task.completed_at = ""

    asyncio.create_task(_run_follow_up(task_id, body.message))
    return {"task_id": task_id, "status": "running"}


async def _run_follow_up(task_id: str, message: str):
    """Run a follow-up message using the cached agent and thread."""
    from agent_factory import create_agent, reset_tool_counters

    task = _tasks[task_id]
    await _broadcast(task_id, "status", {"status": "running"})

    try:
        cached = _task_agents.get(task_id)
        if cached:
            agent, config = cached
        else:
            # Re-create agent if lost (server restart edge case)
            agent = await create_agent()
            config = {"configurable": {"thread_id": task.thread_id}}
            _task_agents[task_id] = (agent, config)

        reset_tool_counters()
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
        )

        # Handle interrupt (same logic as _run_task)
        if result.get("__interrupt__"):
            task.status = "awaiting_approval"
            interrupts = result["__interrupt__"][0].value
            task.interrupt_payload = interrupts
            await _broadcast(task_id, "interrupt", {
                "action_requests": interrupts.get("action_requests", []),
                "review_configs": interrupts.get("review_configs", []),
            })
            evt = asyncio.Event()
            _interrupt_events[task_id] = evt
            await evt.wait()
            decisions = _interrupt_decisions.pop(task_id, [])
            from langgraph.types import Command
            result = await agent.ainvoke(
                Command(resume={"decisions": decisions}),
                config=config,
            )

        messages = result.get("messages", [])
        summary = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
                summary = msg.content
                break

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.result_summary = summary
        task.interrupt_payload = None
        await _broadcast(task_id, "status", {"status": "completed", "summary": summary})

    except Exception as e:
        task.status = "failed"
        task.result_summary = f"Error: {e}"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        await _broadcast(task_id, "status", {"status": "failed", "error": str(e)})


# ---------------------------------------------------------------------------
# WebSocket: Streaming
# ---------------------------------------------------------------------------

@app.websocket("/ws/{task_id}")
async def ws_stream(websocket: WebSocket, task_id: str):
    await websocket.accept()
    _ws_connections.setdefault(task_id, []).append(websocket)

    # Send current status immediately
    task = _tasks.get(task_id)
    if task:
        await websocket.send_text(json.dumps({
            "event": "status",
            "data": {"status": task.status, "summary": task.result_summary},
        }))

    try:
        while True:
            # Keep connection alive; client can also send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        conns = _ws_connections.get(task_id, [])
        if websocket in conns:
            conns.remove(websocket)


# ---------------------------------------------------------------------------
# REST: Ambient
# ---------------------------------------------------------------------------

@app.get("/ambient/status")
async def ambient_status():
    daemon_running = _launchd_daemon_running()
    return {
        "running": _ambient.running or daemon_running,
        "source": "launchd" if daemon_running else ("in-process" if _ambient.running else "stopped"),
        "watch_dir": WATCH_DIR,
    }


@app.post("/ambient/poll")
async def ambient_poll_now():
    await _ambient.poll_now()
    return {"status": "poll_triggered"}


@app.get("/ambient/log")
async def ambient_log(limit: int = 50):
    return read_log(limit)


@app.get("/ambient/manifest")
async def ambient_manifest():
    return {"processed": list(_read_manifest())}


# ---------------------------------------------------------------------------
# REST: Outputs
# ---------------------------------------------------------------------------

@app.get("/outputs")
async def list_outputs():
    if not os.path.isdir(OUTPUT_DIR):
        return []
    files = []
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.startswith("."):
            continue
        fpath = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(fpath):
            files.append({
                "name": f,
                "size": os.path.getsize(fpath),
                "modified": datetime.fromtimestamp(
                    os.path.getmtime(fpath), tz=timezone.utc
                ).isoformat(),
            })
    return files


@app.get("/outputs/{filename}")
async def get_output(filename: str):
    fpath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(fpath):
        raise HTTPException(404, "File not found")
    return FileResponse(fpath)


# ---------------------------------------------------------------------------
# HTML: UI pages (HTMX)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def ui_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def ui_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/ambient", response_class=HTMLResponse)
async def ui_ambient(request: Request):
    return templates.TemplateResponse("ambient.html", {"request": request})


@app.get("/approvals", response_class=HTMLResponse)
async def ui_approvals(request: Request):
    return templates.TemplateResponse("approvals.html", {"request": request})


@app.get("/history", response_class=HTMLResponse)
async def ui_history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
