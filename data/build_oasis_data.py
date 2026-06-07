#!/usr/bin/env python3
"""
Muuntaa Discogs-datan oasis-data.js-muotoon.
Aja: python3 build_oasis_data.py
Edellyttää: data/collection.json ja data/discography.json
"""
import json, os, re

base = os.path.dirname(os.path.abspath(__file__))
col_path  = os.path.join(base, 'collection.json')
disc_path = os.path.join(base, 'discography.json')
out_path  = os.path.join(base, 'oasis-data.js')

with open(col_path)  as f: col  = json.load(f)
with open(disc_path) as f: disc = json.load(f)

owned_mids = set(o['master_id'] for o in col['owned'])
owned_map  = {o['master_id']: o for o in col['owned']}

# Väripaletit labelien mukaan
LABEL_COLORS = {
    'creation': ['#8a5a34','#1d1108'],
    'big brother': ['#3f5d6b','#15212a'],
    'epic': ['#6b6f63','#20231d'],
    'helter skelter': ['#7c8088','#212329'],
    'fierce panda': ['#9a3f3f','#1f0d0d'],
}
FMT_COLORS = {
    '7"':   ['#b5542c','#1f120a'],
    '12"':  ['#403a4a','#16131c'],
    '2xlp': ['#4a6b4f','#16201a'],
    'lp':   ['#6b5a34','#1d1608'],
    '3xlp': ['#3a5a6b','#10181f'],
}
DEFAULT_COLOR = ['#6b5d49','#1d1a14']

def get_color(label, fmt):
    for k, v in LABEL_COLORS.items():
        if k in (label or '').lower():
            return v
    for k, v in FMT_COLORS.items():
        if k in (fmt or '').lower():
            return v
    return DEFAULT_COLOR

def make_id(title, year, fmt):
    s = re.sub(r'[^a-z0-9]', '', (title or '').lower())[:16]
    return f"{s}_{year}_{re.sub(r'[^a-z0-9]', '', (fmt or '').lower())}"

def get_type(fmt, title):
    f = (fmt or '').lower()
    t = (title or '').lower()
    if 'box' in f or 'box' in t: return 'special'
    if any(x in f for x in ['lp', '2x', '3x']): return 'album'
    if any(x in f for x in ['7"', '12"', '10"']): return 'single'
    return 'album'

records = []
seen_ids = set()

# 1. Omat levyt ensin (täsmälliset Discogs-tiedot)
for o in col['owned']:
    mid = o['master_id']
    uid = make_id(o['title'], o['year'], o['format'])
    # Vältä duplikaatit saman masterin eri paineissa
    if mid in seen_ids:
        continue
    seen_ids.add(mid)
    fmt = o['format'] or 'LP'
    records.append({
        'id':     uid,
        'mid':    mid,
        'title':  o['title'],
        'year':   o['year'] or 0,
        'type':   get_type(fmt, o['title']),
        'owned':  True,
        'cat':    o.get('catalog',''),
        'label':  o.get('label',''),
        'format': fmt,
        'color':  get_color(o.get('label',''), fmt),
        'wish':   False,
        'img':    o.get('thumb',''),
        'special': o.get('special'),
    })

# 2. Diskografian puuttuvat
for d in disc['releases']:
    mid = d['mid']
    if mid in seen_ids:
        continue
    seen_ids.add(mid)
    fmt = d['fmt'] or 'LP'
    uid = make_id(d['title'], d['year'], fmt)
    records.append({
        'id':     uid,
        'mid':    mid,
        'title':  d['title'],
        'year':   d['year'] or 0,
        'type':   get_type(fmt, d['title']),
        'owned':  False,
        'cat':    '',
        'label':  d.get('label',''),
        'format': fmt,
        'color':  get_color(d.get('label',''), fmt),
        'wish':   False,
        'img':    d.get('thumb',''),
        'special': None,
    })

# Lajittele vuoden mukaan
records.sort(key=lambda r: (r['year'], r['title']))

# Kirjoita JS
lines = ['// Oasis-kokoelma — generoitu automaattisesti build_oasis_data.py-skriptillä']
lines.append(f'// Päivitetty: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}')
lines.append(f'// Omistaa: {sum(1 for r in records if r["owned"])} / {len(records)}')
lines.append('window.OASIS = [')
for r in records:
    special_js = f'"{r["special"]}"' if r['special'] else 'null'
    lines.append(f'  {{ id:{json.dumps(r["id"])}, mid:{r["mid"]}, title:{json.dumps(r["title"])}, year:{r["year"]}, type:{json.dumps(r["type"])}, owned:{str(r["owned"]).lower()}, cat:{json.dumps(r["cat"])}, label:{json.dumps(r["label"])}, format:{json.dumps(r["format"])}, color:{json.dumps(r["color"])}, wish:false, img:{json.dumps(r["img"])}, special:{special_js} }},')
lines.append('];')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Kirjoitettu {out_path}")
print(f"  {sum(1 for r in records if r['owned'])} omistaa, {sum(1 for r in records if not r['owned'])} puuttuu, {len(records)} yhteensä")
