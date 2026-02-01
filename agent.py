from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
import json
import re
from datetime import datetime


load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini", temperature = 0)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
)

pdf_path = "LinearAlgebraNotes.pdf"

pdf_loader = PyPDFLoader(pdf_path)

try:
    pages = pdf_loader.load()
    print(f"PDF has been loaded and has {len(pages)} pages")
except Exception as e:
    print(f"Error loading PDF: {e}")
    raise

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200

)

pages_split = text_splitter.split_documents(pages)

persist_directory = r"/Users/willbarnard/Documents/RevisionAgent"
collection_name = "linear_algebra_notes"

try:
    vectorstore = Chroma.from_documents(
        documents=pages_split,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    print(f"Create ChromDB vector store!")
except Exception as e:
    print(f"Error setting up ChromaDB: {str(e)}")
    raise

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

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


import requests
from typing import List, Dict
from langchain_core.tools import tool


ANKI_CONNECT_URL = "http://localhost:8765"  # default AnkiConnect URL

@tool
def add_anki_notes(
    topic: str,
    qa_pairs: List[Dict[str, str]],
    parent_deck: str = "Linear Algebra",
    model_name: str = "Basic"
) -> str:
    """
    Adds multiple flashcards to Anki under a subdeck named after the topic.

    Args:
        topic: The user's revision topic.
        qa_pairs: List of {"front": "...", "back": "..."} dictionaries.
        parent_deck: Parent deck to create the subdeck under (default "Linear Algebra").
        model_name: Anki note model to use (default "Basic").

    Returns:
        A summary string.
    """
    if not qa_pairs:
        return "No Q/A pairs provided. Nothing was added."

    deck_name = f"{parent_deck}::{topic}"

    # Create deck if it doesn't exist
    try:
        requests.post(
            ANKI_CONNECT_URL,
            json={"action": "createDeck", "version": 5, "params": {"deck": deck_name}},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        return f"Failed to create deck {deck_name}: {e}"

    # Prepare notes
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

    # Add notes via AnkiConnect
    try:
        response = requests.post(
            ANKI_CONNECT_URL,
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
     
tools = [retrieval_tool, add_anki_notes]

llm = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def should_continue(state: AgentState):
    '''Check if the last message contains tool calls.'''
    result = state['messages'][-1]
    return bool(getattr(result, "tool_calls", []))


system_prompt = system_prompt = """
You are a revision-question generation and Anki persistence agent.

Your responsibilities occur in THREE phases:

PHASE 1 — Retrieval
- The user provides a TOPIC.
- You MUST call retrieval_tool with the topic.
- You may not use outside knowledge.

PHASE 2 — Question Generation
- From the retrieved lecture notes, generate high-quality revision-style
  Question/Answer pairs.
- Questions should be suitable for Anki flashcards.
- Answers must be concise and unambiguous.
- Use precise mathematical language.
- Avoid multi-part questions.

PHASE 3 — Persistence to Anki
- After generating valid Q/A pairs, you MUST write them to Anki
  using the add_anki_notes tool.
- You must convert each Q/A pair into:
  {
    "front": "<question>",
    "back": "<answer>"
  }

Rules for writing to Anki:
- Only write if at least ONE high-quality Q/A pair exists.
- Never invent deck names or model names.
- Use the following defaults unless instructed otherwise:
  - deck_name: "Linear Algebra"
  - model_name: "Basic"
- Do NOT write duplicate or near-duplicate cards.

Output rules:
- When calling tools, return ONLY the tool call.
- After all tools are executed, return a short confirmation message
  summarizing what was added.
- Do NOT include JSON unless calling a tool.
"""

tools_dict = {our_tool.name: our_tool for our_tool in tools}

def call_llm(state: AgentState) -> AgentState:
    '''Function to call the LLM with the current state.'''

    messages = list(state['messages'])
    messages = [SystemMessage(content=system_prompt)] + messages
    message = llm.invoke(messages)
    return {'messages': [message]}



def take_action(state: AgentState) -> AgentState:
    """Execute tool calls from the LLM's response."""

    tool_calls = state['messages'][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"Calling Tool: {t['name']} with query: {t['args'].get('query', 'No query provided')}")
        
        if not t['name'] in tools_dict: # Checks if a valid tool is present
            print(f"\nTool: {t['name']} does not exist.")
            result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
        
        else:
            result = tools_dict[t['name']].invoke(t['args'])
            print(f"Result length: {len(str(result))}")
            

        # Appends the Tool Message
        results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

    print("Tools Execution Complete. Back to the model!")
    return {'messages': results}


graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("retriever_agent", take_action)

graph.add_conditional_edges(
    "llm",
    should_continue,
    {True: "retriever_agent", False: END}
)
graph.add_edge("retriever_agent", "llm")
graph.set_entry_point("llm")

rag_agent = graph.compile()


conversation_history = []

def running_agent():
    print("\n=== RAG AGENT===")
    
    while True:
        user_input = input("\nWhat is your revision topic/s: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        conversation_history.append(HumanMessage(content=f"Generate revision questions on the topic: {user_input}"))

        result = rag_agent.invoke({"messages": conversation_history})

        new_messages = result['messages'][len(conversation_history):]
        conversation_history.extend(new_messages)
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)


running_agent()
