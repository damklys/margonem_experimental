// ==UserScript==
// @name         Kraken Loader
// @namespace    kraken.margonem
// @version      1.3.202610160105
// @description  Pobiera i uruchamia najnowszą wersję Kraken Bot (opcjonalnie Kraken Recorder) z GitHuba – bez ręcznej aktualizacji w Tampermonkey
// @match        https://*.margonem.pl/
// @match        https://www.margonem.pl/*
// @match        https://margonem.pl/*
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

// Ustawienia w konsoli przeglądarki (zapamiętywane, działają od następnego odświeżenia):
//   localStorage['kraken:loader:recorder'] = '1'      – ładuj też Kraken Recorder ('0' – wyłącz)
//   localStorage['kraken:loader:branch'] = 'dev'      – inna gałąź repo (domyślnie main)
//   localStorage['kraken:loader:local'] = 'http://localhost:8765'  – pliki z lokalnego serwera zamiast GitHuba
(async function () {
  'use strict';
  if (window.KrakenLoader) return;
  window.KrakenLoader = true;

  // margonem.pl: bot wylogował się na czas odrodzenia E2 (dane w window.name) – odliczanie i powrót na świat o czasie.
  if (/^(www\.)?margonem\.pl$/.test(location.hostname)) {
    let ret = null;
    try {
      ret = JSON.parse(window.name || 'null');
    } catch (_) {}
    // Dane z adresu (#kraken-return=…&world=…&e2=…) – zapamiętane w sessionStorage, bo strona może zmienić adres.
    const h = new URLSearchParams(location.hash.slice(1));
    if (h.get('kraken-return')) {
      ret = { krakenReturn: +h.get('kraken-return'), world: h.get('world') || '', e2: h.get('e2') || '' };
      try {
        sessionStorage.setItem('kraken:return', JSON.stringify(ret));
      } catch (_) {}
    }
    if (!ret?.krakenReturn) {
      try {
        ret = JSON.parse(sessionStorage.getItem('kraken:return') || 'null');
      } catch (_) {}
    }
    console.log('%c[Kraken Loader]', 'color:#c4ae78', 'margonem.pl – powrót:', ret ? JSON.stringify(ret) : 'brak (window.name: ' + String(window.name).slice(0, 80) + ')');
    if (!ret || !ret.krakenReturn || !/^[a-z0-9-]+$/.test(ret.world || '')) return;
    const box = document.createElement('div');
    box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483647;background:#151a22ee;color:#dde;font:13px sans-serif;padding:8px 12px;border:1px solid #c4ae78;border-radius:6px';
    const cancel = document.createElement('button');
    cancel.textContent = 'Anuluj';
    cancel.style.marginLeft = '8px';
    const label = document.createElement('span');
    box.append(label, cancel);
    let stop = false;
    cancel.onclick = () => {
      stop = true;
      window.name = '';
      try {
        sessionStorage.removeItem('kraken:return');
      } catch (_) {}
      box.remove();
    };
    const tick = () => {
      if (stop) return;
      const left = Math.round((ret.krakenReturn - Date.now()) / 1000);
      if (left <= 0) {
        window.name = '';
        try {
          sessionStorage.removeItem('kraken:return');
        } catch (_) {}
        location.href = `https://${ret.world}.margonem.pl/`;
        return;
      }
      label.textContent = `🦑 Kraken: powrót na ${ret.world}${ret.e2 ? ` (${ret.e2})` : ''} za ${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}`;
      setTimeout(tick, 1000);
    };
    (document.body ? Promise.resolve() : new Promise((r) => addEventListener('DOMContentLoaded', r))).then(() => {
      document.body.appendChild(box);
      tick();
    });
    return;
  }

  const REPO = 'damklys/margonem_experimental';
  const DIR = 'kraken_user_client';
  const LS = (k) => {
    try {
      return localStorage.getItem(k);
    } catch (_) {
      return null;
    }
  };
  const BRANCH = LS('kraken:loader:branch') || 'main';
  const LOCAL = (LS('kraken:loader:local') || '').replace(/\/+$/, '');
  const SCRIPTS = [
    { file: 'kraken-bot.user.js', on: true },
    { file: 'kraken-recorder.user.js', on: LS('kraken:loader:recorder') === '1' },
  ].filter((s) => s.on);
  const CACHE = 'kraken-loader';
  const log = (...a) => console.log('%c[Kraken Loader]', 'color:#c4ae78', ...a);

  // Najnowszy commit gałęzi – adres z SHA omija pamięć podręczną CDN (raw.githubusercontent trzyma ~5 min).
  // Limit API GitHuba to 60 zapytań/h z jednego IP, więc SHA zapamiętujemy na minutę (wiele kart / odświeżeń).
  async function latestRef() {
    try {
      const memo = JSON.parse(sessionStorage.getItem('kraken:loader:sha') || 'null');
      if (memo && memo.branch === BRANCH && Date.now() - memo.ts < 60000) return memo.sha;
    } catch (_) {}
    try {
      const r = await fetch(`https://api.github.com/repos/${REPO}/commits/${encodeURIComponent(BRANCH)}`, {
        headers: { Accept: 'application/vnd.github.sha' },
        cache: 'no-store',
      });
      if (r.ok) {
        const sha = (await r.text()).trim();
        if (/^[0-9a-f]{40}$/.test(sha)) {
          try {
            sessionStorage.setItem('kraken:loader:sha', JSON.stringify({ branch: BRANCH, sha, ts: Date.now() }));
          } catch (_) {}
          return sha;
        }
      }
    } catch (_) {}
    return BRANCH; // bez API: gałąź (może być do kilku minut za najnowszym commitem)
  }

  async function cached(file) {
    try {
      const c = await caches.open(CACHE);
      const r = await c.match(`/${file}`);
      return r ? { code: await r.text(), ref: r.headers.get('x-kraken-ref') || '?' } : null;
    } catch (_) {
      return null;
    }
  }
  async function remember(file, code, ref) {
    try {
      const c = await caches.open(CACHE);
      await c.put(`/${file}`, new Response(code, { headers: { 'content-type': 'text/javascript', 'x-kraken-ref': ref } }));
    } catch (_) {}
  }

  async function download(file, ref) {
    const url = LOCAL ? `${LOCAL}/${file}?t=${Date.now()}` : `https://raw.githubusercontent.com/${REPO}/${ref}/${DIR}/${file}`;
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const code = await r.text();
    if (!/==UserScript==/.test(code)) throw new Error('to nie jest userskrypt');
    return code;
  }

  // Uruchomienie w kontekście strony (jak @grant none): eval globalny, a gdy strona go blokuje (CSP) – <script>.
  function run(file, code) {
    const src = `${code}\n//# sourceURL=kraken/${file}`;
    try {
      (0, eval)(src);
    } catch (e) {
      if (!(e instanceof EvalError)) throw e;
      const s = document.createElement('script');
      s.textContent = src;
      (document.head || document.documentElement).appendChild(s);
      s.remove();
    }
  }

  const ref = LOCAL ? 'local' : await latestRef();
  // Bot czyta stąd repo i commit, z którego pobiera wspólne dane (quests/, routes/, sets/).
  window.KrakenRepo = { repo: REPO, branch: BRANCH, ref: /^[0-9a-f]{40}$/.test(ref) ? ref : '' };
  for (const { file } of SCRIPTS) {
    let code = null;
    let from = '';
    try {
      code = await download(file, ref);
      from = LOCAL ? LOCAL : `${REPO}@${ref.slice(0, 7)}`;
      remember(file, code, ref);
    } catch (e) {
      const c = await cached(file);
      if (c) {
        code = c.code;
        from = `pamięć przeglądarki (${String(c.ref).slice(0, 7)}) – pobieranie nie powiodło się: ${e.message}`;
      } else {
        log(`❌ ${file}: nie udało się pobrać (${e.message}) i brak zapisanej kopii`);
        continue;
      }
    }
    const ver = (/@version\s+(\S+)/.exec(code) || [])[1] || '?';
    log(`▶ ${file} ${ver} – ${from}`);
    try {
      run(file, code);
    } catch (e) {
      log(`❌ ${file}: błąd uruchomienia – ${e.message}`);
      console.error(e);
    }
  }
})();
