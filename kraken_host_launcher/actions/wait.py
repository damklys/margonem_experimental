from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

_CHUNK_S = 0.1   # granulacja sprawdzania stop_event podczas oczekiwania


# ---------------------------------------------------------------------------
# Walidatory
# ---------------------------------------------------------------------------

def validate_seconds(value) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"'seconds' musi być liczbą, otrzymano {type(value).__name__}")
    if value < 0:
        raise ValueError(f"'seconds' musi być nieujemne, otrzymano {value}")
    return float(value)


# ---------------------------------------------------------------------------
# Pomocnik JSON
# ---------------------------------------------------------------------------

def load_from_json(path: str | Path) -> dict:
    """
    Oczekiwany format:
        { "seconds": 5 }
        { "seconds": 2.5 }
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    with p.open(encoding="utf-8") as f:
        cfg = json.load(f)

    allowed = {"seconds"}
    unknown = set(cfg.keys()) - allowed
    if unknown:
        raise ValueError(f"Nieznane klucze w JSON config: {unknown}. Dozwolone: {allowed}")

    if "seconds" not in cfg:
        raise ValueError("JSON config musi zawierać klucz 'seconds'")

    return {"seconds": validate_seconds(cfg["seconds"])}


# ---------------------------------------------------------------------------
# Właściwa implementacja
# ---------------------------------------------------------------------------

def wait(
    driver,
    seconds: float,
    stop_event=None,
    from_json: str | Path | None = None,
) -> float:
    """
    Czeka przez podaną liczbę sekund.

    Argumenty:
        driver     — Selenium WebDriver (nieużywany, wymagany przez konwencję actions)
        seconds    — czas oczekiwania w sekundach (może być ułamkowy)
        stop_event — threading.Event; przerywa oczekiwanie wcześniej gdy ustawiony

    Zwraca faktycznie odczekany czas w sekundach.

    Wywołanie z JSON:
        cfg = load_from_json("wait_config.json")
        wait(driver, **cfg)
    """
    if from_json is not None:
        cfg = load_from_json(from_json)
        return wait(driver, stop_event=stop_event, **cfg)

    seconds = validate_seconds(seconds)

    t0        = time.time()
    deadline  = t0 + seconds

    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        if stop_event is not None and stop_event.is_set():
            break
        time.sleep(min(_CHUNK_S, remaining))

    return time.time() - t0
