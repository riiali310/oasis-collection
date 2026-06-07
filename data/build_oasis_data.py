#!/usr/bin/env python3
import json
import os
from datetime import datetime

base = os.path.dirname(os.path.abspath(__file__))
col_path = os.path.join(base, "collection.json")
disc_path = os.path.join(base, "discography.json")
out_path = os.path.join(base, "oasis-data.js")

with open(col_path, encoding="utf-8") as f:
    col = json.load(f)

with open(disc_path, encoding="utf-8") as f:
    disc = json.load(f)

LABEL_COLORS = {
    "creation": ["#8a5a34", "#1d1108"],
    "big brother": ["#3f5d6b", "#15212a"],
    "epic": ["#6b6f63", "#20231d"],
    "helter skelter": ["#7c8088", "#212329"],
    "fierce panda": ["#9a3f3f", "#1f0d0d"],
}

FMT_COLORS = {
    '7"': ["#b5542c", "#1f120a"],
    '12"': ["#403a4a", "#16131c"],
    "2xlp": ["#4a6b4f", "#16201a"],
    "lp": ["#6b5a34", "#1d1608"],
    "3xlp": ["#3a5a6b", "#10181f"],
}

DEFAULT_COLOR = ["#6b5d49", "#1d1a14"]

SINGLE_TITLES = {
    "supersonic",
    "shakermaker",
    "live forever",
    "cigarettes & alcohol",
    "whatever",
    "some might say",
    "roll with it",
    "wonderwall",
    "don't look back in anger",
    "d'you know what i mean?",
    "stand by me",
    "all around the world",
    "go let it out",
    "who feels love?",
    "sunday morning call",
    "the hindu times",
    "stop crying your heart out",
    "little by little",
    "songbird",
    "lyla",
    "the importance of being idle",
    "let there be love",
    "lord don't slow me down",
    "the shock of the lightning",
    "i'm outta time",
    "falling down",
    "columbia",
    "acquiesce",
    "i am the walrus",
    "fuckin' in the bushes",
    "wibbling rivalry",
}


def normalize_title(title):
    return (
        (title or "")
        .lower()
        .replace("’", "'")
        .replace("`", "'")
        .strip()
    )


def get_color(label, fmt):
    label = (label or "").lower()
    fmt = (fmt or "").lower()

    for k, v in LABEL_COLORS.items():
        if k in label:
            return v

    for k, v in FMT_COLORS.items():
        if k in fmt:
            return v

    return DEFAULT_COLOR


def get_type(fmt, title):
    f = (fmt or "").lower()
    t = normalize_title(title)

    if "box" in f or "box" in t:
        return "special"

    if t in SINGLE_TITLES:
        return "single"

    if any(x in f for x in ['7"', '12"', '10"', "single", "cass", "cd"]):
        return "single"

    if any(x in f for x in ["lp", "2x", "3x", "album"]):
        return "album"

    return "album"


records = []
seen_release_ids = set()
owned_master_ids = set()

for o in col["owned"]:
    release_id = o.get("id")
    master_id = o.get("master_id")

    if release_id in seen_release_ids:
        continue

    seen_release_ids.add(release_id)

    if master_id:
        owned_master_ids.add(master_id)

    fmt = o.get("format") or "LP"

    records.append({
        "id": f"release_{release_id}",
        "release_id": release_id,
        "mid": master_id or release_id,
        "title": o.get("title", ""),
        "year": o.get("year") or 0,
        "type": get_type(fmt, o.get("title", "")),
        "owned": True,
        "cat": o.get("catalog", ""),
        "label": o.get("label", ""),
        "format": fmt,
        "color": get_color(o.get("label", ""), fmt),
        "wish": False,
        "img": o.get("thumb", ""),
        "special": o.get("special"),
    })

seen_missing_mids = set()

for d in disc["releases"]:
    mid = d.get("mid")

    if mid in owned_master_ids:
        continue

    if mid in seen_missing_mids:
        continue

    seen_missing_mids.add(mid)

    fmt = d.get("fmt") or "LP"

    records.append({
        "id": f"missing_{mid}",
        "release_id": None,
        "mid": mid,
        "title": d.get("title", ""),
        "year": d.get("year") or 0,
        "type": get_type(fmt, d.get("title", "")),
        "owned": False,
        "cat": "",
        "label": d.get("label", ""),
        "format": fmt,
        "color": get_color(d.get("label", ""), fmt),
        "wish": False,
        "img": d.get("thumb", ""),
        "special": None,
    })

records.sort(key=lambda r: (r["year"], r["title"], r["format"], r["cat"]))

lines = ["// Oasis-kokoelma - generoitu automaattisesti build_oasis_data.py-skriptillä"]
lines.append(f"// Paivitetty: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
lines.append(f'// Omistaa: {sum(1 for r in records if r["owned"])} / {len(records)}')
lines.append("window.OASIS = [")

for r in records:
    special_js = json.dumps(r["special"]) if r["special"] else "null"

    lines.append(
        f'  {{ id:{json.dumps(r["id"])}, '
        f'release_id:{json.dumps(r["release_id"])}, '
        f'mid:{json.dumps(r["mid"])}, '
        f'title:{json.dumps(r["title"])}, '
        f'year:{json.dumps(r["year"])}, '
        f'type:{json.dumps(r["type"])}, '
        f'owned:{str(r["owned"]).lower()}, '
        f'cat:{json.dumps(r["cat"])}, '
        f'label:{json.dumps(r["label"])}, '
        f'format:{json.dumps(r["format"])}, '
        f'color:{json.dumps(r["color"])}, '
        f'wish:false, '
        f'img:{json.dumps(r["img"])}, '
        f'special:{special_js} }},'
    )

lines.append("];")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

owned_count = sum(1 for r in records if r["owned"])
missing_count = sum(1 for r in records if not r["owned"])

print(f"Kirjoitettu {out_path}")
print(f"  {owned_count} omistaa, {missing_count} puuttuu, {len(records)} yhteensa")
