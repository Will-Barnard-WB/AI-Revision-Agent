"""
Agent tools — enriched docstrings carry the behavioural guidance so the
agent can plan autonomously from tool descriptions alone (Claude-Code style).
"""

import os
import httpx
from pathlib import Path
from typing import List

from langchain_core.tools import tool, InjectedToolArg
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal
from dotenv import load_dotenv

from RAG import (
    get_retriever,
    setup_retriever,
    persist_directory,
    default_collection,
    collection_name_from_filename,
    list_collections,
    embedding_model,
    chunk_size,
    chunk_overlap,
)

load_dotenv()

tavily_client = TavilyClient()


# ---------------------------------------------------------------------------
# Internal helpers (not exposed to the agent)
# ---------------------------------------------------------------------------

def _fetch_webpage(url: str, timeout: float = 10.0) -> str:
    """Fetch a URL and return its content as markdown."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        resp = httpx.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return markdownify(resp.text)
    except Exception as e:
        return f"Error fetching {url}: {e}"


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

@tool
def retrieval_tool(query: str, collection: str | None = None) -> str:
    """Search the vector database for lecture-note content relevant to *query*.

    **When to use this tool**
    - You need factual content from ingested lecture notes to answer a question,
      generate flashcards, or write revision material.
    - Always prefer this over web search — lecture notes are the primary source.

    **Tips for good queries**
    - Be specific: "definition of eigenvalue" beats "eigenvalues".
    - Try multiple angles if first results are thin (e.g. definition, then
      properties, then examples).

    **If results are insufficient**
    - Rephrase with different keywords and call again.
    - After 2–3 attempts, fall back to ``web_search`` for supplementary info.

    Parameters
    ----------
    query : str
        Natural-language search query.
    collection : str, optional
        ChromaDB collection to search.  Leave empty to search the default
        collection.  Call ``list_collections_tool`` to see what's available.

    Returns
    -------
    str
        Formatted document chunks, or a "no results" message.
    """
    retriever = get_retriever(collection)
    docs = retriever.invoke(query)
    if not docs:
        return (
            "No relevant chunks found.  Try rephrasing your query, or use "
            "``list_collections_tool`` to check you're searching the right collection."
        )
    parts = [f"**Chunk {i+1}:**\n{d.page_content}" for i, d in enumerate(docs)]
    return "\n\n---\n\n".join(parts)


@tool
def list_collections_tool() -> str:
    """List every ChromaDB collection currently available.

    Use this before retrieval if you're unsure which collection holds the
    content you need, or to verify a PDF has already been ingested.

    Returns
    -------
    str
        Newline-separated list of collection names, or a message if none exist.
    """
    cols = list_collections()
    if not cols:
        return "No collections exist yet. Ingest a PDF first with ``ingest_pdf_tool``."
    return "Available collections:\n" + "\n".join(f"  • {c}" for c in cols)


# ---------------------------------------------------------------------------
# Document ingestion
# ---------------------------------------------------------------------------

@tool
def ingest_pdf_tool(pdf_file_path: str, collection: str | None = None) -> str:
    """Ingest a PDF into the vector database so its content becomes searchable.

    **When to use this tool**
    - A new PDF has appeared (e.g. the user dropped it into AgentOutput/).
    - The user explicitly asks to add a document.

    **Idempotency note**
    - Calling this twice on the same PDF will create duplicate chunks.
      Check the manifest or ``list_collections_tool`` first.

    Parameters
    ----------
    pdf_file_path : str
        Absolute path to the PDF file.
    collection : str, optional
        Target collection name.  If omitted, a name is derived from the
        filename (e.g. ``Linear_Algebra_Notes.pdf`` → ``linear_algebra_notes``).

    Returns
    -------
    str
        Success summary with chunk count and collection name, or an error.
    """
    path = Path(pdf_file_path)
    if not path.exists():
        return f"❌ File not found: {pdf_file_path}"
    if path.suffix.lower() != ".pdf":
        return f"❌ Not a PDF: {path.suffix}"

    coll = collection or collection_name_from_filename(pdf_file_path)
    try:
        setup_retriever(str(path), coll)
        return (
            f"✅ Ingested '{path.name}' into collection '{coll}'.\n"
            f"You can now search it with retrieval_tool(query, collection='{coll}')."
        )
    except Exception as e:
        return f"❌ Ingestion failed: {e}"


# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------

@tool(parse_docstring=True)
def web_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[Literal["general", "news", "finance"], InjectedToolArg] = "general",
) -> str:
    """Search the web and return full-page content for the top results.

    **When to use this tool**
    - Lecture-note retrieval returned insufficient or no results after 2+ tries.
    - The user explicitly asks for external information.
    - You need real-world examples, current data, or clarifications not in
      the lecture notes.

    **When NOT to use**
    - As a first resort — always try ``retrieval_tool`` first.

    Args:
        query: Search query to execute.
        max_results: Number of pages to fetch (default 1; keep low to save time).
        topic: Category filter — 'general', 'news', or 'finance'.

    Returns:
        Formatted search results with full webpage content in markdown.
    """
    results = tavily_client.search(query, max_results=max_results, topic=topic)
    parts = []
    for r in results.get("results", []):
        content = _fetch_webpage(r["url"])
        parts.append(f"## {r['title']}\n**URL:** {r['url']}\n\n{content}\n\n---")

    if not parts:
        return f"No web results found for '{query}'."
    return f"🔍 {len(parts)} result(s) for '{query}':\n\n" + "\n".join(parts)


# ---------------------------------------------------------------------------
# Memory management
# ---------------------------------------------------------------------------

_MEMORY_PATH = os.path.join(os.path.dirname(__file__), "AgentOutput", ".agent_memory.md")
_MEMORY_CAP = 50  # max entries in Recent Activity


def _read_memory() -> str:
    """Read the full agent memory file, or return empty string."""
    if os.path.exists(_MEMORY_PATH):
        with open(_MEMORY_PATH, "r") as f:
            return f.read()
    return ""


def _write_memory(content: str):
    """Write the full agent memory file."""
    os.makedirs(os.path.dirname(_MEMORY_PATH), exist_ok=True)
    with open(_MEMORY_PATH, "w") as f:
        f.write(content)


def _cap_recent_activity(memory_text: str) -> str:
    """Ensure Recent Activity has at most _MEMORY_CAP entries."""
    lines = memory_text.split("\n")
    result = []
    in_recent = False
    activity_lines: list[str] = []
    other_lines_after: list[str] = []

    for line in lines:
        if line.strip().startswith("## Recent Activity"):
            in_recent = True
            result.append(line)
            continue
        if in_recent and line.strip().startswith("## "):
            # Hit next section — cap activity
            in_recent = False
            other_lines_after.append(line)
            continue
        if in_recent:
            if line.strip().startswith("- ["):
                activity_lines.append(line)
            else:
                result.append(line)  # comments / blanks
            continue
        if other_lines_after:
            other_lines_after.append(line)
        else:
            result.append(line)

    # Keep only the most recent entries
    if len(activity_lines) > _MEMORY_CAP:
        activity_lines = activity_lines[-_MEMORY_CAP:]

    result.extend(activity_lines)
    if not result[-1].strip():
        pass  # already has trailing blank
    else:
        result.append("")
    result.extend(other_lines_after)
    return "\n".join(result)


@tool
def update_memory(section: str, content: str, mode: str = "append") -> str:
    """Update the agent's persistent memory file.

    **Call this at the end of every task** to record what you accomplished,
    what collections you interacted with, and any user preferences you learned.

    Parameters
    ----------
    section : str
        The exact section heading to update.  Must be one of:
        ``User Profile``, ``Subjects & Collections``, ``Anki Decks``,
        ``Recent Activity``, ``User Preferences``.
    content : str
        The text to add or replace.  For ``Recent Activity``, use the format:
        ``- [YYYY-MM-DD] action: description``
    mode : str
        ``"append"`` (default) — add *content* as new lines in the section.
        ``"replace"`` — overwrite the section body with *content*.

    Returns
    -------
    str
        Confirmation message.
    """
    valid_sections = {
        "User Profile", "Subjects & Collections", "Anki Decks",
        "Recent Activity", "User Preferences",
    }
    if section not in valid_sections:
        return f"❌ Invalid section '{section}'. Must be one of: {', '.join(sorted(valid_sections))}"

    memory = _read_memory()
    if not memory.strip():
        return "❌ Memory file not found or empty."

    heading = f"## {section}"
    lines = memory.split("\n")
    new_lines: list[str] = []
    in_target = False
    section_inserted = False

    for line in lines:
        if line.strip() == heading:
            in_target = True
            new_lines.append(line)
            continue
        if in_target and line.strip().startswith("## "):
            # End of target section — insert content
            if mode == "replace":
                new_lines.append(content)
                new_lines.append("")
            # append mode: content already added below
            in_target = False
            section_inserted = True
            new_lines.append(line)
            continue
        if in_target and mode == "append":
            new_lines.append(line)
            # Insert after last non-blank line in section
        elif in_target and mode == "replace":
            continue  # skip existing section content
        else:
            new_lines.append(line)

    # If section was the last one (no next heading found)
    if in_target and not section_inserted:
        if mode == "replace":
            new_lines.append(content)
            new_lines.append("")
        # For append, we add below

    if mode == "append":
        # Find the heading and append after the section content
        result_lines: list[str] = []
        in_target = False
        appended = False
        for line in new_lines:
            if line.strip() == heading:
                in_target = True
                result_lines.append(line)
                continue
            if in_target and line.strip().startswith("## "):
                # Insert content before the next section
                for c in content.strip().split("\n"):
                    result_lines.append(c)
                result_lines.append("")
                in_target = False
                appended = True
                result_lines.append(line)
                continue
            result_lines.append(line)

        if in_target and not appended:
            # Section was last — append at end
            for c in content.strip().split("\n"):
                result_lines.append(c)
            result_lines.append("")

        new_lines = result_lines

    # Update timestamp
    final = "\n".join(new_lines)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    final = final.replace(
        "<!-- Last updated: (will be set by agent) -->",
        f"<!-- Last updated: {now} -->",
    )
    # Also update if it already has a date
    import re as _re
    final = _re.sub(
        r"<!-- Last updated: .* -->",
        f"<!-- Last updated: {now} -->",
        final,
    )

    # Cap recent activity
    final = _cap_recent_activity(final)

    _write_memory(final)
    return f"✅ Memory updated: '{section}' ({mode})"


# Legacy alias so old imports still work
tavily_search = web_search
ingest_documents_tool = ingest_pdf_tool




