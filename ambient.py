"""
Ambient agent — background cron that watches AgentOutput/ for new PDFs,
ingests them into the vector DB, and auto-generates flashcards + revision
materials without any user interaction.

Usage
-----
    python ambient.py            # run as standalone daemon
    from ambient import Ambient  # embed in server.py
"""

import asyncio
import glob
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env so API keys are available when run via launchd / cron
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

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
_amb = _cfg.get("ambient", {})

WATCH_DIR = os.path.abspath(_amb.get("watch_directory", "./AgentOutput"))
MANIFEST_PATH = os.path.abspath(_amb.get("manifest_file", "./AgentOutput/.processed_manifest.md"))
LOG_PATH = os.path.abspath(_amb.get("log_file", "./AgentOutput/.ambient_log.jsonl"))
POLL_INTERVAL = _amb.get("poll_interval_seconds", 300)


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

_MANIFEST_HEADER = """\
# Processed PDF Manifest
<!-- Auto-managed by ambient.py — do not edit manually -->

| Filename | Date Added | Date Processed | Status | Collection | Topic |
|----------|------------|----------------|--------|------------|-------|
"""


def _ensure_manifest():
    """Create the manifest file if it doesn't exist."""
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    if not os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "w") as f:
            f.write(_MANIFEST_HEADER)


def _read_manifest() -> set[str]:
    """Return the set of filenames already in the manifest."""
    _ensure_manifest()
    names = set()
    with open(MANIFEST_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and not line.startswith("| Filename") and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2 and parts[1]:
                    names.add(parts[1])
    return names


def _append_manifest(filename: str, status: str, collection: str, topic: str):
    """Append a row to the manifest markdown table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    row = f"| {filename} | {now} | {now} | {status} | {collection} | {topic} |\n"
    with open(MANIFEST_PATH, "a") as f:
        f.write(row)


# ---------------------------------------------------------------------------
# Structured log
# ---------------------------------------------------------------------------

def _log_event(event_type: str, data: dict):
    """Append a JSON-lines event to the ambient log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **data,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(limit: int = 50) -> list[dict]:
    """Read the most recent *limit* log entries (newest first)."""
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r") as f:
        lines = f.readlines()
    entries = []
    for line in reversed(lines):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if len(entries) >= limit:
            break
    return entries


# ---------------------------------------------------------------------------
# Topic extraction
# ---------------------------------------------------------------------------

def _topic_from_filename(filename: str) -> str:
    """Best-effort topic extraction from a PDF filename.

    Examples
    --------
    >>> _topic_from_filename("Eigenvalues_Lecture_Notes.pdf")
    'Eigenvalues Lecture Notes'
    """
    stem = Path(filename).stem
    # Replace underscores, hyphens, camelCase boundaries with spaces
    topic = re.sub(r"[_\-]+", " ", stem)
    topic = re.sub(r"([a-z])([A-Z])", r"\1 \2", topic)
    return topic.strip().title()


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

async def _process_pdf(pdf_path: str):
    """Ingest a single PDF and kick off flashcard + file generation."""
    from agent_factory import run_agent  # lazy to avoid circular imports
    from RAG import collection_name_from_filename

    filename = os.path.basename(pdf_path)
    topic = _topic_from_filename(filename)
    collection = collection_name_from_filename(filename)

    _log_event("processing_started", {"file": filename, "topic": topic, "collection": collection})

    # Step 1: Ingest into vector DB
    try:
        from RAG import setup_retriever
        setup_retriever(pdf_path, collection)
        _log_event("ingestion_complete", {"file": filename, "collection": collection})
    except Exception as e:
        _log_event("ingestion_failed", {"file": filename, "error": str(e)})
        _append_manifest(filename, "❌ ingestion_failed", collection, topic)
        return

    # Step 2: Ask the agent to generate flashcards + study materials
    message = (
        f"I've just added new lecture notes: '{filename}' (topic: {topic}).\n\n"
        f"The content has been ingested into the '{collection}' collection.\n\n"
        f"Please:\n"
        f"1. Retrieve the key content from collection '{collection}'\n"
        f"2. Generate Anki flashcards covering the main concepts\n"
        f"3. Create a study guide file for this topic\n"
    )

    try:
        result, _config, _agent = await run_agent(
            message=message,
            thread_id=f"ambient-{uuid.uuid4().hex[:8]}",
        )

        # Handle interrupts automatically (auto-approve in ambient mode)
        if result.get("__interrupt__"):
            from langgraph.types import Command
            interrupts = result["__interrupt__"][0].value
            decisions = [{"type": "approve"} for _ in interrupts.get("action_requests", [])]
            result = await _agent.ainvoke(
                Command(resume={"decisions": decisions}),
                config=_config,
            )

        _log_event("agent_complete", {"file": filename, "topic": topic})
        _append_manifest(filename, "✅ complete", collection, topic)

        # Update persistent memory with what was just done
        from tools import update_memory as _update_mem_tool
        from datetime import datetime as _dt, timezone as _tz
        _today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
        _update_mem_tool.invoke({
            "section": "Recent Activity",
            "content": f"- [{_today}] ambient-ingest: Processed '{filename}' → collection '{collection}', generated flashcards + study guide",
            "mode": "append",
        })
        _update_mem_tool.invoke({
            "section": "Subjects & Collections",
            "content": f"- {collection} — {topic}",
            "mode": "append",
        })

    except Exception as e:
        _log_event("agent_failed", {"file": filename, "error": str(e)})
        _append_manifest(filename, "❌ agent_failed", collection, topic)


# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------

async def _poll_once():
    """Single poll: find new PDFs and process them."""
    known = _read_manifest()
    pdf_files = glob.glob(os.path.join(WATCH_DIR, "*.pdf"))
    total_pdfs = len(pdf_files)

    new_pdfs = [p for p in pdf_files if os.path.basename(p) not in known]
    new_names = [os.path.basename(p) for p in new_pdfs]

    if not new_pdfs:
        _log_event("poll_complete", {
            "summary": f"No new PDFs found ({total_pdfs} total, {len(known)} already processed)",
            "total_pdfs": total_pdfs,
            "already_processed": len(known),
            "new_count": 0,
        })
    else:
        _log_event("poll_complete", {
            "summary": f"Found {len(new_pdfs)} new PDF(s): {', '.join(new_names)}",
            "total_pdfs": total_pdfs,
            "already_processed": len(known),
            "new_count": len(new_pdfs),
            "new_files": new_names,
        })

    for pdf_path in new_pdfs:
        await _process_pdf(pdf_path)


async def run_ambient_loop(interval: int | None = None):
    """Run the ambient polling loop forever.

    Parameters
    ----------
    interval : int, optional
        Seconds between polls.  Defaults to config value (300s / 5 min).
    """
    secs = interval or POLL_INTERVAL
    _ensure_manifest()
    _log_event("ambient_started", {"interval_seconds": secs, "watch_dir": WATCH_DIR})

    print(f"🔄 Ambient agent started — watching {WATCH_DIR} every {secs}s")

    while True:
        try:
            await _poll_once()
        except Exception as e:
            _log_event("poll_error", {"error": str(e)})
            print(f"⚠️  Poll error: {e}")
        await asyncio.sleep(secs)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

class Ambient:
    """Wrapper for embedding in server.py as a background task."""

    def __init__(self, interval: int | None = None):
        self.interval = interval or POLL_INTERVAL
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the ambient loop as a background asyncio task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(run_ambient_loop(self.interval))
            return True
        return False  # already running

    async def stop(self):
        """Cancel the background task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def poll_now(self):
        """Trigger an immediate poll (useful from the UI)."""
        await _poll_once()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ambient PDF watcher & flashcard generator")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll then exit (for use with crontab)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help=f"Seconds between polls (default: {POLL_INTERVAL})",
    )
    args = parser.parse_args()

    if args.once:
        print("🔍 Running single ambient poll…")
        asyncio.run(_poll_once())
        print("✅ Single poll complete.")
    else:
        asyncio.run(run_ambient_loop(args.interval))
