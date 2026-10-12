from __future__ import annotations

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def watch_battle(
    driver,
    colossus_class: str = "mmp-collosus",
    attack_key: str = "q",
    timeout_s: float = 3600.0,
    stop_event=None,
    log_fn=print,
) -> str:
    """
    Monitoruje trwającą walkę.  Naciska attack_key co ~3s.
    Zwraca 'win' | 'loss' | 'timeout'.

    Koniec walki jest wykrywany przez pojawienie się:
        div.battle-end-layer  (Walka zakończona.)

    WIN  — przynajmniej jeden .warrior.grave-warrior-npc jest widoczny
           (kolosus / NPC zginął)
    LOSS — brak widocznego grave-warrior-npc (gracze zginęli)
    """
    from anti_afk import check_interrupts

    def _press_attack() -> None:
        try:
            ActionChains(driver).key_down(attack_key).pause(0.15).key_up(attack_key).perform()
        except Exception:
            pass

    def _battle_ended() -> bool:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "div.battle-end-layer")
            return el.is_displayed()
        except Exception:
            return False

    def _colossus_dead() -> bool:
        try:
            for g in driver.find_elements(
                By.CSS_SELECTOR, ".battle-window .warrior.grave-warrior-npc"
            ):
                if g.is_displayed():
                    return True
        except Exception:
            pass
        return False

    log_fn(f"⚔️  watch_battle: walczę (klawisz: {attack_key})…")
    t0       = time.time()
    last_log = 0.0

    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            log_fn("🛑 watch_battle: zatrzymano")
            return "loss"

        check_interrupts(driver, logger=log_fn)

        if _battle_ended():
            time.sleep(0.5)
            if _colossus_dead():
                log_fn("💀 watch_battle: kolosus martwy → WIN")
                return "win"
            else:
                log_fn("😵 watch_battle: brak grobu NPC → LOSS")
                return "loss"

        if time.time() - last_log >= 20:
            elapsed = int(time.time() - t0)
            log_fn(f"⚔️  watch_battle: walczę… ({elapsed}s)")
            last_log = time.time()

        _press_attack()
        time.sleep(3.0)

    log_fn("⏰ watch_battle: timeout")
    return "timeout"


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("colossus_class", "attack_key", "timeout_s") if k in cfg}
