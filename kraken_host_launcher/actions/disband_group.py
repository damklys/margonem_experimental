from __future__ import annotations

import time

from selenium.webdriver.common.by import By


def disband_group(driver, log_fn=print) -> bool:
    """Rozwiązuje drużynę (lider) lub opuszcza ją (follower)."""
    try:
        for btn in driver.find_elements(By.CSS_SELECTOR, ".party__disband"):
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                log_fn("🚫 disband_group: rozwiązuję drużynę")
                time.sleep(2)
                return True
    except Exception:
        pass
    log_fn("⚠️  disband_group: nie znaleziono przycisku rozwiązania drużyny")
    return False


def load_from_json(cfg: dict) -> dict:
    return {}
