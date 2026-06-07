#!/usr/bin/env python3
"""
Päivittää Discogsista:
1. data/collection.json   = omistetut Oasis-julkaisut
2. data/wantlist.json     = puuttuvat Oasis-julkaisut Discogs wantlististä
3. data/discography.json  = artistin diskografia, varalla / vertailuun

Käyttö:
  python3 update.py TOKEN [käyttäjänimi]

Tai ympäristömuuttujalla:
  DISCOGS_TOKEN=xxx python3 update.py
"""

import sys
import json
import time
import urllib.parse
import urllib.request
import os
from datetime import datetime

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DISCOGS_TOKEN")
USERNAME = sys.argv[2] if len(sys.argv) > 2 else None

OASIS_ID = 140140
BASE_API = "https://api.discogs.com"

if not TOKEN:
    print("VIRHE: Anna token: python3 update.py TOKEN")
    sys.exit(1)


def get(url):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Discogs token={TOKEN}",
            "User-Agent": "OasisCollectionSite/2.0 +https://github.com/riiali310/oasis-collection",
        },
    )

    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def sleep():
    # Discogs API tykkää rauhallisesta käytöksestä. Niin pitäisi meidänkin.
    time.sleep(0.45)


def as_text(value):
    """Muuttaa Discogsin sekalaiset arvot turvallisesti tekstiksi."""
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(as_text(v) for v in value)

    if isinstance(value, dict):
        return " ".join(as_text(v) for v in value.values())

    return str(value)


def is_oasis_release(bi):
    artists = bi.get("artists", []) or []
    return any(a.get("id") == OASIS_ID for a in artists)


def first_label(bi):
    labels = bi.get("labels") or []
    if not labels:
        return "", ""

    label = labels[0] or {}
    return label.get("name", "") or "", label.get("catno", "") or ""


def all_format_text(bi):
    parts = []

    for f in bi.get("formats", []) or []:
        name = f.get("name", "")
        qty = f.get("qty", "")
        descs = f.get("descriptions", []) or []

        if qty:
            parts.append(str(qty))

        if name:
            parts.append(str(name))

        parts.extend(str(d) for d in descs if d)

    return " ".join(parts).strip()


def parse_fmt_from_basic_information(bi):
    fmt_text = all_format_text(bi)
    f = fmt_text.lower()

    formats = bi.get("formats", []) or []
    first = formats[0] if formats else {}
    name = (first.get("name") or "").lower()

    try:
        qty = int(first.get("qty", "1") or 1)
    except ValueError:
        qty = 1

    if '7"' in f or "7”" in f:
        return '7"'

    if '10"' in f or "10”" in f:
        return '10"'

    if '12"' in f or "12”" in f:
        return '12"'

    if "cassette" in f or name == "cassette":
        return "Cass"

    if "cd" in f or name == "cd":
        return "CD"

    if "box set" in f or "box" in f:
        return "Box"

    if qty >= 3 and ("vinyl" in f or "lp" in f):
        return f"{qty}xLP"

    if qty == 2 and ("vinyl" in f or "lp" in f):
        return "2xLP"

    if "lp" in f or name == "vinyl" or "vinyl" in f:
        return "LP"

    return first.get("name", "") or "Unknown"


def detect_special(bi, item=None):
    fmt_text = as_text(all_format_text(bi)).lower()
    title = as_text(bi.get("title")).lower()
    label, catalog = first_label(bi)

    notes = ""
    condition = ""

    if item:
        notes = as_text(
            item.get("collection_notes")
            or item.get("notes")
            or ""
        ).lower()

        condition = as_text(
            item.get("collection_media_condition")
            or item.get("condition")
            or ""
        ).lower()

    combined = " ".join([
        fmt_text,
        title,
        as_text(label).lower(),
        as_text(catalog).lower(),
        notes,
        condition,
    ])

    if "test pressing" in combined or "test press" in combined:
        return "TEST"

    if "white label" in combined or "w/lbl" in combined:
        return "WHITE"

    if "promo" in combined or "promotional" in combined:
        return "PROMO"

    if "record store day" in combined:
        return "RSD"

    if "numbered" in combined:
        return "NUM"

    if "limited" in combined or "ltd" in combined:
        return "LTD"

    if "sealed" in notes:
        return "SEALED"

    if "mint" in condition:
        return "MINT"

    if "sampler" in combined:
        return "SAMPLER"

    if "advance" in combined:
        return "ADVANCE"

    if "acetate" in combined:
        return "ACETATE"

    return None


def release_object_from_basic_information(item):
    bi = item.get("basic_information") or item

    label, catalog = first_label(bi)
    special = detect_special(bi, item)

    obj = {
        "id": bi.get("id") or item.get("id"),
        "master_id": bi.get("master_id") or bi.get("id") or item.get("id"),
        "title": bi.get("title", ""),
        "year": bi.get("year") or 0,
        "format": parse_fmt_from_basic_information(bi),
        "format_text": all_format_text(bi),
        "label": label,
        "catalog": catalog,
        "thumb": bi.get("thumb", ""),
    }

    if special:
        obj["special"] = special

    return obj


def fetch_identity_username():
    print("Haetaan käyttäjätunnusta...")
    identity = get(f"{BASE_API}/oauth/identity")
    username = identity["username"]
    print(f"  Kirjautunut: {username}")
    return username


def fetch_collection(username):
    print(f"Haetaan kokoelmaa ({username})...")

    page = 1
    items = []

    while True:
        url = (
            f"{BASE_API}/users/{urllib.parse.quote(username)}/collection/folders/0/releases"
            f"?per_page=100&page={page}"
        )

        data = get(url)
        releases = data.get("releases", [])
        items.extend(releases)

        pages = data.get("pagination", {}).get("pages", page)

        print(f"  sivu {page}/{pages} — {len(items)} levyä")

        if page >= pages:
            break

        page += 1
        sleep()

    oasis_owned = []

    for item in items:
        bi = item.get("basic_information", {})

        if not is_oasis_release(bi):
            continue

        oasis_owned.append(release_object_from_basic_information(item))

    print(f"  Oasis-levyjä kokoelmassa: {len(oasis_owned)}")
    return oasis_owned


def fetch_wantlist(username):
    print(f"Haetaan wantlist ({username})...")

    page = 1
    items = []

    while True:
        url = (
            f"{BASE_API}/users/{urllib.parse.quote(username)}/wants"
            f"?per_page=100&page={page}"
        )

        data = get(url)
        wants = data.get("wants", [])
        items.extend(wants)

        pages = data.get("pagination", {}).get("pages", page)

        print(f"  sivu {page}/{pages} — {len(items)} wanttia")

        if page >= pages:
            break

        page += 1
        sleep()

    oasis_wants = []

    for item in items:
        bi = item.get("basic_information", {})

        if not is_oasis_release(bi):
            continue

        obj = release_object_from_basic_information(item)

        # Wantlistissä nämä ovat puuttuvia, joten pidetään mukana release-id.
        # Tämä mahdollistaa suoran Discogs-linkin puuttuvalle versiolle.
        obj["wanted"] = True

        oasis_wants.append(obj)

    print(f"  Oasis-levyjä wantlistissä: {len(oasis_wants)}")
    return oasis_wants


def parse_discography_fmt(fmt):
    f = (fmt or "").lower()

    if "3x" in f:
        return "3xLP"

    if "2x" in f:
        return "2xLP"

    if '10"' in f or "10”" in f:
        return '10"'

    if '12"' in f or "12”" in f:
        return '12"'

    if '7"' in f or "7”" in f:
        return '7"'

    if "cass" in f:
        return "Cass"

    if "cd" in f:
        return "CD"

    if "box" in f:
        return "Box"

    if "lp" in f or "vinyl" in f:
        return "LP"

    return fmt or "Unknown"


def should_skip_discography_format(fmt):
    # Diskografia on enää varadataa, mutta ei silti kerätä ihan kaikkea roskaa.
    # Ei poisteta cassette/CD tässä liian aggressiivisesti, koska halusit tagit niille.
    f = (fmt or "").lower()

    skip = [
        "file",
        "mp3",
        "flac",
        "dvd",
        "vhs",
        "blu",
        "sacd",
        "minidisc",
        "dat",
        "8-track",
        "shellac",
        "betamax",
        "wire",
    ]

    return any(s in f for s in skip)


def fetch_discography():
    print("Haetaan Oasis-diskografiaa varalle...")

    page = 1
    disc_raw = []

    while True:
        url = (
            f"{BASE_API}/artists/{OASIS_ID}/releases"
            f"?sort=year&sort_order=asc&per_page=100&page={page}"
        )

        data = get(url)
        releases = data.get("releases", [])
        disc_raw.extend(releases)

        pages = data.get("pagination", {}).get("pages", page)

        print(f"  sivu {page}/{pages} — {len(disc_raw)} julkaisua")

        if page >= pages:
            break

        page += 1
        sleep()

    discography = []
    seen_masters = set()

    for r in disc_raw:
        if r.get("role") != "Main":
            continue

        fmt = r.get("format", "")
        title = r.get("title", "")
        artist = r.get("artist", "")

        if should_skip_discography_format(fmt):
            continue

        # Hylkää split-julkaisut, joissa Oasis ei ole ensimmäinen artisti.
        if "/" in artist and "Oasis" not in artist.split("/")[0]:
            continue

        if r.get("type") == "master":
            mid = r.get("id")

            if mid in seen_masters:
                continue

            seen_masters.add(mid)
        else:
            mid = r.get("id")

        discography.append({
            "mid": mid,
            "title": title,
            "year": r.get("year") or 0,
            "fmt": parse_discography_fmt(fmt),
            "format_text": fmt,
            "label": r.get("label", ""),
            "thumb": r.get("thumb", ""),
        })

    print(f"  Julkaisuja diskografiassa: {len(discography)}")
    return discography


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if not USERNAME:
    USERNAME = fetch_identity_username()

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(out_dir, exist_ok=True)

updated = datetime.now().strftime("%Y-%m-%d %H:%M")

owned = fetch_collection(USERNAME)
sleep()

wants = fetch_wantlist(USERNAME)
sleep()

discography = fetch_discography()

collection_path = os.path.join(out_dir, "collection.json")
wantlist_path = os.path.join(out_dir, "wantlist.json")
discography_path = os.path.join(out_dir, "discography.json")

write_json(collection_path, {
    "meta": {
        "username": USERNAME,
        "updated": updated,
        "total": len(owned),
    },
    "owned": owned,
})

write_json(wantlist_path, {
    "meta": {
        "username": USERNAME,
        "updated": updated,
        "total": len(wants),
    },
    "wanted": wants,
})

write_json(discography_path, {
    "updated": updated,
    "total": len(discography),
    "releases": discography,
})

print()
print("Valmis!")
print(f"  Kokoelma:   {len(owned)}")
print(f"  Wantlist:   {len(wants)}")
print(f"  Diskografia:{len(discography)}")
print()
print("Seuraavaksi:")
print("  python3 data/build_oasis_data.py")
print("  git add data/ update.py && git commit -m 'Update Discogs collection and wantlist' && git push")