from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Walidatory
# ---------------------------------------------------------------------------

def validate_location(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"'location' musi być stringiem, otrzymano {type(value).__name__}")
    value = value.strip()
    if not value:
        raise ValueError("'location' nie może być pustym stringiem")
    return value


def validate_timeout(value) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"'timeout_s' musi być liczbą, otrzymano {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"'timeout_s' musi być dodatnie, otrzymano {value}")
    return float(value)


# ---------------------------------------------------------------------------
# Pomocnik JSON
# ---------------------------------------------------------------------------

def load_from_json(path: str | Path) -> dict:
    """
    Oczekiwany format:
        { "location": "Nazwa Lokacji" }
        { "location": "Nazwa Lokacji", "timeout_s": 120 }
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    with p.open(encoding="utf-8") as f:
        cfg = json.load(f)

    allowed = {"location", "timeout_s"}
    unknown = set(cfg.keys()) - allowed
    if unknown:
        raise ValueError(f"Nieznane klucze w JSON config: {unknown}. Dozwolone: {allowed}")

    if "location" not in cfg:
        raise ValueError("JSON config musi zawierać klucz 'location'")

    result: dict = {"location": validate_location(cfg["location"])}
    if "timeout_s" in cfg:
        result["timeout_s"] = validate_timeout(cfg["timeout_s"])

    return result


# ---------------------------------------------------------------------------
# Właściwa implementacja
# ---------------------------------------------------------------------------

def navigate_to(
    driver,
    location: str,
    timeout_s: float = 300.0,
    stop_event=None,
    log_fn=print,
    from_json: str | Path | None = None,
) -> bool:
    """
    Nawiguje do podanej lokacji używając pathfindingu (travel_to).
    """
    if from_json is not None:
        cfg = load_from_json(from_json)
        return navigate_to(driver, stop_event=stop_event, log_fn=log_fn, **cfg)

    location  = validate_location(location)
    timeout_s = validate_timeout(timeout_s)

    log_fn(f"🗺️  navigate_to: '{location}'…")
    from move import travel_to
    result = travel_to(
        driver,
        location,
        stop_event=stop_event,
        wait_location_timeout_s=timeout_s,
    )
    log_fn(f"{'✅' if result else '❌'} navigate_to: '{location}' → {'OK' if result else 'FAILED'}")
    return result
