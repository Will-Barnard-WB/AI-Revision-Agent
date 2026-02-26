#!/bin/bash
set -euo pipefail

PLIST_NAME="com.revisionagent.ambient"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/${PLIST_NAME}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

usage() {
  echo "Usage: $0 {install|uninstall|status|logs}"
  echo ""
  echo "  install   — Install and start the ambient cron daemon"
  echo "  uninstall — Stop and remove the daemon"
  echo "  status    — Check if it's running"
  echo "  logs      — Tail the ambient logs"
  exit 1
}

check_env_file() {
  ENV_FILE="$(cd "$(dirname "$0")" && pwd)/.env"
  if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ No .env file found at $ENV_FILE${NC}"
    echo "  Create one with:  echo 'OPENAI_API_KEY=sk-...' > $ENV_FILE"
    exit 1
  fi
  if ! grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
    echo -e "${YELLOW}⚠  .env exists but has no OPENAI_API_KEY${NC}"
    echo "  Add it:  echo 'OPENAI_API_KEY=sk-...' >> $ENV_FILE"
    exit 1
  fi
  echo -e "${GREEN}✓${NC} .env file found with OPENAI_API_KEY"
}

do_install() {
  echo "Installing ambient cron daemon…"
  echo ""

  # Check python
  if ! /opt/homebrew/bin/python3.11 -c "import yaml, chromadb, langchain_openai" 2>/dev/null; then
    echo -e "${RED}✗ Missing Python dependencies. Run:${NC}"
    echo "  /opt/homebrew/bin/python3.11 -m pip install pyyaml chromadb langchain-openai"
    exit 1
  fi

  # Unload if already loaded
  launchctl bootout "gui/$(id -u)/${PLIST_NAME}" 2>/dev/null || true

  # Check .env
  check_env_file

  # Copy plist
  mkdir -p "$HOME/Library/LaunchAgents"
  cp "$PLIST_SRC" "$PLIST_DST"
  echo -e "${GREEN}✓${NC} Plist copied to $PLIST_DST"

  # Load and start
  launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
  echo -e "${GREEN}✓${NC} Daemon loaded and started"
  echo ""
  echo -e "${GREEN}🔄 Ambient agent is now running in the background!${NC}"
  echo "   It will watch agent_fs/lectures/ for new PDFs every 5 minutes."
  echo "   It survives terminal closures and restarts on login."
  echo ""
  echo "   Check status:   $0 status"
  echo "   View logs:      $0 logs"
  echo "   Uninstall:      $0 uninstall"
}

do_uninstall() {
  echo "Uninstalling ambient cron daemon…"
  launchctl bootout "gui/$(id -u)/${PLIST_NAME}" 2>/dev/null || true
  rm -f "$PLIST_DST"
  echo -e "${GREEN}✓${NC} Daemon stopped and plist removed"
}

do_status() {
  if launchctl print "gui/$(id -u)/${PLIST_NAME}" &>/dev/null; then
    PID=$(launchctl print "gui/$(id -u)/${PLIST_NAME}" 2>/dev/null | grep -m1 "pid" | awk '{print $3}')
    echo -e "${GREEN}● Running${NC}  (PID: ${PID:-unknown})"
  else
    echo -e "${RED}○ Not running${NC}"
  fi
}

do_logs() {
  LOG_DIR="$(cd "$(dirname "$0")" && pwd)/agent_fs/memory"
  echo "=== Ambient JSONL log (last 20 entries) ==="
  if [ -f "$LOG_DIR/.ambient_log.jsonl" ]; then
    tail -20 "$LOG_DIR/.ambient_log.jsonl"
  else
    echo "(no log entries yet)"
  fi
  echo ""
  echo "=== Stdout log ==="
  if [ -f "$LOG_DIR/.ambient_stdout.log" ]; then
    tail -20 "$LOG_DIR/.ambient_stdout.log"
  else
    echo "(empty)"
  fi
  echo ""
  echo "=== Stderr log ==="
  if [ -f "$LOG_DIR/.ambient_stderr.log" ]; then
    tail -20 "$LOG_DIR/.ambient_stderr.log"
  else
    echo "(empty)"
  fi
}

case "${1:-}" in
  install)   do_install ;;
  uninstall) do_uninstall ;;
  status)    do_status ;;
  logs)      do_logs ;;
  *)         usage ;;
esac
