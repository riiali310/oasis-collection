#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime

base = os.path.dirname(os.path.abspath(__file__))
col_path = os.path.join(base, "collection.json")
want_path = os.path.join(base, "wantlist.json")
out_path = os.path.join(base, "oasis-data.js")

with open(col_path, encoding="utf-8") as f:
    col = json.load(f)

with open(want_path, encoding="utf-8") as f:
    want = json.load(f)

LABEL_COLORS = {
    "creation": ["#8a5a34", "#1d1108"],
    "big brother": ["#3f5d6b", "#15212a"],
    "epic": ["#6b6f63", "#20231d"],
    "helter skelter": ["#7c8088", "#212329"],
    "fierce panda": ["#9a3f3f", "#1f0d0d"],
}

FMT_COLORS = {
    '7"': ["#b5542c", "#1f120a"],
    '10"': ["#5d4c6b", "#1a1420"],
    '12"': ["#403a4a", "#16131c"],
    "2xlp": ["#4a6b4f", "#16201a"],
    "lp": ["#6b5a34", "#1d1608"],
    "3xlp": ["#3a5a6b", "#10181f"],
    "cass": ["#6b4f3a", "#1f1710"],
    "cd": ["#6b6f63", "#20231d"],
    "box": ["#60425f", "#1d121d"],
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
    "dig out your soul 7 singles box set",
}


COMPILATION_ALBUM_TITLES = {
    "the masterplan",
    "stop the clocks",
    "time flies 1994 2009",
}

LIVE_ALBUM_TITLES = {
    "familiar to millions",
    "knebworth 1996",
}

ALBUM_BOX_TITLES = {
    "complete studio album collection",
    "oasis complete studio album collection",
    "vinyl lp collectors box set",
    "oasis vinyl lp collectors box set",
}

SINGLES_BOX_TITLES = {
    "definitely maybe 7 singles box set",
    "what s the story morning glory 7 singles box set",
    "what s the story morning glory singles",
    "complete 7 inch singles collection box vol 1",
    "complete 7 inch singles collection box vol 2",
    "complete 7inch singles collection box vol 1",
    "complete 7inch singles collection box vol 2",
    "dig out your soul 7 singles box set",
}

ANNIVERSARY_BOX_WORDS = [
    "anniversary",
    "30th anniversary",
    "25th anniversary",
    "super deluxe",
    "deluxe box",
]

SPECIAL_WORDS = [
    "promo",
    "promotional",
    "white label",
    "w/lbl",
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
    "s/sided",
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


def is_vinyl_format(fmt, title=""):
    f = (fmt or "").lower()
    t = (title or "").lower()

    vinyl_words = [
        '7"',
        '10"',
        '12"',
        "lp",
        "2xlp",
        "3xlp",
        "vinyl",
        "box",
    ]

    non_vinyl_words = [
        "cass",
        "cassette",
        "cd",
        "cdr",
        "dvd",
        "file",
        "mp3",
        "flac",
        "blu",
        "vhs",
        "minidisc",
        "dat",
    ]

    if any(word in f for word in non_vinyl_words):
        return False

    if any(word in f for word in vinyl_words):
        return True

    # Osa boxeista tulee formaattina 7", mutta jos title kertoo box setistä, pidetään se.
    if "box" in t:
        return True

    return False


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


def should_exclude(fmt, title, label=None, special=None):
    f = (fmt or "").lower()
    t = title_key(title)
    l = (label or "").lower()
    s = (special or "").lower()

    combined = " ".join([f, t, l, s])

    if t in OFFICIAL_ALBUM_TITLES:
        return False

    if t in OFFICIAL_SINGLE_TITLES:
        return False

    if t in OFFICIAL_SPECIAL_TITLES:
        return False

    return any(word in combined for word in EXCLUDE_WORDS)


def get_type(fmt, title, special=None, label=None):
    f = (fmt or "").lower()
    t = title_key(title)
    s = (special or "").lower()
    l = (label or "").lower()

    if should_exclude(fmt, title, label, special):
        return None

    combined = " ".join([f, s, l, t])

    if t in ALBUM_BOX_TITLES or t in SINGLES_BOX_TITLES:
        return "special"

    if any(word in combined for word in ANNIVERSARY_BOX_WORDS):
        return "special"

    if any(word in combined for word in SPECIAL_WORDS):
        return "special"

    if t in OFFICIAL_SPECIAL_TITLES:
        return "special"

    if t in OFFICIAL_ALBUM_TITLES:
        return "album"

    if t in OFFICIAL_SINGLE_TITLES:
        return "single"

    if any(x in f for x in ['7"', '10"', '12"', "single", "cass", "cd"]):
        return "single"

    if any(x in f for x in ["lp", "2x", "3x", "album"]):
        return "album"

    return None


def make_tags(release_type, fmt, title, special=None, label=None, year=None):
    f = (fmt or "").lower()
    t = title_key(title)
    s = (special or "").lower()
    l = (label or "").lower()
    tags = []

    if release_type == "album":
        tags.append("Albumi")
    elif release_type == "single":
        tags.append("Single")
    elif release_type == "special":
        tags.append("Erikois")

    if t in COMPILATION_ALBUM_TITLES:
        tags.append("Compilation")

    if t in LIVE_ALBUM_TITLES:
        tags.append("Live album")

    if t in ALBUM_BOX_TITLES:
        tags.append("Album box")

    if t in SINGLES_BOX_TITLES:
        tags.append("Singles box")

    if '7"' in f:
        tags.append('7"')
    if '10"' in f:
        tags.append('10"')
    if '12"' in f:
        tags.append('12"')
    if "cass" in f:
        tags.append("Cassette")
    if "cd" in f:
        tags.append("CD")
    if "lp" in f:
        tags.append("LP")
    if "box" in f or "box" in t:
        tags.append("Box")

    combined = " ".join([f, t, s, l])

    if any(word in combined for word in ANNIVERSARY_BOX_WORDS):
        tags.append("Anniversary box")

    if "promo" in combined or "promotional" in combined:
        tags.append("Promo")
    if "white label" in combined or "w/lbl" in combined:
        tags.append("White Label")
    if "test pressing" in combined or "test press" in combined:
        tags.append("Test Press")
    if "acetate" in combined:
        tags.append("Acetate")
    if "sampler" in combined:
        tags.append("Sampler")
    if "advance" in combined:
        tags.append("Advance")
    if "demo" in combined:
        tags.append("Demo")
    if "limited" in combined or "ltd" in combined:
        tags.append("Limited")
    if "numbered" in combined or s == "num":
        tags.append("Numbered")

    try:
        y = int(year or 0)
    except ValueError:
        y = 0

    if y >= 2010:
        tags.append("Reissue")
    elif 1993 <= y <= 2009:
        tags.append("Original era")

    clean = []
    for tag in tags:
        if tag and tag not in clean:
            clean.append(tag)

    return clean


def make_record(item, owned):
    release_id = item.get("id")
    master_id = item.get("master_id") or release_id
    title = item.get("title", "")
    year = item.get("year") or 0
    fmt = item.get("format") or "Unknown"
    label = item.get("label", "")
    catalog = item.get("catalog", "")
    thumb = item.get("thumb", "")
    special = item.get("special")

    if not is_vinyl_format(fmt, title):
        return None

    release_type = get_type(fmt, title, special, label)

    if release_type is None:
        return None

    return {
        "id": f"release_{release_id}" if owned else f"want_{release_id}",
        "release_id": release_id,
        "mid": master_id,
        "title": title,
        "year": year,
        "type": release_type,
        "owned": bool(owned),
        "cat": catalog,
        "label": label,
        "format": fmt,
        "color": get_color(label, fmt),
        "wish": False,
        "img": thumb,
        "special": special,
        "tags": make_tags(release_type, fmt, title, special, label, year),
    }


records = []
seen_ids = set()

for item in col.get("owned", []):
    rec = make_record(item, owned=True)

    if not rec:
        continue

    if rec["release_id"] in seen_ids:
        continue

    seen_ids.add(rec["release_id"])
    records.append(rec)

for item in want.get("wanted", []):
    rec = make_record(item, owned=False)

    if not rec:
        continue

    if rec["release_id"] in seen_ids:
        continue

    seen_ids.add(rec["release_id"])
    records.append(rec)

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
        f'special:{special_js}, '
        f'tags:{json.dumps(r.get("tags", []))} }},'
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
