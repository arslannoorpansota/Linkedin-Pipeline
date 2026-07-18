#!/usr/bin/env python3
"""One-time Google OAuth re-authorization for the BD Pipeline sheet.

Run this when sheet writes fail with 'invalid_grant: Token has been expired or revoked'.
It opens a browser, you approve as the SHEET OWNER (alifaizanblackia@gmail.com),
and it writes a fresh scripts/token.json.

    scripts/.venv/bin/python scripts/reauth.py
"""
import os, shutil, sys
from datetime import datetime, timezone
from google_auth_oauthlib.flow import InstalledAppFlow

HERE = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(HERE, "credentials.json")
TOKEN = os.path.join(HERE, "token.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

if not os.path.exists(CREDS):
    sys.exit("ERROR: scripts/credentials.json not found — can't run the OAuth flow.")

# back up the dead token
if os.path.exists(TOKEN):
    shutil.copy2(TOKEN, TOKEN + ".bak")
    print("backed up old token -> token.json.bak")

flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
try:
    # opens a browser on this machine and captures the redirect automatically
    creds = flow.run_local_server(port=0, prompt="consent")
except Exception as e:
    print("run_local_server failed (%s); falling back to manual URL." % e)
    auth_url, _ = flow.authorization_url(prompt="consent")
    print("\nOpen this URL, approve as the sheet owner, paste the code back:\n\n" + auth_url + "\n")
    code = input("Authorization code: ").strip()
    flow.fetch_token(code=code)
    creds = flow.credentials

with open(TOKEN, "w") as f:
    f.write(creds.to_json())
os.chmod(TOKEN, 0o600)
print("\nOK: fresh token.json written at", datetime.now(timezone.utc).isoformat())
print("Sign in was for the account that OWNS the sheet (alifaizanblackia@gmail.com).")
