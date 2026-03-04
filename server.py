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

GET    /outputs              List files/folders in agent_fs/
GET    /outputs/{path:path}  Serve a specific file or list a subfolder

GET    /                     Web UI (HTMX)
"""

import asyncio
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

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
    _cfg.get("paths", {}).get("agent_fs", "./agent_fs")
)
_model_cfg = _cfg.get("model", {})
_summary_cfg = _cfg.get("summaries", {})

SUMMARY_INPUT_CHAR_LIMIT = int(_summary_cfg.get("max_input_chars", 4000))
SUMMARY_OUTPUT_CHAR_LIMIT = int(_summary_cfg.get("max_output_chars", 600))
MAX_ACTIVITY_SUMMARIES_PER_REQUEST = int(_summary_cfg.get("max_activity_summaries_per_request", 8))
TASK_SUMMARY_OUTPUT_CHAR_LIMIT = int(_summary_cfg.get("max_task_summary_chars", 220))

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
    conversation_turns: list[dict] = Field(default_factory=list)
    conversation_summary: str = ""
    conversation_summary_hash: str = ""
    interrupt_payload: Optional[dict] = None  # set when status == awaiting_approval
    output_files: list[str] = Field(default_factory=list)
    source: str = "user"               # user | ambient

_tasks: dict[str, Task] = {}
_task_agents: dict[str, tuple] = {}   # task_id -> (agent, config) — reused for follow-ups
_interrupt_events: dict[str, asyncio.Event] = {}
_interrupt_decisions: dict[str, list] = {}
_ws_connections: dict[str, list[WebSocket]] = {}  # task_id -> list of WS
_activity_summary_cache: dict[str, str] = {}
_summary_model = None


def _truncate(text: str, n: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _extract_text_content(content: Any) -> str:
    """Extract plain text from str or Anthropic/OpenAI content blocks."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    parts.append(str(item.get("text")))
            elif hasattr(item, "text"):
                parts.append(str(getattr(item, "text")))
        return "\n".join(p.strip() for p in parts if p and str(p).strip()).strip()
    return ""


def _last_assistant_text(messages: list[Any]) -> str:
    for msg in reversed(messages or []):
        cls = msg.__class__.__name__.lower()
        role = getattr(msg, "role", "")
        if "ai" not in cls and role != "assistant":
            continue
        content = getattr(msg, "content", None)
        text = _extract_text_content(content)
        if text:
            return text
    return ""


def _fallback_thread_summary(turns: list[dict], default: str = "") -> str:
    user_turns = [t.get("text", "") for t in turns if t.get("role") == "user" and t.get("text")]
    ai_turns = [t.get("text", "") for t in turns if t.get("role") == "assistant" and t.get("text")]
    if user_turns and ai_turns:
        return _truncate(
            f"User asked about {user_turns[-1]}. Agent responded with an explanation and next-step support.",
            TASK_SUMMARY_OUTPUT_CHAR_LIMIT,
        )
    if ai_turns:
        return _truncate(ai_turns[-1], TASK_SUMMARY_OUTPUT_CHAR_LIMIT)
    return _truncate(default or "Task completed.", TASK_SUMMARY_OUTPUT_CHAR_LIMIT)


def _conversation_hash(turns: list[dict]) -> str:
    payload = json.dumps(turns or [], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _activity_entry_hash(entry: dict) -> str:
    payload = f"{entry.get('date','')}|{entry.get('action','')}|{entry.get('description','')}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_summary_model():
    global _summary_model
    if _summary_model is None:
        provider = _model_cfg.get("provider", "anthropic")
        name = _model_cfg.get("name", "claude-sonnet-4-6")
        model_name = f"{provider}:{name}"
        _summary_model = init_chat_model(
            model=model_name,
            temperature=0.0,
            max_tokens=int(_summary_cfg.get("max_model_tokens", 700)),
        )
    return _summary_model


async def _summarize_text(prompt: str, fallback: str) -> str:
    """LLM summary helper with safe fallback and output truncation."""
    try:
        model = _get_summary_model()
        resp = await model.ainvoke([
            {
                "role": "system",
                "content": "Write concise plain-English summaries. Keep factual and avoid adding new facts.",
            },
            {"role": "user", "content": _truncate(prompt, SUMMARY_INPUT_CHAR_LIMIT)},
        ])
        text = _extract_text_content(getattr(resp, "content", ""))
        return _truncate(text or fallback, SUMMARY_OUTPUT_CHAR_LIMIT)
    except Exception:
        return _truncate(fallback, SUMMARY_OUTPUT_CHAR_LIMIT)


async def _refresh_task_conversation_summary(task: Task):
    turns = task.conversation_turns or []
    if not turns:
        task.conversation_summary = _truncate(task.result_summary or task.message, TASK_SUMMARY_OUTPUT_CHAR_LIMIT)
        task.conversation_summary_hash = ""
        return

    digest = _conversation_hash(turns)
    if digest == task.conversation_summary_hash and task.conversation_summary:
        return

    snippets: list[str] = []
    for t in turns[-8:]:
        role = t.get("role", "assistant")
        text = _truncate(t.get("text", ""), 280)
        snippets.append(f"{role.upper()}: {text}")
    transcript = "\n".join(snippets)

    prompt = (
        "Summarise this full conversation thread for a small task-history card in plain English. "
        "Output 1-2 short sentences only (max 45 words). Include user goal and outcome.\n\n"
        f"{transcript}"
    )
    fallback = _fallback_thread_summary(turns, task.result_summary or task.message or "Task completed.")
    task.conversation_summary = _truncate(
        await _summarize_text(prompt, fallback),
        TASK_SUMMARY_OUTPUT_CHAR_LIMIT,
    )
    task.conversation_summary_hash = digest


async def _plain_english_activity_summary(entry: dict) -> str:
    key = _activity_entry_hash(entry)
    cached = _activity_summary_cache.get(key)
    if cached:
        return cached

    action = entry.get("action", "note")
    description = entry.get("description", "")
    prompt = (
        "Rewrite this activity log line in plain English in one short sentence. "
        "Keep exact meaning and avoid extra assumptions.\n\n"
        f"Action: {action}\nDescription: {description}"
    )
    fallback = f"{action}: {description}".strip()
    summary = await _summarize_text(prompt, fallback)
    _activity_summary_cache[key] = summary
    return summary


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
    from agent_factory import create_agent

    task = _tasks[task_id]
    task.status = "running"
    task.thread_id = f"task-{task_id}"
    task.conversation_turns.append({
        "role": "user",
        "text": task.message,
        "at": datetime.now(timezone.utc).isoformat(),
    })
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
        summary = _last_assistant_text(messages)
        if summary:
            task.conversation_turns.append({
                "role": "assistant",
                "text": summary,
                "at": datetime.now(timezone.utc).isoformat(),
            })

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.result_summary = summary
        task.interrupt_payload = None
        await _refresh_task_conversation_summary(task)

        await _broadcast(task_id, "status", {
            "status": "completed",
            "summary": summary,
            "conversation_summary": task.conversation_summary,
        })

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
    from agent_factory import create_agent

    task = _tasks[task_id]
    task.conversation_turns.append({
        "role": "user",
        "text": message,
        "at": datetime.now(timezone.utc).isoformat(),
    })
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
        summary = _last_assistant_text(messages)
        if summary:
            task.conversation_turns.append({
                "role": "assistant",
                "text": summary,
                "at": datetime.now(timezone.utc).isoformat(),
            })

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.result_summary = summary
        task.interrupt_payload = None
        await _refresh_task_conversation_summary(task)
        await _broadcast(task_id, "status", {
            "status": "completed",
            "summary": summary,
            "conversation_summary": task.conversation_summary,
        })

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
async def list_outputs(path: str = ""):
    """List files and folders inside agent_fs/, optionally at a sub-path."""
    target = os.path.normpath(os.path.join(OUTPUT_DIR, path))
    # Prevent directory traversal
    if not target.startswith(OUTPUT_DIR):
        raise HTTPException(403, "Forbidden")
    if not os.path.isdir(target):
        raise HTTPException(404, "Directory not found")
    items = []
    for name in sorted(os.listdir(target)):
        if name.startswith(".") or name == "memory":
            continue
        full = os.path.join(target, name)
        rel = os.path.relpath(full, OUTPUT_DIR)
        if os.path.isdir(full):
            items.append({"name": name, "path": rel, "type": "folder"})
        else:
            items.append({
                "name": name,
                "path": rel,
                "type": "file",
                "size": os.path.getsize(full),
                "modified": datetime.fromtimestamp(
                    os.path.getmtime(full), tz=timezone.utc
                ).isoformat(),
            })
    return items


@app.get("/outputs/{path:path}")
async def get_output(path: str):
    """Serve a file or list a subdirectory inside agent_fs/."""
    fpath = os.path.normpath(os.path.join(OUTPUT_DIR, path))
    if not fpath.startswith(OUTPUT_DIR):
        raise HTTPException(403, "Forbidden")
    if os.path.isdir(fpath):
        # If it's a directory, return its listing
        return await list_outputs(path)
    if not os.path.isfile(fpath):
        raise HTTPException(404, "File not found")
    return FileResponse(fpath)


# ---------------------------------------------------------------------------
# REST: History (persistent from agent memory)
# ---------------------------------------------------------------------------

MEMORY_PATH = os.path.join(OUTPUT_DIR, "memory", ".agent_memory.md")

@app.get("/api/history")
async def api_history(limit: int = 10):
    """Parse Recent Activity from .agent_memory.md and return structured JSON."""
    entries: list[dict] = []
    try:
        if not os.path.isfile(MEMORY_PATH):
            return entries
        with open(MEMORY_PATH, "r") as f:
            content = f.read()

        # Find the ## Recent Activity section
        in_section = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("## Recent Activity"):
                in_section = True
                continue
            if in_section and stripped.startswith("## "):
                break  # next section
            if in_section and stripped.startswith("- "):
                # Parse canonical or relaxed format
                m = re.match(r"^-\s*\[([^\]]+)\]\s*([^:]+):\s*(.*)$", stripped)
                if m:
                    date_str = m.group(1).strip()
                    action = m.group(2).strip()
                    description = m.group(3).strip()
                else:
                    date_str = ""
                    action = "note"
                    description = re.sub(r"^-\s*", "", stripped).strip()

                entries.append({
                    "date": date_str,
                    "action": action,
                    "description": description,
                })
    except Exception:
        pass

    # Return newest first, capped at limit
    entries = list(reversed(entries))
    entries = entries[: max(1, min(limit, 50))]

    # Plain-English summaries (cached)
    for idx, entry in enumerate(entries):
        if idx < MAX_ACTIVITY_SUMMARIES_PER_REQUEST:
            entry["plain_summary"] = await _plain_english_activity_summary(entry)
        else:
            entry["plain_summary"] = _truncate(
                f"{entry.get('action', 'note')}: {entry.get('description', '')}",
                SUMMARY_OUTPUT_CHAR_LIMIT,
            )

    return entries


# ---------------------------------------------------------------------------
# REST: Upload lecture PDF
# ---------------------------------------------------------------------------

LECTURES_DIR = os.path.join(OUTPUT_DIR, "lectures")

@app.post("/upload-lecture")
async def upload_lecture(file: UploadFile = File(...)):
    """Upload a PDF to agent_fs/lectures/ for ambient processing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    os.makedirs(LECTURES_DIR, exist_ok=True)
    dest = os.path.join(LECTURES_DIR, file.filename)

    # Avoid overwriting
    if os.path.exists(dest):
        raise HTTPException(409, f"File '{file.filename}' already exists in lectures/")

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    return {"status": "uploaded", "filename": file.filename, "path": f"lectures/{file.filename}"}


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


@app.get("/files", response_class=HTMLResponse)
async def ui_files(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT, reload=True)
