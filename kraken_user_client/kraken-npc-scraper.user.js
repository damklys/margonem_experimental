// ==UserScript==
// @name         Kraken NPC Scraper
// @namespace    kraken.margonem
// @version      1.8.202610182345
// @description  Zbiera z map tylko odłamki, elity III i skrzynie (z opisem i ikonką); eksport do JSON
// @match        https://*.margonem.pl/
// @exclude      https://margonem.pl/*
// @exclude      https://www.margonem.pl/*
// @exclude      https://forum.margonem.pl/*
// @exclude      https://commons.margonem.pl/*
// @exclude      https://dev-commons.margonem.pl/*
// @exclude      https://new.margonem.pl/*
// @exclude      https://public-api.margonem.pl/*
// @grant        none
// @sandbox      raw
// @inject-into  page
// @run-at       document-idle
// @noframes
// ==/UserScript==

(function () {
  'use strict';

  const KEY = 'kraken:npcscraper';
  const NPC_IMG = 'https://micc.garmory-cdn.cloud/obrazki/npc/';
  const TYPES = { 0: 'NPC', 1: 'NPC', 2: 'potwór', 3: 'potwór agresywny', 4: 'obiekt', 5: 'obiekt', 6: 'obiekt', 7: 'obiekt' };
  const PROF = { w: 'wojownik', p: 'paladyn', b: 'tancerz ostrzy', h: 'łowca', t: 'tropiciel', m: 'mag' };

  const engine = () => (typeof window.getEngine === 'function' ? window.getEngine() : window.Engine) || null;
  const mapName = () => String(engine()?.map?.d?.name || '').trim();
  const load = () => {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || { auto: true, maps: {} };
    } catch (_) {
      return { auto: true, maps: {} };
    }
  };
  const save = (db) => {
    try {
      localStorage.setItem(KEY, JSON.stringify(db));
    } catch (e) {
      console.warn('[NPC Scraper] zapis nieudany', e);
    }
  };

  // Ranga z wt (silnik): <10 zwykły, 10–19 elita, 20–29 elita II, 30–79 elita III, 80–99 heros, ≥100 tytan.
  function rank(wt) {
    if (wt >= 100) return 'tytan';
    if (wt >= 80) return 'heros';
    if (wt >= 30) return 'elita III';
    if (wt >= 20) return 'elita II';
    if (wt >= 10) return 'elita';
    return 'zwykły';
  }

  // Ranga z dymka gry (<i class="npc-class">elita III</i>) – działa też dla obiektów typu 0; bez dymka z wt.
  function rankOf(d, tip) {
    const m = /class="npc-class"[^>]*>([^<]+)</.exec(tip?.html || '');
    if (m) return m[1].trim();
    return +d.wt >= 10 ? rank(+d.wt) : '';
  }

  // Kopalnie (jak w bocie): złoża = odłamki, skrzynie i E3 każdej kopalni po nazwie – np. Kopalnia Krwawej Pychy (300 lvl):
  // „Zamrożony czarodziej” (złoże), „Zaklęta skrzynia”, E3 „Erktos”.
  const MINE = {
    odlamek: ['Pokaźne złoże', 'Naładowany kryształ', 'Błękitne złoże', 'Niewydobyty minerał', 'Sterta kości', 'Zamrożony czarodziej'],
    skrzynia: ['Stara skrzynia', 'Zdradliwa skrzynia', 'Świątynna skrzynia', 'Zakopana skrzynia', 'Zaklęta skrzynia'],
    e3: ['Tarmus Wuden', 'Vonaros', 'Wyznawca Ciemnych Mocy', 'Szkielet Władcy Żywiołów', 'Erktos'],
  };
  const isMine = (kind, n) => MINE[kind].some((x) => x.toLowerCase() === String(n.nick || '').trim().toLowerCase());

  // Co zapisujemy: odłamki (nazwa; w grze to „Sterta kości”), elity III (ranga), skrzynie (nazwa lub ikonka) + własne nazwy z panelu.
  const KINDS = {
    // Odłamki: po nazwie albo ta sama kategoria co „Sterta kości” – obiekt (nie potwór, type 0) z klasą „elita” w dymku
    // (tak samo oznaczony jest „Niewydobyty minerał”).
    odlamek: { label: 'Odłamki', test: (n) => isMine('odlamek', n) || /odłam|sterta kości|niewydobyt/i.test(n.nick) || (+n.type === 0 && /^elita$/i.test(n.rank || '')) },
    e3: { label: 'E3', test: (n) => isMine('e3', n) || /elita III/i.test(n.rank) },
    skrzynia: { label: 'Skrzynie', test: (n) => isMine('skrzynia', n) || /skrzyn|skrzynk|kufer/i.test(n.nick) || /skrzyn/i.test(n.icon) },
  };
  function kindOf(n, db) {
    for (const [k, v] of Object.entries(KINDS)) if (db.kinds?.[k] !== false && v.test(n)) return k;
    const extra = (db.extra || '').split(',').map((x) => x.trim().toLowerCase()).filter(Boolean);
    if (extra.some((x) => n.nick.toLowerCase().includes(x))) return 'inne';
    return '';
  }

  function iconUrl(icon) {
    if (!icon) return '';
    if (/^(https?:)?\/\//.test(icon)) return icon;
    return NPC_IMG + String(icon).replace(/^\/+/, '');
  }

  const stripHtml = (h) => {
    const el = document.createElement('div');
    el.innerHTML = String(h);
    return el.textContent.replace(/\s+/g, ' ').trim();
  };

  // Treść dymka z gry, jeśli obiekt ją udostępnia (różne wersje silnika – kilka prób).
  function tipOf(o) {
    for (const k of ['tip', 'getTip', 'getTipContent', 'createTip', 'tipContent']) {
      try {
        let v = o[k];
        if (typeof v === 'function') v = v.call(o);
        if (Array.isArray(v)) v = v[0];
        if (v && typeof v === 'string') return { html: v, text: stripHtml(v) };
      } catch (_) {}
    }
    for (const k of ['tip', 'opis', 'desc', 'description']) {
      const v = o.d?.[k];
      if (v && typeof v === 'string') return { html: v, text: stripHtml(v) };
    }
    return null;
  }

  // Wszystkie proste pola d (liczby/teksty) – gdyby czegoś zabrakło w polach głównych.
  function rawOf(d) {
    const out = {};
    for (const [k, v] of Object.entries(d || {})) if (v == null || ['string', 'number', 'boolean'].includes(typeof v)) out[k] = v;
    return out;
  }

  function list() {
    const npcs = engine()?.npcs;
    if (!npcs) return [];
    let arr = [];
    try {
      arr = npcs.getDrawableList?.() || [];
    } catch (_) {}
    if (!arr.length) {
      try {
        arr = Object.values(npcs.check?.() || {});
      } catch (_) {}
    }
    return arr.filter((o) => o && o.d && o.d.nick);
  }

  function describe(d, tip) {
    const wt = +d.wt || 0;
    const type = +d.type || 0;
    const parts = [TYPES[type] || `typ ${type}`];
    const r = rankOf(d, tip);
    if (r) parts.push(r);
    if (+d.lvl) parts.push(`lvl ${+d.lvl}${d.prof ? PROF[d.prof] ? ' ' + PROF[d.prof] : ' ' + d.prof : ''}`);
    if (+d.grp) parts.push(`grupa ${+d.grp}`);
    if (tip?.text) parts.push(tip.text);
    return parts.join(' · ');
  }

  function collect(quiet) {
    const map = mapName();
    if (!map) return 0;
    const eng = engine();
    const now = new Date().toISOString();
    const db = load();
    const rec = (db.maps[map] = db.maps[map] || { id: null, npcs: {} });
    // Wpisy z wcześniejszej wersji (wszystko) albo z wyłączonych grup – usuwamy.
    for (const [k, n] of Object.entries(rec.npcs)) if (!kindOf(n, db)) delete rec.npcs[k];
    rec.id = +eng?.map?.d?.id || rec.id;
    rec.ts = now;
    let added = 0;
    // Na bieżącej mapie trzymamy tylko to, co teraz na niej jest – zebrane/zabite znika z listy.
    // Pusta lista (mapa jeszcze się wczytuje) niczego nie usuwa.
    const now_ = list();
    if (now_.length) {
      const live = new Set(now_.map((o) => `${o.d.nick}|${+o.d.x}|${+o.d.y}`));
      for (const k of Object.keys(rec.npcs)) if (!live.has(k)) delete rec.npcs[k];
    }
    for (const o of now_) {
      const d = o.d;
      const tip = tipOf(o);
      const key = `${d.nick}|${+d.x}|${+d.y}`;
      const wt = +d.wt || 0;
      const type = +d.type || 0;
      const kind = kindOf({ nick: d.nick, icon: d.icon || '', rank: rankOf(d, tip), type: +d.type || 0 }, db);
      if (!kind) continue;
      if (!rec.npcs[key]) added++;
      rec.npcs[key] = {
        kind,
        id: +d.id || null,
        tpl: +d.tpl || null,
        nick: d.nick,
        type,
        typeName: TYPES[type] || `typ ${type}`,
        rank: rankOf(d, tip),
        wt,
        lvl: +d.lvl || 0,
        prof: d.prof || '',
        grp: +d.grp || 0,
        x: +d.x,
        y: +d.y,
        actions: +d.actions || 0,
        icon: d.icon || '',
        iconUrl: iconUrl(d.icon),
        opis: describe(d, tip),
        tipHtml: tip?.html || '',
        raw: rawOf(d),
        seen: now,
      };
    }
    if (!Object.keys(rec.npcs).length) delete db.maps[map];
    save(db);
    render();
    if (!quiet) console.log(`[NPC Scraper] '${map}': ${Object.keys(rec.npcs).length} NPC (nowych ${added})`);
    return added;
  }

  function flat(db = load()) {
    const out = [];
    for (const [map, rec] of Object.entries(db.maps)) for (const n of Object.values(rec.npcs)) out.push({ map, mapId: rec.id, ...n });
    return out;
  }

  function download(name, text) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => (URL.revokeObjectURL(a.href), a.remove()), 1000);
  }

  // ───────── odległość z kolizjami ─────────
  const N4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let gridKey = '';
  let gridWalk = null;
  // Mapa przechodnich kratek (kolizje silnika, bit 1 = ściana); dopóki kolizje się nie wczytały – null.
  function grid() {
    try {
      const M = engine().map;
      const C = M.col;
      const W = +M.d.x;
      const H = +M.d.y;
      if (!C || typeof C.check !== 'function' || !(W > 0 && H > 0)) return null;
      const key = `${M.d.id}|${W}x${H}`;
      if (gridKey !== key) {
        const walk = new Uint8Array(W * H);
        let walls = 0;
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const free = (C.check(x, y) & 1) === 0;
          walk[y * W + x] = free ? 1 : 0;
          if (!free) walls++;
        }
        if (!walls) return null;
        gridKey = key;
        gridWalk = walk;
      }
      return { W, H, walk: gridWalk };
    } catch (_) {
      return null;
    }
  }
  const heroPos = () => {
    const d = engine()?.hero?.d;
    return d ? { x: Math.round(+d.x), y: Math.round(+d.y) } : null;
  };
  // BFS od gracza (4 kierunki); start może leżeć na kratce zablokowanej.
  function bfs(g, sx, sy) {
    const D = new Int32Array(g.W * g.H).fill(-1);
    if (sx < 0 || sy < 0 || sx >= g.W || sy >= g.H) return D;
    const q = [sx, sy];
    D[sy * g.W + sx] = 0;
    for (let i = 0; i < q.length; i += 2) {
      const x = q[i];
      const y = q[i + 1];
      const v = D[y * g.W + x];
      for (const [dx, dy] of N4) {
        const nx = x + dx;
        const ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= g.W || ny >= g.H) continue;
        const k = ny * g.W + nx;
        if (g.walk[k] && D[k] < 0) {
          D[k] = v + 1;
          q.push(nx, ny);
        }
      }
    }
    return D;
  }
  // Najbliższa osiągalna kratka: sam obiekt albo pole obok (obiekty zwykle stoją na kolizji). null = brak drogi.
  function reach(g, D, x, y) {
    let best = null;
    for (const [dx, dy] of [[0, 0], ...N4]) {
      const nx = x + dx;
      const ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= g.W || ny >= g.H) continue;
      const v = D[ny * g.W + nx];
      if (v >= 0 && (!best || v < best.d)) best = { d: v, x: nx, y: ny };
    }
    return best;
  }
  // Odległości do wpisów bieżącej mapy; bez kolizji – odległość w linii prostej (Czebyszew), oznaczona „~”.
  function withDistance(rows) {
    const h = heroPos();
    if (!h) return rows.map((n) => ({ ...n, dist: null }));
    const g = grid();
    if (!g) return rows.map((n) => ({ ...n, dist: Math.max(Math.abs(n.x - h.x), Math.abs(n.y - h.y)), approx: true, go: { x: n.x, y: n.y } }));
    const D = bfs(g, h.x, h.y);
    return rows.map((n) => {
      const r = reach(g, D, n.x, n.y);
      return { ...n, dist: r ? r.d : null, go: r ? { x: r.x, y: r.y } : null };
    });
  }
  // Osobny zasięg dla każdej grupy (db.ranges[kind]): r kratek od gracza w każdą stronę, 0 = cała mapa; „inne” – bez limitu.
  const rangeOf = (db, kind) => Math.max(0, Math.floor(+db.ranges?.[kind] || 0));
  function inRange(rows, db) {
    const h = heroPos();
    if (!h) return rows;
    return rows.filter((n) => {
      const r = rangeOf(db, n.kind);
      return !r || (Math.abs(n.x - h.x) <= r && Math.abs(n.y - h.y) <= r);
    });
  }
  function goTo(x, y) {
    try {
      const hero = engine().hero;
      if (typeof hero.autoGoTo === 'function') hero.autoGoTo({ x, y }, false);
    } catch (e) {
      console.warn('[NPC Scraper] podejście nieudane', e);
    }
  }

  // ───────── panel ─────────
  let panel;
  let filter = '';
  function render() {
    if (!panel) return;
    const db = load();
    const all = flat(db);
    const map = mapName();
    const here = all.filter((n) => n.map === map);
    const by = (k) => all.filter((n) => n.kind === k).length;
    panel.querySelector('.ks-stats').textContent =
      `Map: ${Object.keys(db.maps).length} · odłamki ${by('odlamek')} · E3 ${by('e3')} · skrzynie ${by('skrzynia')} · inne ${by('inne')}`;
    panel.querySelector('.ks-auto').checked = !!db.auto;
    for (const el of panel.querySelectorAll('[data-kind]')) el.checked = db.kinds?.[el.dataset.kind] !== false;
    const ex = panel.querySelector('.ks-extra');
    if (document.activeElement !== ex) ex.value = db.extra || '';
    const f = filter.toLowerCase();
    // Bieżąca mapa: od najbliższego drogą (kolizje), nieosiągalne na końcu; wyszukiwanie po wszystkich mapach – bez sortowania.
    const rows = f
      ? all.filter((n) => `${n.nick} ${n.map} ${n.opis}`.toLowerCase().includes(f)).slice(0, 300)
      : withDistance(inRange(here, db)).sort((a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9));
    panel.querySelector('.ks-title').textContent = f ? `Szukaj: ${rows.length}` : `${map || '—'}: ${rows.length}${rows.length !== here.length ? ` w zasięgu (z ${here.length})` : ''}`;
    for (const rg of panel.querySelectorAll('[data-range]')) if (document.activeElement !== rg) rg.value = rangeOf(db, rg.dataset.range) || '';
    const box = panel.querySelector('.ks-list');
    box.textContent = '';
    for (const n of rows) {
      const row = document.createElement('div');
      row.className = 'ks-row';
      row.title = n.opis;
      const img = document.createElement('div');
      img.className = 'ks-ico';
      if (n.iconUrl) img.style.backgroundImage = `url("${n.iconUrl}")`;
      const txt = document.createElement('div');
      txt.innerHTML = '';
      const b = document.createElement('b');
      b.textContent = n.nick;
      const s = document.createElement('small');
      const dist = n.map !== map ? '' : n.dist == null ? 'brak drogi · ' : `${n.approx ? '~' : ''}${n.dist} kr. · `;
      s.textContent = `${f ? n.map + ' · ' : ''}${dist}(${n.x},${n.y}) ${n.opis}`;
      txt.className = 'ks-txt';
      txt.append(b, document.createElement('br'), s);
      row.append(img, txt);
      const go = n.go || (n.map === map ? { x: n.x, y: n.y } : null);
      if (go) {
        const btn = document.createElement('button');
        btn.textContent = 'Podejdź';
        // mousedown, nie click: lista odświeża się co sekundę i mogłaby podmienić przycisk w trakcie kliknięcia.
        btn.addEventListener('mousedown', (e) => (e.preventDefault(), goTo(go.x, go.y)));
        row.appendChild(btn);
      }
      box.appendChild(row);
    }
  }

  function buildPanel() {
    const css = document.createElement('style');
    css.textContent = `
#ks-panel{position:fixed;left:8px;bottom:8px;z-index:99999;width:340px;max-height:60vh;display:flex;flex-direction:column;background:#151a22ee;color:#dde;font:12px/1.3 sans-serif;border:1px solid #445;border-radius:6px;box-shadow:0 2px 10px #0008}
#ks-panel header{display:flex;align-items:center;gap:6px;padding:5px 7px;background:#222a36;border-radius:6px 6px 0 0;cursor:move}
#ks-panel header b{flex:1}
#ks-panel.min .ks-body{display:none}
#ks-panel .ks-body{display:flex;flex-direction:column;gap:5px;padding:6px;min-height:0}
#ks-panel button{background:#2d3a4d;color:#dde;border:1px solid #556;border-radius:4px;padding:2px 7px;cursor:pointer;font-size:12px}
#ks-panel button:hover{background:#3b4c64}
#ks-panel input[type=number]{background:#0d1117;color:#dde;border:1px solid #445;border-radius:4px;padding:2px 4px}
#ks-panel input[type=text]{width:100%;box-sizing:border-box;background:#0d1117;color:#dde;border:1px solid #445;border-radius:4px;padding:3px 5px}
#ks-panel .ks-btns{display:flex;flex-wrap:wrap;gap:4px;align-items:center}
#ks-panel .ks-stats{color:#9ab;font-size:11px}
#ks-panel .ks-title{font-weight:bold}
#ks-panel .ks-list{overflow:auto;min-height:0;flex:1}
#ks-panel .ks-row{display:flex;gap:6px;align-items:center;padding:2px 0;border-bottom:1px solid #2a3240}
#ks-panel .ks-ico{width:32px;height:32px;flex:none;background:no-repeat 0 0;background-size:auto;image-rendering:pixelated;overflow:hidden}
#ks-panel small{color:#9ab}
#ks-panel .ks-kinds{display:grid;grid-template-columns:auto auto;gap:3px 10px;align-items:center}
#ks-panel .ks-kinds input[type=number]{width:52px}
#ks-panel .ks-txt{flex:1;min-width:0}
#ks-panel .ks-row button{flex:none}`;
    document.head.appendChild(css);
    panel = document.createElement('div');
    panel.id = 'ks-panel';
    panel.innerHTML = `
<header><b>🐙 NPC Scraper</b><button data-a="min" title="Zwiń">–</button></header>
<div class="ks-body">
  <div class="ks-btns">
    <button data-a="collect">Zbierz teraz</button>
    <button data-a="json">Eksport JSON</button>
    <button data-a="jsonmap">JSON wg map</button>
    <button data-a="clear">Wyczyść</button>
    <label><input type="checkbox" class="ks-auto"> auto po wejściu na mapę</label>
  </div>
  <div class="ks-kinds">${Object.entries(KINDS)
    .map(([k, v]) => `<label><input type="checkbox" data-kind="${k}"> ${v.label}</label><span>zasięg <input type="number" data-range="${k}" min="0" step="1" placeholder="mapa"> kr.</span>`)
    .join('')}</div>
  <small>Zasięg: kratek od postaci w każdą stronę; puste/0 = cała mapa.</small>
  <input type="text" class="ks-extra" placeholder="Dodatkowe nazwy (po przecinku), np. Niewydobyty minerał">
  <div class="ks-stats"></div>
  <input type="text" class="ks-filter" placeholder="Szukaj we wszystkich mapach (nazwa, mapa, opis)…">
  <div class="ks-title"></div>
  <div class="ks-list"></div>
</div>`;
    document.body.appendChild(panel);
    panel.addEventListener('click', (e) => {
      const a = e.target.closest('button')?.dataset.a;
      if (!a) return;
      if (a === 'min') panel.classList.toggle('min');
      if (a === 'collect') collect();
      if (a === 'json') download(`npc-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(flat(), null, 1));
      if (a === 'jsonmap') download(`npc-mapy-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(load().maps, null, 1));
      if (a === 'clear' && confirm('Usunąć wszystkie zebrane wpisy?')) {
        const db = load();
        db.maps = {};
        save(db);
        render();
      }
    });
    panel.querySelector('.ks-auto').addEventListener('change', (e) => {
      const db = load();
      db.auto = e.target.checked;
      save(db);
    });
    panel.addEventListener('change', (e) => {
      const k = e.target.dataset?.kind;
      if (!k) return;
      const db = load();
      db.kinds = { ...(db.kinds || {}), [k]: e.target.checked };
      save(db);
    });
    panel.addEventListener('input', (e) => {
      const k = e.target.dataset?.range;
      if (!k) return;
      const db = load();
      db.ranges = { ...(db.ranges || {}), [k]: Math.max(0, Math.floor(+e.target.value || 0)) };
      save(db);
    });
    panel.querySelector('.ks-extra').addEventListener('change', (e) => {
      const db = load();
      db.extra = e.target.value;
      save(db);
    });
    panel.querySelector('.ks-filter').addEventListener('input', (e) => {
      filter = e.target.value.trim();
      render();
    });
    // Przeciąganie za nagłówek.
    const head = panel.querySelector('header');
    head.addEventListener('mousedown', (e) => {
      if (e.target.closest('button')) return;
      const r = panel.getBoundingClientRect();
      const dx = e.clientX - r.left;
      const dy = e.clientY - r.top;
      const move = (ev) => Object.assign(panel.style, { left: ev.clientX - dx + 'px', top: ev.clientY - dy + 'px', bottom: 'auto' });
      const up = () => (removeEventListener('mousemove', move), removeEventListener('mouseup', up));
      addEventListener('mousemove', move);
      addEventListener('mouseup', up);
    });
    render();
  }

  // Auto: co 0,5 s zbieramy bieżącą mapę (nowe i znikające obiekty); po zmianie mapy 1 s przerwy na wczytanie.
  // Zbieranie samo odświeża listę; przy wyłączonym auto – samo odświeżenie (odległości).
  let lastMap = '';
  let mapSince = 0;
  function tick() {
    const map = mapName();
    if (map !== lastMap) {
      lastMap = map;
      mapSince = Date.now();
    }
    if (map && load().auto && Date.now() - mapSince > 1000) collect(true);
    else if (panel && !panel.classList.contains('min') && !filter) render();
  }

  // Do konsoli: KrakenNpc.all(), KrakenNpc.here(), KrakenNpc.inspect('Nazwa') – surowy obiekt z silnika.
  window.KrakenNpc = {
    collect,
    all: () => flat(),
    here: () => flat().filter((n) => n.map === mapName()),
    inspect: (nick) => list().find((o) => o.d.nick === nick) || null,
  };

  const start = setInterval(() => {
    if (!engine()?.npcs || !document.body) return;
    clearInterval(start);
    buildPanel();
    setInterval(tick, 500);
  }, 1000);
})();
