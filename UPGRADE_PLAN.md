# RevisionAgent v2 Upgrade Plan — Towards an Autonomous Revision Agent

**Created:** 22 February 2026  
**Status:** ✅ Implementation Complete

---

## Context

v1 delivered the ambient cron, minimal prompts, and a web UI. But the agent is still a **pipeline** — it follows a fixed delegation pattern, starts fresh every session, and can't self-correct. This plan closes the gap to a genuinely autonomous agent (Claude Code / OpenClaw style, specialised for revision).

### What We Have
- ✅ LangGraph DeepAgent with 3 sub-agents (info-retrieval, anki-flashcard, file-handling)
- ✅ Ambient cron via launchd daemon polling every 5 minutes
- ✅ HTMX web UI with chat, ambient dashboard, task history
- ✅ Minimal prompts — agent plans from tool docstrings
- ✅ RAG (ChromaDB), Anki MCP, web search, human-in-the-loop file approval
- ✅ `write_todos()` already available from DeepAgents for planning/tracking

### What's Missing (Ranked by Impact)
1. **No persistent memory** — every session starts from zero
2. **No dynamic planning** — fixed sub-agent routing, doesn't use `write_todos()` for task decomposition
3. **No self-correction** — if retrieval returns junk, it ploughs ahead anyway
4. **No filesystem awareness** — can't explore files, only access predefined tools
5. **No conversation threading** — each UI task is one-shot, no follow-ups

---

## Phase 1: Agent Memory (Persistent State Across Sessions)

### Goal
The agent knows what you're studying, what decks exist, what's been done, and your preferences — loaded into every session automatically and updated after every task.

- [x] **1.1 — Create `AGENT_MEMORY.md` seed file**
  - Location: `AgentOutput/.agent_memory.md`
  - Sections: `## User Profile`, `## Subjects & Collections`, `## Anki Decks`, `## Recent Activity`, `## User Preferences`
  - Seed from current state (existing collections, manifest, decks)

- [x] **1.2 — Memory loading into prompts**
  - In `agent_factory.py` → `create_agent()`: read `.agent_memory.md` at startup
  - Append contents to `ORCHESTRATOR_PROMPT` under a `## Session Context` header

- [x] **1.3 — `update_memory` tool**
  - New tool in `tools.py`: `update_memory(section, content, mode="append"|"replace")`
  - Cap `## Recent Activity` at 50 entries (drop oldest when exceeded)
  - Docstring: "Call at end of every task to record what you did"

- [x] **1.4 — Ambient cron memory updates**
  - After `_process_pdf()` in `ambient.py`: update memory directly

### Files: `tools.py`, `agent_factory.py`, `prompts.py`, `ambient.py`, new `AgentOutput/.agent_memory.md`

---

## Phase 2: Dynamic Planning & Task Decomposition

### Goal
Agent uses `write_todos()` to plan, executes steps in sequence, adapts mid-task.

- [x] **2.1 — Orchestrator prompt: planning approach**
  - Add explicit `## Approach` section using `write_todos()`
  - Frame sub-agents as available specialists, not a fixed pipeline

### Files: `prompts.py`

---

## Phase 3: Self-Correction (Prompt-Driven)

### Goal
Prompt-driven retry patterns — no extra tools. Claude Code style.

- [x] **3.1 — Retrieval retry pattern** in `INFO_RETRIEVAL_PROMPT`
- [x] **3.2 — Flashcard validation loop** in `FLASHCARD_PROMPT`
- [x] **3.3 — General quality standard** in `ORCHESTRATOR_PROMPT`

### Files: `prompts.py`

---

## Phase 4: Filesystem Awareness

### Goal
Agent can explore files, check what exists, avoid duplicates.

- [x] **4.1–4.3 — Already provided by `FilesystemBackend`**
  - `ls` — list directory contents
  - `read_file` — read text files with pagination
  - `write_file` / `edit_file` — create and modify files (with HITL interrupt)
  - `glob` — find files by pattern
  - `grep` — search text across files
  - These are auto-injected into every agent and sub-agent by the middleware.
  - No custom tools needed.

### Files: _(no changes — built-in)_

---

## Phase 5: Conversation Threading (UI Multi-Turn)

### Goal
Follow-up messages within the same chat thread.

- [x] **5.1 — Server: `POST /tasks/{id}/message` endpoint**
- [x] **5.2 — Chat UI: multi-turn + "New Chat" button**
- [x] **5.3 — Agent: reuse instance per thread**

### Files: `server.py`, `ui/templates/chat.html`, `agent_factory.py`

---

## Implementation Order

```
Phase 1 (Memory) → Phase 2 (Planning) → Phase 3 (Self-Correction) → Phase 4 (Filesystem) → Phase 5 (Threading)
```

| Phase | Effort | New Tools | Files Changed |
|---|---|---|---|
| 1 — Memory | Small | 1 (`update_memory`) | 4 + 1 new |
| 2 — Planning | Tiny | 0 (uses `write_todos`) | 1 |
| 3 — Self-Correction | Tiny | 0 (prompt-driven) | 1 |
| 4 — Filesystem | None | 0 (built-in) | 0 |
| 5 — Threading | Medium | 0 | 3 |

---

## Out of Scope (Future)
- Shell execution tool (sandboxed subprocess)
- Multi-model routing (GPT-4o for planning, 4o-mini for execution)
- SQLite task persistence
- Eval framework for flashcard quality
- Push notifications on ambient completion
