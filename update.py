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
    qty = int(f.get('qty', '1') or 1)
    name = f.get('name', '')
    if '7"' in descs:        fmt = '7"'
    elif '12"' in descs:     fmt = '12"'
    elif '10"' in descs:     fmt = '10"'
    elif name == 'Cassette': fmt = 'Cass'
    elif qty >= 3:           fmt = f'{qty}xLP'
    elif qty == 2:           fmt = '2xLP'
    elif 'LP' in descs or name == 'Vinyl': fmt = 'LP'
    else:                    fmt = name[:8]

    special = None
    desc_str = ' '.join(descs).lower()
    cond = (item.get('collection_media_condition') or '').lower()
    notes = (item.get('collection_notes') or '').lower()
    if 'mint' in cond:                  special = 'MINT'
    elif 'sealed' in notes:             special = 'SEALED'
    elif 'record store day' in desc_str: special = 'RSD'
    elif 'promo' in desc_str:           special = 'PROMO'
    elif 'numbered' in desc_str:        special = 'NUM'
    elif 'limited' in desc_str:         special = 'LTD'

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

# ── 3. Diskografia ───────────────────────────────────────────────
print("Haetaan Oasis-diskografiaa Discogsista...")
page, disc_raw = 1, []
while True:
    data = get(f'https://api.discogs.com/artists/{OASIS_ID}/releases?sort=year&sort_order=asc&per_page=100&page={page}')
    disc_raw += data['releases']
    pages = data['pagination']['pages']
    print(f"  sivu {page}/{pages} — {len(disc_raw)} julkaisua")
    if page >= pages: break
    page += 1; sleep()

# Suodata: vain Main-rooli, vain vinyl/LP/single, ei CD/DVD/VHS/kasetti/tiedosto
VINYL_FORMATS = {'Vinyl', '7"', '10"', '12"', 'LP', '2xLP', '3xLP', 'Box Set'}
SKIP_FORMATS  = {'CD', 'CDr', 'DVD', 'VHS', 'Cassette', 'File', 'Flexi', 'Transcription', 'SACD', 'DVD-V', 'CDr'}

discography = []
seen_masters = set()

for r in disc_raw:
    if r.get('role') != 'Main':
        continue

    fmt = r.get('format', '')
    title = r.get('title', '')
    year = r.get('year', 0)

    # Ohita selvästi ei-vinyyli
    skip = False
    for sf in SKIP_FORMATS:
        if sf.lower() in fmt.lower():
            skip = True; break
    if skip:
        continue

    # Ohita split-julkaisut (muut artistit)
    artist = r.get('artist', '')
    if '/' in artist and 'Oasis' not in artist.split('/')[0]:
        continue

    # Master-julkaisut: yksi per master_id
    mid = None
    if r.get('type') == 'master':
        mid = r['id']
        if mid in seen_masters:
            continue
        seen_masters.add(mid)
    else:
        # Yksittäinen release ilman masteria — käytä release id:tä
        mid = r['id']

    # Päättele formaatti
    if '3xLP' in fmt or '3x' in fmt:      fmtout = '3xLP'
    elif '2xLP' in fmt or '2x' in fmt:    fmtout = '2xLP'
    elif 'LP' in fmt:                      fmtout = 'LP'
    elif '12"' in fmt or '12"' in fmt:    fmtout = '12"'
    elif '10"' in fmt:                     fmtout = '10"'
    elif '7"' in fmt or '7"' in fmt:      fmtout = '7"'
    elif 'Box' in fmt:                     fmtout = 'Box'
    elif not fmt:                          fmtout = 'LP'
    else:                                  fmtout = fmt[:8]

    thumb = r.get('thumb', '')

    discography.append({
        'mid':   mid,
        'title': title,
        'year':  year,
        'fmt':   fmtout,
        'label': r.get('label', ''),
        'thumb': thumb,
        'type':  r.get('type', 'release')
    })

print(f"  Vinyyli-/LP-julkaisuja diskografiassa: {len(discography)}")

# ── 4. Tallenna ──────────────────────────────────────────────────
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(out_dir, exist_ok=True)

# collection.json
col_path = os.path.join(out_dir, 'collection.json')
with open(col_path, 'w', encoding='utf-8') as f:
    json.dump({
        'meta': {'username': USERNAME, 'updated': datetime.now().strftime('%Y-%m-%d %H:%M'), 'total': len(oasis_owned)},
        'owned': oasis_owned
    }, f, ensure_ascii=False, indent=2)

# discography.json
disc_path = os.path.join(out_dir, 'discography.json')
with open(disc_path, 'w', encoding='utf-8') as f:
    json.dump({
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total': len(discography),
        'releases': discography
    }, f, ensure_ascii=False, indent=2)

print(f"\nValmis!")
print(f"  Kokoelma:   {col_path}  ({len(oasis_owned)} levyä)")
print(f"  Diskografia: {disc_path}  ({len(discography)} julkaisua)")
print(f"\nSeuraavaksi:")
print(f"  git add data/")
print(f"  git commit -m 'Päivitä kokoelma ja diskografia'")
print(f"  git push")
