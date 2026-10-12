from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def quick_fight(driver, log_fn=print) -> bool:
    """
    Naciska F (Szybka walka), następnie klika 'Drużyna' w dialogu wyboru trybu.
    """
    log_fn("⚔️  quick_fight: naciskam F (Szybka walka)…")
    try:
        ActionChains(driver).key_down("f").pause(0.15).key_up("f").perform()
    except Exception as e:
        log_fn(f"⚠️  quick_fight: błąd naciśnięcia F — {e}")
        return False

    t0 = time.time()
    while time.time() - t0 < 5.0:
        try:
            for b in driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'button') and contains(@class,'small')]"
                "[.//div[contains(@class,'label') and text()='Drużyna']]",
            ):
                if b.is_displayed():
                    driver.execute_script("arguments[0].click();", b)
                    log_fn("✅ quick_fight: Szybka walka → Drużyna")
                    return True
        except Exception:
            pass
        time.sleep(0.2)

    log_fn("⚠️  quick_fight: dialog 'Drużyna' nie pojawił się — kontynuuję")
    return False


def load_from_json(cfg: dict) -> dict:
    return {}
