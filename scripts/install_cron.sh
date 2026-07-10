#!/usr/bin/env bash
# Install a daily cron job that syncs reports -> Google Sheet.
# Default: every day at 21:00 (9pm). Override with: ./install_cron.sh "30 22"
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER="$SCRIPT_DIR/run_daily_sync.sh"
SCHEDULE="${1:-0 21}"   # "minute hour" — default 21:00

chmod +x "$WRAPPER"

CRON_LINE="$SCHEDULE * * * $WRAPPER"
MARK="# electrocom-bd-sheet-sync"

# Remove any prior version of our job, then add the new one.
# (|| true guards against grep exit 1 / empty crontab under `set -e`.)
EXISTING="$(crontab -l 2>/dev/null | grep -v "$MARK" || true)"
printf '%s\n%s\n' "$EXISTING" "$CRON_LINE $MARK" | grep -v '^$' | crontab -

echo "Installed cron job:"
crontab -l | grep "$MARK"
echo
echo "Logs: $SCRIPT_DIR/sync.log"
echo "To remove:  crontab -l | grep -v '$MARK' | crontab -"
