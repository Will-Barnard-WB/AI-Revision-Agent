"""
RAG (Retrieval Augmented Generation) module.

Manages ChromaDB vector stores for multiple document collections.
Each PDF / subject gets its own collection, allowing multi-subject coexistence.
"""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import yaml
import os
import re

load_dotenv()

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

_cfg = _load_config()
_rag_cfg = _cfg.get("rag", {})

persist_directory = os.path.abspath(
    _cfg.get("paths", {}).get("chroma_persist", os.path.dirname(__file__))
)
default_collection = _rag_cfg.get("default_collection")
embedding_model = _rag_cfg.get("embedding_model", "text-embedding-3-small")
chunk_size = _rag_cfg.get("chunk_size", 1000)
chunk_overlap = _rag_cfg.get("chunk_overlap", 200)
retrieval_k = _rag_cfg.get("retrieval_k", 5)

# Legacy alias so existing imports don't break
collection_name = default_collection

# ---------------------------------------------------------------------------
# Collection name utilities
# ---------------------------------------------------------------------------

def collection_name_from_filename(filename: str) -> str:
    """Derive a safe ChromaDB collection name from a PDF filename.

    Examples
    --------
    >>> collection_name_from_filename("Linear Algebra Notes.pdf")
    'linear_algebra_notes'
    >>> collection_name_from_filename("MT2505-Eigenvalues.pdf")
    'mt2505_eigenvalues'
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    # ChromaDB requires collection names 3-63 chars, starting with alphanumeric
    if len(name) < 3:
        name = name + "_col"
    return name[:63]


def list_collections() -> list[str]:
    """Return names of all existing ChromaDB collections."""
    import chromadb
    client = chromadb.PersistentClient(path=persist_directory)
    return [c.name for c in client.list_collections()]


# ---------------------------------------------------------------------------
# Retriever cache  (collection_name -> retriever)
# ---------------------------------------------------------------------------

_retrievers: dict = {}


def get_retriever(coll_name: str | None = None):
    """Get a retriever for a given collection.

    Parameters
    ----------
    coll_name : str, optional
        The ChromaDB collection to query. Must be provided explicitly.

    Returns
    -------
    A LangChain retriever backed by the specified Chroma collection.
    """
    coll = coll_name
    if not coll:
        raise ValueError("Collection name is required for get_retriever().")
    if coll not in _retrievers:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        vectorstore = Chroma(
            persist_directory=persist_directory,
            collection_name=coll,
            embedding_function=embeddings,
        )
        _retrievers[coll] = vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": retrieval_k}
        )
    return _retrievers[coll]


def setup_retriever(pdf_path: str, coll_name: str | None = None):
    """Ingest a PDF and return a retriever for the new collection.

    Parameters
    ----------
    pdf_path : str
        Absolute path to the PDF to ingest.
    coll_name : str, optional
        Target collection name. If *None*, one is derived from the filename.

    Returns
    -------
    A LangChain retriever for the newly created / updated collection.
    """
    coll = coll_name or collection_name_from_filename(pdf_path)
    embeddings = OpenAIEmbeddings(model=embedding_model)

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=coll,
    )
    print(f"✅ Vector store '{coll}' created with {len(chunks)} chunks")

    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": retrieval_k}
    )
    _retrievers[coll] = retriever
    return retriever
