from __future__ import annotations

from selenium.webdriver.common.by import By


def check_role(driver, role: str = None, log_fn=print) -> str:
    """
    Zwraca 'leader' lub 'follower'.
    Jeśli role podano explicite — zwraca go bez detekcji z DOM.
    """
    if role is not None:
        log_fn(f"👑 check_role: rola z konfiguracji = {role}")
        return role

    try:
        items = driver.find_elements(
            By.CSS_SELECTOR,
            ".party .party__list .party-member.tw-list-item",
        )
        for item in items:
            try:
                crown = item.find_element(By.CSS_SELECTOR, ".party__crown")
                if not crown.is_displayed():
                    continue
                has_kick = False
                try:
                    btn = item.find_element(By.CSS_SELECTOR, ".kick-out-party.kick-out")
                    has_kick = btn.is_displayed()
                except Exception:
                    pass
                detected = "follower" if has_kick else "leader"
                log_fn(f"👑 check_role: wykryto z DOM = {detected}")
                return detected
            except Exception:
                pass
    except Exception:
        pass

    log_fn("👑 check_role: brak grupy / nie wykryto — domyślnie follower")
    return "follower"


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("role",) if k in cfg}
