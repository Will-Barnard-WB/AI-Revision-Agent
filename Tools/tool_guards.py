"""Per-message guardrails for tool-call budgets.

This module wraps selected tools with counters that reset on each new user
turn. Limits are loaded from ``config.yaml -> limits``.
"""

from __future__ import annotations

import os
from typing import Literal

import yaml
from langchain_core.tools import BaseTool, tool


def _load_config() -> dict:
    """Load project config.yaml (best-effort)."""
    root = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(root, "config.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


class ToolCallGuard:
    """Counter-based guard for retrieval and web-search tool budgets."""

    def __init__(self, max_retrieval_calls: int = 3, max_web_searches: int = 3):
        self.max_retrieval_calls = max(0, int(max_retrieval_calls))
        self.max_web_searches = max(0, int(max_web_searches))
        self.reset_for_new_turn()

    @classmethod
    def from_config(cls, config: dict | None = None) -> "ToolCallGuard":
        cfg = config or _load_config()
        lim = cfg.get("limits", {})
        return cls(
            max_retrieval_calls=lim.get("max_retrieval_calls", 3),
            max_web_searches=lim.get("max_web_searches", 3),
        )

    def reset_for_new_turn(self):
        """Reset per-message counters. Call this once for each new user turn."""
        self.retrieval_calls = 0
        self.web_search_calls = 0

    def _limit_message(self, kind: str, limit: int) -> str:
        return (
            f"⚠️ {kind} call limit reached for this user request "
            f"({limit}/{limit}). Do not retry this tool again in this turn. "
            "Ask the user for clarification, a narrower goal, or permission to continue."
        )

    def wrap_tools(self, retrieval: BaseTool, web: BaseTool) -> tuple[BaseTool, BaseTool]:
        """Return guarded versions of ``retrieval_tool`` and ``web_search``."""

        retrieval_description = (
            retrieval.description
            + "\n\n[Guardrail] This tool is budget-limited per user request. "
            + f"Maximum calls: {self.max_retrieval_calls}."
        )
        web_description = (
            web.description
            + "\n\n[Guardrail] This tool is budget-limited per user request. "
            + f"Maximum calls: {self.max_web_searches}."
        )

        @tool("retrieval_tool", description=retrieval_description)
        def retrieval_tool_guarded(query: str, collection: str | None = None) -> str:
            if self.retrieval_calls >= self.max_retrieval_calls:
                return self._limit_message("retrieval_tool", self.max_retrieval_calls)
            self.retrieval_calls += 1
            return retrieval.invoke({"query": query, "collection": collection})

        @tool("web_search", description=web_description)
        def web_search_guarded(
            query: str,
            max_results: int = 1,
            topic: Literal["general", "news", "finance"] = "general",
        ) -> str:
            if self.web_search_calls >= self.max_web_searches:
                return self._limit_message("web_search", self.max_web_searches)
            self.web_search_calls += 1
            return web.invoke(
                {
                    "query": query,
                    "max_results": max_results,
                    "topic": topic,
                }
            )

        return retrieval_tool_guarded, web_search_guarded