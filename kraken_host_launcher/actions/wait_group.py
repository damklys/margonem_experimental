from __future__ import annotations

import time
from typing import Optional

from selenium.webdriver.common.by import By


def wait_group(
    driver,
    min_size: int = 5,
    position: Optional[dict] = None,
    timeout_s: float = 600.0,
    stop_event=None,
    log_fn=print,
) -> int:
    """
    Follower: akceptuje zaproszenia do grupy i czeka aż rozmiar >= min_size.
    Repositioning only after stasis/captcha handling (jak oryginał kolos_mode).
    """
    from kolos_mode import _party_size, _click_minimap_pos
    from anti_afk import check_interrupts

    log_fn(f"⏳ wait_group: czekam na grupę ≥{min_size} graczy…")
    t0       = time.time()
    last_log = 0.0

    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            break

        # Reposition tylko gdy check_interrupts coś obsłużył (staza/captcha)
        interrupted = check_interrupts(driver, logger=log_fn)
        if interrupted and position:
            _click_minimap_pos(driver, float(position["top"]), float(position["left"]))

        # Akceptuj zaproszenia
        try:
            for alert in driver.find_elements(By.CSS_SELECTOR, ".askAlert"):
                try:
                    text = (alert.text or "").lower()
                    if "drużyn" in text or "party" in text:
                        btn = alert.find_element(By.CSS_SELECTOR, ".alert-accept-hotkey")
                        if btn.is_displayed():
                            btn.click()
                            log_fn("✅ wait_group: zaakceptowałem zaproszenie do drużyny")
                            time.sleep(1)
                except Exception:
                    pass
        except Exception:
            pass

        size = _party_size(driver)
        if size >= min_size:
            log_fn(f"✅ wait_group: dołączyłem do grupy ({size} graczy)")
            return size

        if time.time() - last_log >= 30:
            elapsed = int(time.time() - t0)
            log_fn(f"⏳ wait_group: czekam… (drużyna: {size}/{min_size}, {elapsed}s)")
            last_log = time.time()

        time.sleep(3)

    size = _party_size(driver)
    log_fn(f"⏰ wait_group: timeout — drużyna: {size}")
    return size


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("min_size", "position", "timeout_s") if k in cfg}
