# Oasis Vinyl Collection — GitHub Pages

## Asennus (~5 min)

### 1. Luo GitHub-tili ja uusi repo
1. Mene [github.com](https://github.com) → Sign up (jos ei ole tiliä)
2. New repository → nimi esim. `oasis-collection`
3. Public ✓ → Create repository

### 2. Lataa tiedostot repoon
GitHub-sivulla klikkaa **uploading an existing file** ja lataa:
- `index.html`
- `data/collection.json` (luo ensin kansio `data/`)
- `update.py`

Tai jos käytät komentoriviä:
```bash
git init
git add .
git commit -m "Ensimmäinen versio"
git remote add origin https://github.com/KÄYTTÄJÄNIMI/oasis-collection.git
git push -u origin main
```

### 3. Ota GitHub Pages käyttöön
Settings → Pages → Source: **Deploy from a branch** → Branch: `main` → Save

Sivu on muutaman minuutin kuluttua osoitteessa:
**https://KÄYTTÄJÄNIMI.github.io/oasis-collection**

---

## Salasanan vaihto

`index.html` tiedostossa rivi (noin rivillä 230):
```js
const PASS_HASH = 'a47f54b...';
```

Laske uusi hash osoitteessa: https://emn178.github.io/online-tools/sha256.html
Oletussalasana on `oasis1994` — vaihda se!

---

## Kokoelman päivittäminen

Kun ostat uuden levyn:

```bash
# Päivitä Discogsista
python3 update.py SINUN_DISCOGS_TOKEN

# Vie GitHubiin
git add data/collection.json
git commit -m "Lisätty: Albumin nimi"
git push
```

Sivu päivittyy automaattisesti muutamassa minuutissa.

Token löytyy: discogs.com → Settings → Developers → Generate token

---

## Rakenne

```
oasis-collection/
├── index.html          ← Koko sivu (HTML + CSS + JS)
├── data/
│   └── collection.json ← Kokoelma-data (päivitetään skriptillä)
├── update.py           ← Discogs-hakuskripti
└── README.md
```
