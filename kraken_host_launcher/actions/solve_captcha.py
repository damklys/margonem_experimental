from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Stałe
# ---------------------------------------------------------------------------

IMMEDIATELY = "immediately"
AT_THE_END  = "at_the_end"
AT_TIME     = "at_time"

_AT_TIME_RE = re.compile(r'^at_time\((\d+(?:\.\d+)?)\)$')


# ---------------------------------------------------------------------------
# Typ wyniku
# ---------------------------------------------------------------------------

class CaptchaTask:
    """
    Zaplanowane wywołanie solve_captcha.

    Atrybuty:
        schedule — "immediately" | "at_the_end" | "at_time"
        delay_s  — opóźnienie w sekundach (znaczące tylko dla at_time)
        result   — True jeśli captcha rozwiązana, False jeśli nie, None jeśli jeszcze nie uruchomiono
    """

    def __init__(self, driver, schedule: str, delay_s: float = 0.0):
        self.driver    = driver
        self.schedule  = schedule
        self.delay_s   = delay_s
        self.result:   Optional[bool]           = None
        self._timer:   Optional[threading.Timer] = None

    def execute(self) -> bool:
        """Uruchamia rozwiązywanie captchy natychmiast. Bezpieczne do wywołania z wątku timera."""
        from captcha import check_and_solve_captcha
        self.result = check_and_solve_captcha(self.driver)
        return self.result

    def cancel(self) -> None:
        """Anuluje zaplanowany timer. Nie ma efektu dla immediately i at_the_end."""
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def __repr__(self) -> str:
        extra = f", delay_s={self.delay_s}" if self.schedule == AT_TIME else ""
        return f"CaptchaTask(schedule={self.schedule!r}{extra}, result={self.result!r})"


# ---------------------------------------------------------------------------
# Walidacja argumentu action
# ---------------------------------------------------------------------------

def _parse_action(value: str) -> tuple[str, float]:
    """
    Parsuje wartość 'action' → (schedule, delay_s).
    Rzuca ValueError przy nieprawidłowym formacie.
    """
    if value == IMMEDIATELY:
        return IMMEDIATELY, 0.0
    if value == AT_THE_END:
        return AT_THE_END, 0.0
    m = _AT_TIME_RE.match(value)
    if m:
        return AT_TIME, float(m.group(1))
    raise ValueError(
        f"Nieprawidłowy argument 'action': {value!r}. "
        f"Dozwolone: 'immediately', 'at_the_end', 'at_time(<sekundy>)'"
    )


def validate_action(value: str) -> str:
    """Waliduje i normalizuje wartość 'action'. Rzuca TypeError/ValueError przy błędzie."""
    if not isinstance(value, str):
        raise TypeError(f"'action' musi być stringiem, otrzymano {type(value).__name__}")
    _parse_action(value)
    return value


# ---------------------------------------------------------------------------
# Pomocnik JSON
# ---------------------------------------------------------------------------

def load_from_json(path: str | Path) -> dict:
    """
    Wczytuje konfigurację z pliku JSON.

    Oczekiwany format:
        { "action": "immediately" }
        { "action": "at_the_end" }
        { "action": "at_time(30)" }

    Zwraca słownik gotowy do rozpakowania jako **kwargs do solve_captcha.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    with p.open(encoding="utf-8") as f:
        cfg = json.load(f)

    allowed = {"action"}
    unknown = set(cfg.keys()) - allowed
    if unknown:
        raise ValueError(f"Nieznane klucze w JSON config: {unknown}. Dozwolone: {allowed}")

    if "action" not in cfg:
        raise ValueError("JSON config musi zawierać klucz 'action'")

    return {"action": validate_action(cfg["action"])}


# ---------------------------------------------------------------------------
# Właściwa implementacja
# ---------------------------------------------------------------------------

def solve_captcha(driver, action: str = IMMEDIATELY) -> CaptchaTask:
    """
    Planuje lub natychmiast wykonuje rozwiązanie captchy.

    Argumenty:
        driver — Selenium WebDriver
        action — kiedy rozwiązać captchę:
                 "immediately"    — rozwiązuje synchronicznie w tym wywołaniu
                 "at_the_end"     — zwraca nieuruchomione zadanie; executor
                                    wywołuje task.execute() w odpowiednim miejscu przepływu
                 "at_time(<s>)"   — uruchamia po <s> sekundach w wątku demona

    Zwraca CaptchaTask:
        .schedule  — tryb uruchomienia
        .delay_s   — opóźnienie w sekundach (0.0 dla immediately i at_the_end)
        .result    — True/False po zakończeniu, None przed uruchomieniem
        .execute() — wywołuje captchę ręcznie (przydatne dla at_the_end)
        .cancel()  — anuluje timer (tylko for at_time, noop dla pozostałych)

    Przykład wywołania z JSON:
        cfg = load_from_json("actions/captcha.json")
        task = solve_captcha(driver, **cfg)
    """
    validate_action(action)
    schedule, delay_s = _parse_action(action)
    task = CaptchaTask(driver, schedule, delay_s)

    if schedule == IMMEDIATELY:
        task.execute()

    elif schedule == AT_TIME:
        timer = threading.Timer(delay_s, task.execute)
        timer.daemon = True
        task._timer = timer
        timer.start()

    # AT_THE_END: zwracamy nieuruchomione zadanie — executor decyduje kiedy uruchomić

    return task
