from selenium.webdriver.common.by import By
import time


def _battle_visible(driver) -> bool:
    """Sprawdza czy trwa walka przez widoczność .battle-area."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".battle-area")
        if el.is_displayed():
            return True
    except Exception:
        pass
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".skill-usable-slots")
        if el.is_displayed():
            return True
    except Exception:
        pass
    try:
        el = driver.find_element(By.CSS_SELECTOR, "div.battle-window")
        return "display: block" in (el.get_attribute("style") or "")
    except Exception:
        return False


def _battle_ended(driver) -> bool:
    try:
        el = driver.find_element(By.CSS_SELECTOR, "div.battle-end-layer")
        return el.is_displayed()
    except Exception:
        return False


def _hp_zero(driver) -> bool:
    try:
        el = driver.find_element(By.CSS_SELECTOR,
                                  "div.hp-indicator .hpp span.value")
        val = el.text.strip().replace("%", "").replace(",", ".")
        return float(val) <= 0
    except Exception:
        return False


def _is_unconscious(driver) -> bool:
    try:
        el = driver.find_element(By.CSS_SELECTOR,
                                  "div.inner-text[data-trans='unconcious_info_txt']")
        return el.is_displayed()
    except Exception:
        return False


def _click_leave(driver) -> bool:
    try:
        btn = driver.find_element(By.CSS_SELECTOR,
                                   "div.button.green.close-battle-ground")
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        return False


def _wait_for_consciousness(driver, logger, stop_event,
                             appear_timeout: float = 30.0,
                             disappear_timeout: float = 2400.0):
    """Czeka aż komunikat o nieprzytomności pojawi się i zniknie."""
    logger("😵 Czekam na odzyskanie przytomności...")
    t0 = time.time()

    while time.time() - t0 < appear_timeout:
        if stop_event.is_set():
            return
        if _is_unconscious(driver):
            break
        time.sleep(0.5)

    t0 = time.time()
    last_log = t0
    while time.time() - t0 < disappear_timeout:
        if stop_event.is_set():
            return
        if not _is_unconscious(driver):
            logger("✅ Odzyskałem przytomność, restartuję trasę...")
            return
        if time.time() - last_log >= 60.0:
            elapsed_min = int((time.time() - t0) / 60)
            logger(f"😵 Nadal nieprzytomny... ({elapsed_min} min)")
            last_log = time.time()
        time.sleep(1.0)

    logger("⚠️  Timeout oczekiwania na przytomność (40 min)")


def _get_timer_text(driver) -> str:
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".c-timer__text")
        return (el.text or "").strip()
    except Exception:
        return ""


def _click_skill_slot(driver, skill_num: int, logger=None) -> bool:
    """
    Klika kratkę skilla według numeru 1-8.
    Sloty 1-4 = lewa strona (slot 0-3), sloty 5-8 = prawa strona (slot 4-7).
    """
    slot_idx = skill_num - 1
    try:
        skill_el = driver.find_element(
            By.CSS_SELECTOR,
            f'.skill-usable-slot[slot="{slot_idx}"] .battle-skill'
        )
        driver.execute_script("arguments[0].click();", skill_el)
        if logger:
            logger(f"  🎯 skill {skill_num} (slot {slot_idx}) – kliknięto")
        return True
    except Exception as e:
        if logger:
            logger(f"  ⚠️  skill {skill_num} (slot {slot_idx}) – błąd: {e}")
        return False


def _is_forward_disabled(driver) -> bool:
    """
    True jeśli przycisk ruchu (slot 1, battle-skill-id=-2) nie ma klasy 'e' (disabled).
    """
    try:
        skill = driver.find_element(
            By.CSS_SELECTOR,
            '.skill-usable-slot[slot="1"] .battle-skill'
        )
        classes = (skill.get_attribute("class") or "").split()
        return "e" not in classes
    except Exception:
        return True


def _click_auto_fight(driver) -> bool:
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "div.button.green.auto-fight-btn")
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        return False


def _handle_battle_with_actions(driver, logger, stop_event, actions) -> str:
    """
    Battle z sekwencją akcji.
    Timer "1s" → kliknij następny skill z actions[] (cyklicznie).
    Timer "0s" → sprawdź slot ruchu (skill 2); jeśli disabled → skill 1, else → skill 2.
    Zwraca wynik bez przywracania mapy — robi to wywołujący _handle_active_battle.
    """
    action_idx = 0
    last_timer = ""
    n = len(actions)

    while True:
        if stop_event.is_set():
            return "stopped"

        try:
            btn = driver.find_element(By.CSS_SELECTOR, "div.button.green.close-battle-ground")
            if btn.is_displayed():
                logger("💀 Zginąłem! Opuszczam walkę...")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                _wait_for_consciousness(driver, logger, stop_event)
                return "dead"
        except Exception:
            pass

        if _battle_ended(driver):
            if _hp_zero(driver):
                logger("💀 Zginąłem!")
                _click_leave(driver)
                time.sleep(1.5)
                _wait_for_consciousness(driver, logger, stop_event)
                return "dead"
            logger("✅ Walka zakończona – zwycięstwo!")
            return "victory"

        if not _battle_visible(driver):
            logger("✅ Walka zakończona!")
            return "victory"

        timer = _get_timer_text(driver)
        if timer != last_timer:
            logger(f"  ⏱ timer: {timer}")
            if timer in ("1s", "1") and actions:
                slot_in_seq = action_idx % n
                skill_num = int(actions[slot_in_seq])
                logger(f"  🎯 akcja [{slot_in_seq + 1}/{n}]: skill {skill_num}")
                _click_skill_slot(driver, skill_num, logger)
                action_idx += 1
            elif timer in ("0s", "0"):
                fwd_dis = _is_forward_disabled(driver)
                move = 1 if fwd_dis else 2
                logger(f"  ⬅➡ ruch: skill {move} ({'stój' if fwd_dis else 'naprzód'})")
                _click_skill_slot(driver, move, logger)
            last_timer = timer

        time.sleep(0.1)


def _map_was_enabled(driver) -> bool:
    """Odczytuje aktualny stan minimapy (True = widoczna)."""
    try:
        wrapper = driver.find_element(By.CSS_SELECTOR, ".mmpWrapper")
        return "display: block" in (wrapper.get_attribute("style") or "")
    except Exception:
        return False


def _restore_map(driver, was_enabled: bool) -> None:
    try:
        from enable_map import enable_map
        enable_map(driver, enabled=was_enabled)
    except Exception:
        pass


def _handle_active_battle(driver, logger, stop_event, actions=None) -> str:
    """Obsługuje trwającą walkę. Zwraca 'victory', 'dead' lub 'stopped'."""
    map_before = _map_was_enabled(driver)
    try:
        from enable_map import enable_map
        enable_map(driver, enabled=False)
    except Exception:
        pass

    if actions:
        logger("⚔️  Walka! Minimap wyłączona, tryb akcji...")
        result = _handle_battle_with_actions(driver, logger, stop_event, actions)
        if result != "stopped":
            _restore_map(driver, map_before)
        return result

    if _click_auto_fight(driver):
        logger("⚔️  Walka! Minimap wyłączona, włączono szybką walkę, czekam na zakończenie...")
    else:
        logger("⚔️  Walka! Minimap wyłączona, czekam na zakończenie...")

    while True:
        if stop_event.is_set():
            return "stopped"

        try:
            btn = driver.find_element(By.CSS_SELECTOR,
                                       "div.button.green.close-battle-ground")
            if btn.is_displayed():
                logger("💀 Zginąłem! Opuszczam walkę...")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                _wait_for_consciousness(driver, logger, stop_event)
                _restore_map(driver, map_before)
                return "dead"
        except Exception:
            pass

        if _battle_ended(driver):
            if _hp_zero(driver):
                logger("💀 Zginąłem! Opuszczam walkę...")
                _click_leave(driver)
                time.sleep(1.5)
                _wait_for_consciousness(driver, logger, stop_event)
                _restore_map(driver, map_before)
                return "dead"
            else:
                logger("✅ Walka zakończona – zwycięstwo!")
                _restore_map(driver, map_before)
                return "victory"

        if not _battle_visible(driver):
            logger("✅ Walka zakończona!")
            _restore_map(driver, map_before)
            return "victory"

        time.sleep(0.5)


def check_and_handle_battle(driver, logger, stop_event, actions=None) -> str:
    """
    Wywołuj na początku każdej iteracji głównej pętli.

    Zwraca:
      'ok'      – brak walki, kontynuuj normalnie
      'victory' – walka zakończona wygraną, kontynuuj
      'dead'    – zginąłeś, zresetuj trasę i kontynuuj
      'stopped' – stop_event ustawiony
    """
    if not _battle_visible(driver):
        driver._battle_first_seen = None
        return "ok"

    now = time.time()
    first_seen = getattr(driver, "_battle_first_seen", None)
    if first_seen is None:
        driver._battle_first_seen = now
        return "ok"

    if now - first_seen < 10.0:
        return "ok"

    driver._battle_first_seen = None
    return _handle_active_battle(driver, logger, stop_event, actions=actions)
