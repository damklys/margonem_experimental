"""
Mine (Kopalnia) mode: weekly dungeon run with action-based battle system.
"""
import re
import time
import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


# ---- location / hero helpers ----

def _get_location_text(driver) -> str:
    for sel in ("span.location", "#map-name"):
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            t = (el.text or "").strip()
            if t:
                return t
        except Exception:
            pass
    return ""


def _hero_pos(driver):
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        style = hero.get_attribute("style") or ""
        tm = re.search(r'top:\s*([\d.]+)px', style)
        lm = re.search(r'left:\s*([\d.]+)px', style)
        if tm and lm:
            return float(tm.group(1)), float(lm.group(1))
    except Exception:
        pass
    return None, None


def _click_minimap_pos(driver, top: float, left: float) -> bool:
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        hero_rect = driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();"
            "return {left:r.left,top:r.top,width:r.width,height:r.height};",
            hero,
        )
        hero_style = hero.get_attribute("style") or ""
        lm = re.search(r'left:\s*([\d.]+)px', hero_style)
        tm = re.search(r'top:\s*([\d.]+)px', hero_style)
        hero_css_left = float(lm.group(1)) if lm else 0.0
        hero_css_top  = float(tm.group(1)) if tm else 0.0

        hx = hero_rect["left"] + hero_rect["width"]  / 2
        hy = hero_rect["top"]  + hero_rect["height"] / 2
        tx = hx + (left - hero_css_left)
        ty = hy + (top  - hero_css_top)

        mmap = driver.find_element(By.CSS_SELECTOR, ".mmpMap")
        driver.execute_script("""
            var el = arguments[0]; var cx = arguments[1]; var cy = arguments[2];
            ['mousedown', 'mouseup', 'click'].forEach(function(evType) {
                el.dispatchEvent(new MouseEvent(evType, {
                    bubbles: true, cancelable: true, view: window,
                    clientX: cx, clientY: cy
                }));
            });
        """, mmap, tx, ty)
        return True
    except Exception as e:
        print(f"⚠️  mine _click_minimap_pos: {e}")
        return False


def _wait_for_hero_at_pos(driver, top: float, left: float,
                           tolerance: float = 22.0, timeout: float = 35.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        ht, hl = _hero_pos(driver)
        if ht is not None and abs(ht - top) <= tolerance and abs(hl - left) <= tolerance:
            return True
        time.sleep(0.5)
    return False


def _wait_for_location(driver, location: str, timeout: float = 30.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _get_location_text(driver) == location:
            return True
        time.sleep(1)
    return False


def _press_key(driver, key: str) -> None:
    try:
        ActionChains(driver).send_keys(str(key)).perform()
    except Exception as e:
        print(f"⚠️  mine _press_key({key}): {e}")


def _navigate_to_pos(driver, location: str, top, left, stop_event, log,
                      tolerance: float = 22.0) -> bool:
    from move import travel_to
    from enable_map import enable_map

    cur = _get_location_text(driver)
    if cur != location:
        log(f"🗺️  Mine: jadę do '{location}'...")
        if not travel_to(driver, location, stop_event=stop_event):
            log(f"❌ Mine: nie udało się dotrzeć do '{location}'")
            return False

    if stop_event.is_set():
        return False

    if top is None or left is None:
        return True

    ht, hl = _hero_pos(driver)
    if ht is not None and abs(ht - top) <= tolerance and abs(hl - left) <= tolerance:
        return True

    try:
        enable_map(driver, enabled=True)
    except Exception:
        pass

    _click_minimap_pos(driver, top, left)
    reached = _wait_for_hero_at_pos(driver, top, left, tolerance=tolerance)

    try:
        enable_map(driver, enabled=False)
    except Exception:
        pass

    if not reached:
        log(f"⚠️  Mine: nie dotarłem na pozycję ({top:.0f},{left:.0f})")
        return False
    return True


# ---- dialogue system ----

_DIALOG_CSS = (
    ".dialog-window, .npcDialog, .dialog, .ask-wrapper, "
    ".dialogWindow, .npc-dialog"
)
_OPTION_CSS = ".option, .dialog-option, li.option, .dialog-btn, a.option"


def _dialogue_visible(driver) -> bool:
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, _DIALOG_CSS):
            if el.is_displayed():
                return True
    except Exception:
        pass
    return False


def _wait_for_dialogue(driver, timeout: float = 10.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if _dialogue_visible(driver):
            return True
        time.sleep(0.3)
    return False


def _click_dialogue_option(driver, index: int, log=None) -> bool:
    """Click 1-based dialogue option."""
    try:
        for container in driver.find_elements(By.CSS_SELECTOR, _DIALOG_CSS):
            if not container.is_displayed():
                continue
            opts = container.find_elements(By.CSS_SELECTOR, _OPTION_CSS)
            if not opts:
                opts = [el for el in container.find_elements(By.CSS_SELECTOR, "li, a")
                        if el.is_displayed() and el.text.strip()]
            if opts and index <= len(opts):
                driver.execute_script("arguments[0].click();", opts[index - 1])
                return True
    except Exception as e:
        if log:
            log(f"⚠️  Mine: dialogue click {index}: {e}")
    # Fallback: press number key
    try:
        ActionChains(driver).send_keys(str(index)).perform()
        return True
    except Exception:
        pass
    return False


def _execute_dialogue_sequence(driver, sequence: list, log=None) -> bool:
    for idx in sequence:
        if not _wait_for_dialogue(driver, timeout=10.0):
            if log:
                log(f"⚠️  Mine: brak dialogu przed opcją {idx}")
            return False
        time.sleep(0.4)
        if not _click_dialogue_option(driver, idx, log=log):
            if log:
                log(f"⚠️  Mine: nie kliknięto opcji {idx}")
            return False
        time.sleep(0.8)
    return True


# ---- battle action system ----

def _get_timer_text(driver) -> str:
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".c-timer__text")
        return (el.text or "").strip()
    except Exception:
        return ""


def _click_skill_slot(driver, skill_num: int, log=None) -> bool:
    """Klika kratkę skilla (1-8). Slot = skill_num - 1."""
    slot_idx = skill_num - 1
    try:
        skill_el = driver.find_element(
            By.CSS_SELECTOR,
            f'.skill-usable-slot[slot="{slot_idx}"] .battle-skill'
        )
        driver.execute_script("arguments[0].click();", skill_el)
        if log:
            log(f"  🎯 skill {skill_num} (slot {slot_idx}) – kliknięto")
        return True
    except Exception as e:
        if log:
            log(f"  ⚠️  skill {skill_num} (slot {slot_idx}) – błąd: {e}")
        return False


def _is_forward_disabled(driver) -> bool:
    """True jeśli slot ruchu (slot 1, battle-skill-id=-2) nie ma klasy 'e'."""
    try:
        skill = driver.find_element(
            By.CSS_SELECTOR,
            '.skill-usable-slot[slot="1"] .battle-skill'
        )
        classes = (skill.get_attribute("class") or "").split()
        return "e" not in classes
    except Exception:
        return True


def _battle_visible(driver) -> bool:
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
        el = driver.find_element(By.CSS_SELECTOR, "div.hp-indicator .hpp span.value")
        val = el.text.strip().replace("%", "").replace(",", ".")
        return float(val) <= 0
    except Exception:
        return False


def _click_leave_battle(driver) -> bool:
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "div.button.green.close-battle-ground")
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        return False


def _is_unconscious(driver) -> bool:
    try:
        el = driver.find_element(By.CSS_SELECTOR,
                                  "div.inner-text[data-trans='unconcious_info_txt']")
        return el.is_displayed()
    except Exception:
        return False


def _wait_for_revival(driver, log, stop_event, max_wait: float = 2400.0) -> bool:
    log("😵 Mine: czekam na odrodzenie...")
    t0 = time.time()
    last_log = t0
    for _ in range(30):
        if stop_event.is_set():
            return False
        if _is_unconscious(driver):
            break
        time.sleep(0.5)
    while time.time() - t0 < max_wait:
        if stop_event.is_set():
            return False
        if not _is_unconscious(driver):
            log("✅ Mine: odrodziłem się")
            return True
        if time.time() - last_log >= 60:
            log(f"😵 Mine: nadal nieprzytomny ({int((time.time()-t0)//60)} min)...")
            last_log = time.time()
        time.sleep(2)
    log("⚠️  Mine: timeout odrodzenia")
    return False


def handle_battle_with_actions(driver, actions: list, log, stop_event) -> str:
    """
    Battle z sekwencją akcji.
    Timer "1s" → kliknij następny skill z actions[] (cyklicznie).
    Timer "0s" → sprawdź slot ruchu (skill 2): disabled→skill 1, enabled→skill 2.
    Returns: 'victory', 'dead', 'stopped'
    """
    from enable_map import enable_map
    try:
        enable_map(driver, enabled=False)
    except Exception:
        pass

    action_idx = 0
    last_timer = ""
    n = len(actions)
    log(f"⚔️  Mine: walka (akcje: {actions})!")

    while True:
        if stop_event.is_set():
            try:
                enable_map(driver, enabled=True)
            except Exception:
                pass
            return "stopped"

        try:
            leave_btn = driver.find_element(By.CSS_SELECTOR,
                                             "div.button.green.close-battle-ground")
            if leave_btn.is_displayed():
                log("💀 Mine: zginąłem! Opuszczam walkę...")
                driver.execute_script("arguments[0].click();", leave_btn)
                time.sleep(1.5)
                _wait_for_revival(driver, log, stop_event)
                return "dead"
        except Exception:
            pass

        if _battle_ended(driver):
            if _hp_zero(driver):
                log("💀 Mine: zginąłem!")
                _click_leave_battle(driver)
                time.sleep(1.5)
                _wait_for_revival(driver, log, stop_event)
                return "dead"
            log("✅ Mine: walka zakończona – zwycięstwo!")
            try:
                enable_map(driver, enabled=True)
            except Exception:
                pass
            return "victory"

        if not _battle_visible(driver):
            log("✅ Mine: walka zakończona!")
            try:
                enable_map(driver, enabled=True)
            except Exception:
                pass
            return "victory"

        timer = _get_timer_text(driver)
        if timer != last_timer:
            log(f"  ⏱ timer: {timer}")
            if timer in ("1s", "1") and actions:
                slot_in_seq = action_idx % n
                skill_num = int(actions[slot_in_seq])
                log(f"  🎯 akcja [{slot_in_seq + 1}/{n}]: skill {skill_num}")
                _click_skill_slot(driver, skill_num, log)
                action_idx += 1
            elif timer in ("0s", "0"):
                fwd_dis = _is_forward_disabled(driver)
                move = 1 if fwd_dis else 2
                log(f"  ⬅➡ ruch: skill {move} ({'stój' if fwd_dis else 'naprzód'})")
                _click_skill_slot(driver, move, log)
            last_timer = timer

        time.sleep(0.1)


# ---- elite detection ----

def _find_nearby_elite(driver, hero_top: float, hero_left: float,
                        frame_size: float, radius_tiles: int = 7):
    """Find nearest mmp-elite within radius from hero position."""
    radius_px = radius_tiles * frame_size
    try:
        best = None
        best_dist = float("inf")
        for el in driver.find_elements(By.CSS_SELECTOR, ".mmpMapObject.mmp-elite"):
            style = el.get_attribute("style") or ""
            tm = re.search(r'top:\s*([\d.]+)px', style)
            lm = re.search(r'left:\s*([\d.]+)px', style)
            if not (tm and lm):
                continue
            et = float(tm.group(1))
            el_left = float(lm.group(1))
            dist = ((et - hero_top)**2 + (el_left - hero_left)**2) ** 0.5
            if dist <= radius_px and dist < best_dist:
                best = {"top": et, "left": el_left}
                best_dist = dist
        return best
    except Exception:
        return None


def _check_captcha(driver, log):
    try:
        from anti_afk import check_interrupts
        check_interrupts(driver, logger=log)
    except Exception:
        pass


# ---- timing helpers ----

_DAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
         "friday": 4, "saturday": 5, "sunday": 6}


def _parse_hm(s: str):
    h, m = map(int, s.split(":"))
    return h, m


def _is_right_day(day_str: str) -> bool:
    if not day_str:
        return True
    target = _DAYS.get(day_str.lower(), -1)
    return target == -1 or datetime.datetime.now().weekday() == target


def _time_passed(h: int, m: int) -> bool:
    now = datetime.datetime.now()
    return now.hour > h or (now.hour == h and now.minute >= m)


def _wait_until_time(h: int, m: int, day_str: str, driver, log, stop_event) -> bool:
    while not stop_event.is_set():
        if _is_right_day(day_str) and _time_passed(h, m):
            return True
        now = datetime.datetime.now()
        target_mins  = h * 60 + m
        current_mins = now.hour * 60 + now.minute
        diff = target_mins - current_mins
        if diff <= 0:
            diff += 24 * 60
        day_name = day_str or "każdy dzień"
        log(f"⏰ Mine: czekam do {h:02d}:{m:02d} ({day_name}), ~{diff} min")
        _check_captcha(driver, log)
        time.sleep(min(60, max(10, diff * 30)))
    return False


# ---- main mine loop ----

def run_mine(driver, cfg: dict, stop_event, log,
             auto_enter: bool = True,
             mine_position_idx: int = 0,
             enter_signal_event=None) -> None:
    """
    Main mine loop.

    Phases:
    1. Wait until enter_waiting time (and correct day), travel to NPC, execute
       travel_dialogue_sequence → arrive at waiting_location.
    2. Wait until enter_time, interact with enter_object via enter_dialogue_sequence
       → arrive in fight_location.
    3. Navigate to selected position, battle loop with action-based combat.
    4. On death: wait for revival, return to waiting_location, re-enter.

    auto_enter=False: skip timing waits, use enter_signal_event (threading.Event)
    for phase-2 entry signal.
    """
    npc_location   = cfg.get("npc_location", "")
    npc_pos        = cfg.get("npc_position", {})
    travel_seq     = cfg.get("travel_dialogue_sequence", [])
    waiting_loc    = cfg.get("waiting_location", "")
    enter_obj_pos  = cfg.get("enter_object_position", {})
    enter_seq      = cfg.get("enter_dialogue_sequence", [])
    enter_day      = cfg.get("enter_day", "")
    enter_time_str = cfg.get("enter_time", "20:00")
    enter_wait_str = cfg.get("enter_waiting", "19:45")
    fight_loc      = cfg.get("fight_location", "")
    positions      = cfg.get("positions", [])
    actions        = cfg.get("actions") or cfg.get("action") or []
    attack_key     = cfg.get("attack_key", "q")
    frame_size     = float(cfg.get("frame_size", 11.0))

    pos = positions[mine_position_idx] if (positions and mine_position_idx < len(positions)) else {}
    pos_top   = pos.get("top")
    pos_left  = pos.get("left")
    pos_label = pos.get("label", f"pozycja {mine_position_idx}")

    log(f"⛏️  Mine START | {pos_label} | auto={auto_enter}")

    eh_wait,  em_wait  = _parse_hm(enter_wait_str)
    eh_enter, em_enter = _parse_hm(enter_time_str)

    while not stop_event.is_set():
        cur_loc = _get_location_text(driver)

        # ── FAZA 1: poza předsionkiem i kopalnią → jedź do NPC ──────────────
        if cur_loc not in (waiting_loc, fight_loc):
            if not auto_enter:
                log("⏳ Mine (manual): czekam aż znajdę się w předsionku kopalni...")
                while not stop_event.is_set():
                    _check_captcha(driver, log)
                    cur_loc = _get_location_text(driver)
                    if cur_loc in (waiting_loc, fight_loc):
                        break
                    time.sleep(5)
                if stop_event.is_set():
                    break
                continue

            log(f"⏰ Mine: czekam do {enter_wait_str} ({enter_day or 'codziennie'})...")
            if not _wait_until_time(eh_wait, em_wait, enter_day, driver, log, stop_event):
                break

            log(f"🧭 Mine: jadę do NPC w '{npc_location}'...")
            if not _navigate_to_pos(driver, npc_location,
                                     npc_pos.get("top"), npc_pos.get("left"),
                                     stop_event, log):
                log("⚠️  Mine: retry za 15s...")
                time.sleep(15)
                continue

            if stop_event.is_set():
                break

            log(f"🗣️  Mine: rozmowa z NPC (sekwencja {travel_seq})...")
            if not _execute_dialogue_sequence(driver, travel_seq, log=log):
                log("⚠️  Mine: błąd dialogu z NPC, retry za 15s...")
                time.sleep(15)
                continue

            if not _wait_for_location(driver, waiting_loc, timeout=30.0):
                cur = _get_location_text(driver)
                log(f"⚠️  Mine: oczekiwano '{waiting_loc}', jestem na '{cur}', retry...")
                time.sleep(10)
                continue

            log(f"✅ Mine: jestem w '{waiting_loc}'")
            cur_loc = waiting_loc

        # ── FAZA 2: předsionek → czekaj i wejdź do kopalni ─────────────────
        if cur_loc == waiting_loc:
            if not auto_enter:
                log("⏳ Mine (manual): czekam na sygnał wejścia do kopalni...")
                if enter_signal_event is not None:
                    enter_signal_event.clear()
                    while not stop_event.is_set():
                        _check_captcha(driver, log)
                        if enter_signal_event.wait(timeout=5):
                            enter_signal_event.clear()
                            break
                        if _get_location_text(driver) == fight_loc:
                            break
                else:
                    while not stop_event.is_set():
                        _check_captcha(driver, log)
                        if _get_location_text(driver) == fight_loc:
                            break
                        time.sleep(3)
                if stop_event.is_set():
                    break
            else:
                log(f"⏰ Mine: czekam do {enter_time_str}...")
                if not _wait_until_time(eh_enter, em_enter, enter_day,
                                        driver, log, stop_event):
                    break

                entered = False
                while not stop_event.is_set() and not entered:
                    log(f"🚪 Mine: próbuję wejść przez '{cfg.get('enter_object','obiekt')}'...")
                    if not _navigate_to_pos(driver, waiting_loc,
                                             enter_obj_pos.get("top"),
                                             enter_obj_pos.get("left"),
                                             stop_event, log):
                        log("⚠️  Mine: retry za 5s...")
                        time.sleep(5)
                        continue

                    if stop_event.is_set():
                        break

                    if not _execute_dialogue_sequence(driver, enter_seq, log=log):
                        log("⚠️  Mine: błąd dialogu wejścia, retry za 5s...")
                        time.sleep(5)
                        continue

                    if _wait_for_location(driver, fight_loc, timeout=15.0):
                        log(f"✅ Mine: wszedłem do '{fight_loc}'")
                        entered = True
                    else:
                        cur = _get_location_text(driver)
                        log(f"⚠️  Mine: oczekiwano '{fight_loc}', jestem na '{cur}', retry 5s...")
                        time.sleep(5)

                if stop_event.is_set():
                    break

            cur_loc = _get_location_text(driver)

        # ── FAZA 3: kopalnia → nawiguj na pozycję i walcz ───────────────────
        if cur_loc != fight_loc:
            continue

        if pos_top is not None:
            log(f"🦶 Mine: idę na pozycję '{pos_label}' ({pos_top:.0f},{pos_left:.0f})...")
            if not _navigate_to_pos(driver, fight_loc, pos_top, pos_left, stop_event, log):
                log("⚠️  Mine: nie dotarłem na pozycję, retry za 5s...")
                time.sleep(5)
                continue

        if stop_event.is_set():
            break

        log("⚔️  Mine: jestem na pozycji, czekam na walkę...")
        died_in_mine = False

        # ── FAZA 4: pętla walki ──────────────────────────────────────────────
        while not stop_event.is_set():
            _check_captcha(driver, log)

            if _get_location_text(driver) != fight_loc:
                log("⚠️  Mine: opuściłem kopalnię – restartuję...")
                break

            # Elite w promieniu 7 kafelków
            if pos_top is not None:
                ht, hl = _hero_pos(driver)
                if ht is not None:
                    elite = _find_nearby_elite(driver, ht, hl, frame_size, 7)
                    if elite:
                        log(f"⚡ Mine: elite ({elite['top']:.0f},{elite['left']:.0f}) – atakuję!")
                        _navigate_to_pos(driver, fight_loc,
                                          elite["top"], elite["left"],
                                          stop_event, log)
                        _press_key(driver, attack_key)
                        t0_e = time.time()
                        while not _battle_visible(driver) and time.time() - t0_e < 12:
                            time.sleep(0.5)
                        if _battle_visible(driver):
                            result = handle_battle_with_actions(driver, actions, log, stop_event)
                            if result == "stopped":
                                break
                            if result == "dead":
                                died_in_mine = True
                                break
                        log(f"🔙 Mine: wracam na pozycję '{pos_label}'...")
                        _navigate_to_pos(driver, fight_loc, pos_top, pos_left,
                                          stop_event, log)
                        continue

            # Aktywna walka (z opóźnieniem 10s jak w check_and_handle_battle)
            now = time.time()
            first_seen = getattr(driver, "_mine_battle_first_seen", None)

            if _battle_visible(driver):
                if first_seen is None:
                    driver._mine_battle_first_seen = now
                elif now - first_seen >= 10.0:
                    driver._mine_battle_first_seen = None
                    result = handle_battle_with_actions(driver, actions, log, stop_event)
                    if result == "stopped":
                        break
                    if result == "dead":
                        died_in_mine = True
                        break
                    if pos_top is not None:
                        log(f"🔙 Mine: wracam na pozycję '{pos_label}'...")
                        _navigate_to_pos(driver, fight_loc, pos_top, pos_left,
                                          stop_event, log)
            else:
                driver._mine_battle_first_seen = None

            time.sleep(0.5)

        if stop_event.is_set():
            break

        # Odrodzenie — wróć do předsionka
        if died_in_mine:
            _wait_for_revival(driver, log, stop_event)
            if stop_event.is_set():
                break
            log(f"🔄 Mine: po śmierci wracam do '{waiting_loc}'...")
            for _ in range(3):
                if stop_event.is_set():
                    break
                if _navigate_to_pos(driver, waiting_loc, None, None, stop_event, log):
                    log(f"✅ Mine: jestem w '{waiting_loc}'")
                    break
                time.sleep(5)

    log("🛑 Mine: stop")


# ---- Elite-only mode (testowanie elite) ----

def run_mine_elite_only(driver, cfg: dict, stop_event, log,
                         fight_location: str = "",
                         position_idx: int = 0) -> None:
    """Elite patrol: stój na pozycji, wykrywaj i zabijaj elity w promieniu."""
    fight_loc  = fight_location or cfg.get("fight_location", "")
    positions  = cfg.get("positions", [])
    actions    = cfg.get("actions") or cfg.get("action") or []
    attack_key = cfg.get("attack_key", "q")
    frame_size = float(cfg.get("frame_size", 11.0))

    pos = positions[position_idx] if (positions and position_idx < len(positions)) else {}
    pos_top  = pos.get("top")
    pos_left = pos.get("left")

    log(f"⚡ Elite-only START | fight_loc={fight_loc}")

    while not stop_event.is_set():
        _check_captcha(driver, log)

        if fight_loc and _get_location_text(driver) != fight_loc:
            from move import travel_to
            travel_to(driver, fight_loc, stop_event=stop_event)
            continue

        if pos_top is not None:
            ht, hl = _hero_pos(driver)
            if ht is not None:
                elite = _find_nearby_elite(driver, ht, hl, frame_size, 7)
                if elite:
                    _navigate_to_pos(driver, fight_loc,
                                      elite["top"], elite["left"],
                                      stop_event, log)
                    _press_key(driver, attack_key)
                    t0_e = time.time()
                    while not _battle_visible(driver) and time.time() - t0_e < 12:
                        time.sleep(0.5)
                    if _battle_visible(driver):
                        result = handle_battle_with_actions(driver, actions, log, stop_event)
                        if result == "stopped":
                            break
                        if result == "dead":
                            _wait_for_revival(driver, log, stop_event)
                    if pos_top is not None and not stop_event.is_set():
                        _navigate_to_pos(driver, fight_loc, pos_top, pos_left,
                                          stop_event, log)
                    continue

        time.sleep(1)

    log("🛑 Elite-only: stop")
