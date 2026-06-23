#!/usr/bin/env bash
# Daily sync wrapper — called by cron. Logs to scripts/sync.log.
# Uses the venv python so no system packages are needed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$SCRIPT_DIR/.venv/bin/python"
LOG="$SCRIPT_DIR/sync.log"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') sync start ====="
  "$VENV_PY" "$SCRIPT_DIR/sync_reports_to_sheet.py"
  "$VENV_PY" "$SCRIPT_DIR/format_sheet.py" || echo "(format step skipped)"
  echo "===== sync done ====="
} >> "$LOG" 2>&1
