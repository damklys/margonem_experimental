from __future__ import annotations

import time

from selenium.webdriver.common.by import By


def wait_death(driver, timeout_s: float = 120.0, stop_event=None, log_fn=print) -> bool:
    """
    Czeka na śmierć, następnie na respawn bohatera.
    """
    from anti_afk import check_interrupts

    _SELECTORS = (
        "div.dead-overlay.map-overlay",
        "div.dead-overlay",
        ".unconscious-screen",
        "div.dead-hero-overlay",
        "div.inner-text[data-trans='unconcious_info_txt']",
    )

    def _is_dead() -> bool:
        for sel in _SELECTORS:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    return True
            except Exception:
                pass
        return False

    log_fn("💀 wait_death: czekam na ekran śmierci…")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            return False
        check_interrupts(driver, logger=log_fn)
        if _is_dead():
            log_fn("💀 wait_death: ekran śmierci wykryty — czekam na respawn…")
            break
        time.sleep(2.0)

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            return False
        check_interrupts(driver, logger=log_fn)
        if not _is_dead():
            log_fn("✅ wait_death: respawn — bohater żyje")
            return True
        time.sleep(2.0)

    log_fn("⏰ wait_death: timeout")
    return False


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("timeout_s",) if k in cfg}
