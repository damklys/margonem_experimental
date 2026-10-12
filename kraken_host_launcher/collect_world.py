import base64
import json
import os
import re
import time

from selenium.webdriver.common.by import By

_WORLD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world")

_SCAN_GW_JS = """
var callback = arguments[arguments.length - 1];
var gwEls = Array.from(document.querySelectorAll('.mmpMapObject.mmp-gw'));
if (!gwEls.length) { callback([]); return; }

function readTipName(tipEl) {
    if (!tipEl) return null;
    var content = tipEl.querySelector('.content') || tipEl;
    var center = content.querySelector('center');
    if (center) {
        for (var i = 0; i < center.childNodes.length; i++) {
            var node = center.childNodes[i];
            if (node.nodeType === 3) {
                var t = node.textContent.trim();
                if (t) return t;
            }
        }
    }
    var lines = (content.innerText || '').split('\\n');
    return lines[0].trim() || null;
}

var results = [];
var seen = {};
var idx = 0;

function processNext() {
    if (idx >= gwEls.length) { callback(results); return; }
    var el = gwEls[idx++];
    var style = el.getAttribute('style') || '';
    var leftM = style.match(/left:\\s*([\\d.]+)px/);
    var topM  = style.match(/top:\\s*([\\d.]+)px/);
    var left = leftM ? parseFloat(leftM[1]) : 0;
    var top  = topM  ? parseFloat(topM[1])  : 0;

    var rect = el.getBoundingClientRect();
    var ex = rect.left + rect.width / 2;
    var ey = rect.top  + rect.height / 2;

    ['pointerover', 'mouseover', 'mouseenter', 'mousemove'].forEach(function(type) {
        el.dispatchEvent(new MouseEvent(type, {
            bubbles: true, cancelable: true, view: window, clientX: ex, clientY: ey
        }));
    });
    if (window.jQuery) window.jQuery(el).trigger('mouseenter').trigger('mouseover');

    setTimeout(function() {
        var tips = Array.from(document.querySelectorAll('.tip-wrapper'));
        var tip = tips.find(function(t) { return t.offsetHeight > 0; });
        var name = readTipName(tip);
        if (name && !seen[name]) {
            seen[name] = true;
            results.push({ name: name, top: top, left: left });
        }
        processNext();
    }, 300);
}

processNext();
"""


_EXTRACT_MAP_IMG_JS = """
var el = document.querySelector('.mmpMap');
if (!el) return null;
var bg = el.style.backgroundImage;
var m = bg.match(/base64,([A-Za-z0-9+/=]+)/);
return m ? m[1] : null;
"""

ALL_OBJECT_TYPES = [
    "mmp-mob",
    "mmp-gw",
    "mmp-elite",
    "mmp-elite2",
    "mmp-elite3",
    "mmp-titan-resp",
    "mmp-collosus",
    "mmp-heros-resp",
    "mmp-npc",
    "mmp-item",
]

_SCAN_MAP_OBJECTS_JS = """
var callback = arguments[arguments.length - 1];

var TYPES = [
    {css: '.mmpMapObject.mmp-mob',        type: 'mmp-mob',        has_level: true,  has_group: true  },
    {css: '.mmpMapObject.mmp-gw',         type: 'mmp-gw',         has_level: false, has_group: false },
    {css: '.mmpMapObject.mmp-elite',      type: 'mmp-elite',      has_level: true,  has_group: true  },
    {css: '.mmpMapObject.mmp-elite2',     type: 'mmp-elite2',     has_level: true,  has_group: true  },
    {css: '.mmpMapObject.mmp-elite3',     type: 'mmp-elite3',     has_level: true,  has_group: true  },
    {css: '.mmpMapObject.mmp-titan-resp', type: 'mmp-titan-resp', has_level: false, has_group: false },
    {css: '.mmpMapObject.mmp-collosus',   type: 'mmp-collosus',   has_level: false, has_group: false },
    {css: '.mmpMapObject.mmp-heros-resp', type: 'mmp-heros-resp', has_level: false, has_group: false },
    {css: '.mmpMapObject.mmp-npc',        type: 'mmp-npc',        has_level: false, has_group: false },
    {css: '.mmpMapObject.mmp-item',       type: 'mmp-item',       has_level: false, has_group: false },
];

var queue = [];
TYPES.forEach(function(t) {
    Array.from(document.querySelectorAll(t.css)).forEach(function(el) {
        queue.push({el: el, type: t.type, has_level: t.has_level, has_group: t.has_group});
    });
});

if (!queue.length) { callback([]); return; }

function readActiveTip() {
    var tips = document.querySelectorAll('.tip-wrapper');
    for (var i = 0; i < tips.length; i++) {
        if (tips[i].offsetHeight > 0) return tips[i];
    }
    return null;
}

function parseTip(tip) {
    var result = {name: null, level: null, grp: false, x: null, y: null};
    if (!tip) return result;
    var c = tip.querySelector('.content') || tip;

    // Strategia 1: mob/elite — name w <strong>
    var strong = c.querySelector('strong');
    if (strong) result.name = strong.textContent.trim() || null;

    // Strategia 2: gw/npc — name jako text-node w <center>
    if (!result.name) {
        var center = c.querySelector('center');
        if (center) {
            for (var i = 0; i < center.childNodes.length; i++) {
                var node = center.childNodes[i];
                if (node.nodeType === 3) {
                    var t = node.textContent.trim();
                    if (t) { result.name = t; break; }
                }
            }
        }
    }

    // Fallback: pierwsza niepusta linia innerText
    if (!result.name) {
        var lines = (c.innerText || '').trim().split('\\n');
        for (var i = 0; i < lines.length; i++) {
            var l = lines[i].trim();
            if (l) { result.name = l; break; }
        }
    }

    // Poziom + grp ze <span>
    var span = c.querySelector('span');
    if (span) {
        var raw = span.textContent.trim();
        result.level = parseInt(raw) || null;
        result.grp   = raw.indexOf('grp') !== -1;
    }

    // Współrzędne mapy z szarego <div>
    var coordEl = c.querySelector('div[style*="gray"]');
    if (coordEl) {
        var m = coordEl.textContent.trim().match(/(\\d+),(\\d+)/);
        if (m) { result.x = parseInt(m[1]); result.y = parseInt(m[2]); }
    }

    return result;
}

var results = [];
var idx = 0;

function next() {
    if (idx >= queue.length) { callback(results); return; }
    var item = queue[idx++];
    var el   = item.el;
    var style = el.getAttribute('style') || '';

    var lm = style.match(/left:\\s*([\\d.]+)px/);
    var tm = style.match(/top:\\s*([\\d.]+)px/);
    var left = lm ? parseFloat(lm[1]) : 0;
    var top  = tm ? parseFloat(tm[1]) : 0;

    var r  = el.getBoundingClientRect();
    var cx = r.left + r.width  / 2;
    var cy = r.top  + r.height / 2;
    ['pointerover', 'mouseover', 'mouseenter', 'mousemove'].forEach(function(ev) {
        el.dispatchEvent(new MouseEvent(ev, {
            bubbles: true, cancelable: true, view: window,
            clientX: cx, clientY: cy
        }));
    });
    if (window.jQuery) window.jQuery(el).trigger('mouseenter').trigger('mouseover');

    setTimeout(function() {
        var parsed = parseTip(readActiveTip());

        var obj = {
            type:   item.type,
            tip_id: el.getAttribute('tip-id'),
            name:   parsed.name,
            top:    top,
            left:   left,
        };

        if (item.has_level) {
            obj.level = parsed.level;
            obj.x     = parsed.x;
            obj.y     = parsed.y;
        }

        if (item.has_group) {
            var wg = el.getAttribute('wgroup');
            obj.grp = parsed.grp || (wg !== null && wg !== '' && wg !== '0');
        }

        results.push(obj);
        next();
    }, 300);
}

next();
"""

_FRAME_SIZE_JS = """
var hero = document.querySelector('.mmpMapObject.mmp-hero');
if (!hero) return null;
var style = hero.getAttribute('style') || '';
var m = style.match(/width:\\s*([\\d.]+)px/);
return m ? parseFloat(m[1]) : null;
"""


def scan_map_objects(driver, logger=None, timeout_s: float = 120.0) -> "dict[str, list]":
    """
    Skanuje wszystkie typy obiektów na mapie przez hover + tooltip.

    Zwraca słownik pogrupowany po typie:
    {
        "mmp-mob":        [{tip_id, name, level, top, left, x, y, grp}, ...],
        "mmp-gw":         [{tip_id, name, top, left}, ...],
        "mmp-elite":      [...],
        "mmp-elite2":     [...],
        "mmp-elite3":     [...],
        "mmp-titan-resp": [...],
        "mmp-collosus":   [...],
        "mmp-heros-resp": [...],
        "mmp-npc":        [{tip_id, name, top, left}, ...],
        "mmp-item":       [{tip_id, name, top, left}, ...],
    }
    Klucze zawsze istnieją (pusta lista gdy brak obiektów danego typu).
    """
    try:
        driver.set_script_timeout(max(timeout_s, 120.0))
    except Exception:
        pass

    raw = []
    try:
        raw = driver.execute_async_script(_SCAN_MAP_OBJECTS_JS) or []
    except Exception as e:
        if logger:
            logger(f"⚠️  scan_map_objects błąd: {e}")

    by_type: dict = {t: [] for t in ALL_OBJECT_TYPES}
    for obj in raw:
        t = obj.get("type")
        if t in by_type:
            by_type[t].append(obj)

    if logger:
        summary = ", ".join(
            f"{t.split('-', 1)[1]}={len(v)}"
            for t, v in by_type.items() if v
        )
        logger(f"🔍 scan_map_objects: {summary or 'brak obiektów'}")

    return by_type


def get_frame_size(driver) -> "float | None":
    """Odczytuje szerokość kafelka (frame_size) z elementu .mmp-hero."""
    try:
        val = driver.execute_script(_FRAME_SIZE_JS)
        return float(val) if val is not None else None
    except Exception:
        return None


def _safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def world_file_path(location: str) -> str:
    return os.path.join(_WORLD_DIR, _safe_filename(location) + ".json")


def map_image_path(location: str) -> str:
    return os.path.join(_WORLD_DIR, _safe_filename(location) + ".png")


def save_map_image(driver, location: str, logger=None) -> bool:
    """
    Wyciąga base64 PNG z background-image elementu .mmpMap i zapisuje
    jako <location>.png w ./world/. Nie nadpisuje jeśli plik już istnieje.
    Zwraca True jeśli plik został zapisany, False w przeciwnym razie.
    """
    img_path = map_image_path(location)
    if os.path.isfile(img_path):
        return False

    try:
        b64 = driver.execute_script(_EXTRACT_MAP_IMG_JS)
    except Exception as e:
        if logger:
            logger(f"⚠️  Collect: błąd przy pobieraniu obrazu mapy: {e}")
        return False

    if not b64:
        if logger:
            logger(f"⚠️  Collect: brak obrazu minimapy dla '{location}'")
        return False

    try:
        os.makedirs(_WORLD_DIR, exist_ok=True)
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(b64))
        if logger:
            logger(f"🖼️  Collect: zapisano obraz mapy → {os.path.basename(img_path)}")
        return True
    except Exception as e:
        if logger:
            logger(f"⚠️  Collect: błąd zapisu obrazu mapy: {e}")
        return False


def world_file_exists(location: str) -> bool:
    return os.path.isfile(world_file_path(location))


def scan_gateways(driver, logger=None, timeout_s: float = 30.0) -> list:
    """
    Skanuje wszystkie .mmp-gw na aktualnej mapie przez hover + tooltip.
    Zwraca listę {"name": str, "top": float, "left": float}.
    """
    try:
        driver.set_script_timeout(max(timeout_s, 30.0))
    except Exception:
        pass
    try:
        results = driver.execute_async_script(_SCAN_GW_JS)
        return results or []
    except Exception as e:
        if logger:
            logger(f"⚠️  scan_gateways błąd: {e}")
        return []


def build_world_json(
    location: str,
    gateways: list,
    objects: "dict[str, list] | None" = None,
    frame_size: "float | None" = None,
) -> dict:
    destinations = [
        {
            "name": gw["name"],
            "directly": True,
            "gw": {"top": round(gw["top"], 3), "left": round(gw["left"], 3)},
        }
        for gw in gateways
    ]
    data = {
        "location":     location,
        "type":         "",
        "destination":  destinations,
        "heros":        [],
        "included_mobs": [],
        "excluded_mobs": [],
        "objects":      objects if objects is not None else {t: [] for t in ALL_OBJECT_TYPES},
    }
    if frame_size is not None:
        data["frame_size"] = frame_size
    return data


def save_world_json(location: str, data: dict) -> str:
    os.makedirs(_WORLD_DIR, exist_ok=True)
    path = world_file_path(location)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _load_world_json(location: str) -> dict:
    with open(world_file_path(location), "r", encoding="utf-8") as f:
        return json.load(f)


def collect_current_map(driver, logger=None) -> str:
    """
    Skanuje aktualną mapę i zapisuje / uzupełnia plik world JSON.

    Zwraca:
      'created'  – plik właśnie stworzony od zera
      'updated'  – plik istniał, uzupełniono brakujące dane
      'ok'       – plik istniał, nic nowego
      'no_map'   – nie udało się odczytać nazwy mapy
    """
    from move import _get_location_text
    location = _get_location_text(driver)
    if not location:
        if logger:
            logger("⚠️  Collect: nie udało się odczytać nazwy mapy")
        return "no_map"

    save_map_image(driver, location, logger=logger)

    if logger:
        logger(f"🔍 Collect: skanowanie '{location}'...")

    gateways   = scan_gateways(driver, logger=logger)
    objects    = scan_map_objects(driver, logger=logger)
    frame_size = get_frame_size(driver)

    if not world_file_exists(location):
        data = build_world_json(location, gateways, objects=objects, frame_size=frame_size)
        path = save_world_json(location, data)
        if logger:
            gw_info = ", ".join(g["name"] for g in gateways) if gateways else "brak"
            obj_counts = ", ".join(
                f"{t.split('-',1)[1]}={len(v)}"
                for t, v in objects.items() if v
            )
            logger(
                f"💾 Collect: nowy plik '{os.path.basename(path)}'"
                f" — przejścia: {gw_info}"
                + (f" — obiekty: {obj_counts}" if obj_counts else "")
            )
        return "created"

    data    = _load_world_json(location)
    changed = False

    # --- 1. brakujące przejścia ---
    existing_gw = {d["name"] for d in data.get("destination", [])}
    added_gw = []
    for gw in gateways:
        if gw["name"] not in existing_gw:
            data.setdefault("destination", []).append({
                "name": gw["name"],
                "directly": True,
                "gw": {"top": round(gw["top"], 3), "left": round(gw["left"], 3)},
            })
            added_gw.append(gw["name"])
    if added_gw:
        changed = True
        if logger:
            logger(f"➕ Collect: '{location}' – nowe przejścia: {', '.join(added_gw)}")

    # --- 2. objects — migracja ze starego formatu + uzupełnianie pustych typów ---
    # Migracja: stary plik miał płaskie 'mobs', przenosimy do 'objects'
    if "mobs" in data and "objects" not in data:
        old_mobs = data.pop("mobs")
        data["objects"] = {t: [] for t in ALL_OBJECT_TYPES}
        for obj in (old_mobs or []):
            raw_type = obj.get("type", "")
            mapped = raw_type if raw_type.startswith("mmp-") else f"mmp-{raw_type}"
            if mapped in data["objects"]:
                data["objects"][mapped].append(obj)
        changed = True
        if logger:
            logger(f"🔄 Collect: '{location}' – zmigrowano 'mobs' → 'objects'")

    existing_objects = data.setdefault("objects", {t: [] for t in ALL_OBJECT_TYPES})
    updated_types = []
    for obj_type, new_list in objects.items():
        if new_list and not existing_objects.get(obj_type):
            existing_objects[obj_type] = new_list
            updated_types.append(f"{obj_type.split('-',1)[1]}={len(new_list)}")
    if updated_types:
        changed = True
        if logger:
            logger(f"➕ Collect: '{location}' – nowe obiekty: {', '.join(updated_types)}")

    # --- 3. frame_size ---
    if frame_size is not None and "frame_size" not in data:
        data["frame_size"] = frame_size
        changed = True

    if changed:
        save_world_json(location, data)
        return "updated"

    if logger:
        logger(f"✅ Collect: '{location}' – brak nowych danych")
    return "ok"
