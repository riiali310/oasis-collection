#!/usr/bin/env python3
import json
import os
import re
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


def normalize_title(title):
    return (
        (title or "")
        .lower()
        .replace("’", "'")
        .replace("`", "'")
        .strip()
    )


def title_key(title):
    t = normalize_title(title)
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


OFFICIAL_ALBUM_TITLES = {
    "definitely maybe",
    "what s the story morning glory",
    "be here now",
    "the masterplan",
    "standing on the shoulder of giants",
    "heathen chemistry",
    "don t believe the truth",
    "dig out your soul",

    # Official live / compilations
    "familiar to millions",
    "stop the clocks",
    "time flies 1994 2009",
    "knebworth 1996",
}

OFFICIAL_SINGLE_TITLES = {
    "supersonic",
    "shakermaker",
    "live forever",
    "cigarettes and alcohol",
    "whatever",
    "some might say",
    "roll with it",
    "wonderwall",
    "don t look back in anger",
    "champagne supernova",
    "d you know what i mean",
    "stand by me",
    "all around the world",
    "don t go away",
    "go let it out",
    "who feels love",
    "sunday morning call",
    "the hindu times",
    "stop crying your heart out",
    "little by little",
    "little by little she is love",
    "songbird",
    "lyla",
    "the importance of being idle",
    "let there be love",
    "lord don t slow me down",
    "the shock of the lightning",
    "i m outta time",
    "i m outta time remixes",
    "falling down",
    "falling down a monstrous psychedelic bubble exploding in your mind",

    # Official / semi-official single-related releases
    "columbia",
    "acquiesce",
    "i am the walrus",
    "fuckin in the bushes",
}

OFFICIAL_SPECIAL_TITLES = {
    "5 tracks taken from the forthcoming album definitely maybe",
    "cum on feel the noize",
    "it s good to be free",
    "wibbling rivalry",
    "live demonstration",
    "what s the story morning glory singles",
}

SPECIAL_WORDS = [
    "promo",
    "promotional",
    "white label",
    "test pressing",
    "test press",
    "acetate",
    "sampler",
    "advance",
    "demo",
    "numbered",
    "limited",
    "ltd",
    "box",
]

EXCLUDE_WORDS = [
    "bootleg",
    "unofficial",
    "radio broadcast",
    "broadcast",
    "fm broadcast",
    "live at",
    "live in",
    "live by the sea",
    "bbc radio",
    "interview",
    "documentary",
    "tribute",
    "karaoke",
]


def should_exclude(fmt, title, label=None, special=None):
    f = (fmt or "").lower()
    t = title_key(title)
    l = (label or "").lower()
    s = (special or "").lower()

    combined = " ".join([f, t, l, s])

    # Official exceptions first
    if t in OFFICIAL_ALBUM_TITLES:
        return False

    if t in OFFICIAL_SINGLE_TITLES:
        return False

    if t in OFFICIAL_SPECIAL_TITLES:
        return False

    return any(word in combined for word in EXCLUDE_WORDS)


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


def get_type(fmt, title, special=None, label=None):
    f = (fmt or "").lower()
    t = title_key(title)
    s = (special or "").lower()
    l = (label or "").lower()

    if should_exclude(fmt, title, label, special):
        return None

    combined = " ".join([f, s, l, t])

    # Special first. A promo 12" is a special release, not a normal single.
    if any(word in combined for word in SPECIAL_WORDS):
        return "special"

    if t in OFFICIAL_SPECIAL_TITLES:
        return "special"

    if t in OFFICIAL_ALBUM_TITLES:
        return "album"

    if t in OFFICIAL_SINGLE_TITLES:
        return "single"

    # Format is only a fallback. It must not overrule collector logic.
    if any(x in f for x in ['7"', '10"', '12"', "single", "cass", "cd"]):
        return "single"

    if any(x in f for x in ["lp", "2x", "3x", "album"]):
        return "album"

    # Unknown junk stays out.
    return None


records = []
seen_release_ids = set()
owned_master_ids = set()

for o in col["owned"]:
    release_id = o.get("id")
    master_id = o.get("master_id")
    fmt = o.get("format") or "LP"
    title = o.get("title", "")
    label = o.get("label", "")
    special = o.get("special")

    release_type = get_type(fmt, title, special, label)

    if release_type is None:
        continue

    if release_id in seen_release_ids:
        continue

    seen_release_ids.add(release_id)

    if master_id:
        owned_master_ids.add(master_id)

    records.append({
        "id": f"release_{release_id}",
        "release_id": release_id,
        "mid": master_id or release_id,
        "title": title,
        "year": o.get("year") or 0,
        "type": release_type,
        "owned": True,
        "cat": o.get("catalog", ""),
        "label": label,
        "format": fmt,
        "color": get_color(label, fmt),
        "wish": False,
        "img": o.get("thumb", ""),
        "special": special,
    })

seen_missing_mids = set()

for d in disc["releases"]:
    mid = d.get("mid")
    fmt = d.get("fmt") or "LP"
    title = d.get("title", "")
    label = d.get("label", "")

    release_type = get_type(fmt, title, None, label)

    if release_type is None:
        continue

    if mid in owned_master_ids:
        continue

    if mid in seen_missing_mids:
        continue

    seen_missing_mids.add(mid)

    records.append({
        "id": f"missing_{mid}",
        "release_id": None,
        "mid": mid,
        "title": title,
        "year": d.get("year") or 0,
        "type": release_type,
        "owned": False,
        "cat": "",
        "label": label,
        "format": fmt,
        "color": get_color(label, fmt),
        "wish": False,
        "img": d.get("thumb", ""),
        "special": None,
    })

records.sort(key=lambda r: (r["year"], r["type"], r["title"], r["format"], r["cat"]))

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

album_count = sum(1 for r in records if r["type"] == "album")
single_count = sum(1 for r in records if r["type"] == "single")
special_count = sum(1 for r in records if r["type"] == "special")

print(f"Kirjoitettu {out_path}")
print(f"  {owned_count} omistaa, {missing_count} puuttuu, {len(records)} yhteensa")
print(f"  Albumit: {album_count}, Sinkut: {single_count}, Erikoiset: {special_count}")
