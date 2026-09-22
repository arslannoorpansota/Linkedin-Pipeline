#!/usr/bin/env bash
# One command for the whole pipeline. Run it as often as you like: it works out
# what has been done, does whatever it can, and tells you the single next step.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA="$ROOT/data"
DL="${DOWNLOADS:-$HOME/Downloads}"
mkdir -p "$DATA"

B=$'\033[1m'; D=$'\033[2m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; X=$'\033[0m'

step()  { printf '\n%s%s%s\n' "$B" "$*" "$X"; }
ok()    { printf '  %s✓%s %s\n' "$G" "$X" "$*"; }
info()  { printf '  %s%s%s\n' "$D" "$*" "$X"; }
warn()  { printf '  %s!%s %s\n' "$Y" "$X" "$*"; }

next() {
  printf '\n%s──────────────────────────────────────────────%s\n' "$D" "$X"
  printf '%sNEXT:%s %s\n' "$B" "$X" "$1"
  shift
  for line in "$@"; do printf '      %s\n' "$line"; done
  printf '\n%sThen run ./run.sh again.%s\n\n' "$D" "$X"
  exit 0
}

count_csv() {
  python3 -c "import csv,sys
try: print(sum(1 for _ in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))))
except Exception: print(0)" "$1" 2>/dev/null || echo 0
}

# ── 1. leads from the extension ────────────────────────────────────────────
if [ ! -f "$DATA/leads.csv" ]; then
  newest=$(ls -t "$DL"/leads-*.csv 2>/dev/null | head -1)
  if [ -z "$newest" ]; then
    next "Collect some leads." \
      "1. Open a Sales Navigator search in Chrome." \
      "2. Open the Lead Collector extension." \
      "3. Press Start collecting, wait for it to finish." \
      "4. Press Download leads."
  fi
  mv "$newest" "$DATA/leads.csv"
  newest_json=$(ls -t "$DL"/leads-*.json 2>/dev/null | head -1)
  [ -n "$newest_json" ] && mv "$newest_json" "$DATA/leads.json"
fi

step "1. Leads collected"
ok "$(count_csv "$DATA/leads.csv") leads in data/leads.csv"

# ── 2. filtered by Claude ──────────────────────────────────────────────────
if [ ! -f "$DATA/leads_filtered.csv" ]; then
  next "Pick the ones worth contacting." \
    "Open Claude Code here and say:" \
    "" \
    "  ${B}Filter data/leads.csv using FILTER_PROMPT.md.${X}" \
    "  ${B}My ideal customer is: <describe them>${X}" \
    "" \
    "It writes data/leads_filtered.csv when it's done."
fi

step "2. Leads filtered"
kept=$(count_csv "$DATA/leads_filtered.csv")
ok "$kept kept out of $(count_csv "$DATA/leads.csv")"

if [ -f "$DATA/decisions.json" ]; then
  if python3 "$ROOT/enrich/check_filter.py" "$DATA/leads.csv" \
       "$DATA/leads_filtered.csv" -d "$DATA/decisions.json" >/dev/null 2>&1; then
    ok "every lead accounted for"
  else
    warn "some leads are unaccounted for — details:"
    python3 "$ROOT/enrich/check_filter.py" "$DATA/leads.csv" \
      "$DATA/leads_filtered.csv" -d "$DATA/decisions.json" 2>&1 | sed 's/^/      /'
  fi
fi

# ── 3. look them up ────────────────────────────────────────────────────────
need_enrich=1
if [ -f "$DATA/out/leads.json" ]; then
  done_n=$(python3 -c "import json,sys
d=json.load(open(sys.argv[1]))['records']
print(sum(1 for v in d.values() if v.get('stage')=='enriched'))" "$DATA/out/leads.json" 2>/dev/null || echo 0)
  [ "$done_n" -ge "$kept" ] && need_enrich=0
fi

if [ "$need_enrich" = 1 ]; then
  if [ ! -f "$ROOT/enrich/.env" ]; then
    next "Give the tool your LinkedIn session so it can look people up." \
      "1. cp enrich/.env.example enrich/.env" \
      "2. In Chrome on linkedin.com, open Cookie-Editor." \
      "3. Copy the values of ${B}li_at${X} and ${B}JSESSIONID${X} into that file."
  fi
  step "3. Looking up profiles and companies"
  info "this is the slow part — roughly 6 seconds per lead"
  leads_arg=()
  [ -f "$DATA/leads.json" ] && leads_arg=(--leads "$DATA/leads.json")
  ( cd "$ROOT/enrich" && python3 enrich.py "$DATA/leads_filtered.csv" \
      "${leads_arg[@]}" -o "$DATA/out" --activity "$@" ) || {
        printf '\n%sStopped. Everything so far is saved — run ./run.sh again later.%s\n\n' "$Y" "$X"
        exit 2; }
else
  step "3. Profiles looked up"
  ok "$done_n leads enriched"
fi

# ── 4. shortlist + notes ───────────────────────────────────────────────────
if [ ! -f "$DATA/shortlist.json" ]; then
  next "Choose who to message." \
    "Open Claude Code here and say:" \
    "" \
    "  ${B}Shortlist data/out/leads_flat.json using OUTREACH_PROMPT.md.${X}" \
    "" \
    "It writes data/shortlist.json with a note for each person."
fi

step "4. Shortlist ready"

# ── 5. worksheet ───────────────────────────────────────────────────────────
step "5. Building your worksheet"
( cd "$ROOT/enrich" && python3 outreach.py "$DATA/shortlist.json" \
    -e "$DATA/out/leads_flat.json" -o "$DATA/outreach.html" ) || exit 1
command -v xdg-open >/dev/null && xdg-open "$DATA/outreach.html" >/dev/null 2>&1 &

printf '\n%s──────────────────────────────────────────────%s\n' "$D" "$X"
printf '%sAll done.%s Your worksheet is open in the browser.\n' "$B" "$X"
printf '      Work down the list, tick each one off as you send it.\n'
printf '      When finished, press Export contacted.csv so those people\n'
printf '      are skipped next time.\n\n'
