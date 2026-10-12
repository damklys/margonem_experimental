from __future__ import annotations

import time
from typing import Optional


def wait_battle(
    driver,
    timeout_s: float = 600.0,
    fight_position: Optional[dict] = None,
    stop_event=None,
    log_fn=print,
) -> bool:
    """
    Czeka na pojawienie się okna walki.
    W pętli oczekiwania sprawdza captchę/anti-afk i utrzymuje pozycję.
    """
    from anti_afk import check_interrupts
    from kolos_mode import _click_minimap_pos

    def _battle_visible() -> bool:
        from selenium.webdriver.common.by import By
        try:
            el = driver.find_element(By.CSS_SELECTOR, ".battle-area")
            if el.is_displayed():
                return True
        except Exception:
            pass
        try:
            el = driver.find_element(By.CSS_SELECTOR, "div.battle-window")
            return "display: block" in (el.get_attribute("style") or "")
        except Exception:
            return False

    if _battle_visible():
        log_fn("⚔️  wait_battle: okno walki już widoczne")
        return True

    log_fn("⏳ wait_battle: czekam na okno walki…")
    t0       = time.time()
    last_log = 0.0

    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            return False

        check_interrupts(driver, logger=log_fn)

        if fight_position:
            _click_minimap_pos(driver, float(fight_position["top"]), float(fight_position["left"]))

        if _battle_visible():
            log_fn("⚔️  wait_battle: okno walki pojawiło się!")
            return True

        if time.time() - last_log >= 30:
            elapsed = int(time.time() - t0)
            log_fn(f"⏳ wait_battle: wciąż czekam… ({elapsed}s)")
            last_log = time.time()

        time.sleep(2.0)

    log_fn("⏰ wait_battle: timeout — okno walki nie pojawiło się")
    return False


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("timeout_s", "fight_position") if k in cfg}
