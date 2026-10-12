from __future__ import annotations

import json
import functools
import inspect
from pathlib import Path
from typing import overload, Any, Optional

from selenium.webdriver.common.by import By


# ---------------------------------------------------------------------------
# Typy zwracane
# ---------------------------------------------------------------------------

class FoundObject:
    def __init__(
        self,
        tip_id: Any,
        top: float,
        left: float,
        type: str,
        name: str | None = None,
        lvl: int | None = None,
    ):
        self.tip_id = tip_id
        self.top    = top
        self.left   = left
        self.type   = type
        self.name   = name
        self.lvl    = lvl

    def __repr__(self):
        return (
            f"FoundObject(tip_id={self.tip_id!r}, top={self.top}, "
            f"left={self.left}, type={self.type!r}, "
            f"name={self.name!r}, lvl={self.lvl!r})"
        )


# ---------------------------------------------------------------------------
# Stałe
# ---------------------------------------------------------------------------

DEFAULT_TYPES = ["mmp-mob", "mmp-elite", "mmp-npc"]

_TYPE_CSS = {
    "mmp-mob":   "div.mmpMapObject.mmp-mob",
    "mmp-elite": "div.mmpMapObject.mmp-elite",
    "mmp-npc":   "div.mmpMapObject.mmp-npc",
}

_ZONE_TOLERANCE = 15.0  # px


# ---------------------------------------------------------------------------
# JS do odczytu tooltipa (nazwa + poziom) — na bazie kill_object.py
# ---------------------------------------------------------------------------

_ASYNC_TIP_JS = """
var callback = arguments[arguments.length - 1];
var tipId    = arguments[0];
var maxMs    = arguments[1];
var pollMs   = 50;

var el = document.querySelector('[tip-id="' + tipId + '"]');
if (!el) { callback(null); return; }

var r = el.getBoundingClientRect();
var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
['pointerover','mouseover','mouseenter','mousemove'].forEach(function(t) {
    el.dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true,
                                        view:window, clientX:cx, clientY:cy}));
});
if (window.jQuery) window.jQuery(el).trigger('mouseenter').trigger('mouseover');

var elapsed = 0;
function readTip() {
    var tips = document.querySelectorAll('.tip-wrapper');
    for (var i = 0; i < tips.length; i++) {
        if (tips[i].offsetHeight > 0) {
            var c = tips[i].querySelector('.content') || tips[i];
            var span = c.querySelector('span');
            if (span) {
                var text = span.textContent.trim();
                var lvlMatch = text.match(/(\\d+)/);
                var lvl  = lvlMatch ? parseInt(lvlMatch[1]) : null;
                var name = text.replace(/\\s*[\\[(]?\\d+[a-zA-Z]?[\\])]?.*$/, '').trim();
                callback({name: name, lvl: lvl});
                return;
            }
        }
    }
    elapsed += pollMs;
    if (elapsed < maxMs) { setTimeout(readTip, pollMs); }
    else { callback(null); }
}
setTimeout(readTip, pollMs);
"""


# ---------------------------------------------------------------------------
# Helpers DOM
# ---------------------------------------------------------------------------

def _parse_top_left(style: str) -> tuple[Optional[float], Optional[float]]:
    """Zwraca (top, left) z CSS style lub (None, None)."""
    try:
        parts = {}
        for item in style.split(";"):
            if ":" in item:
                k, v = item.strip().split(":", 1)
                parts[k.strip()] = v.strip().replace("px", "")
        return float(parts["top"]), float(parts["left"])
    except Exception:
        return None, None


def _in_zone(
    top: float,
    left: float,
    zones: tuple,
    tolerance: float = _ZONE_TOLERANCE,
) -> bool:
    """Sprawdza czy (top, left) leży w zasięgu ±tolerance od którejkolwiek ze stref.
    Strefy używają konwencji {x: left, y: top}."""
    for z in zones:
        if abs(left - z["x"]) <= tolerance and abs(top - z["y"]) <= tolerance:
            return True
    return False


def _fetch_tip(
    driver,
    tip_id: int | str,
    hover_wait_ms: int = 500,
) -> Optional[dict]:
    """Pobiera {'name': str, 'lvl': int} z tooltipa przez hover JS.
    Zwraca None gdy element niedostępny lub tooltip się nie pojawił."""
    try:
        raw = driver.execute_async_script(_ASYNC_TIP_JS, str(tip_id), hover_wait_ms)
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Walidatory
# ---------------------------------------------------------------------------

def validate_types(value: list) -> list:
    if not isinstance(value, list):
        raise TypeError(f"'type' must be a list, got {type(value).__name__}")
    if not value:
        return DEFAULT_TYPES.copy()
    for item in value:
        if not isinstance(item, str):
            raise TypeError(
                f"Each type must be a string, got {type(item).__name__}: {item!r}"
            )
        if item not in DEFAULT_TYPES:
            raise ValueError(
                f"Unknown type: {item!r}. Allowed: {DEFAULT_TYPES}"
            )
    return value


def validate_names(value: tuple | list) -> tuple:
    if not isinstance(value, (list, tuple)):
        raise TypeError(
            f"'name' must be a list or tuple, got {type(value).__name__}"
        )
    for item in value:
        if not isinstance(item, str):
            raise TypeError(
                f"Each name must be a string, got {type(item).__name__}: {item!r}"
            )
    return tuple(value)


def validate_xy_list(value: tuple | list, field: str) -> tuple:
    if not isinstance(value, (list, tuple)):
        raise TypeError(
            f"'{field}' must be a list or tuple, got {type(value).__name__}"
        )
    result = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(
                f"'{field}[{i}]' must be a dict with 'x' and 'y', "
                f"got {type(item).__name__}"
            )
        if "x" not in item or "y" not in item:
            raise ValueError(
                f"'{field}[{i}]' must contain both 'x' and 'y' keys, "
                f"got: {set(item.keys())}"
            )
        x, y = item["x"], item["y"]
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError(
                f"'{field}[{i}]' x and y must be numeric, "
                f"got x={type(x).__name__}, y={type(y).__name__}"
            )
        result.append({"x": x, "y": y})
    return tuple(result)


def validate_lvl(value: dict) -> dict:
    if not isinstance(value, dict):
        raise TypeError(f"'lvl' must be a dict, got {type(value).__name__}")
    if not value:
        return {}
    unknown = set(value.keys()) - {"min", "max"}
    if unknown:
        raise ValueError(
            f"'lvl' has unknown keys: {unknown}. Allowed: {{'min', 'max'}}"
        )
    result = {}
    for key in ("min", "max"):
        if key in value:
            v = value[key]
            if not isinstance(v, (int, float)):
                raise TypeError(
                    f"'lvl.{key}' must be numeric, got {type(v).__name__}"
                )
            result[key] = v
    if "min" in result and "max" in result and result["min"] > result["max"]:
        raise ValueError(
            f"'lvl.min' ({result['min']}) cannot be greater than "
            f"'lvl.max' ({result['max']})"
        )
    return result


# ---------------------------------------------------------------------------
# Dekorator @validate
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "type":     (validate_types,                             []),
    "name":     (validate_names,                             ()),
    "included": (lambda v: validate_xy_list(v, "included"),  ()),
    "lvl":      (validate_lvl,                               {}),
    "excluded": (lambda v: validate_xy_list(v, "excluded"),  ()),
}


def validate(func):
    """Waliduje argumenty find_object przed wywołaniem właściwej logiki.
    Pomija walidację gdy przekazano _already_validated=True (ścieżka from_json)."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.pop("_already_validated", False):
            return func(*args, **kwargs)

        sig    = inspect.signature(func)
        bound  = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)

        for arg_name, (validator, default) in _VALIDATORS.items():
            raw = params.get(arg_name, default)
            try:
                params[arg_name] = validator(raw)
            except (TypeError, ValueError) as e:
                raise type(e)(f"Validation error for '{arg_name}': {e}") from e

        return func(**params)
    return wrapper


# ---------------------------------------------------------------------------
# Pomocnik JSON
# ---------------------------------------------------------------------------

def load_from_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with p.open(encoding="utf-8") as f:
        cfg = json.load(f)

    allowed = set(_VALIDATORS.keys())
    unknown = set(cfg.keys()) - allowed
    if unknown:
        raise ValueError(f"Unknown keys in JSON config: {unknown}")

    result = {}
    for arg_name, (validator, default) in _VALIDATORS.items():
        raw = cfg.get(arg_name, default)
        try:
            result[arg_name] = validator(raw)
        except (TypeError, ValueError) as e:
            raise type(e)(f"JSON config error for '{arg_name}': {e}") from e

    return result


# ---------------------------------------------------------------------------
# Sygnatury dla type checkerów i IDE  (@overload)
# ---------------------------------------------------------------------------

@overload
def find_object(driver, *, from_json: str | Path) -> list[FoundObject]: ...

@overload
def find_object(
    driver,
    type:     list  = ...,
    name:     tuple = ...,
    included: tuple = ...,
    lvl:      dict  = ...,
    excluded: tuple = ...,
) -> list[FoundObject]: ...


# ---------------------------------------------------------------------------
# Właściwa implementacja
# ---------------------------------------------------------------------------

@validate
def find_object(
    driver,
    type:      list             = [],
    name:      tuple            = (),
    included:  tuple            = (),
    lvl:       dict             = {},
    excluded:  tuple            = (),
    from_json: str | Path | None = None,
) -> list[FoundObject]:
    """
    Wyszukuje obiekty na mapie spełniające podane kryteria.

    Argumenty:
        driver    — Selenium WebDriver
        type      — lista typów obiektów: "mmp-mob" | "mmp-elite" | "mmp-npc"
                    domyślnie szuka wszystkich trzech
        name      — krotka nazw; zwraca tylko obiekty o nazwie z tej listy
                    (wymaga odczytu tooltipa — wolniejsze)
        included  — lista stref {"x": left, "y": top}; zwraca tylko obiekty
                    w pobliżu tych pozycji (tolerancja ±15px)
        lvl       — słownik {"min": int, "max": int}; filtruje po poziomie
                    (wymaga odczytu tooltipa — wolniejsze)
        excluded  — lista stref {"x": left, "y": top}; pomija obiekty
                    w pobliżu tych pozycji
        from_json — ścieżka do pliku JSON z powyższymi parametrami

    Zwraca listę FoundObject posortowaną po tip_id.
    """
    if from_json is not None:
        validated = load_from_json(from_json)
        return find_object(driver, **validated, _already_validated=True)

    need_tip = bool(name) or bool(lvl)
    results: list[FoundObject] = []

    for obj_type in type:
        css = _TYPE_CSS[obj_type]
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, css)
        except Exception:
            continue

        for el in elements:
            try:
                tip_id_str = el.get_attribute("tip-id")
                style      = el.get_attribute("style") or ""
            except Exception:
                continue

            if not tip_id_str:
                continue

            top, left = _parse_top_left(style)
            if top is None or left is None:
                continue

            if excluded and _in_zone(top, left, excluded):
                continue

            if included and not _in_zone(top, left, included):
                continue

            tip_id = int(tip_id_str)
            obj_name: str | None = None
            obj_lvl:  int | None = None

            if need_tip:
                tip = _fetch_tip(driver, tip_id)
                if tip is not None:
                    obj_name = tip.get("name") or None
                    obj_lvl  = tip.get("lvl")

            if name and obj_name not in name:
                continue

            if lvl:
                if obj_lvl is None:
                    continue
                if "min" in lvl and obj_lvl < lvl["min"]:
                    continue
                if "max" in lvl and obj_lvl > lvl["max"]:
                    continue

            results.append(FoundObject(
                tip_id=tip_id,
                top=top,
                left=left,
                type=obj_type,
                name=obj_name,
                lvl=obj_lvl,
            ))

    return results
