from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

persist_directory = "/Users/willbarnard/Documents/RevisionAgent"
collection_name = "linear_algebra_notes"

def setup_retriever():
    """Create the vector store from PDF - run this once"""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    pdf_path = "LinearAlgebraNotes.pdf"
    pdf_loader = PyPDFLoader(pdf_path)
    pages = pdf_loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    pages_split = text_splitter.split_documents(pages)
    
    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    print(f"Vector store created with {len(pages_split)} documents")
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

_retriever = None

def get_retriever():
    """Get retriever - loads from existing database"""
    global _retriever
    if _retriever is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_function=embeddings
        )
        _retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    return _retriever
