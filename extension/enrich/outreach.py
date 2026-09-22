#!/usr/bin/env python3
"""Stage 5 — build a local worksheet for sending notes by hand.

Joins the shortlist to the enriched records and writes a self-contained HTML
page: one card per lead with their profile link, why they were shortlisted,
and the drafted note. Nothing is sent; the page tracks what you have done and
exports a suppression list when you are finished.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outreach Worksheet</title>
<style>
:root {
  --bg:#fff; --fg:#16181d; --muted:#646b7a; --line:#e3e6eb;
  --accent:#2f6f4f; --accent-fg:#fff; --surface:#f7f8fa; --done:#8a9199;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#14161a; --fg:#e8eaee; --muted:#9aa2b1; --line:#2a2e36;
    --accent:#5aa981; --accent-fg:#0d1512; --surface:#1b1e24; --done:#5b626c;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:32px 16px 80px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--muted);margin:0 0 24px}
.bar{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
  padding:12px 0;margin-bottom:24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:5}
.prog{flex:1;min-width:120px;height:6px;background:var(--surface);border-radius:3px;overflow:hidden}
.prog i{display:block;height:100%;background:var(--accent);width:0;transition:width .2s}
button{font:inherit;padding:7px 14px;border-radius:7px;border:1px solid var(--line);
  background:var(--surface);color:var(--fg);cursor:pointer}
button.primary{background:var(--accent);color:var(--accent-fg);border-color:transparent;font-weight:600}
.card{border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:14px;background:var(--surface)}
.card.done{opacity:.5}
.card.done .name{text-decoration:line-through;color:var(--done)}
.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.name{font-weight:650;font-size:16px;margin:0}
.meta{color:var(--muted);font-size:13px;margin:2px 0 0}
.why{font-size:13px;color:var(--muted);border-left:2px solid var(--line);padding-left:10px;margin:12px 0}
.note{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:12px;
  white-space:pre-wrap;font-size:14px;margin:12px 0 10px}
.count{font-size:12px;color:var(--muted);margin-left:4px}
.count.over{color:#c0392b;font-weight:600}
.acts{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
a.open{display:inline-block;padding:7px 14px;border-radius:7px;background:var(--accent);
  color:var(--accent-fg);text-decoration:none;font-weight:600;font-size:14px}
a.open.alt{background:transparent;color:var(--fg);border:1px solid var(--line)}
label.done-chk{display:flex;align-items:center;gap:6px;color:var(--muted);font-size:13px;margin-left:auto}
.posts{font-size:12px;color:var(--muted);margin-top:10px}
.posts summary{cursor:pointer}
.posts p{border-left:2px solid var(--line);padding-left:10px;margin:8px 0}
@media(max-width:560px){.top{flex-direction:column}label.done-chk{margin-left:0}}
</style></head><body><div class="wrap">
<h1>Outreach Worksheet</h1>
<p class="sub">__COUNT__ leads · notes are drafts — read before sending · nothing here sends itself</p>
<div class="bar">
  <div class="prog"><i id="bar"></i></div>
  <span id="stat" class="count"></span>
  <button id="export">Export contacted.csv</button>
</div>
__CARDS__
</div>
<script>
const KEY='lle-outreach-done';
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY))||{}}catch{return{}}};
const save=s=>{try{localStorage.setItem(KEY,JSON.stringify(s))}catch{}};
let state=load();
const cards=[...document.querySelectorAll('.card')];

function sync(){
  let n=0;
  for(const c of cards){
    const k=c.dataset.key, on=!!state[k];
    c.classList.toggle('done',on);
    c.querySelector('input').checked=on;
    if(on)n++;
  }
  document.getElementById('bar').style.width=(cards.length?n/cards.length*100:0)+'%';
  document.getElementById('stat').textContent=n+' / '+cards.length+' done';
}

for(const c of cards){
  c.querySelector('input').addEventListener('change',e=>{
    state[c.dataset.key]=e.target.checked;
    if(!e.target.checked)delete state[c.dataset.key];
    save(state);sync();
  });
  const btn=c.querySelector('.copy');
  if(btn)btn.addEventListener('click',async()=>{
    try{await navigator.clipboard.writeText(c.querySelector('.note').textContent);
      btn.textContent='Copied';setTimeout(()=>btn.textContent='Copy note',1200);}
    catch{btn.textContent='Select manually';}
  });
}

document.getElementById('export').addEventListener('click',()=>{
  const rows=cards.filter(c=>state[c.dataset.key])
    .map(c=>'"'+c.dataset.url.replace(/"/g,'""')+'"');
  if(!rows.length)return alert('Nothing marked done yet.');
  const csv='\\uFEFF"salesUrl"\\r\\n'+rows.join('\\r\\n')+'\\r\\n';
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  a.download='contacted.csv';a.click();
});
sync();
</script></body></html>
"""

CARD = """<div class="card" data-key="{key}" data-url="{url}">
  <div class="top">
    <div>
      <p class="name">{name}</p>
      <p class="meta">{title}{company}{location}</p>
    </div>
    <label class="done-chk"><input type="checkbox"> sent</label>
  </div>
  {why}
  {note}
  <div class="acts">
    <a class="open" href="{url}" target="_blank" rel="noopener">Open in Sales Navigator</a>
    {public}
    {copy}
  </div>
  {posts}
</div>"""


def esc(value: object) -> str:
    return html.escape(str(value)) if value else ""


def build_card(lead: dict, entry: dict) -> str:
    profile = lead.get("profile") or {}
    company = lead.get("company") or {}
    url = lead.get("salesUrl") or (
        f"https://www.linkedin.com/sales/lead/{lead['profileId']}"
        if lead.get("profileId") else "")

    name = lead.get("fullName") or profile.get("fullName") or "(no name)"
    title = lead.get("currentTitle") or profile.get("headline") or ""
    company_name = company.get("name") or lead.get("companyName") or ""
    size = f" · {company['staffRange']}" if company.get("staffRange") else ""
    location = profile.get("location") or lead.get("location") or ""

    note = entry.get("note") or ""
    note_html = ""
    copy_html = ""
    if note:
        over = " over" if len(note) > 300 else ""
        note_html = (f'<div class="note">{esc(note)}</div>'
                     f'<span class="count{over}">{len(note)} chars'
                     f'{" — over the 300 connection-note limit" if over else ""}</span>')
        copy_html = '<button class="copy">Copy note</button>'

    posts = lead.get("activity") or []
    posts_html = ""
    if posts:
        items = "".join(f"<p>{esc(p.get('text', ''))[:400]}</p>" for p in posts[:3])
        posts_html = (f'<details class="posts"><summary>{len(posts)} recent post(s)</summary>'
                      f'{items}</details>')

    public_url = lead.get("linkedinUrl")
    public_link = (f'<a class="open alt" href="{esc(public_url)}" target="_blank" '
                   f'rel="noopener">LinkedIn profile</a>') if public_url else ""

    return CARD.format(
        public=public_link,
        key=esc(entry.get("key") or url),
        url=esc(url),
        name=esc(name),
        title=esc(title),
        company=f" at {esc(company_name)}{esc(size)}" if company_name else "",
        location=f" · {esc(location)}" if location else "",
        why=f'<div class="why">{esc(entry["reason"])}</div>' if entry.get("reason") else "",
        note=note_html,
        copy=copy_html,
        posts=posts_html,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("shortlist", type=Path, help="shortlist.json from filter pass 2")
    parser.add_argument("-e", "--enriched", type=Path, default=Path("out/leads_flat.json"))
    parser.add_argument("-o", "--output", type=Path, default=Path("outreach.html"))
    args = parser.parse_args()

    flat = json.loads(args.enriched.read_text(encoding="utf-8"))
    leads = flat.get("leads", flat) if isinstance(flat, dict) else flat

    index: dict[str, dict] = {}
    for lead in leads:
        for field in ("profileId", "salesUrn", "memberId", "salesUrl"):
            value = lead.get(field)
            if isinstance(value, str) and value:
                index.setdefault(value, lead)

    entries = json.loads(args.shortlist.read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("leads") or entries.get("shortlist") or []

    cards, missing, skipped = [], 0, 0
    for entry in entries:
        if entry.get("keep") is False:
            skipped += 1
            continue
        lead = index.get(entry.get("key", ""))
        if lead is None:
            missing += 1
            continue
        cards.append(build_card(lead, entry))

    if not cards:
        raise SystemExit("Nothing to write — no shortlist entry matched an enriched lead.")

    args.output.write_text(
        TEMPLATE.replace("__CARDS__", "\n".join(cards)).replace("__COUNT__", str(len(cards))),
        encoding="utf-8")

    print(f"{len(cards)} cards -> {args.output}")
    if skipped:
        print(f"{skipped} entry(s) marked keep:false, omitted")
    if missing:
        print(f"! {missing} shortlist entry(s) matched no enriched lead", flush=True)
    print("\nOpen it, work down the list, tick 'sent' as you go.")
    print("When done: Export contacted.csv -> feed to enrich.py --suppress")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
