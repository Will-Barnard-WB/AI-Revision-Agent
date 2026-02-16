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

load_dotenv()

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




@tool
def add_anki_notes(topic: str,qa_pairs: List[Dict[str, str]], parent_deck: str = "Linear Algebra", model_name: str = "Basic") -> str:
    '''
    Add Q/A pairs as Anki notes under a topic subdeck.
    '''
    
    if not qa_pairs:
        return "No Q/A pairs provided. Nothing was added."

    deck_name = f"{parent_deck}::{topic}"

    try:
        requests.post(
            os.getenv("ANKI_CONNECT_URL", "http://localhost:8765"),
            json={"action": "createDeck", "version": 5, "params": {"deck": deck_name}},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        return f"Failed to create deck {deck_name}: {e}"

    anki_notes = []
    for qa in qa_pairs:
        if "front" not in qa or "back" not in qa:
            return "Invalid Q/A pair format. Each must have 'front' and 'back'."
        anki_notes.append({
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {"Front": qa["front"], "Back": qa["back"]},
            "tags": ["auto_generated", "rag"]
        })

    try:
        response = requests.post(
            os.getenv("ANKI_CONNECT_URL", "http://localhost:8765"),
            json={"action": "addNotes", "version": 5, "params": {"notes": anki_notes}},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        return f"Failed to connect to AnkiConnect: {e}"

    if result.get("error") is not None:
        return f"AnkiConnect error: {result['error']}"

    added_count = len([r for r in result.get("result", []) if r is not None])
    return f"Successfully added {added_count} flashcards to '{deck_name}'."



