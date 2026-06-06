#!/usr/bin/env python3
"""
Päivittää kokoelmasi Discogsista ja tallentaa data/collection.json-tiedostoon.
Käyttö:
  python3 update.py TOKEN                  # Käyttää Discogs-käyttäjätunnuksesi
  python3 update.py TOKEN muukäyttäjä     # Käyttää muuta käyttäjätunnusta
"""
import sys, json, time, urllib.request, urllib.error, os
from datetime import datetime

TOKEN    = sys.argv[1] if len(sys.argv) > 1 else None
USERNAME = sys.argv[2] if len(sys.argv) > 2 else None
OASIS_ARTIST_ID = 140140

if not TOKEN:
    print("VIRHE: Anna Discogs-token ensimmäisenä argumenttina")
    print("  python3 update.py SINUN_TOKEN")
    sys.exit(1)

def get(url):
    req = urllib.request.Request(url, headers={
        'Authorization': f'Discogs token={TOKEN}',
        'User-Agent': 'OasisCollectionSite/1.0'
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def sleep(): time.sleep(0.4)

# 1. Selvitä käyttäjätunnus jos ei annettu
if not USERNAME:
    print("Haetaan käyttäjätunnusta...")
    identity = get('https://api.discogs.com/oauth/identity')
    USERNAME = identity['username']
    print(f"  Kirjautunut: {USERNAME}")

# 2. Hae kokoelma
print(f"Haetaan kokoelmaa käyttäjältä {USERNAME}...")
page, items = 1, []
while True:
    data = get(f'https://api.discogs.com/users/{USERNAME}/collection/folders/0/releases?per_page=100&page={page}')
    items += data['releases']
    pages = data['pagination']['pages']
    print(f"  sivu {page}/{pages} — {len(items)} levyä")
    if page >= pages: break
    page += 1; sleep()

# 3. Suodata Oasis
oasis = []
for item in items:
    bi = item.get('basic_information', {})
    if not any(a['id'] == OASIS_ARTIST_ID for a in bi.get('artists', [])):
        continue
    fmts = bi.get('formats', [{}])
    f = fmts[0] if fmts else {}
    descs = f.get('descriptions', [])
    qty = int(f.get('qty', '1') or 1)
    name = f.get('name', '')
    if '7"' in descs:       fmt = '7"'
    elif '12"' in descs:    fmt = '12"'
    elif '10"' in descs:    fmt = '10"'
    elif name == 'Cassette': fmt = 'Cass'
    elif qty >= 3:           fmt = f'{qty}xLP'
    elif qty == 2:           fmt = '2xLP'
    elif 'LP' in descs or name == 'Vinyl': fmt = 'LP'
    else:                    fmt = name[:8]

    special = None
    all_descs = ' '.join(descs).lower()
    if 'mint' in (item.get('collection_media_condition','') or '').lower(): special = 'MINT'
    elif 'sealed' in (item.get('collection_notes','') or '').lower():       special = 'SEALED'
    elif 'record store day' in all_descs:  special = 'RSD'
    elif 'promo' in all_descs:             special = 'PROMO'
    elif 'numbered' in all_descs:          special = 'NUM'
    elif 'limited' in all_descs:           special = 'LTD'

    oasis.append({
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

print(f"  Oasis-levyjä: {len(oasis)}")

# 4. Tallenna
out_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'collection.json')

output = {
    'meta': {
        'username': USERNAME,
        'updated':  datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total':    len(oasis)
    },
    'owned': oasis
}
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nValmis! Tallennettu {out_path}")
print(f"Levyjä yhteensä: {len(oasis)}")
print("\nSeuraavaksi:")
print("  git add data/collection.json")
print("  git commit -m 'Päivitä kokoelma'")
print("  git push")
