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

@mcp.tool( description="List all available Anki deck names, including hierarchical decks in 'Parent::Child' format.")
async def list_decks() -> List[str]:
    """Return a list of all decks."""
    return await anki_req("deckNames")

@mcp.tool(description="Create a new Anki deck with the given name. Supports hierarchical structure using '::'. Returns structured result.")
async def create_deck(name: str) -> dict:
    """Create a deck; return structured error if it already exists."""
    try:
        await anki_req("createDeck", {"deck": name})
        return {"success": True, "message": f"Deck '{name}' created."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="List all flashcards in an existing deck. Returns the front, back, and note ID for each card.")
async def list_cards(deck_name: str) -> List[dict]:
    """Return all cards in a deck."""
    note_ids = await anki_req("findNotes", {"query": f"deck:{deck_name}"})
    if not note_ids:
        return []
    notes = await anki_req("notesInfo", {"notes": note_ids})
    results = []
    for n in notes:
        fields = n["fields"]
        results.append({
            "noteId": n["noteId"],
            "front": fields["Front"]["value"],
            "back": fields["Back"]["value"],
        })
    return results

@mcp.tool(description="Add a flashcard to an EXISTING Anki deck. Returns structured success/error.")
async def add_card(deck: str, front: str, back: str) -> Dict:
    """Add a note to a deck; return error if deck doesn't exist."""
    params = {
        "note": {
            "deckName": deck,
            "modelName": "Basic",
            "fields": {"Front": front, "Back": back},
            "options": {"allowDuplicate": True},
            "tags": [],
        }
    }
    try:
        note_id = await anki_req("addNote", params)
        return {"success": True, "note_id": note_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
