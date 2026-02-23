#!/bin/bash
# Start both servers for local development/testing.
# Usage: ./dev.sh
# Ctrl+C stops both.

PYTHON=/opt/homebrew/bin/python3.11
DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill "$ANKI_PID" "$SERVER_PID" 2>/dev/null
    wait "$ANKI_PID" "$SERVER_PID" 2>/dev/null
    echo "Done."
}
trap cleanup INT TERM

echo "Starting Anki MCP server on :8000..."
"$PYTHON" "$DIR/anki_mcp_server.py" &
ANKI_PID=$!

sleep 1

echo "Starting web server on :8080..."
"$PYTHON" -m uvicorn server:app --host 0.0.0.0 --port 8080 --app-dir "$DIR" &
SERVER_PID=$!

echo ""
echo "  Anki MCP : http://localhost:8000"
echo "  Web UI   : http://localhost:8080"
echo ""
echo "Ctrl+C to stop both."

wait "$SERVER_PID"
