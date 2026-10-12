# move.py
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# ----------------- helpers -----------------

def _parse_style_xy(style: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        left = float(parts.get("left"))
        top = float(parts.get("top"))
        return left, top
    except Exception:
        return None, None


def _dist2(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _get_location_text(driver) -> str:
    el = driver.find_element(By.CSS_SELECTOR, "span.location")
    return (el.text or "").strip()


def get_character_level(driver) -> Optional[int]:
    try:
        el = driver.find_element(By.CSS_SELECTOR, "span.heroname")
        m = re.search(r'\((\d+)[a-zA-Z]\)', el.text or "")
        return int(m.group(1)) if m else None
    except Exception:
        return None


def _wait_for_location(
    driver,
    expected: str,
    timeout_s: float = 3.0,
    poll: float = 0.10,
) -> bool:
    t0 = time.time()
    while time.time() - t0 <= timeout_s:
        try:
            if _get_location_text(driver) == expected:
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def _load_config(cfg: Union[str, Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if isinstance(cfg, list):
        return cfg

    if isinstance(cfg, dict):
        if "route" in cfg and isinstance(cfg["route"], list):
            return cfg["route"]
        return list(cfg.values())

    if not isinstance(cfg, str):
        raise TypeError("cfg must be path (str) or parsed config (dict/list)")

    path = cfg
    ext = os.path.splitext(path.lower())[1]

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    if ext in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "Brak PyYAML. Zainstaluj: pip install pyyaml albo użyj JSON."
            ) from e
        data = yaml.safe_load(raw)
    else:
        data = json.loads(raw)

    if isinstance(data, dict) and "route" in data and isinstance(data["route"], list):
        return data["route"]
    if isinstance(data, list):
        return data

    raise ValueError("Config must be a list of steps or {'route':[...]}.")


def _find_best_match_element_by_xy(
    driver,
    css_selector: str,
    target_left: float,
    target_top: float,
    max_px_delta: float = 8.0,
):
    els = driver.find_elements(By.CSS_SELECTOR, css_selector)
    if not els:
        return None

    target = (float(target_left), float(target_top))
    best = None
    best_d2 = 1e18

    for el in els:
        style = el.get_attribute("style") or ""
        left, top = _parse_style_xy(style)
        if left is None or top is None:
            continue

        cand = (left, top)
        d2 = _dist2(cand, target)

        if d2 < best_d2:
            best_d2 = d2
            best = (el, left, top)

    if best is None:
        return None

    el, left, top = best

    if abs(left - target[0]) > max_px_delta or abs(top - target[1]) > max_px_delta:
        return None

    return el


def _js_click(driver, el) -> None:
    driver.execute_script("arguments[0].click();", el)


def _get_hero_css_pos(driver) -> "Optional[Tuple[float, float]]":
    """Zwraca (top, left) bohatera z CSS style lub None."""
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        style = hero.get_attribute("style") or ""
        lm = re.search(r'left:\s*([\d.]+)px', style)
        tm = re.search(r'top:\s*([\d.]+)px',  style)
        if lm and tm:
            return float(tm.group(1)), float(lm.group(1))
    except Exception:
        pass
    return None


def _send_key_k(driver) -> bool:
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys("k")
        return True
    except Exception:
        try:
            html = driver.find_element(By.TAG_NAME, "html")
            html.send_keys("k")
            return True
        except Exception:
            return False


# ----------------- API -----------------

def move_to_next_map(
    driver,
    config: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    *,
    max_px_delta: float = 8.0,
    after_static_sleep: float = 0.25,
    after_gw_sleep: float = 0.10,
    wait_location_timeout_s: float = 3.0,
    force_resync: bool = False,
) -> bool:
    """
    Gdy brak mobów: przechodzimy zgodnie z sekwencją w configu.

    Odczytuje aktualną mapę z span.location, wybiera krok na podstawie
    driver._move_seq_idx, klika przejście i czeka na potwierdzenie zmiany lokacji.
    Jeśli lokacja się nie zmieni, próbuje klawiszem 'K' jako fallback.

    Zwraca True jeśli wykonało przejście i potwierdziło zmianę, inaczej False.
    """
    steps = _load_config(config)
    if not steps:
        return False

    loc = _get_location_text(driver)

    idx = int(getattr(driver, "_move_seq_idx", 0))
    if idx < 0 or idx >= len(steps):
        idx = 0

    def step_loc(i: int) -> str:
        return str(steps[i].get("location", "")).strip()

    # --- resync: znajdź pierwsze wystąpienie aktualnej lokacji w route ---
    if force_resync:
        found = None
        for i in range(len(steps)):
            if loc == step_loc(i):
                found = i
                break
        if found is None:
            print(f"🟠 move: Nie znam lokacji '{loc}' (brak w configu).")
            return False
        idx = found

    # --- jeśli idx nie pasuje do lokacji, szukamy dopasowania do przodu od idx ---
    if loc != step_loc(idx):
        found = None
        for offset in range(len(steps)):
            j = (idx + offset) % len(steps)
            if loc == step_loc(j):
                found = j
                break
        if found is None:
            print(f"🟠 move: Nie znam lokacji '{loc}' (brak w configu).")
            return False
        idx = found

    step = steps[idx]
    next_idx = (idx + 1) % len(steps)
    expected_next_loc = step_loc(next_idx)

    # 1) static_object (opcjonalnie)
    static_obj = step.get("static_object")
    if static_obj:
        st_top = float(static_obj["top"])
        st_left = float(static_obj["left"])
        sel = static_obj.get("selector", "div.mmpMapObject")

        el = _find_best_match_element_by_xy(
            driver, sel, st_left, st_top, max_px_delta=max_px_delta
        )
        if el is None:
            print(f"🟠 move: Nie znalazłem static_object na '{loc}' @ (top={st_top}, left={st_left}).")
            return False

        _js_click(driver, el)
        print(f"🧩 move: Klik static_object @ left={st_left} top={st_top} (loc='{loc}')")
        time.sleep(after_static_sleep)

    # 2) przejście gw
    gw_top = float(step["gw_top"])
    gw_left = float(step["gw_left"])
    gw_selector = step.get("gw_selector", "div.mmpMapObject.mmp-gw")

    gw_el = _find_best_match_element_by_xy(
        driver, gw_selector, gw_left, gw_top, max_px_delta=max_px_delta
    )
    if gw_el is None:
        print(f"🟠 move: Nie znalazłem przejścia gw na '{loc}' @ (top={gw_top}, left={gw_left}).")
        return False

    _js_click(driver, gw_el)
    print(f"➡️ move: Przejście gw @ left={gw_left} top={gw_top} (loc='{loc}')")

    # 3) potwierdź zmianę lokacji
    time.sleep(after_gw_sleep)
    ok = _wait_for_location(driver, expected_next_loc, timeout_s=wait_location_timeout_s)

    if ok:
        setattr(driver, "_move_seq_idx", next_idx)
        print(f"✅ move: Lokacja potwierdzona -> '{expected_next_loc}' (seq={next_idx})")
        return True

    # 4) fallback: klawisz "K"
    print(
        f"🟠 move: Nie potwierdzono zmiany lokacji na '{expected_next_loc}' "
        f"(timeout={wait_location_timeout_s}s). Próbuję przejść klawiszem 'K'..."
    )

    sent = _send_key_k(driver)
    if not sent:
        print("🔴 move: Nie udało się wysłać klawisza 'K'. Zostaję na miejscu.")
        return False

    time.sleep(0.15)
    ok_k = _wait_for_location(driver, expected_next_loc, timeout_s=wait_location_timeout_s)

    if ok_k:
        setattr(driver, "_move_seq_idx", next_idx)
        print(f"✅ move: Lokacja potwierdzona po klawiszu 'K' -> '{expected_next_loc}' (seq={next_idx})")
        return True

    print(f"🔴 move: Nadal brak zmiany lokacji na '{expected_next_loc}'. Zostaję na seq={idx}.")
    return False


def travel_to(
    driver,
    target_location: str,
    *,
    stop_event=None,
    max_px_delta: float = 8.0,
    wait_location_timeout_s: float = 300.0,
    interrupt_fn=None,
) -> bool:
    """Navigate to target_location using pathfinding.

    Uses find_route to compute the shortest path, then executes each hop
    sequentially.  Indirect destinations (directly: false in world JSONs) are
    expanded into flat gateway-click sequences automatically by find_route.

    interrupt_fn(driver) -> bool: jeśli zwróci True, travel_to przerywa i zwraca False.

    Returns True on success, False on failure.
    """
    from find_route import route as compute_route

    current = _get_location_text(driver)
    if current == target_location:
        return True

    try:
        travel_data = compute_route(current, target_location)
    except Exception as e:
        print(f"🔴 travel_to: brak trasy {current!r} → {target_location!r}: {e}")
        return False

    hops = travel_data.get("route", [])
    if not hops:
        return _get_location_text(driver) == target_location

    print(
        f"🗺️  travel_to [{current} → {target_location}]: "
        f"{' → '.join(h['location'] for h in hops)} → {target_location}"
    )

    _STUCK_CHECK_S = 5.0   # co ile sekund sprawdzamy pozycję bohatera
    _POLL_S        = 0.20  # jak często sprawdzamy lokację w pętli

    for i, hop in enumerate(hops):
        if stop_event is not None and stop_event.is_set():
            return False

        expected_next = hops[i + 1]["location"] if i + 1 < len(hops) else target_location
        gw_selector   = hop.get("gw_selector", "div.mmpMapObject.mmp-gw")
        gw_left       = float(hop["gw_left"])
        gw_top        = float(hop["gw_top"])

        gw_el = _find_best_match_element_by_xy(
            driver, gw_selector, gw_left, gw_top, max_px_delta=max_px_delta,
        )
        if gw_el is None:
            print(
                f"🔴 travel_to: brak bramki @ ({gw_left}, {gw_top}) "
                f"na {hop['location']!r}"
            )
            return False

        _js_click(driver, gw_el)
        print(f"➡️  travel_to [{i+1}/{len(hops)}]: {hop['location']} → {expected_next}")

        # Monitoruj pozycję bohatera — retry jeśli stoi w miejscu przez 5s
        # Pierwsze 2 retry w odstępach 2s, potem normalny 5s
        _EARLY_RETRY_S   = 2.0
        _EARLY_RETRY_N   = 2
        _INTERRUPT_CHECK = 3.0  # co ile sekund sprawdzamy captchę / stasis

        t0               = time.time()
        last_check       = t0
        last_interrupt   = t0
        last_pos         = _get_hero_css_pos(driver)
        arrived          = False
        retry_count      = 0

        while time.time() - t0 < wait_location_timeout_s:
            if stop_event is not None and stop_event.is_set():
                return False

            time.sleep(_POLL_S)

            try:
                if _get_location_text(driver) == expected_next:
                    arrived = True
                    break
            except Exception:
                pass

            now = time.time()

            # Captcha + anti-AFK
            if now - last_interrupt >= _INTERRUPT_CHECK:
                try:
                    from anti_afk import check_interrupts
                    check_interrupts(driver)
                except Exception:
                    pass
                if interrupt_fn is not None:
                    try:
                        if interrupt_fn(driver):
                            return False
                    except Exception:
                        pass
                last_interrupt = now

            check_interval = _EARLY_RETRY_S if retry_count < _EARLY_RETRY_N else _STUCK_CHECK_S
            if now - last_check >= check_interval:
                cur_pos = _get_hero_css_pos(driver)
                if cur_pos is not None and last_pos is not None:
                    dt = abs(cur_pos[0] - last_pos[0]) + abs(cur_pos[1] - last_pos[1])
                    if dt < 1.0:
                        print(
                            f"🔄 travel_to: bohater nie ruszył ({cur_pos[0]:.1f},{cur_pos[1]:.1f}) "
                            f"— ponawiam klik bramki @ ({gw_left},{gw_top})"
                        )
                        gw_retry = _find_best_match_element_by_xy(
                            driver, gw_selector, gw_left, gw_top, max_px_delta=max_px_delta,
                        )
                        if gw_retry is not None:
                            _js_click(driver, gw_retry)
                        else:
                            print(f"⚠️  travel_to: bramka zniknęła z mapy przy retry")
                        retry_count += 1
                last_pos   = cur_pos
                last_check = now

        if not arrived:
            print(f"🔴 travel_to: timeout oczekując {expected_next!r} po przejściu z {hop['location']!r}")
            return False

    return True
