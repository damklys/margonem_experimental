# kill_e2.py
from selenium.webdriver.common.by import By
import time


def _parse_style_xy(style: str):
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        return float(parts["left"]), float(parts["top"])
    except Exception:
        return None, None


def _center_from_element(el):
    """
    Zwraca (cx, cy, tile) bazując na:
    - left/top ze style
    - width/height z rect
    tile = max(width,height)
    """
    style = el.get_attribute("style") or ""
    left, top = _parse_style_xy(style)
    if left is None or top is None:
        return None, None, None

    r = el.rect
    w = float(r.get("width") or 0)
    h = float(r.get("height") or 0)
    tile = max(w, h) if max(w, h) > 0 else 11.0

    cx = left + w / 2.0
    cy = top + h / 2.0
    return cx, cy, tile


def _in_attack_range(hero_c, e2_c, tile):
    """
    Zasięg ataku: obok + po przekątnej.
    Chebyshev distance <= 1 kafelek (+ tolerancja).
    """
    hx, hy = hero_c
    mx, my = e2_c

    dx = abs(hx - mx) / tile
    dy = abs(hy - my) / tile

    tol = 0.25
    return max(dx, dy) <= 1.0 + tol


def _find_hero(driver):
    return driver.find_element(By.CSS_SELECTOR, "div.mmpMapObject.mmp-hero")


def _find_e2(driver, tip_id: int):
    return driver.find_element(By.CSS_SELECTOR, f'div.mmpMapObject.mmp-elite2[tip-id="{tip_id}"]')


def _safe_get_snapshot(driver, tip_id: int):
    """
    Snapshot: (hero_center, e2_center, tile) albo None jeśli brak/DOM się zmienia.
    """
    try:
        hero = _find_hero(driver)
        e2 = _find_e2(driver, tip_id)
        hx, hy, tile = _center_from_element(hero)
        mx, my, _ = _center_from_element(e2)
    except Exception:
        return None

    if None in (hx, hy, mx, my, tile):
        return None

    return (hx, hy), (mx, my), tile


def _can_press_q(driver, cooldown_s: float) -> bool:
    """
    Globalny cooldown Q zapisany w driverze.
    Dzięki temu Q nie spamuje między kolejnymi wywołaniami kill_e2().
    """
    now = time.time()
    last = getattr(driver, "_last_q_time", 0.0)
    if now - last >= cooldown_s:
        setattr(driver, "_last_q_time", now)
        return True
    return False


def _press_q(driver):
    driver.find_element(By.TAG_NAME, "body").send_keys("q")


def _e2_tile_pos(driver, tip_id: int):
    """Zwraca (tile_x, tile_y) E2 na podstawie CSS left/top i rozmiaru kafla."""
    try:
        e2 = _find_e2(driver, tip_id)
        style = e2.get_attribute("style") or ""
        left, top = _parse_style_xy(style)
        r = e2.rect
        w = float(r.get("width") or 0)
        h = float(r.get("height") or 0)
        tile = max(w, h) if max(w, h) > 0 else 11.0
        return round(left / tile), round(top / tile)
    except Exception:
        return None, None


def _auto_go_to_e2(driver, tip_id: int):
    tx, ty = _e2_tile_pos(driver, tip_id)
    if tx is None:
        return False
    try:
        driver.execute_script(
            "getEngine().hero.autoGoTo({x: arguments[0], y: arguments[1]}, false);",
            tx, ty,
        )
        return True
    except Exception:
        return False


def kill_e2(
    driver,
    tip_id: int,
    poll: float = 0.12,
    max_time_s: float = 12.0,
    repath_if_stuck_s: float = 1.2,
    q_cooldown_s: float = 3.0,
):
    t0 = time.time()

    if not _auto_go_to_e2(driver, tip_id):
        print("❌ e2 nie istnieje (start)")
        return False
    print(f"🎯 autoGoTo e2 {tip_id}")

    last_hero_pos = None
    last_move_time = time.time()
    last_repath_time = 0.0

    while True:
        if time.time() - t0 > max_time_s:
            print(f"⏱️ Timeout podejścia do e2 {tip_id}")
            return False

        snap = _safe_get_snapshot(driver, tip_id)
        if snap is None:
            try:
                _ = _find_e2(driver, tip_id)
            except Exception:
                print(f"⚰️ e2 {tip_id} zniknął")
                return False
            time.sleep(poll)
            continue

        hero_c, e2_c, tile = snap

        # --- jeśli w zasięgu -> Q ---
        if _in_attack_range(hero_c, e2_c, tile):
            if _can_press_q(driver, q_cooldown_s):
                print(f"⚔️ Zasięg OK (tile={tile:.1f}) -> Q")
                _press_q(driver)
                return True
            else:
                time.sleep(poll)
                continue

        # --- re-path gdy stuck ---
        now = time.time()
        if last_hero_pos is None:
            last_hero_pos = hero_c
            last_move_time = now
        else:
            moved = (abs(hero_c[0] - last_hero_pos[0]) > 0.8) or (abs(hero_c[1] - last_hero_pos[1]) > 0.8)
            if moved:
                last_hero_pos = hero_c
                last_move_time = now
            elif (now - last_move_time >= repath_if_stuck_s) and (now - last_repath_time >= 0.8):
                if _auto_go_to_e2(driver, tip_id):
                    print(f"🔁 Re-path autoGoTo e2 {tip_id}")
                    last_repath_time = now
                    last_move_time = now
                else:
                    print(f"⚰️ e2 {tip_id} zniknął przy re-path")
                    return False

        time.sleep(poll)
