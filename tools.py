import subprocess
import shlex
from langchain_core.tools import tool
from RAG import get_retriever, persist_directory, collection_name
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from typing import List, Dict
from pathlib import Path
import os
import requests

import httpx
from langchain_core.tools import InjectedToolArg, tool
from markdownify import markdownify
from tavily import TavilyClient
from typing_extensions import Annotated, Literal

load_dotenv()

tavily_client = TavilyClient()


def fetch_webpage_content(url: str, timeout: float = 10.0) -> str:
    """Fetch and convert webpage content to markdown.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Webpage content as markdown
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return markdownify(response.text)
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"


@tool(parse_docstring=True)
def tavily_search(
    query: str,
    max_results: Annotated[int, InjectedToolArg] = 1,
    topic: Annotated[
        Literal["general", "news", "finance"], InjectedToolArg
    ] = "general",
) -> str:
    """Search the web for information on a given query.

    Uses Tavily to discover relevant URLs, then fetches and returns full webpage content as markdown.

    Args:
        query: Search query to execute
        max_results: Maximum number of results to return (default: 1)
        topic: Topic filter - 'general', 'news', or 'finance' (default: 'general')

    Returns:
        Formatted search results with full webpage content
    """
    # Use Tavily to discover URLs
    search_results = tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
    )

    # Fetch full content for each URL
    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]

        # Fetch webpage content
        content = fetch_webpage_content(url)

        result_text = f"""## {title}
**URL:** {url}

{content}

---
"""
        result_texts.append(result_text)

    # Format final response
    response = f"""🔍 Found {len(result_texts)} result(s) for '{query}':

{chr(10).join(result_texts)}"""

    return response


@tool
def retrieval_tool(query: str) -> str:
    '''
    This tool searches and returns the information from the Linear Algebra Notes document.
    '''

    retriever = get_retriever()
    docs = retriever.invoke(query)

    if not docs:
        return "I found no relevant information in the Linear Algebra Notes document."
    
    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i+1}:\n{doc.page_content}")

    return "\n\n".join(results)


@tool
def think_tool(reflection: str) -> str:
    """
    Tool for critical reflection and deliberate decision-making.
    
    Use this tool SPARINGLY for critical decision points only - NOT for routine planning or before every tool call.
    
    WHEN TO USE THIS TOOL (Critical Decisions Only):
    1. "Do I have enough context to delegate to a subagent, or do I need more information?"
    2. "Should I parallelize subagent delegations or execute sequentially?"
    3. "Has the situation changed mid-execution? Should I adjust my approach?"
    4. "Are the retrieved results sufficient, or do I need alternative queries?"
    
    WHEN NOT TO USE THIS TOOL:
    - Before every tool call (use write_todos instead for multi-step tasks)
    - To create TODO lists (use write_todos tool for task management)
    - For routine decisions or straightforward execution
    - Multiple times per task iteration
    
    HOW TO USE:
    think_tool(
      reflection="Decision: Do I have enough eigenvalue content to delegate to flashcard agent?
                  Analysis: Retrieved 5 chunks covering definition, properties, and examples.
                  Conclusion: Sufficient. Will delegate to anki-flashcard with full context."
    )
    
    This tool creates a deliberate pause for thoughtful reasoning. Keep reflections brief and focused.
    """
    return f"Reflection recorded: {reflection}"


@tool
def ingest_documents_tool(pdf_file_path: str) -> str:
    """
    Ingest new PDF documents into the shared Chroma vector database.
    
    This tool:
    1. Loads a PDF file from the provided path
    2. Splits it into chunks (1000 chars with 200 char overlap)
    3. Generates OpenAI embeddings
    4. Stores in the existing Chroma database (persists across sessions)
    5. Returns success/failure status with document count
    
    Args:
        pdf_file_path: Absolute path to the PDF file to ingest
        
    Returns:
        Success message with document count, or error message if ingestion fails
        
    IMPORTANT:
    - Uses the same vectorDB as retrieval_tool (persist_directory + collection_name)
    - Call this ONCE per unique PDF to avoid duplicates
    - After ingestion, retrieval_tool will immediately find documents from new PDF
    """
    try:
        # Validate file exists
        pdf_path = Path(pdf_file_path)
        if not pdf_path.exists():
            return f"❌ ERROR: PDF file not found at {pdf_file_path}"
        
        if not pdf_path.suffix.lower() == '.pdf':
            return f"❌ ERROR: File is not a PDF. Expected .pdf, got {pdf_path.suffix}"
        
        # Load PDF
        print(f"📖 Loading PDF: {pdf_path.name}...")
        pdf_loader = PyPDFLoader(str(pdf_path))
        pages = pdf_loader.load()
        
        if not pages:
            return f"❌ ERROR: No content extracted from PDF {pdf_file_path}"
        
        # Split into chunks
        print(f"✂️  Splitting into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        pages_split = text_splitter.split_documents(pages)
        
        # Generate embeddings and store in existing Chroma database
        print(f"🔄 Generating embeddings and storing in vector database...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Add to existing collection (or create if doesn't exist)
        vectorstore = Chroma.from_documents(
            documents=pages_split,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        return (
            f"✅ Successfully ingested '{pdf_path.name}'\n"
            f"   📄 Documents ingested: {len(pages_split)}\n"
            f"   📂 Vector DB: {collection_name}\n"
            f"   💾 Persisted to: {persist_directory}\n"
            f"   🔍 Ready for retrieval_tool queries"
        )
    
    except ImportError as e:
        return f"❌ ERROR: Missing required library. {str(e)}"
    except Exception as e:
        return f"❌ ERROR: Failed to ingest documents. {str(e)}"




