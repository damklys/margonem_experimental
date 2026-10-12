from __future__ import annotations

import time

from selenium.webdriver.common.by import By


def use_repeat_entry(driver, timeout_s: float = 10.0, log_fn=print) -> bool:
    """
    Czeka na opcję dialogową 'Korzystam z przedmiotu pozwalającego na ponowne
    wykonanie Próby Sił.' i klika ją.
    Zwraca True jeśli kliknięto, False jeśli nie pojawiła się w czasie timeout_s.
    """
    log_fn("🔁 use_repeat_entry: czekam na opcję dialogową Próby Sił…")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            answers = driver.find_elements(
                By.CSS_SELECTOR, "li.dialogue-window-answer.answer"
            )
            for ans in answers:
                text = ans.text or ""
                if "Korzystam z przedmiotu" in text and "Próby Sił" in text:
                    driver.execute_script("arguments[0].click();", ans)
                    log_fn("✅ use_repeat_entry: kliknięto opcję ponownego wejścia")
                    return True
        except Exception:
            pass
        time.sleep(0.5)

    log_fn("ℹ️  use_repeat_entry: opcja dialogowa nie pojawiła się")
    return False


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("timeout_s",) if k in cfg}
