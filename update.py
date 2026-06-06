#!/usr/bin/env python3
"""
Päivittää kokoelman JA diskografian Discogsista.
Käyttö: python3 update.py TOKEN [käyttäjänimi]
"""
import sys, json, time, urllib.request, os
from datetime import datetime

TOKEN    = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DISCOGS_TOKEN')
USERNAME = sys.argv[2] if len(sys.argv) > 2 else None
OASIS_ID = 140140

if not TOKEN:
    print("VIRHE: Anna token: python3 update.py TOKEN")
    sys.exit(1)

def get(url):
    req = urllib.request.Request(url, headers={
        'Authorization': f'Discogs token={TOKEN}',
        'User-Agent': 'OasisCollectionSite/1.0'
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def sleep(): time.sleep(0.4)

# Hylätään vain selvästi ei-vinyyli formaatit
SKIP_FMTS = ['cd', 'cdr', 'dvd', 'vhs', 'cass', 'file', 'mp3', 'flac',
             'sacd', 'blu', 'lathe', 'transcription', 'dvdr', 'shellac',
             'betamax', 'minidisc', 'dat ', '8-track', 'acetate', 'wire']

def skip_format(fmt):
    f = fmt.lower()
    return any(s in f for s in SKIP_FMTS)

def parse_fmt(fmt):
    f = fmt or ''
    if '3x' in f: return '3xLP'
    if '2x' in f: return '2xLP'
    if '10"' in f or '10\u201d' in f: return '10"'
    if '12"' in f or '12\u201d' in f: return '12"'
    if '7"'  in f or '7\u201d'  in f: return '7"'
    if 'lp'  in f.lower():             return 'LP'
    if 'box' in f.lower():             return 'Box'
    return 'LP'

# ── 1. Käyttäjätunnus ────────────────────────────────────────────
if not USERNAME:
    print("Haetaan käyttäjätunnusta...")
    USERNAME = get('https://api.discogs.com/oauth/identity')['username']
    print(f"  Kirjautunut: {USERNAME}")

# ── 2. Kokoelma ──────────────────────────────────────────────────
print(f"Haetaan kokoelmaa ({USERNAME})...")
page, items = 1, []
while True:
    data = get(f'https://api.discogs.com/users/{USERNAME}/collection/folders/0/releases?per_page=100&page={page}')
    items += data['releases']
    pages = data['pagination']['pages']
    print(f"  sivu {page}/{pages} — {len(items)} levyä")
    if page >= pages: break
    page += 1; sleep()

oasis_owned = []
for item in items:
    bi = item.get('basic_information', {})
    if not any(a['id'] == OASIS_ID for a in bi.get('artists', [])):
        continue
    fmts = bi.get('formats', [{}])
    f = fmts[0] if fmts else {}
    descs = f.get('descriptions', [])
    qty   = int(f.get('qty', '1') or 1)
    name  = f.get('name', '')
    desc_str = ' '.join(descs)

    if '7"' in desc_str or '7\u201d' in desc_str:     fmt = '7"'
    elif '12"' in desc_str or '12\u201d' in desc_str: fmt = '12"'
    elif '10"' in desc_str or '10\u201d' in desc_str: fmt = '10"'
    elif name == 'Cassette':                           fmt = 'Cass'
    elif qty >= 3:                                     fmt = f'{qty}xLP'
    elif qty == 2:                                     fmt = '2xLP'
    elif 'LP' in desc_str or name == 'Vinyl':         fmt = 'LP'
    else:                                              fmt = name[:8]

    special = None
    dl    = desc_str.lower()
    cond  = (item.get('collection_media_condition') or '').lower()
    notes = (item.get('collection_notes') or '').lower()
    if 'mint' in cond:                   special = 'MINT'
    elif 'sealed' in notes:              special = 'SEALED'
    elif 'record store day' in dl:       special = 'RSD'
    elif 'promo' in dl:                  special = 'PROMO'
    elif 'numbered' in dl:               special = 'NUM'
    elif 'limited' in dl:                special = 'LTD'

    oasis_owned.append({
        'id':        bi.get('id'),
        'master_id': bi.get('master_id') or bi.get('id'),
        'title':     bi.get('title'),
        'year':      bi.get('year'),
        'format':    fmt,
        'label':     (bi.get('labels') or [{'name':''}])[0].get('name',''),
        'catalog':   (bi.get('labels') or [{'catno':''}])[0].get('catno',''),
        'thumb':     bi.get('thumb',''),
        **(({'special': special}) if special else {})
    })

print(f"  Oasis-levyjä kokoelmassa: {len(oasis_owned)}")

# ── 3. Diskografia — kaikki vinyyli, ei CD/kasetti ───────────────
print("Haetaan Oasis-diskografiaa...")
page, disc_raw = 1, []
while True:
    data = get(f'https://api.discogs.com/artists/{OASIS_ID}/releases?sort=year&sort_order=asc&per_page=100&page={page}')
    disc_raw += data['releases']
    pages = data['pagination']['pages']
    print(f"  sivu {page}/{pages} — {len(disc_raw)} julkaisua")
    if page >= pages: break
    page += 1; sleep()

discography = []
seen_masters = set()

for r in disc_raw:
    if r.get('role') != 'Main':
        continue

    fmt   = r.get('format', '')
    title = r.get('title', '')
    year  = r.get('year', 0)

    # Hylkää vain selvästi ei-vinyyli formaatit
    if skip_format(fmt):
        continue

    # Hylkää split-julkaisut joissa Oasis ei ole ensimmäinen
    artist = r.get('artist', '')
    if '/' in artist and 'Oasis' not in artist.split('/')[0]:
        continue

    # Master: yksi per master_id
    if r.get('type') == 'master':
        mid = r['id']
        if mid in seen_masters:
            continue
        seen_masters.add(mid)
    else:
        mid = r['id']

    discography.append({
        'mid':   mid,
        'title': title,
        'year':  year,
        'fmt':   parse_fmt(fmt),
        'label': r.get('label', ''),
        'thumb': r.get('thumb', ''),
    })

print(f"  Julkaisuja diskografiassa: {len(discography)}")

# ── 4. Tallenna ──────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(out_dir, exist_ok=True)

col_path = os.path.join(out_dir, 'collection.json')
with open(col_path, 'w', encoding='utf-8') as f:
    json.dump({
        'meta': {'username': USERNAME, 'updated': datetime.now().strftime('%Y-%m-%d %H:%M'), 'total': len(oasis_owned)},
        'owned': oasis_owned
    }, f, ensure_ascii=False, indent=2)

disc_path = os.path.join(out_dir, 'discography.json')
with open(disc_path, 'w', encoding='utf-8') as f:
    json.dump({
        'updated':  datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total':    len(discography),
        'releases': discography
    }, f, ensure_ascii=False, indent=2)

print(f"\nValmis! Kokoelma: {len(oasis_owned)}, Diskografia: {len(discography)}")
print("  git add data/ && git commit -m 'Päivitä' && git push")
