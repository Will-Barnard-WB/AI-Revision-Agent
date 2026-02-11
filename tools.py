import subprocess
import shlex
from langchain_core.tools import tool
from RAG import retriever
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
def thinking_tool(tasks: str, reasoning : str, tool_calls: list ) -> dict:
    """
    This tool is used for the agent's internal reasoning and planning. It should return a structured To-Do list and the next tool calls.
    The agent must call this tool before any other tool to plan its actions.
    The output should include:
1. A numbered To-Do list of all steps the agent plans to take,
2. A clear explanation of the agent's thought process and reasoning behind the plan.
3. A list of the next tool calls to execute, with their parameters, in the exact order they should be called.
    The agent should use this tool iteratively after each tool execution to update its plan and ensure it is on track to complete the task efficiently and correctly.
    """
    return (tasks, reasoning, tool_calls)

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



