from __future__ import annotations

import time
from typing import Optional


def move_to(
    driver,
    position: dict,
    tolerance: float = 25.0,
    timeout_s: float = 30.0,
    stop_event=None,
    log_fn=print,
) -> bool:
    """
    Przesuwa bohatera na (top, left) na bieżącej mapie przez kliknięcie minimapy.
    """
    from kolos_mode import _click_minimap_pos, _hero_pos
    from enable_map import enable_map
    from anti_afk import check_interrupts

    top  = float(position["top"])
    left = float(position["left"])
    tol  = float(position.get("tolerance", tolerance))

    def _at_target() -> bool:
        ht, hl = _hero_pos(driver)
        return ht is not None and abs(ht - top) <= tol and abs(hl - left) <= tol

    if _at_target():
        log_fn(f"🦶 move_to: już na pozycji ({top}, {left})")
        return True

    log_fn(f"🦶 move_to: idę na ({top}, {left})…")
    try:
        enable_map(driver, enabled=True)
    except Exception:
        pass

    _click_minimap_pos(driver, top, left)

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            break
        check_interrupts(driver, logger=log_fn)
        if _at_target():
            try:
                enable_map(driver, enabled=False)
            except Exception:
                pass
            log_fn(f"✅ move_to: dotarłem na ({top}, {left})")
            return True
        time.sleep(1.0)

    try:
        enable_map(driver, enabled=False)
    except Exception:
        pass
    log_fn(f"⏰ move_to: timeout — nie dotarłem na ({top}, {left})")
    return False


def load_from_json(cfg: dict) -> dict:
    result = {"position": cfg["position"]}
    for k in ("tolerance", "timeout_s"):
        if k in cfg:
            result[k] = cfg[k]
    return result
