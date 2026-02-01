from typing import List, Dict
from dotenv import load_dotenv
import requests
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# Load environment variables
load_dotenv()

# --- LLM and Embeddings ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# --- Load PDF and split into chunks ---
pdf_path = "LinearAlgebraNotes.pdf"
pdf_loader = PyPDFLoader(pdf_path)
pages = pdf_loader.load()
print(f"PDF loaded: {len(pages)} pages")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
pages_split = text_splitter.split_documents(pages)

# --- Chroma vector store ---
persist_directory = "/Users/willbarnard/Documents/RevisionAgent"
collection_name = "linear_algebra_notes"

vectorstore = Chroma.from_documents(
    documents=pages_split,
    embedding=embeddings,
    persist_directory=persist_directory,
    collection_name=collection_name
)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# --- Tools ---
@tool
def retrieval_tool(query: str) -> str:
    """Retrieve relevant content from the Linear Algebra Notes."""
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant information found in the notes."
    results = [f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
    return "\n\n".join(results)


ANKI_CONNECT_URL = "http://localhost:8765"

@tool
def add_anki_notes(
    topic: str,
    qa_pairs: List[Dict[str, str]],
    parent_deck: str = "Linear Algebra",
    model_name: str = "Basic"
) -> str:
    """Add Q/A pairs as Anki notes under a topic subdeck."""
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


# --- Agent setup ---
tools = [retrieval_tool, add_anki_notes]

system_prompt = """
You are a revision-question generation and Anki persistence agent.

PHASE 1 — Retrieval:
- User provides a TOPIC.
- Call retrieval_tool with the topic.

PHASE 2 — Question Generation:
- From the retrieved notes, generate high-quality Q/A pairs suitable for Anki.
- Questions should be concise and clear.
- Each Q/A pair should be:
  {"front": "<question>", "back": "<answer>"}

PHASE 3 — Persistence:
- Write the Q/A pairs to Anki using add_anki_notes.
- Use the following call format exactly:
    add_anki_notes call_<ID>
    topic: "<topic>"
    parent_deck: "Linear Algebra"
    model_name: "Basic"
    qa_pairs: <qa_pairs>
- If qa_pairs is empty, do NOT call add_anki_notes; instead, return a short warning message stating that no Q/A pairs could be generated.

Rules:
- Only call tools, do not provide raw answers.
- Avoid duplicates.
- Use default deck: "Linear Algebra" and model: "Basic".
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

# --- Agent loop ---
conversation_history = []

agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: eigenvalues."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: the first isomorphism theorem."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: quotient spaces."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: symmetric bilinear forms."}})
agent.invoke({"messages": {"role": "user", "content": f"Generate revision questions on the topic: maximum likelihood estimators."}})


