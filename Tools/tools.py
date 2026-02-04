from langchain_core.tools import tool
from Database.RAG import retriever
from dotenv import load_dotenv
from typing import List, Dict
import os
import requests

load_dotenv()

@tool
def retrieval_tool(query: str) -> str:
    '''
    This tool searches and returns the information from the Linear Algebra Notes document.
    '''

    docs = retriever.invoke(query)

    if not docs:
        return "I found no relevant information in the Linear Algebra Notes document."
    
    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i+1}:\n{doc.page_content}")

    return "\n\n".join(results)

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
