# Daily Reports → Google Sheet Sync

Automatically parses `reports/YYYY-MM-DD.md` and pushes lead touchpoints into the
**ElectroCom BD Pipeline** Google Sheet every day.

- **Lead entries** (DM, Email, Follow-Up, Lead Research) → one row each on the **Pipeline** tab, mapped to `sheets/SCHEMA.md` columns.
- **Every entry** (incl. Profile Setup / Assets / Infra) → one row on the **Activity Log** tab, so "all the data" lands somewhere.
- **Idempotent:** a state file (`.sheet_sync_state.json`) tracks what's already pushed, keyed by `date|agent|target`. Running daily only appends *new* entries — no duplicates.

---

## One-time setup (~10 min)

You chose **OAuth (your own Google login)**, so the sync writes to a sheet in *your* Drive.

### 1. Create an OAuth client in Google Cloud
1. Go to <https://console.cloud.google.com/> → create a project (or pick one).
2. **APIs & Services → Library →** enable **Google Sheets API** and **Google Drive API**.
3. **APIs & Services → OAuth consent screen →** User type **External** → fill app name + your email → add yourself under **Test users**. (No need to publish/verify; test mode is fine.)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID →** Application type **Desktop app**.
5. **Download JSON** and save it here as:

   ```
   scripts/credentials.json
   ```

### 2. First run (one-time browser consent)
```bash
# Run from the repo root
scripts/.venv/bin/python scripts/sync_reports_to_sheet.py
```
A browser opens → log in → "Allow". A `token.json` is cached (refreshes itself after this, so cron runs are silent).

On first run it **creates** the "ElectroCom BD Pipeline" spreadsheet in your Drive, writes the headers, pushes all current entries, and prints the sheet URL. The id is saved to `scripts/sheet_config.json`.

> Already have a sheet you want to use instead? Put its id in `scripts/sheet_config.json`:
> `{ "spreadsheet_id": "1AbC...the-long-id-from-the-url..." }`

### 3. Turn on the daily automation
```bash
scripts/install_cron.sh          # runs every day at 21:00
scripts/install_cron.sh "30 22"  # or a custom "minute hour"
```
That's it — new report entries flow into the sheet automatically each evening.

---

## Manual / handy commands
```bash
# Dry run — parse + print rows, no auth, no write:
scripts/.venv/bin/python scripts/sync_reports_to_sheet.py --dry-run

# Sync now:
scripts/.venv/bin/python scripts/sync_reports_to_sheet.py

# Just one day:
scripts/.venv/bin/python scripts/sync_reports_to_sheet.py --date 2026-06-22

# Re-authorize (e.g. token revoked):
scripts/.venv/bin/python scripts/sync_reports_to_sheet.py --reauth
```

Cron logs: `scripts/sync.log`.

---

## Files
| File | What |
|---|---|
| `sync_reports_to_sheet.py` | Parser + Sheets sync (idempotent) |
| `run_daily_sync.sh` | Cron wrapper (logs to `sync.log`) |
| `install_cron.sh` | Installs/updates the daily cron job |
| `credentials.json` | **You provide** — OAuth desktop client (git-ignored) |
| `token.json` | Auto — cached login (git-ignored) |
| `sheet_config.json` | Auto — stores spreadsheet id/url (git-ignored) |
| `.sheet_sync_state.json` | Auto — dedup state (git-ignored) |
| `.venv/` | Python env with Google API libs (git-ignored) |

> **Never commit** `credentials.json`, `token.json`, or `sheet_config.json` — they're secrets. See `.gitignore`.
