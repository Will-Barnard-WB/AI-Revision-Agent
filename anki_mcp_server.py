from fastmcp import FastMCP
import httpx
from typing import List, Dict

ANKI_URL = "http://localhost:8765"

mcp = FastMCP("AnkiConnect MCP Server")

async def anki_req(action: str, params: dict = None):
    """Helper for AnkiConnect calls."""
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    async with httpx.AsyncClient() as client:
        r = await client.post(ANKI_URL, json=payload, timeout=30)
        body = r.json()
        if body.get("error"):
            raise RuntimeError(body["error"])
        return body["result"]

@mcp.tool(description="List all available Anki deck names, including hierarchical decks in 'Parent::Child' format. Call this FIRST before creating cards to check if a deck already exists and to discover the naming convention.")
async def list_decks() -> List[str]:
    """Return a list of all decks."""
    return await anki_req("deckNames")

@mcp.tool(description="Create a new Anki deck. Supports hierarchical naming with '::' (e.g. 'Linear Algebra::Eigenvalues'). Always call list_decks() first to avoid creating duplicates. Returns {success: true/false}.")
async def create_deck(name: str) -> dict:
    """Create a deck; return structured error if it already exists."""
    try:
        await anki_req("createDeck", {"deck": name})
        return {"success": True, "message": f"Deck '{name}' created."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="List all flashcards in an existing deck. Returns front, back, and noteId for each card. Use this for GAP ANALYSIS before generating new cards — compare existing cards against your planned content to avoid duplicates.")
async def list_cards(deck_name: str) -> List[dict]:
    """Return all cards in a deck."""
    # Use the correct AnkiConnect query format: deck:"Deck Name"
    query = f'deck:"{deck_name}"'
    note_ids = await anki_req("findNotes", {"query": query})
    if not note_ids:
        return []
    notes = await anki_req("notesInfo", {"notes": note_ids})
    results = []
    for n in notes:
        fields = n.get("fields", {})
        results.append({
            "noteId": n.get("noteId"),
            "front": fields.get("Front", {}).get("value", ""),
            "back": fields.get("Back", {}).get("value", ""),
        })
    return results

@mcp.tool(description="Add a single flashcard to an EXISTING deck. The deck must already exist (call create_deck first). Automatically rejects exact duplicates. Returns {success: true, note_id} on success, {success: false, skipped: true} for duplicates, or {success: false, error} on failure. Call one at a time for each card.")
async def add_card(deck: str, front: str, back: str) -> Dict:
    """Add a note to a deck; return error if deck doesn't exist or card is a duplicate."""
    params = {
        "note": {
            "deckName": deck,
            "modelName": "Basic",
            "fields": {"Front": front, "Back": back},
            "options": {"allowDuplicate": False},
            "tags": [],
        }
    }
    try:
        note_id = await anki_req("addNote", params)
        return {"success": True, "note_id": note_id}
    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower():
            return {"success": False, "skipped": True, "reason": "duplicate"}
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    
    mcp.run(transport="http", port=8000)
    
