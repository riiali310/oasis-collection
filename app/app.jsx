// Oasis — Vinyylikokoelma. Interaktiivinen sovellus. Teema: "The Sleeve".
const { useState, useEffect, useMemo } = React;

const PASSWORD = "liveforever";
const DISCOGS = "https://www.discogs.com/user/freeal/collection";
const QUOTES = [
  ["“Is it worth the aggravation to find yourself a job when there’s nothing worth working for?”", "Cigarettes & Alcohol"],
  ["“You and I are gonna live forever.”", "Live Forever"],
  ["“So Sally can wait, she knows it’s too late as we’re walking on by.”", "Don't Look Back in Anger"],
  ["“Maybe you’re gonna be the one that saves me.”", "Wonderwall"],
];
const TYPE_LABEL = { album: "Albumi", single: "Sinkku", special: "Erikois ★" };
const SPECIAL_LABEL = { PROMO: "PROMO", LTD: "LTD", NUM: "NUM", MINT: "MINT", TEST: "TEST", WHITE: "WHITE" };
const specialText = (r) => r.special || r.note || "";
const visibleTags = (r) => (r.tags || []).slice(0, 5);

function lsGet(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }
function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }

// Sinkun formaatti: 7" / 12" / CD
const normFmt = (r) => {
  const f = (r.format || "").toLowerCase();
  if (f.includes("12")) return '12"';
  if (f.includes("7")) return '7"';
  if (f.includes("cd")) return "CD";
  return "muu";
};

// ── Kansikuvat ─────────────────────────────────────────────
// Discogs-kuva (record.img) menee aina edelle. Jos sitä ei ole, haetaan
// oikea kansitaide live-esikatseluna ja välimuistitetaan selaimeen.
function jsonp(url) {
  return new Promise((resolve, reject) => {
    const cb = "itcb_" + Math.random().toString(36).slice(2);
    const s = document.createElement("script");
    const clean = () => { try { delete window[cb]; } catch {} s.remove(); clearTimeout(t); };
    const t = setTimeout(() => { clean(); reject(); }, 8000);
    window[cb] = (d) => { clean(); resolve(d); };
    s.onerror = () => { clean(); reject(); };
    s.src = url + (url.includes("?") ? "&" : "?") + "callback=" + cb;
    document.body.appendChild(s);
  });
}
async function fetchArt(rec) {
  const clean = rec.title.replace(/[()?'’★]/g, "").replace(/—.*$/, "").trim();
  const term = encodeURIComponent("oasis " + clean);
  const data = await jsonp(`https://itunes.apple.com/search?term=${term}&country=GB&media=music&limit=5`);
  const hit = (data.results || []).find(x => x.artworkUrl100);
  return hit ? hit.artworkUrl100.replace("100x100bb", "600x600bb") : "";
}
function useArt(base) {
  const [art, setArt] = useState(() => lsGet("oasis.art2", {}));
  useEffect(() => {
    let stop = false;
    (async () => {
      const cache = { ...art };
      for (const r of base) {
        if (r.img || cache[r.id] !== undefined) continue;
        if (r.type === "single") continue; // sinkkujen oikeat kannet vain Discogs-kuvasta (r.img)
        let url = "";
        try { url = await fetchArt(r); } catch { url = ""; }
        if (stop) return;
        cache[r.id] = url;
        setArt({ ...cache });
        lsSet("oasis.art2", cache);
        await new Promise(z => setTimeout(z, 220));
      }
    })();
    return () => { stop = true; };
  }, []);
  return art;
}

// <img> kannelle, fallback typografiseen sleeveen virheessä
function CoverImg({ src, alt }) {
  const [err, setErr] = useState(false);
  useEffect(() => setErr(false), [src]);
  if (!src || err) return null;
  return <img className="sleeve-img" src={src} alt={alt} loading="lazy" onError={() => setErr(true)} />;
}

// ── Icons ──
const IcSearch = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>;
const IcGrid = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/></svg>;
const IcList = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>;

// ── Cover (gallery) ──
function Cover({ r, editing, hidden, onOpen, onHide }) {
  const [c1, c2] = r.color;
  const hasImg = !!r._img;
  return (
    <div className={"cover" + (r.owned ? "" : " miss") + (hidden ? " ishidden" : "")} onClick={() => editing ? onHide(r.id) : onOpen(r)}>
      {editing && <button className="xbtn" onClick={(e) => { e.stopPropagation(); onHide(r.id); }}>{hidden ? "↺" : "✕"}</button>}
      <div className={"sleeve" + (hasImg ? " hasimg" : "")} style={{ background: `linear-gradient(155deg, ${c1}, ${c2})`, "--lblc": r.color[0] }}>
        <CoverImg src={r._img} alt={r.title} />
        {!hasImg && <div className="vinyl" />}
        {r.wish && !r.owned && <span className="wishflag">TOIVE</span>}
        {specialText(r) && <span className="specialflag">{specialText(r)}</span>}
        {hasImg ? (
          <div className="sleeve-scrim">
            <div className="s-foot"><span>{r.year}</span><span>{r.format}</span></div>
          </div>
        ) : (
          <div className="sleeve-in">
            <div className="s-band">{r.type === "special" ? "★ " + (r.note || "ERIKOIS") : r.label}</div>
            <div><div className="s-title">{r.title}</div></div>
            <div className="s-foot"><span>{r.year}</span><span>{r.format}</span></div>
          </div>
        )}
        {!r.owned && <div className="stamp">PUUTTUU</div>}
      </div>
      <div className="cmeta">
        <span className="cat">{r.cat}</span>
        {r.completionTotal > 1 && r.completionMissing > 0 && <span className="comp-pill">{r.completionOwned}/{r.completionTotal}</span>}
        <span className={"dot " + (r.owned ? "on" : "off")} />
      </div>
      {visibleTags(r).length > 0 && (
        <div className="tagline">
          {visibleTags(r).map(tag => <span key={tag}>{tag}</span>)}
        </div>
      )}
    </div>
  );
}

// ── List row ──
function Row({ r, editing, hidden, onOpen, onHide }) {
  const [c1, c2] = r.color;
  return (
    <div className={"row" + (r.owned ? "" : " miss") + (hidden ? " ishidden" : "")} style={hidden ? { opacity: .4 } : null} onClick={() => editing ? onHide(r.id) : onOpen(r)}>
      <div className="row-cov" style={{ background: `linear-gradient(155deg, ${c1}, ${c2})` }}>
        <CoverImg src={r._img} alt={r.title} />
      </div>
      <div className="row-title">
        {r.title}
        {specialText(r) && <span className="row-special">{specialText(r)}</span>}
        {r.completionTotal > 1 && r.completionMissing > 0 && <span className="row-completion">{r.completionOwned}/{r.completionTotal}</span>}
        <small>{TYPE_LABEL[r.type]} · {r.label}</small>
        {visibleTags(r).length > 0 && (
          <span className="row-tags">{visibleTags(r).map(tag => <em key={tag}>{tag}</em>)}</span>
        )}
      </div>
      <div className="c fmt">{r.format}</div>
      <div className="c cat-col mono">{r.cat}</div>
      <div className={"badge " + (r.owned ? "own" : "miss")}>{r.owned ? "● HYLLYSSÄ" : "○ PUUTTUU"}</div>
      <div>{editing
        ? <button className="xbtn" style={{ display: "flex" }} onClick={(e) => { e.stopPropagation(); onHide(r.id); }}>{hidden ? "↺" : "✕"}</button>
        : <span className="mono" style={{ color: "var(--ink3)", fontSize: 12 }}>{r.year}</span>}</div>
    </div>
  );
}

// ── Detail modal ──
function Detail({ r, auth, allRecords, onClose, onToggleOwned, onToggleWish }) {
  const [c1, c2] = r.color;
  useEffect(() => {
    const h = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h);
  }, []);
  const variants = (allRecords || [])
    .filter(x => x.mid === r.mid || x.title === r.title)
    .sort((a, b) => a.year - b.year || a.format.localeCompare(b.format) || a.cat.localeCompare(b.cat));

  const discogsUrl = r.release_id
    ? `https://www.discogs.com/release/${r.release_id}`
    : `https://www.discogs.com/search/?q=${encodeURIComponent("Oasis " + r.title + " " + (r.cat || ""))}`;

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="mclose" onClick={onClose}>✕</button>
        <div className="detail">
          <div className={"detail-cov" + (r.owned ? "" : " miss") + (r._img ? " hasimg" : "")} style={{ background: `linear-gradient(155deg, ${c1}, ${c2})` }}>
            <CoverImg src={r._img} alt={r.title} />
            {!r._img && <div className="vinyl" style={{ "--lblc": c1 }} />}
            {!r._img && (
              <div className="sleeve-in">
                <div className="s-band">{r.type === "special" ? "★ " + (r.note || "ERIKOIS") : r.label}</div>
                <div className="s-title" style={{ fontSize: 30 }}>{r.title}</div>
                <div className="s-foot"><span>{r.year}</span><span>{r.format}</span></div>
              </div>
            )}
            {!r.owned && <div className="stamp">PUUTTUU</div>}
          </div>
          <div className="detail-info">
            <div className="di-type">{TYPE_LABEL[r.type]}{specialText(r) ? " · " + specialText(r) : ""}</div>
            <div className="di-title">{r.title}</div>
            <div className="di-grid">
              <div className="di-cell"><div className="k">Vuosi</div><div className="v">{r.year}</div></div>
              <div className="di-cell"><div className="k">Formaatti</div><div className="v">{r.format}</div></div>
              <div className="di-cell"><div className="k">Label</div><div className="v" style={{ fontSize: 18 }}>{r.label}</div></div>
              <div className="di-cell"><div className="k">Katalogi</div><div className="v mono" style={{ fontSize: 16 }}>{r.cat}</div></div>
            </div>
            <div className="di-status">
              <span className={"dot " + (r.owned ? "on" : "off")} />
              {r.owned ? "Hyllyssä" : (r.wish ? "Puuttuu · toivelistalla" : "Puuttuu")}
            </div>
            {visibleTags(r).length > 0 && (
              <div className="detail-tags">
                {visibleTags(r).map(tag => <span key={tag}>{tag}</span>)}
              </div>
            )}
            {variants.length > 1 && (
              <div className="compare">
                <div className="compare-title">Saman julkaisun versiot <span>{r.completionOwned}/{r.completionTotal} omistettu</span></div>
                {variants.map(v => (
                  <div className={"compare-row" + (v.id === r.id ? " current" : "")} key={v.id}>
                    <span className={"dot " + (v.owned ? "on" : "off")} />
                    <span>{v.format}</span>
                    <strong>{v.cat || "—"}</strong>
                    <em>{v.year}</em>
                    {specialText(v) && <b>{specialText(v)}</b>}
                  </div>
                ))}
              </div>
            )}
            <div className="di-actions">
              <a className="btn primary" href={discogsUrl} target="_blank" rel="noreferrer">Discogsissa ↗</a>
              {auth ? (
                <button className={"btn" + (r.owned ? " danger" : "")} onClick={() => onToggleOwned(r.id)}>
                  {r.owned ? "Merkitse puuttuvaksi" : "Merkitse omistetuksi"}
                </button>
              ) : (
                <button className="btn" onClick={() => onToggleWish(r.id)}>
                  {r.wish ? "★ Poista toivelistalta" : "☆ Lisää toivelistalle"}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Login modal ──
function Login({ onClose, onSuccess }) {
  const [pw, setPw] = useState(""); const [err, setErr] = useState("");
  const submit = () => { if (pw === PASSWORD) onSuccess(); else setErr("Väärä salasana — yritä uudelleen."); };
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal login" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 420 }}>
        <button className="mclose" onClick={onClose}>✕</button>
        <h2>Kirjaudu sisään</h2>
        <p>Kirjautuneena voit muokata kokoelmaa: piilottaa kortteja ja merkitä levyjä omistetuiksi.</p>
        <label>Salasana</label>
        <input type="password" autoFocus value={pw} onChange={(e) => { setPw(e.target.value); setErr(""); }} onKeyDown={(e) => e.key === "Enter" && submit()} placeholder="••••••••" />
        <div className="err">{err}</div>
        <div className="login-act">
          <button className="btn primary" onClick={submit}>Kirjaudu</button>
          <button className="btn" onClick={onClose}>Peruuta</button>
        </div>
        <div className="hint">Demo-salasana: <b>liveforever</b></div>
      </div>
    </div>
  );
}


function ProgressRing({ label, owned, total }) {
  const pct = total ? Math.round((owned / total) * 100) : 0;
  return (
    <div className="ring-card">
      <div className="ring" style={{ "--p": pct }}>
        <span>{pct}%</span>
      </div>
      <div>
        <div className="ring-label">{label}</div>
        <div className="ring-sub">{owned}/{total}</div>
      </div>
    </div>
  );
}

function Timeline({ records }) {
  const years = Array.from(new Set(records.map(r => r.year).filter(Boolean))).sort((a, b) => a - b);
  const ownedByYear = Object.fromEntries(years.map(y => [y, records.filter(r => r.year === y && r.owned).length]));
  const totalByYear = Object.fromEntries(years.map(y => [y, records.filter(r => r.year === y).length]));
  const max = Math.max(1, ...years.map(y => totalByYear[y]));
  return (
    <section className="timeline">
      <div className="timeline-head">
        <span>Collection timeline</span>
        <i>julkaisut vuosittain</i>
      </div>
      <div className="timeline-bars">
        {years.map(y => (
          <div className="yearbar" key={y} title={`${y}: ${ownedByYear[y]}/${totalByYear[y]}`}>
            <div className="yb-track" style={{ height: Math.max(12, (totalByYear[y] / max) * 92) }}>
              <span style={{ height: `${Math.round((ownedByYear[y] / totalByYear[y]) * 100)}%` }} />
            </div>
            <b>{String(y).slice(2)}</b>
          </div>
        ))}
      </div>
    </section>
  );
}

function CreationTracker({ records, onOpen }) {
  const creation = records.filter(r => {
    const label = (r.label || "").toLowerCase();
    const cat = (r.cat || "").toUpperCase();
    return label.includes("creation") || cat.startsWith("CRE") || cat.startsWith("CTP");
  });

  if (!creation.length) return null;

  const owned = creation.filter(r => r.owned);
  const missing = creation.filter(r => !r.owned);
  const pct = Math.round((owned.length / creation.length) * 100);

  const isPromo = (r) => (r.tags || []).some(t =>
    ["Promo", "White Label", "Test Press", "Advance", "Sampler", "Acetate"].includes(t)
  );

  const groups = [
    ['7" singles', r => r.format === '7"'],
    ['12" singles', r => r.format === '12"'],
    ["Promos", isPromo],
    ["Albums / LPs", r => r.type === "album"],
    ["Box sets", r => (r.tags || []).includes("Box")],
  ].filter(([, fn]) => creation.some(fn));

  return (
    <section className="creation-tracker">
      <div className="creation-head">
        <div>
          <span>Creation Records Tracker</span>
          <i>alkuperäinen Oasis-ydinsarja</i>
        </div>
        <strong>{owned.length}/{creation.length}</strong>
      </div>

      <div className="creation-bar">
        <span style={{ width: pct + "%" }} />
      </div>

      <div className="creation-groups">
        {groups.map(([label, fn]) => {
          const list = creation.filter(fn);
          const own = list.filter(r => r.owned).length;

          return (
            <button className="creation-group" key={label} onClick={() => {
              const firstMissing = list.find(r => !r.owned);
              if (firstMissing) onOpen(firstMissing);
            }}>
              <b>{own}/{list.length}</b>
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      {missing.length > 0 && (
        <div className="creation-missing">
          <div className="creation-sub">Missing Creation</div>
          {missing.slice(0, 8).map(r => (
            <button key={r.id} onClick={() => onOpen(r)}>
              <span>{r.title}</span>
              <em>{r.format} · {r.cat || r.label}</em>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function AlmostComplete({ records, onOpen }) {
  const groups = useMemo(() => {
    const map = {};
    records.forEach(r => {
      const key = r.mid || r.title;
      if (!map[key]) map[key] = [];
      map[key].push(r);
    });

    return Object.values(map)
      .map(group => {
        const owned = group.filter(r => r.owned);
        const missing = group.filter(r => !r.owned);
        const sorted = [...group].sort((a, b) =>
          a.year - b.year ||
          String(a.format).localeCompare(String(b.format)) ||
          String(a.cat).localeCompare(String(b.cat))
        );

        return {
          key: group[0].mid || group[0].title,
          title: group[0].title,
          owned,
          missing,
          total: group.length,
          records: sorted,
          openRecord: missing[0] || owned[0] || group[0],
        };
      })
      .filter(g => g.total > 1 && g.owned.length > 0 && g.missing.length > 0)
      .sort((a, b) =>
        a.missing.length - b.missing.length ||
        b.owned.length - a.owned.length ||
        a.title.localeCompare(b.title)
      )
      .slice(0, 6);
  }, [records]);

  if (!groups.length) return null;

  return (
    <section className="almost">
      <div className="almost-head">
        <span>Almost Complete</span>
        <i>julkaisut, joista puuttuu enää muutama versio</i>
      </div>
      <div className="almost-grid">
        {groups.map(g => (
          <button className="almost-card" key={g.key} onClick={() => onOpen(g.openRecord)}>
            <div className="almost-top">
              <strong>{g.title}</strong>
              <span>{g.owned.length}/{g.total}</span>
            </div>
            <div className="almost-bar">
              <span style={{ width: `${Math.round((g.owned.length / g.total) * 100)}%` }} />
            </div>
            <div className="almost-missing">
              {g.missing.slice(0, 3).map(r => (
                <em key={r.id}>{r.format}{r.cat ? ` · ${r.cat}` : ""}</em>
              ))}
              {g.missing.length > 3 && <em>+{g.missing.length - 3} lisää</em>}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

// ── App ──
function App() {
  const base = window.OASIS || [];
  const art = useArt(base);
  const [ownOverride, setOwnOverride] = useState(() => lsGet("oasis.own", {}));
  const [wishOverride, setWishOverride] = useState(() => lsGet("oasis.wish", {}));
  const [hiddenIds, setHiddenIds] = useState(() => lsGet("oasis.hidden", []));
  const [auth, setAuth] = useState(() => lsGet("oasis.auth", false));
  const [editing, setEditing] = useState(false);
  const [showHidden, setShowHidden] = useState(false);

  const [own, setOwn] = useState("all");          // all | own | miss
  const [types, setTypes] = useState({ album: true, single: true, special: true });
  const [fmt, setFmt] = useState({ '7"': true, '12"': true });
  const [sort, setSort] = useState(() => lsGet("oasis.sort", "year"));
  const [view, setView] = useState(() => lsGet("oasis.view", "grid"));
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [quote] = useState(() => QUOTES[Math.floor(Math.random() * QUOTES.length)]);

  useEffect(() => lsSet("oasis.own", ownOverride), [ownOverride]);
  useEffect(() => lsSet("oasis.wish", wishOverride), [wishOverride]);
  useEffect(() => lsSet("oasis.hidden", hiddenIds), [hiddenIds]);
  useEffect(() => lsSet("oasis.auth", auth), [auth]);
  useEffect(() => lsSet("oasis.sort", sort), [sort]);
  useEffect(() => lsSet("oasis.view", view), [view]);

  // merge overrides + cover art + master completion
  const records = useMemo(() => {
    const merged = base.map(r => ({
      ...r,
      owned: r.id in ownOverride ? ownOverride[r.id] : r.owned,
      wish: r.id in wishOverride ? wishOverride[r.id] : r.wish,
      _img: r.img || art[r.id] || "",
    }));

    const groups = {};
    merged.forEach(r => {
      const key = r.mid || r.title;
      if (!groups[key]) groups[key] = [];
      groups[key].push(r);
    });

    return merged.map(r => {
      const group = groups[r.mid || r.title] || [r];
      const completionOwned = group.filter(x => x.owned).length;
      const completionTotal = group.length;

      return {
        ...r,
        completionOwned,
        completionTotal,
        completionMissing: completionTotal - completionOwned,
      };
    });
  }, [base, ownOverride, wishOverride, art]);

  const ownedCount = records.filter(r => r.owned).length;
  const total = records.length;
  const pct = Math.round((ownedCount / total) * 100);
  const counts = {
    album: records.filter(r => r.type === "album").length,
    single: records.filter(r => r.type === "single").length,
    special: records.filter(r => r.type === "special").length,
  };
  const ownedBy = (t) => records.filter(r => r.type === t && r.owned).length;

  const hiddenSet = new Set(hiddenIds);
  const filtered = useMemo(() => {
    let list = records.filter(r => {
      if (!types[r.type]) return false;
      if (r.type === "single" && !fmt[normFmt(r)]) return false;
      if (own === "own" && !r.owned) return false;
      if (own === "miss" && r.owned) return false;
      if (q) {
        const needle = q.toLowerCase();
        const hay = [r.title, r.year, r.cat, r.label, r.format, r.type, specialText(r), ...(r.tags || [])].join(" ").toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      if (!editing && !showHidden && hiddenSet.has(r.id)) return false;
      return true;
    });
    list.sort((a, b) => {
      if (sort === "year") return a.year - b.year || a.title.localeCompare(b.title);
      if (sort === "name") return a.title.localeCompare(b.title) || a.year - b.year;
      if (sort === "owned") return (b.owned - a.owned) || a.year - b.year;
      return 0;
    });
    return list;
  }, [records, types, fmt, own, q, sort, editing, showHidden, hiddenIds]);

  const singleOnly = types.single && !types.album && !types.special;

  const toggleType = (t) => setTypes(s => ({ ...s, [t]: !s[t] }));
  const toggleFmt = (f) => setFmt(s => ({ ...s, [f]: !s[f] }));
  const toggleOwned = (id) => setOwnOverride(s => ({ ...s, [id]: !(records.find(r => r.id === id).owned) }));
  const toggleWish = (id) => setWishOverride(s => ({ ...s, [id]: !(records.find(r => r.id === id).wish) }));
  const toggleHide = (id) => setHiddenIds(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);
  const logout = () => { setAuth(false); setEditing(false); };

  // keep selected in sync with overrides
  const selLive = sel ? records.find(r => r.id === sel.id) : null;

  const renderItems = (list, head) => view === "grid" ? (
    <div className="grid">
      {list.map(r => <Cover key={r.id} r={r} editing={editing} hidden={hiddenSet.has(r.id)} onOpen={setSel} onHide={toggleHide} />)}
    </div>
  ) : (
    <div className="list">
      {head && (
        <div className="row row-head">
          <span></span><span>Nimi</span><span>Formaatti</span><span>Katalogi</span><span>Tila</span><span></span>
        </div>
      )}
      {list.map(r => <Row key={r.id} r={r} editing={editing} hidden={hiddenSet.has(r.id)} onOpen={setSel} onHide={toggleHide} />)}
    </div>
  );

  const fmtGroups = ['7"', '12"'].map(f => [f, filtered.filter(r => normFmt(r) === f)]).filter(([, l]) => l.length);

  return (
    <div className={"wrap" + (editing ? " editing" : "")}>
      {/* Header */}
      <header className="hd">
        <div className="hd-brand">
          <div className="logo">oasis</div>
          <div className="hd-sub">VINYYLIKOKOELMA · est. 1994</div>
        </div>
        <div className="hd-act">
          {auth && (
            <button className={"pill" + (editing ? " editon" : "")} onClick={() => setEditing(e => !e)}>
              {editing ? "✓ Valmis" : "✎ Muokkaa"}
            </button>
          )}
          <a className="pill" href={DISCOGS} target="_blank" rel="noreferrer">Discogs ↗</a>
          {auth
            ? <button className="pill gear" title="Kirjaudu ulos" onClick={logout}>⎋</button>
            : <button className="pill gear" title="Kirjaudu" onClick={() => setLoginOpen(true)}>⚙</button>}
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div>
          <div className="hero-num">{ownedCount}<span>/{total}</span></div>
          <div className="hero-lab">levyä hyllyssä</div>
          <div className="bar"><span style={{ width: pct + "%" }} /></div>
          <div className="bar-cap">{pct}% kokoelmasta · {total - ownedCount} puuttuu</div>
        </div>
        <div className="hero-r">
          <div className="breakdown rings">
            <ProgressRing label="Albumit" owned={ownedBy("album")} total={counts.album} />
            <ProgressRing label="Sinkut" owned={ownedBy("single")} total={counts.single} />
            <ProgressRing label="Erikoiset" owned={ownedBy("special")} total={counts.special} />
          </div>
          <div className="quote">{quote[0]}<b>— {quote[1]}</b></div>
        </div>
      </section>

      <CreationTracker records={records} onOpen={setSel} />
      <AlmostComplete records={records} onOpen={setSel} />

      {/* Controls */}
      <div className="ctrl">
        <div className="ctrl-l">
          <div className="tabs">
            {[["all", "Kaikki"], ["own", "Omistaa"], ["miss", "Puuttuu"]].map(([k, l]) => (
              <button key={k} className={"tab" + (own === k ? " on" : "")} onClick={() => setOwn(k)}>{l}</button>
            ))}
          </div>
          <div className="chips">
            {[["album", "Albumit"], ["single", "Sinkut"], ["special", "Erikoiset ★"]].map(([t, l]) => (
              <button key={t} className={"chip" + (types[t] ? " on" : "")} onClick={() => toggleType(t)}>{l}</button>
            ))}
          </div>
        </div>
        <div className="ctrl-r">
          <div className="search">
            <IcSearch />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="hae…" />
          </div>
          <select className="sel" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="year">Vuosi ↑</option>
            <option value="name">Nimi A–Z</option>
            <option value="owned">Omistaa ensin</option>
          </select>
          <div className="view">
            <button className={view === "grid" ? "on" : ""} onClick={() => setView("grid")} title="Galleria"><IcGrid /></button>
            <button className={view === "list" ? "on" : ""} onClick={() => setView("list")} title="Lista"><IcList /></button>
          </div>
        </div>
      </div>

      {/* Sinkun formaatti — näkyy kun sinkut ovat mukana */}
      {singleOnly && (
        <div className="subfilter">
          <span className="subfilter-l">Sinkun formaatti</span>
          <div className="chips">
            {['7"', '12"'].map(f => (
              <button key={f} className={"chip" + (fmt[f] ? " on" : "")} onClick={() => toggleFmt(f)}>{f}</button>
            ))}
          </div>
        </div>
      )}

      {/* Meta line */}
      <div className="meta-line">
        <span>{filtered.length} {filtered.length === 1 ? "levy" : "levyä"} näkyvissä{editing ? " · muokkaustila päällä" : ""}</span>
        <span style={{ display: "flex", gap: 16, alignItems: "center" }}>
          {hiddenIds.length > 0 && (
            <button className="hidden-toggle" onClick={() => setShowHidden(s => !s)}>
              {showHidden ? "Piilota piilotetut" : "Näytä piilotetut"} ({hiddenIds.length})
            </button>
          )}
          {editing && hiddenIds.length > 0 && (
            <button className="hidden-toggle" onClick={() => setHiddenIds([])}>Palauta kaikki</button>
          )}
          <span>Päivitetty: 06/2026</span>
        </span>
      </div>

      {/* Body */}
      {filtered.length === 0 ? (
        <div className="empty">
          <div className="e-t">Ei tuloksia</div>
          <div className="e-s">Kokeile toista suodatinta tai hakusanaa.</div>
        </div>
      ) : singleOnly ? (
        fmtGroups.map(([f, list]) => (
          <section className="fmt-group" key={f}>
            <h3 className="fmt-h"><span className="fmt-tag">{f}</span> {f === '7"' ? "seitsem\u00e4ntuumaiset" : "kaksitoistatuumaiset"} <i>{list.length}</i></h3>
            {renderItems(list, false)}
          </section>
        ))
      ) : (
        renderItems(filtered, true)
      )}

      {selLive && <Detail r={selLive} auth={auth} allRecords={records} onClose={() => setSel(null)} onToggleOwned={toggleOwned} onToggleWish={toggleWish} />}
      {loginOpen && <Login onClose={() => setLoginOpen(false)} onSuccess={() => { setAuth(true); setLoginOpen(false); setEditing(true); }} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
