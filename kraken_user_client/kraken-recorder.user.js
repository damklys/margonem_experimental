// ==UserScript==
// @name         Kraken Recorder
// @namespace    kraken.margonem
// @version      1.2.202610122230
// @description  Nagrywanie rozgrywki (ruch, kliknięcia, klawisze, mapy, NPC, dialogi, okna, przedmioty, zapytania do gry) – materiał do automatyzacji tutoriala
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
  if (window.KrakenRec) return;
  window.KrakenRec = true;

  const VERSION = '1.2.202610122230';
  const REC_KEY = 'kraken:rec';
  const UI_KEY = 'kraken:rec:ui';
  const MAX_CHARS = 4500000; // localStorage ma ~5 MB na domenę
  const WORLD = location.hostname.split('.')[0];

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const engine = () => {
    try {
      return typeof window.getEngine === 'function' ? window.getEngine() : window.Engine || null;
    } catch (_) {
      return null;
    }
  };
  const shown = (el) => !!(el && el.isConnected && el.getClientRects().length);
  const txt = (el, n = 120) => String(el?.innerText ?? el?.textContent ?? '').replace(/\s+/g, ' ').trim().slice(0, n);

  // ── stan nagrania ──
  let rec = load() || { events: [], recording: false, t0: 0 };
  function load() {
    try {
      return JSON.parse(localStorage.getItem(REC_KEY) || 'null');
    } catch (_) {
      return null;
    }
  }
  let dirty = false;
  let full = false;
  function save() {
    if (!dirty) return;
    dirty = false;
    const s = JSON.stringify(rec);
    if (s.length > MAX_CHARS) {
      if (!full) log('⚠️ Pamięć prawie pełna – pobierz nagranie i wyczyść');
      full = true;
    }
    try {
      localStorage.setItem(REC_KEY, s);
    } catch (e) {
      log(`⚠️ Zapis nieudany (${e.name}) – pobierz nagranie`);
    }
  }
  setInterval(save, 3000);
  window.addEventListener('beforeunload', save);

  function heroInfo() {
    const d = engine()?.hero?.d || {};
    const m = engine()?.map?.d || {};
    return { x: +d.x, y: +d.y, map: m.id, mapName: m.name };
  }
  // Każde zdarzenie: { t: ms od startu, e: typ, ...dane, x, y, map } (pozycja bohatera w chwili zdarzenia).
  function ev(e, data = {}, withPos = true) {
    if (!rec.recording) return;
    const h = withPos ? heroInfo() : {};
    rec.events.push({ t: Date.now() - rec.t0, e, ...data, ...(withPos ? { hx: h.x, hy: h.y, map: h.map } : {}) });
    dirty = true;
    render();
  }

  // ── opis elementu DOM (do kliknięć) ──
  function describe(el) {
    if (!el || el.nodeType !== 1) return null;
    const path = [];
    for (let n = el, i = 0; n && n !== document.body && i < 6; n = n.parentElement, i++) {
      const cls = [...n.classList].slice(0, 3).join('.');
      path.unshift(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (cls ? '.' + cls : ''));
    }
    const win = el.closest('.c-window, .border-window') || el.closest('[class$="-window"], [class*="-window "]');
    return {
      path: path.join(' > '),
      text: txt(el, 80),
      win: win ? txt(win.querySelector('.header-label .text, .header-label, .title'), 40) || [...win.classList].slice(0, 2).join('.') : '',
      data: Object.keys(el.dataset || {}).length ? { ...el.dataset } : undefined,
      tip: el.getAttribute?.('tip') || el.closest?.('[tip]')?.getAttribute('tip')?.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 80) || undefined,
    };
  }

  // ── nazwy obiektów z silnika (NPC / moby / gracze) ──
  function npcById(id) {
    try {
      const o = (engine().npcs.getDrawableList() || []).find((o) => o?.d && String(o.d.id) === String(id));
      return o ? { nick: o.d.nick, nx: +o.d.x, ny: +o.d.y, lvl: o.d.lvl, type: o.d.type, wt: o.d.wt } : null;
    } catch (_) {
      return null;
    }
  }

  // ── zapytania do gry (_g): ruch, rozmowy, walki, przejścia, przedmioty ──
  let lastG = '';
  let lastGt = 0;
  function hookG() {
    const og = window._g;
    if (typeof og !== 'function' || og.__krRec) return;
    const wrapped = function (q, ...rest) {
      try {
        const s = String(q);
        if (rec.recording && s !== '_' && !(s === lastG && Date.now() - lastGt < 300)) {
          lastG = s;
          lastGt = Date.now();
          const data = { q: s };
          const id = /[?&](?:id|npc)=(-?\d+)/.exec('&' + s)?.[1];
          if (id && /^(talk|fight|npc)/.test(s)) Object.assign(data, { obj: npcById(Math.abs(+id)) || npcById(id) });
          ev('g', data);
        }
      } catch (_) {}
      return og.call(this, q, ...rest);
    };
    wrapped.__krRec = true;
    window._g = wrapped;
  }

  // ── mysz i klawiatura ──
  document.addEventListener(
    'click',
    (e) => {
      if (!rec.recording || e.target.closest?.('#kr-rec')) return;
      const li = e.target.closest?.('.dialogue-window-answer');
      if (li) {
        const all = [...document.querySelectorAll('.dialogue-window-answer')].filter(shown);
        ev('answer', { i: all.indexOf(li) + 1, text: txt(li, 120), npc: dialogSig.split('|')[0] });
        return;
      }
      ev('click', { cx: e.clientX, cy: e.clientY, btn: e.button, trusted: e.isTrusted, el: describe(e.target), canvas: e.target.tagName === 'CANVAS' || undefined });
    },
    true
  );
  document.addEventListener(
    'contextmenu',
    (e) => {
      if (!rec.recording || e.target.closest?.('#kr-rec')) return;
      ev('rclick', { cx: e.clientX, cy: e.clientY, el: describe(e.target) });
    },
    true
  );
  document.addEventListener(
    'dblclick',
    (e) => {
      if (!rec.recording || e.target.closest?.('#kr-rec')) return;
      ev('dblclick', { cx: e.clientX, cy: e.clientY, el: describe(e.target) });
    },
    true
  );
  const held = new Set();
  document.addEventListener(
    'keydown',
    (e) => {
      if (!rec.recording || e.target.closest?.('#kr-rec')) return;
      const inInput = /^(INPUT|TEXTAREA)$/.test(e.target.tagName) || e.target.isContentEditable;
      if (inInput) return; // treść pól zapisuje 'input'
      if (held.has(e.code)) return; // przytrzymany klawisz: tylko pierwsze wciśnięcie
      held.add(e.code);
      ev('key', { key: e.key, code: e.code, mods: [e.ctrlKey && 'ctrl', e.shiftKey && 'shift', e.altKey && 'alt'].filter(Boolean).join('+') || undefined });
    },
    true
  );
  document.addEventListener(
    'keyup',
    (e) => {
      if (!held.has(e.code)) return;
      held.delete(e.code);
      if (rec.recording && /^(Key[WASD]|Arrow)/.test(e.code)) ev('keyup', { key: e.key, code: e.code });
    },
    true
  );
  document.addEventListener(
    'change',
    (e) => {
      const el = e.target;
      if (!rec.recording || el.closest?.('#kr-rec') || !/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
      ev('input', { el: describe(el), value: el.type === 'password' ? '***' : el.type === 'checkbox' ? el.checked : String(el.value).slice(0, 200) });
    },
    true
  );

  // ── stan gry: pozycja, mapa, poziom, przedmioty, okna, dialogi, tutorial ──
  let pos = null;
  let mapId = null;
  let lvl = null;
  let items = null;
  let dialogSig = '';
  let windows = new Set();
  let tutSig = '';

  function bagItems() {
    try {
      const list = engine().items.fetchLocationItems('g') || [];
      const out = new Map();
      for (const it of list) out.set(String(it.id), { name: it.name, st: it.st, cl: it.cl });
      return out;
    } catch (_) {
      return null;
    }
  }

  function dialogState() {
    const answers = [...document.querySelectorAll('.dialogue-window-answer')].filter(shown);
    const win = document.querySelector('.dialogue-window') || answers[0]?.closest('.c-window, [class*="dialogue"]');
    if (!win || !shown(win)) return null;
    const msg = win.querySelector('.message, .dialogue-window-message, [class*="message"], [class*="text-content"]');
    const all = txt(win, 1500);
    const ans = answers.map((a) => ({ text: txt(a, 120), icon: [...(a.querySelector('.icon')?.classList || [])].filter((c) => c !== 'icon').join(' ') || undefined }));
    let text = msg ? txt(msg, 1500) : all;
    for (const a of ans) text = text.replace(a.text, '').trim();
    return { npc: txt(win.querySelector('.header-label, .npc-name, [class*="name"]'), 60), text, answers: ans };
  }

  function windowTitles() {
    const out = new Set();
    for (const w of document.querySelectorAll('.c-window')) {
      if (!shown(w)) continue;
      const t = txt(w.querySelector('.header-label .text, .header-label'), 50);
      if (t) out.add(t);
    }
    return out;
  }

  function tutorialState() {
    const els = [...document.querySelectorAll('[class*="tutorial"], [class*="Tutorial"], .tutorial-window, .info-box, .hint')].filter(shown);
    return els.map((e) => txt(e, 400)).filter(Boolean).join(' | ').slice(0, 1500);
  }

  async function poll() {
    for (;;) {
      await sleep(200);
      if (!rec.recording) continue;
      hookG();
      const E = engine();
      if (!E?.hero?.d) continue;
      const h = heroInfo();
      // mapa
      if (h.map != null && h.map !== mapId) {
        const prev = mapId;
        mapId = h.map;
        const m = E.map?.d || {};
        ev('map', { id: m.id, name: m.name, w: m.x, h: m.y, from: prev, x: h.x, y: h.y }, false);
        pos = null;
      }
      // pozycja (tylko zmiany)
      if (!pos || pos.x !== h.x || pos.y !== h.y) {
        pos = { x: h.x, y: h.y };
        ev('pos', { x: h.x, y: h.y }, false);
      }
      // poziom
      const L = +E.hero.d.lvl;
      if (L && L !== lvl) {
        if (lvl != null) ev('lvl', { lvl: L, from: lvl });
        lvl = L;
      }
    }
  }

  // Obserwowane zadania (okno „Obserwowane zadania”): id, tytuł, opis i cele (typ misji + treść).
  // Czytamy z DOM także przy zwiniętym oknie (textContent zamiast innerText).
  const tc = (el, n = 400) => String(el?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, n);
  function questState() {
    return [...document.querySelectorAll('.quest-observe-list .one-observe')].map((q) => ({
      id: /quest-observe-(\d+)/.exec(q.className)?.[1] || tc(q.querySelector('.one-observe__debug')),
      title: tc(q.querySelector('.one-observe__title.full') || q.querySelector('.one-observe__title'), 120),
      desc: tc(q.querySelector('.quest-description.full') || q.querySelector('.quest-description'), 600),
      missions: [...q.querySelectorAll('.one-quest-mission')].map((m) => ({
        type: /mission-type-(\d+)/.exec(m.className)?.[1],
        label: tc(m.querySelector('.mission-type-label'), 60).replace(/:$/, ''),
        name: tc(m.querySelector('.one-name'), 120),
        text: tc(m, 200),
        done: /done|complete|finished/.test(m.className) || undefined,
      })),
    }));
  }
  let questSig = '';
  let quests = new Map();
  function checkQuests() {
    const list = questState();
    const sig = JSON.stringify(list);
    if (sig === questSig) return;
    questSig = sig;
    const now = new Map(list.map((q) => [q.id, q]));
    for (const [id, q] of now) {
      const old = quests.get(id);
      if (!old) ev('questAdd', q);
      else if (JSON.stringify(old) !== JSON.stringify(q)) ev('questUpd', { ...q, prev: { desc: old.desc !== q.desc ? old.desc : undefined, missions: JSON.stringify(old.missions) !== JSON.stringify(q.missions) ? old.missions : undefined } });
    }
    for (const [id, q] of quests) if (!now.has(id)) ev('questDel', { id, title: q.title });
    quests = now;
  }

  async function pollSlow() {
    for (;;) {
      await sleep(700);
      if (!rec.recording || !engine()?.hero?.d) continue;
      // dialogi
      const d = dialogState();
      const sig = d ? d.npc + '|' + d.text + '|' + d.answers.map((a) => a.text).join('|') : '';
      if (sig !== dialogSig) {
        dialogSig = sig;
        ev(d ? 'dialog' : 'dialogEnd', d || {});
      }
      // zadania
      checkQuests();
      // okna gry
      const ws = windowTitles();
      for (const t of ws) if (!windows.has(t)) ev('winOpen', { title: t });
      for (const t of windows) if (!ws.has(t)) ev('winClose', { title: t });
      windows = ws;
      // tutorial / podpowiedzi
      const tut = tutorialState();
      if (tut !== tutSig) {
        tutSig = tut;
        if (tut) ev('tutorial', { text: tut });
      }
      // przedmioty w torbach
      const now = bagItems();
      if (now && items) {
        for (const [id, it] of now) if (!items.has(id)) ev('itemAdd', { id, ...it });
        for (const [id, it] of items) if (!now.has(id)) ev('itemDel', { id, ...it });
      }
      if (now) items = now;
    }
  }

  // Komunikaty gry (dymki / logi) – nowe węzły z tekstem w typowych kontenerach.
  new MutationObserver((muts) => {
    if (!rec.recording) return;
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType !== 1 || n.closest?.('#kr-rec, [class*="chat"], .dialogue-window')) continue;
        const box = n.closest?.('.message-box, .alert, .mAlert, .info-message, [class*="notification"], [class*="toast"], .big-messages, .warn-box');
        if (!box && !/message|alert|notif|toast|warn/i.test(n.className || '')) continue;
        const t = txt(n, 300);
        if (t) ev('msg', { text: t, cls: String(n.className).slice(0, 60) });
      }
    }
  }).observe(document.documentElement, { childList: true, subtree: true });

  // ── sterowanie nagraniem ──
  function start() {
    if (!rec.events.length) rec.t0 = Date.now();
    rec.recording = true;
    mapId = null;
    pos = null;
    lvl = null;
    items = null;
    dialogSig = '';
    windows = new Set();
    questSig = '';
    quests = new Map();
    const d = engine()?.hero?.d || {};
    ev('start', { version: VERSION, world: WORLD, nick: d.nick, lvl: d.lvl, prof: d.prof, gold: d.gold, ua: navigator.userAgent.slice(0, 80) });
    hookG();
    log('⏺ Nagrywanie');
    save();
  }
  function stop() {
    ev('stop');
    rec.recording = false;
    dirty = true;
    save();
    log(`⏹ Zatrzymano (${rec.events.length} zdarzeń)`);
    render();
  }
  function mark() {
    const note = window.prompt('Znacznik (np. „krok 3: rozmowa z Ryszardem”):', '');
    if (note == null) return;
    const was = rec.recording;
    rec.recording = true;
    ev('mark', { note });
    rec.recording = was;
    save();
  }

  function download(name, content, type) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content], { type }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }
  const stamp = () => new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
  function downloadJson() {
    save();
    download(`kraken-nagranie-${WORLD}-${stamp()}.json`, JSON.stringify({ kraken: 'nagranie', version: VERSION, world: WORLD, t0: new Date(rec.t0).toISOString(), events: rec.events }), 'application/json');
  }
  // Czytelna oś czasu (bez pojedynczych kroków ruchu – te są zwinięte w „idzie z → do”).
  function timeline() {
    const out = [];
    const fmt = (t) => {
      const s = Math.floor(t / 1000);
      return `${String(Math.floor(s / 60)).padStart(3, ' ')}:${String(s % 60).padStart(2, '0')}`;
    };
    let walk = null;
    const flush = () => {
      if (walk) out.push(`${fmt(walk.t)}  🚶 ${walk.from} → ${walk.to} (${walk.n} kroków)`);
      walk = null;
    };
    for (const e of rec.events) {
      if (e.e === 'pos') {
        if (!walk) walk = { t: e.t, from: `${e.x},${e.y}`, n: 0 };
        walk.to = `${e.x},${e.y}`;
        walk.n++;
        continue;
      }
      if (e.e === 'keyup') continue;
      flush();
      const at = e.hx != null ? ` @${e.hx},${e.hy}` : '';
      const line = {
        start: () => `▶ START ${e.nick} (${e.lvl} lvl, ${e.prof}) – ${e.world}`,
        stop: () => '⏹ STOP',
        mark: () => `📌 ${e.note}`,
        map: () => `🗺️ MAPA: ${e.name} [${e.id}] (${e.w}×${e.h}) wejście ${e.x},${e.y}`,
        g: () => `📡 ${e.q}${e.obj ? `  ← ${e.obj.nick} (${e.obj.nx},${e.obj.ny})` : ''}${at}`,
        click: () => `🖱️ ${e.canvas ? 'mapa' : e.el?.text || e.el?.path}${e.el?.win ? ` [okno: ${e.el.win}]` : ''}${e.el?.tip ? ` {${e.el.tip}}` : ''}${at}`,
        rclick: () => `🖱️ PPM ${e.el?.text || e.el?.path}${at}`,
        dblclick: () => `🖱️ 2× ${e.el?.text || e.el?.path}${at}`,
        key: () => `⌨️ ${e.mods ? e.mods + '+' : ''}${e.key}${at}`,
        input: () => `✏️ ${e.el?.path}: ${e.value}`,
        dialog: () => `💬 ${e.npc}: ${e.text}\n${e.answers.map((a, i) => `           ${i + 1}) ${a.text}`).join('\n')}`,
        answer: () => `💬 ➜ wybór ${e.i}) ${e.text}`,
        dialogEnd: () => '💬 (koniec dialogu)',
        winOpen: () => `🪟 + ${e.title}`,
        winClose: () => `🪟 − ${e.title}`,
        tutorial: () => `🎓 ${e.text}`,
        itemAdd: () => `🎒 + ${e.name}`,
        itemDel: () => `🎒 − ${e.name}`,
        lvl: () => `📈 poziom ${e.lvl}`,
        questAdd: () => `📜 + ZADANIE [${e.id}] ${e.title}: ${e.desc}${e.missions.map((m) => `\n           ▸ ${m.text}`).join('')}`,
        questUpd: () => `📜 ~ [${e.id}] ${e.title}${e.prev?.desc ? `: ${e.desc}` : ''}${e.missions.map((m) => `\n           ▸ ${m.text}`).join('')}`,
        questDel: () => `📜 − ZADANIE [${e.id}] ${e.title}`,
        msg: () => `📣 ${e.text}`,
        reload: () => '🔄 przeładowanie strony',
      }[e.e];
      out.push(`${fmt(e.t)}  ${line ? line() : e.e}`);
    }
    flush();
    return out.join('\n');
  }
  function downloadTxt() {
    save();
    download(`kraken-nagranie-${WORLD}-${stamp()}.txt`, timeline(), 'text/plain;charset=utf-8');
  }

  // ── okienko ──
  const css = `
#kr-rec{position:fixed;top:220px;left:20px;width:230px;z-index:2147483003;background:#0b0e1a;color:#c4ae78;border:1px solid #1e2a48;
  border-radius:8px;font:12px/1.35 "Segoe UI",system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.5)}
#kr-rec *{box-sizing:border-box}
#kr-rec .h{display:flex;align-items:center;gap:6px;padding:4px 8px;background:#111526;border-radius:8px 8px 0 0;cursor:move;user-select:none}
#kr-rec .h b{flex:1}
#kr-rec .h button{background:none;border:none;color:#5a6a88;cursor:pointer}
#kr-rec .b{padding:6px 8px;display:flex;flex-direction:column;gap:5px}
#kr-rec.min .b{display:none}
#kr-rec .row{display:flex;gap:5px}
#kr-rec .row button{flex:1}
#kr-rec button{background:#1a2038;border:1px solid #2a3558;color:#c4ae78;border-radius:4px;padding:3px 6px;cursor:pointer}
#kr-rec button.on{background:#5a1a1a;border-color:#a33;color:#fff}
#kr-rec .c{color:#9aa6c4}
#kr-rec .dot{width:9px;height:9px;border-radius:50%;background:#333}
#kr-rec.rec .dot{background:#e33;animation:krb 1s infinite}
@keyframes krb{50%{opacity:.3}}
#kr-rec .l{color:#5a6a88;font-size:11px;max-height:70px;overflow-y:auto;white-space:pre-wrap}`;
  const ui = {};
  const lines = [];
  function log(msg) {
    lines.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
    while (lines.length > 20) lines.shift();
    console.log('[Kraken Rec]', msg);
    if (ui.log) ui.log.textContent = lines.slice().reverse().join('\n');
  }
  let renderQ = false;
  function render() {
    if (renderQ || !ui.count) return;
    renderQ = true;
    requestAnimationFrame(() => {
      renderQ = false;
      const n = rec.events.length;
      const last = rec.events[n - 1];
      const min = last ? Math.round(last.t / 60000) : 0;
      const counts = {};
      for (const e of rec.events) counts[e.e] = (counts[e.e] || 0) + 1;
      ui.count.textContent = `Zdarzeń: ${n} · ${min} min · mapy ${counts.map || 0} · dialogi ${counts.dialog || 0} · zadania ${(counts.questAdd || 0) + (counts.questUpd || 0)} · kliki ${counts.click || 0}`;
      ui.root.classList.toggle('rec', rec.recording);
      ui.toggle.textContent = rec.recording ? '⏹ Stop' : '⏺ Nagrywaj';
      ui.toggle.classList.toggle('on', rec.recording);
    });
  }
  function settings() {
    try {
      return JSON.parse(localStorage.getItem(UI_KEY) || '{}');
    } catch (_) {
      return {};
    }
  }
  function saveSettings(patch) {
    try {
      localStorage.setItem(UI_KEY, JSON.stringify(Object.assign(settings(), patch)));
    } catch (_) {}
  }
  function build() {
    const st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);
    const root = document.createElement('div');
    root.id = 'kr-rec';
    root.innerHTML = `<div class="h"><span class="dot"></span><b>🎬 Kraken Rec</b><button title="Zwiń / rozwiń">▾</button></div>
<div class="b">
  <div class="c" data-u="count"></div>
  <div class="row"><button data-u="toggle"></button><button data-u="mark" title="Dodaj notatkę w nagraniu">📌 Znacznik</button></div>
  <div class="row"><button data-u="json">Pobierz JSON</button><button data-u="txt">Oś czasu .txt</button></div>
  <div class="row"><button data-u="clear">Wyczyść</button></div>
  <div class="l" data-u="log"></div>
</div>`;
    document.body.appendChild(root);
    ui.root = root;
    for (const el of root.querySelectorAll('[data-u]')) ui[el.dataset.u] = el;
    for (const t of ['keydown', 'keyup', 'keypress', 'mousedown', 'click', 'wheel']) root.addEventListener(t, (e) => e.stopPropagation());
    const s = settings();
    if (s.left != null) {
      root.style.left = s.left + 'px';
      root.style.top = s.top + 'px';
    }
    root.classList.toggle('min', !!s.min);
    root.querySelector('.h button').addEventListener('click', () => {
      root.classList.toggle('min');
      saveSettings({ min: root.classList.contains('min') });
    });
    const head = root.querySelector('.h');
    head.addEventListener('pointerdown', (e) => {
      if (e.target.closest('button')) return;
      const r = root.getBoundingClientRect();
      const ox = e.clientX - r.left;
      const oy = e.clientY - r.top;
      const move = (ev2) => {
        root.style.left = Math.max(0, ev2.clientX - ox) + 'px';
        root.style.top = Math.max(0, ev2.clientY - oy) + 'px';
      };
      const up = () => {
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', up);
        const b = root.getBoundingClientRect();
        saveSettings({ left: Math.round(b.left), top: Math.round(b.top) });
      };
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', up);
    });
    ui.toggle.addEventListener('click', () => (rec.recording ? stop() : start()));
    ui.mark.addEventListener('click', mark);
    ui.json.addEventListener('click', downloadJson);
    ui.txt.addEventListener('click', downloadTxt);
    ui.clear.addEventListener('click', () => {
      if (!window.confirm('Usunąć całe nagranie z pamięci przeglądarki?')) return;
      rec = { events: [], recording: false, t0: 0 };
      full = false;
      localStorage.removeItem(REC_KEY);
      log('🗑️ Wyczyszczono');
      render();
    });
    render();
  }

  (async function init() {
    while (!(engine()?.hero?.d && document.body)) await sleep(500);
    build();
    log(`🎬 Kraken Rec ${VERSION} – ${WORLD}`);
    // Nagrywanie trwa dalej po przeładowaniu strony.
    if (rec.recording) {
      ev('reload', {}, true);
      hookG();
      log(`⏺ Wznowiono nagrywanie (${rec.events.length} zdarzeń)`);
    }
    poll();
    pollSlow();
  })();
})();
