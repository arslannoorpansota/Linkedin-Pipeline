"""Fetch each company's public site and pull the signals the triage needs.

No LinkedIn involved: WEBSITE_GAP_TRIAGE asks whether their site shows work we
could do, and that is on the open web.
"""
import csv, json, re, sys, concurrent.futures as cf
import urllib.request, urllib.error, ssl

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/131.0 Safari/537.36')
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Things that mean they already ship software, or already have builders.
BUILDER = re.compile(r'\b(careers?|we.re hiring|join our team|engineering team|'
                     r'our engineers|developer|cto\b|chief technology)\b', re.I)
APPISH = re.compile(r'\b(app store|google play|download the app|log ?in|sign ?up|'
                    r'dashboard|patient portal|book (?:a demo|online)|api|platform)\b', re.I)
BUILT_WITH = re.compile(r'(wix|squarespace|godaddy|wordpress|webflow|shopify|carrd)', re.I)

def fetch(url, timeout=12):
    if not url.startswith('http'): url = 'https://' + url
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read(400_000)
        return r.status, r.geturl(), raw.decode('utf-8', 'replace')

def analyse(row):
    url = row['website']
    out = {**row, 'httpStatus': '', 'finalUrl': '', 'title': '', 'builtWith': '',
           'hasCareers': '', 'appSignals': '', 'siteWords': '', 'fetchError': ''}
    if not url:
        out['fetchError'] = 'no website on file'
        return out
    try:
        status, final, body = fetch(url)
    except Exception as e:
        out['fetchError'] = f'{type(e).__name__}: {e}'[:120]
        return out
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', body, flags=re.S|re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    out['httpStatus'] = status
    out['finalUrl'] = final
    out['title'] = (re.search(r'<title[^>]*>(.*?)</title>', body, re.S|re.I) or [None,''])[1].strip()[:120]
    out['builtWith'] = ','.join(sorted(set(m.lower() for m in BUILT_WITH.findall(body))))
    out['hasCareers'] = 'yes' if BUILDER.search(text) else ''
    out['appSignals'] = ','.join(sorted(set(m.lower() for m in APPISH.findall(text)))[:6])
    out['siteWords'] = str(len(text.split()))
    return out

rows = list(csv.DictReader(open('data/to_rate.csv', encoding='utf-8-sig')))
done = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for i, r in enumerate(ex.map(analyse, rows), 1):
        done.append(r)
        if i % 15 == 0: print(f'  {i}/{len(rows)}', flush=True)

with open('data/site_scan.csv','w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(done[0])); w.writeheader(); w.writerows(done)

ok = sum(1 for x in done if x['httpStatus'] == 200)
print(f'\nfetched ok : {ok}/{len(done)}')
print(f'errors     : {sum(1 for x in done if x["fetchError"])}')
