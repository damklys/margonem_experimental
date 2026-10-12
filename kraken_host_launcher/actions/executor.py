from __future__ import annotations

import inspect
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# ActionRegistry
# ---------------------------------------------------------------------------

class ActionRegistry:
    """
    Mapuje nazwy akcji (string) na callables o sygnaturze:
        fn(driver, **params) -> Any

    Przykład budowania:
        registry = ActionRegistry()
        registry.register("find_object",  find_object)
        registry.register("kill_object",  kill_object_action)
        registry.register("solve_captcha", solve_captcha)
    """

    def __init__(self):
        self._actions: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        self._actions[name] = fn

    def get(self, name: str) -> Optional[Callable]:
        return self._actions.get(name)

    def names(self) -> list[str]:
        return sorted(self._actions.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._actions


# ---------------------------------------------------------------------------
# PlaybookContext — współdzielony stan między krokami
# ---------------------------------------------------------------------------

class PlaybookContext:
    """
    Przechowuje zmienne produkowane przez kroki (save_as)
    i udostępnia je kolejnym krokom przez referencje $zmienna.
    """

    def __init__(self):
        self._store: dict[str, Any] = {}

    def set(self, name: str, value: Any) -> None:
        self._store[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        return self._store.get(name, default)

    def __contains__(self, name: str) -> bool:
        return name in self._store

    def __repr__(self) -> str:
        return f"PlaybookContext({self._store!r})"


# ---------------------------------------------------------------------------
# Rozwiązywanie zmiennych $var i $var[index]
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r'^\$([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)\])?$')


def _resolve_value(value: Any, ctx: PlaybookContext) -> Any:
    """
    Zamienia referencje $zmienna i $zmienna[idx] na wartości z kontekstu.
    Wartości niebędące stringiem lub nierozpoczynające się od '$' są zwracane bez zmian.
    """
    if not isinstance(value, str):
        return value
    m = _VAR_RE.match(value)
    if not m:
        return value
    name, index = m.group(1), m.group(2)
    resolved = ctx.get(name)
    if index is not None and resolved is not None:
        try:
            resolved = resolved[int(index)]
        except (IndexError, TypeError, KeyError):
            resolved = None
    return resolved


def _resolve_params(params: dict, ctx: PlaybookContext) -> dict:
    return {k: _resolve_value(v, ctx) for k, v in params.items()}


# ---------------------------------------------------------------------------
# Ewaluacja warunków
# ---------------------------------------------------------------------------

def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, dict, tuple, str)):
        return len(value) == 0
    return False


def _eval_condition(cond: dict, ctx: PlaybookContext) -> bool:
    """
    Ewaluuje słownik warunków. Zwraca True gdy WSZYSTKIE warunki są spełnione.

    Obsługiwane formy:
        {"$var": "empty"}        — None / [] / {} / "" / ()
        {"$var": "not_empty"}    — niepusta
        {"$var": "true"}         — wartość truthy
        {"$var": "false"}        — wartość falsy
        {"$var": "eq:X"}         — str(value) == X
        {"$var": "neq:X"}        — str(value) != X
        {"$var": "gt:N"}         — float(value) > N
        {"$var": "gte:N"}        — float(value) >= N
        {"$var": "lt:N"}         — float(value) < N
        {"$var": "lte:N"}        — float(value) <= N
    """
    for key, check in cond.items():
        value = _resolve_value(key, ctx) if key.startswith("$") else ctx.get(key)
        if check == "empty" and not _is_empty(value):
            return False
        if check == "not_empty" and _is_empty(value):
            return False
        if check == "true" and not value:
            return False
        if check == "false" and value:
            return False
        if isinstance(check, str):
            if check.startswith("eq:") and str(value) != check[3:]:
                return False
            if check.startswith("neq:") and str(value) == check[4:]:
                return False
            for prefix, op in (("gt:", ">"), ("gte:", ">="), ("lt:", "<"), ("lte:", "<=")):
                if check.startswith(prefix):
                    try:
                        n = float(check[len(prefix):])
                        v = float(value)
                        if op == ">"  and not (v >  n): return False
                        if op == ">=" and not (v >= n): return False
                        if op == "<"  and not (v <  n): return False
                        if op == "<=" and not (v <= n): return False
                    except (TypeError, ValueError):
                        return False
    return True


# ---------------------------------------------------------------------------
# PlaybookExecutor
# ---------------------------------------------------------------------------

class PlaybookExecutor:
    """
    Wykonuje playbook wczytany z JSON.

    Schemat playbooka:
    {
        "name": "...",
        "steps": [
            // krok akcji
            {
                "action":    "nazwa_akcji",
                "params":    { "klucz": "wartość lub $zmienna" },
                "save_as":   "nazwa_zmiennej",   // opcjonalne — zapisuje wynik w kontekście
                "skip_when": { "$zmienna": "empty" }  // opcjonalne — pomija krok gdy warunek spełniony
            },
            // krok pętli
            {
                "loop": {
                    "steps":          [...],
                    "stop_when":      { "$zmienna": "..." },  // opcjonalne — warunek stopu po iteracji
                    "max_iterations": 100000,                 // opcjonalne
                    "sleep_s":        0.1                     // opcjonalne — pauza między iteracjami
                }
            }
        ]
    }

    Użycie:
        registry = ActionRegistry()
        registry.register("find_object",   find_object)
        registry.register("kill_object",   kill_object_action)
        registry.register("solve_captcha", solve_captcha)

        executor = PlaybookExecutor(driver, registry=registry, stop_event=stop, log_fn=self.log)
        playbook = load_playbook("playbooks/basic_farm.json")
        executor.run(playbook)
    """

    def __init__(
        self,
        driver,
        *,
        registry: ActionRegistry,
        stop_event=None,
        log_fn: Callable[[str], None] = print,
    ):
        self.driver     = driver
        self.registry   = registry
        self.stop_event = stop_event
        self.log        = log_fn
        self.ctx        = PlaybookContext()

    # ------------------------------------------------------------------
    # Publiczne API
    # ------------------------------------------------------------------

    def run(self, playbook: dict) -> None:
        """Uruchamia playbook synchronicznie. Blokuje do ukończenia lub zatrzymania."""
        name = playbook.get("name", "<unnamed>")
        self.log(f"▶️  Playbook: {name}")
        for k, v in playbook.get("context_init", {}).items():
            self.ctx.set(k, v)
        for step in playbook.get("steps", []):
            if self._stopped():
                break
            self._exec_step(step)
        self.log(f"⏹️  Playbook zakończony: {name}")

    # ------------------------------------------------------------------
    # Wewnętrzna logika
    # ------------------------------------------------------------------

    def _stopped(self) -> bool:
        return self.stop_event is not None and self.stop_event.is_set()

    def _exec_step(self, step: dict) -> Any:
        if "loop" in step:
            self._exec_loop(step["loop"])
            return None
        if "if" in step:
            self._exec_conditional(step)
            return None
        if "set" in step:
            for k, v in step["set"].items():
                self.ctx.set(k, _resolve_value(v, self.ctx) if isinstance(v, str) else v)
            return None
        if "action" in step:
            return self._exec_action(step)
        self.log(f"⚠️  Nieznany typ kroku: {list(step.keys())}")
        return None

    def _exec_conditional(self, step: dict) -> None:
        branch = "then" if _eval_condition(step["if"], self.ctx) else "else"
        for s in step.get(branch, []):
            if self._stopped():
                return
            self._exec_step(s)

    def _exec_loop(self, loop_def: dict) -> None:
        steps      = loop_def.get("steps", [])
        stop_when  = loop_def.get("stop_when")       # warunek stopu — dict lub None
        max_iter   = int(loop_def.get("max_iterations", 100_000))
        sleep_s    = float(loop_def.get("sleep_s", 0.0))

        for i in range(max_iter):
            if self._stopped():
                break

            for step in steps:
                if self._stopped():
                    return
                self._exec_step(step)

            if stop_when is not None and _eval_condition(stop_when, self.ctx):
                self.log(f"🔁 Pętla: warunek stop_when spełniony po {i + 1} iteracjach")
                break

            if sleep_s > 0:
                time.sleep(sleep_s)

    def _exec_action(self, step: dict) -> Any:
        action_name = step["action"]
        raw_params  = step.get("params", {})
        save_as     = step.get("save_as")
        skip_when   = step.get("skip_when")

        if skip_when is not None and _eval_condition(skip_when, self.ctx):
            self.log(f"⏭️  Pomijam '{action_name}' (skip_when)")
            return None

        params = _resolve_params(raw_params, self.ctx)

        fn = self.registry.get(action_name)
        if fn is None:
            self.log(
                f"❌ Nieznana akcja: '{action_name}'. "
                f"Dostępne: {self.registry.names()}"
            )
            return None

        # Wstrzyknij stop_event, registry i log_fn jeśli akcja je akceptuje
        try:
            sig = inspect.signature(fn)
            if self.stop_event is not None and "stop_event" not in params:
                if "stop_event" in sig.parameters:
                    params["stop_event"] = self.stop_event
            if self.registry is not None and "registry" not in params:
                if "registry" in sig.parameters:
                    params["registry"] = self.registry
            if "log_fn" not in params and "log_fn" in sig.parameters:
                params["log_fn"] = self.log
        except (ValueError, TypeError):
            pass

        _SILENT = {"wait", "anti_afk", "solve_captcha"}
        if action_name not in _SILENT:
            self.log(f"▶  {action_name}")
        try:
            result = fn(self.driver, **params)
        except Exception as e:
            self.log(f"❌ Błąd akcji '{action_name}': {e}")
            return None
        if action_name not in _SILENT:
            self.log(f"✓  {action_name} → {result!r}")

        if save_as is not None:
            self.ctx.set(save_as, result)

        return result


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_playbook(path: str | Path) -> dict:
    """
    Wczytuje i waliduje strukturalnie playbook z pliku JSON.

    Rzuca: FileNotFoundError, ValueError, json.JSONDecodeError.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Playbook nie znaleziony: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Playbook musi być obiektem JSON (słownikiem)")
    if "steps" not in data:
        raise ValueError("Playbook musi zawierać klucz 'steps'")
    if not isinstance(data["steps"], list):
        raise ValueError("'steps' musi być listą")

    return data
