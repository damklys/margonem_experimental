"""E2 (Elite II) mode: position-based hunting with leader gather and attacker logic."""
import re
import time

from selenium.webdriver.common.by import By


# ── helpers ──────────────────────────────────────────────────────────────────

def _location(driver) -> str:
    for sel in ("span.location", "#map-name"):
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            t = (el.text or "").strip()
            if t:
                return t
        except Exception:
            pass
    return ""


def _hero_pos_css(driver):
    """(top_px, left_px) from hero element CSS style."""
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        style = hero.get_attribute("style") or ""
        tm = re.search(r'top:\s*([\d.]+)px', style)
        lm = re.search(r'left:\s*([\d.]+)px', style)
        if tm and lm:
            return float(tm.group(1)), float(lm.group(1))
    except Exception:
        pass
    return None, None


def _map_show(driver):
    try:
        from enable_map import enable_map
        enable_map(driver, enabled=True)
    except Exception:
        pass


def _map_hide(driver):
    try:
        from enable_map import enable_map
        enable_map(driver, enabled=False)
    except Exception:
        pass


def _auto_go_to(driver, x: int, y: int) -> bool:
    try:
        driver.execute_script(
            "getEngine().hero.autoGoTo({x: arguments[0], y: arguments[1]}, false);",
            int(x), int(y),
        )
        return True
    except Exception:
        return False


def _at_pos(driver, top: float, left: float, tol: float) -> bool:
    ht, hl = _hero_pos_css(driver)
    if ht is None:
        return False
    return abs(ht - top) <= tol and abs(hl - left) <= tol


def _go_to_pos(driver, x: int, y: int, top: float, left: float, tol: float, timeout: float = 30.0) -> bool:
    _auto_go_to(driver, x, y)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _at_pos(driver, top, left, tol):
            return True
        time.sleep(0.2)
    return False


def _press_key(driver, key: str):
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(key)
    except Exception:
        pass


def _detect_e2(driver):
    from get_near_e2 import get_near_e2
    return get_near_e2(driver)


# ── main loop ─────────────────────────────────────────────────────────────────

def run_e2(
    driver,
    e2_cfg: dict,
    is_leader: bool,
    is_attacker: bool,
    wait_pos: dict,
    stop_event,
    log_fn=print,
):
    from move import travel_to
    from captcha import check_and_solve_captcha
    from kill_e2 import kill_e2

    location   = e2_cfg["location"]
    pos_top    = float(wait_pos["top"])
    pos_left   = float(wait_pos["left"])
    tol        = float(e2_cfg.get("tolerance_px", 14.0))
    gather_key = e2_cfg.get("gather_key", "g")

    last_gather  = 0.0
    last_e2_seen = 0.0
    need_return  = True
    at_position  = False

    log_fn(
        f"🦑 E2 start │ "
        f"{'lider' if is_leader else 'follow'} │ "
        f"{'attacker' if is_attacker else 'support'} │ "
        f"poz=({wait_pos['x']},{wait_pos['y']})"
    )

    if is_attacker:
        _map_show(driver)
    else:
        _map_hide(driver)

    while not stop_event.is_set():
        check_and_solve_captcha(driver)

        # ── 1. Upewnij się że jesteś w odpowiedniej lokacji ──────────────
        try:
            loc = _location(driver)
        except Exception:
            time.sleep(1)
            continue

        if loc != location:
            if is_attacker:
                _map_show(driver)
            log_fn(f"🗺️  Jadę do {location}…")
            if not travel_to(driver, location, stop_event=stop_event):
                log_fn(f"❌ Nie dotarłem do {location}")
                time.sleep(5)
                continue
            log_fn(f"✅ {location}")
            if is_attacker:
                _map_show(driver)
            need_return = True
            at_position = False

        # ── 2. Lider: zbieranie grupy co 3 s ────────────────────────────
        now = time.time()
        if is_leader and now - last_gather >= 3.0:
            _press_key(driver, gather_key)
            last_gather = now

        # ── 3. Skanuj E2 ────────────────────────────────────────────────
        e2_id = _detect_e2(driver)

        if e2_id is not None:
            last_e2_seen = time.time()
            at_position  = False
            if is_attacker:
                log_fn(f"⚔️  E2 id={e2_id} — podchodzę i atakuję!")
                kill_e2(driver, e2_id)
                need_return = True

        else:
            e2_ago = (time.time() - last_e2_seen) if last_e2_seen > 0 else 9999.0
            can_return = (not is_attacker) or (e2_ago >= 5.0)

            if need_return and can_return:
                log_fn(f"↩️  Wracam na ({wait_pos['x']},{wait_pos['y']})")
                if _go_to_pos(driver, wait_pos["x"], wait_pos["y"], pos_top, pos_left, tol):
                    need_return = False
                    at_position = True
                    log_fn(f"📍 Pozycja ({wait_pos['x']},{wait_pos['y']}) osiągnięta")
                    if not is_attacker:
                        _map_hide(driver)
            elif not need_return and not _at_pos(driver, pos_top, pos_left, tol):
                need_return = True
                at_position = False

        time.sleep(0.3)
