from __future__ import annotations

import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def end_battle(
    driver,
    exit_location: Optional[str] = None,
    timeout_s: float = 30.0,
    stop_event=None,
    log_fn=print,
) -> bool:
    """
    Czeka na 'Walka zakończona.' (battle-end-layer), następnie klika
    przycisk 'Opuść walkę' lub wysyła klawisz Z jako fallback.
    Opcjonalnie nawiguje do exit_location.
    """
    log_fn("🚪 end_battle: czekam na ekran końca walki…")

    # Czekaj na battle-end-layer
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            return False
        try:
            el = driver.find_element(By.CSS_SELECTOR, "div.battle-end-layer")
            if el.is_displayed():
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        log_fn("⚠️  end_battle: ekran końca walki nie pojawił się — próbuję mimo to")

    time.sleep(0.5)

    # Kliknij przycisk 'Opuść walkę'
    clicked = False
    try:
        btn = driver.find_element(
            By.CSS_SELECTOR, "div.button.green.close-battle-ground.small"
        )
        driver.execute_script("arguments[0].click();", btn)
        log_fn("🚪 end_battle: kliknąłem 'Opuść walkę'")
        clicked = True
    except Exception:
        pass

    if not clicked:
        try:
            ActionChains(driver).key_down("z").pause(0.15).key_up("z").perform()
            log_fn("🚪 end_battle: wysłałem klawisz Z")
            clicked = True
        except Exception as e:
            log_fn(f"⚠️  end_battle: nie udało się opuścić walki — {e}")
            return False

    time.sleep(2.0)

    if exit_location:
        log_fn(f"🗺️  end_battle: nawiguję do '{exit_location}'…")
        try:
            from move import travel_to
            travel_to(driver, exit_location, stop_event=stop_event)
            log_fn(f"✅ end_battle: dotarłem do '{exit_location}'")
        except Exception as e:
            log_fn(f"⚠️  end_battle: błąd nawigacji — {e}")

    return True


def load_from_json(cfg: dict) -> dict:
    result = {}
    for k in ("exit_location", "timeout_s"):
        if k in cfg:
            result[k] = cfg[k]
    return result
