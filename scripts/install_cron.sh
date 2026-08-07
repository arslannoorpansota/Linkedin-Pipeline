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

# Cadence reminder — weekday mornings (09:00 Mon–Fri): refresh the
# "Cadence Reminders" tab with every lead whose touch is due/overdue.
VENV_PY="$SCRIPT_DIR/.venv/bin/python"
REMIND_LINE="0 9 * * 1-5 $VENV_PY $SCRIPT_DIR/cadence_reminder.py >> $SCRIPT_DIR/sync.log 2>&1"
RMARK="# electrocom-cadence-reminder"

# Remove any prior version of our jobs, then add the new ones.
# (|| true guards against grep exit 1 / empty crontab under `set -e`.)
EXISTING="$(crontab -l 2>/dev/null | grep -v "$MARK" | grep -v "$RMARK" || true)"
printf '%s\n%s\n%s\n' "$EXISTING" "$CRON_LINE $MARK" "$REMIND_LINE $RMARK" | grep -v '^$' | crontab -

echo "Installed cron jobs:"
crontab -l | grep -E "$MARK|$RMARK"
echo
echo "Logs: $SCRIPT_DIR/sync.log"
echo "To remove:  crontab -l | grep -vE '$MARK|$RMARK' | crontab -"
