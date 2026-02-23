"""
Agent factory — reusable creation of the LangGraph DeepAgent.

Used by:
- ``final_agent.py``  (interactive / CLI)
- ``ambient.py``      (background cron)
- ``server.py``       (web UI backend)
"""

import os
import uuid
import yaml

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver

from multi_server_mcp_client import client as mcp_client
from tools import (
    retrieval_tool,
    ingest_pdf_tool,
    web_search,
    list_collections_tool,
    update_memory,
    _read_memory,
)
from prompts import (
    ORCHESTRATOR_PROMPT,
    INFO_RETRIEVAL_PROMPT,
    FLASHCARD_PROMPT,
    FILE_HANDLING_PROMPT,
)

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
_model_cfg = _cfg.get("model", {})

MODEL_NAME = f"{_model_cfg.get('provider', 'openai')}:{_model_cfg.get('name', 'gpt-4o-mini')}"
TEMPERATURE = _model_cfg.get("temperature", 0.0)

# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

async def create_agent(
    checkpointer=None,
    model_name: str | None = None,
    temperature: float | None = None,
):
    """Create and return a fully-configured DeepAgent.

    Parameters
    ----------
    checkpointer : optional
        LangGraph checkpointer for state persistence.  Defaults to an
        in-memory ``MemorySaver``.
    model_name : str, optional
        Override the model from config (e.g. ``"openai:gpt-4o"``).
    temperature : float, optional
        Override temperature from config.

    Returns
    -------
    agent : DeepAgent
        Ready-to-invoke agent instance.
    """
    model = init_chat_model(
        model=model_name or MODEL_NAME,
        temperature=temperature if temperature is not None else TEMPERATURE,
    )

    if checkpointer is None:
        checkpointer = MemorySaver()

    # Fetch MCP tools (Anki)
    mcp_tools = await mcp_client.get_tools()

    # -- Load persistent memory into orchestrator prompt -------------------
    memory_text = _read_memory()
    live_prompt = ORCHESTRATOR_PROMPT.replace("{agent_memory}", memory_text or "(no memory yet)")

    # -- Sub-agents --------------------------------------------------------

    anki_flashcard_sub_agent = {
        "name": "anki-flashcard",
        "description": (
            "Specialist for Anki flashcard generation & deck management. "
            "Provide topic name and lecture excerpts in the task description."
        ),
        "system_prompt": FLASHCARD_PROMPT,
        "tools": mcp_tools,
    }

    information_retrieval_sub_agent = {
        "name": "information-retrieval",
        "description": (
            "Specialist for RAG retrieval, PDF ingestion, and web research. "
            "Provide specific queries or document paths."
        ),
        "system_prompt": INFO_RETRIEVAL_PROMPT,
        "tools": [retrieval_tool, ingest_pdf_tool, web_search, list_collections_tool],
    }

    file_handling_sub_agent = {
        "name": "file-handling",
        "description": (
            "Specialist for creating revision materials (study guides, "
            "practice exams, lecture summaries). Provide topic and content."
        ),
        "system_prompt": FILE_HANDLING_PROMPT,
        # Uses LangGraph's built-in file-handling tools
    }

    # -- All tools available to the orchestrator ---------------------------

    # NOTE: FilesystemBackend auto-injects ls, read_file, write_file,
    # edit_file, glob, grep into all agents — no need to add them here.
    all_tools = [
        retrieval_tool,
        ingest_pdf_tool,
        web_search,
        list_collections_tool,
        update_memory,
    ] + mcp_tools

    interrupt_on = {
        "write_file": {"allowed_decisions": ["approve", "reject"]},
    }

    agent = create_deep_agent(
        model=model,
        tools=all_tools,
        system_prompt=live_prompt,
        subagents=[
            anki_flashcard_sub_agent,
            information_retrieval_sub_agent,
            file_handling_sub_agent,
        ],
        backend=FilesystemBackend(root_dir=".", virtual_mode=False),
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
    )

    return agent


async def run_agent(message: str, thread_id: str | None = None, agent=None):
    """Convenience wrapper: create (or reuse) an agent and run a single message.

    Parameters
    ----------
    message : str
        The user's request.
    thread_id : str, optional
        LangGraph thread ID for state continuity.  Auto-generated if omitted.
    agent : optional
        Pre-created agent. If None, one is created on the fly.

    Returns
    -------
    result : dict
        The agent's output (including ``messages`` and possibly ``__interrupt__``).
    """
    if agent is None:
        agent = await create_agent()

    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )
    return result, config, agent
