"""
KOLOS mode: leader zbiórka + atak kolosusa, follower akceptuje zaproszenia.
"""
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


# ---- helpers ----

def _get_location_text(driver) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, "#map-name").text.strip()
    except Exception:
        return ""


def _party_size(driver) -> int:
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".party-window .amount")
        return int(el.text.strip().strip("()"))
    except Exception:
        return 0


def _click_minimap_pos(driver, top: float, left: float) -> bool:
    """
    Kliknij pozycję (top, left) na minimapie przez dispatchEvent.
    top/left to CSS-piksele w przestrzeni .mmpMap.

    Viewport-pozycja kliknięcia = pozycja bohatera w viewporcie + delta CSS
    (target_css - hero_css). Dispatchujemy mousedown+mouseup+click z clientX/Y,
    co jest równoważne realnemu kliknięciu myszy w grze.
    """
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        hero_rect = driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();"
            "return {left:r.left,top:r.top,width:r.width,height:r.height};",
            hero,
        )
        hero_style = hero.get_attribute("style") or ""
        lm = re.search(r'left:\s*([\d.]+)px', hero_style)
        tm = re.search(r'top:\s*([\d.]+)px',  hero_style)
        hero_css_left = float(lm.group(1)) if lm else 0.0
        hero_css_top  = float(tm.group(1)) if tm else 0.0

        hx = hero_rect["left"] + hero_rect["width"]  / 2
        hy = hero_rect["top"]  + hero_rect["height"] / 2

        # Viewport-pozycja docelowego kafelka
        tx = hx + (left - hero_css_left)
        ty = hy + (top  - hero_css_top)

        mmap = driver.find_element(By.CSS_SELECTOR, ".mmpMap")
        driver.execute_script("""
            var el = arguments[0];
            var cx = arguments[1];
            var cy = arguments[2];
            ['mousedown', 'mouseup', 'click'].forEach(function(evType) {
                el.dispatchEvent(new MouseEvent(evType, {
                    bubbles: true, cancelable: true, view: window,
                    clientX: cx, clientY: cy
                }));
            });
        """, mmap, tx, ty)
        return True
    except Exception as e:
        print(f"⚠️  kolos _click_minimap_pos: {e}")
        return False


def _hero_pos(driver):
    """Zwraca (top, left) bohatera z atrybutu style .mmp-hero lub (None, None)."""
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


def _wait_for_hero_at_pos(driver, top: float, left: float,
                           tolerance: float = 15.0, timeout: float = 30.0) -> bool:
    """Czekaj aż bohater dotrze do (top, left) ± tolerance pikseli."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        ht, hl = _hero_pos(driver)
        if ht is not None and abs(ht - top) <= tolerance and abs(hl - left) <= tolerance:
            return True
        time.sleep(1)
    return False


def _count_map_players(driver) -> int:
    count = 0
    for cls in (".mmpMapObject.mmp-clan", ".mmpMapObject.mmp-other", ".mmpMapObject.mmp-enemy"):
        try:
            count += len(driver.find_elements(By.CSS_SELECTOR, cls))
        except Exception:
            pass
    return count


def _count_mmp_others(driver) -> int:
    """Liczba .mmpMapObject.mmp-other na minimapie (= inni gracze w tej samej lokacji)."""
    try:
        return len(driver.find_elements(By.CSS_SELECTOR, ".mmpMapObject.mmp-other"))
    except Exception:
        return 0


def _colossus_visible(driver, colossus_class: str) -> bool:
    try:
        return len(driver.find_elements(By.CSS_SELECTOR, f".mmpMapObject.{colossus_class}")) > 0
    except Exception:
        return False


def _press_key(driver, key: str) -> None:
    try:
        ActionChains(driver).key_down(key).pause(0.15).key_up(key).perform()
    except Exception as e:
        print(f"⚠️  kolos _press_key({key}): {e}")


def _check_captcha(driver, log) -> bool:
    """Sprawdza captchę i stasis. Zwraca True jeśli wykonano akcję."""
    try:
        from anti_afk import check_interrupts
        return check_interrupts(driver, logger=log)
    except Exception:
        return False


def _colossus_dead_in_battle(driver) -> bool:
    """True jeśli kolos w oknie walki ma klasę die-warrior i widoczny grób."""
    try:
        el = driver.find_element(
            By.CSS_SELECTOR,
            ".one-warrior.wt-colossus.die-warrior",
        )
        grave = el.find_element(By.CSS_SELECTOR, ".warrior.grave-warrior-npc")
        return grave.is_displayed()
    except Exception:
        return False


def _click_leave_battle(driver, log) -> None:
    """Klika 'Opuść walkę' lub wysyła klawisz Z jako fallback."""
    try:
        btn = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'label') and contains(text(),'Opuść walkę')]"
            "/ancestor::div[contains(@class,'button')]",
        )
        driver.execute_script("arguments[0].click();", btn)
        log("🚪 Kolos: opuściłem walkę")
        return
    except Exception:
        pass
    try:
        ActionChains(driver).key_down("z").pause(0.15).key_up("z").perform()
        log("🚪 Kolos: opuściłem walkę [Z]")
    except Exception as e:
        log(f"⚠️  Kolos: nie udało się opuścić walki: {e}")


def _disband_party(driver, log) -> None:
    """Rozwiązuje drużynę (lider) lub opuszcza ją. Szuka widocznego przycisku .party__disband."""
    try:
        for btn in driver.find_elements(By.CSS_SELECTOR, ".party__disband"):
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                log("🚫 Kolos: rozwiązuję drużynę po przegranej")
                time.sleep(2)
                return
    except Exception as e:
        log(f"⚠️  Kolos: błąd rozwiązywania drużyny: {e}")


def _is_colossus_done_today(driver) -> bool:
    """True jeśli widoczny dialog blokady sali (kolos ukończony dziś)."""
    try:
        msg = driver.find_element(By.CSS_SELECTOR, ".npc-message")
        if not msg.is_displayed():
            return False
        text = msg.text or ""
        return "zasklepi" in text or "kolosalnych bestii" in text
    except Exception:
        return False


def _click_colossus_done_exit(driver, log) -> None:
    """Klika 'Odchodzę' w dialogu blokady sali (ukończono dziś)."""
    try:
        spans = driver.find_elements(By.CSS_SELECTOR, "li.dialogue-window-answer span.answer-text")
        for span in spans:
            if "Odchod" in (span.text or ""):
                driver.execute_script("arguments[0].click();", span)
                log("🚪 Kolos: kliknięto 'Odchodzę' w dialogu blokady")
                return
    except Exception:
        pass
    try:
        li = driver.find_element(By.CSS_SELECTOR, "li.dialogue-window-answer.answer.line_exit")
        driver.execute_script("arguments[0].click();", li)
        log("🚪 Kolos: zamknięto dialog blokady sali")
    except Exception as e:
        log(f"⚠️  Kolos: nie udało się zamknąć dialogu blokady: {e}")


def _go_to_exit(driver, exit_location: str, stop_event, log) -> None:
    """Nawiguje do exit_location po zakończeniu walki z kolosem."""
    if not exit_location:
        return
    try:
        from move import travel_to
        log(f"🗺️  Kolos: kieruję się do wyjścia: '{exit_location}'...")
        travel_to(driver, exit_location, stop_event=stop_event)
    except Exception as e:
        log(f"⚠️  Kolos: błąd nawigacji do exit_location: {e}")


def _go_to_map(driver, location: str, pos: dict, stop_event, log) -> bool:
    """
    1. travel_to(location) jeśli nie jesteśmy na miejscu.
    2. Aktywuj mapę, kliknij docelową pozycję, poczekaj aż bohater dotrze,
       zamknij mapę.
    3. Sprawdź ponownie lokalizację.
    """
    from move import travel_to
    from enable_map import enable_map

    cur = _get_location_text(driver)
    if cur != location:
        log(f"🗺️  Kolos: travel_to '{location}'...")
        ok = travel_to(driver, location, stop_event=stop_event,
                       interrupt_fn=_is_colossus_done_today)
        if not ok:
            if _is_colossus_done_today(driver):
                return False  # caller sprawdzi dialog i obsłuży pauzę
            log(f"❌ Kolos: nie udało się dotrzeć do '{location}'")
            return False
        log(f"✅ Kolos: dotarłem do '{location}'")

    if stop_event.is_set():
        return False

    if pos:
        target_top  = pos.get("top",  0)
        target_left = pos.get("left", 0)

        pos_tolerance = float(pos.get("tolerance", 25.0))

        # Sprawdź czy bohater już jest na miejscu
        ht, hl = _hero_pos(driver)
        if ht is not None and abs(ht - target_top) <= pos_tolerance and abs(hl - target_left) <= pos_tolerance:
            return True

        log(f"🦶 Kolos: pozycjonuję na ({target_top}, {target_left})...")
        try:
            enable_map(driver, enabled=True)
        except Exception:
            pass

        _click_minimap_pos(driver, target_top, target_left)

        reached = _wait_for_hero_at_pos(driver, target_top, target_left,
                                         tolerance=pos_tolerance, timeout=60.0)
        try:
            enable_map(driver, enabled=False)
        except Exception:
            pass

        if not reached:
            # Pozycja nieosiągnięta — sprawdź czy jesteśmy chociaż w prawidłowej lokalizacji
            cur = _get_location_text(driver)
            if not cur:
                # map-name chwilowo pusty — poczekaj chwilę i sprawdź ponownie
                time.sleep(2)
                cur = _get_location_text(driver)
            if cur == location:
                log(f"⚠️  Kolos: nie dotarłem na dokładną pozycję ({target_top}, {target_left}), jestem w '{location}' — kontynuuję")
            else:
                log(f"⚠️  Kolos: nie dotarłem na pozycję ({target_top}, {target_left}), lokalizacja: '{cur}'")
                return False

        # Upewnij się, że jesteśmy w prawidłowej lokalizacji
        # (map-name może być chwilowo pusty po przejściu — czekamy max 10s)
        else:
            cur = ""
            for _ in range(20):
                cur = _get_location_text(driver)
                if cur:
                    break
                time.sleep(0.5)
            if cur and cur != location:
                log(f"❌ Kolos: nieoczekiwana lokalizacja '{cur}' po pozycjonowaniu")
                return False

    return True


# ---- FOLLOWER ----

def run_kolos_follower(driver, cfg: dict, stop_event, log) -> None:
    """
    Follower loop:
      1. Nawiguj do gathering_location.
      2. Akceptuj zaproszenie do drużyny.
      3. Poczekaj aż drużyna ma >= follower_min_party graczy.
      4. Nawiguj do fight_location i atakuj kolosusa.
      5. Powtórz.
    """
    gathering_loc  = cfg.get("gathering_location", "")
    gathering_pos  = cfg.get("gathering_position", {})
    fight_loc      = cfg.get("fight_location", "")
    fight_pos      = cfg.get("fight_position", {})
    exit_location  = cfg.get("exit_location", "")
    colossus_cls   = cfg.get("colossus_class", "mmp-collosus")
    attack_key     = cfg.get("attack_key", "q")
    follower_min   = int(cfg.get("follower_min_party", 5))

    needs_reinvite = False  # po przegranej czekaj na świeże zaproszenie

    log(f"🔵 Kolos FOLLOWER: start | min drużyna: {follower_min}")

    while not stop_event.is_set():

        # --- faza 1: nawigacja do miejsca zbiórki ---
        if gathering_loc:
            while not stop_event.is_set():
                _check_captcha(driver, log)
                if _go_to_map(driver, gathering_loc, gathering_pos, stop_event, log):
                    break
                log("🔄 Kolos FOLLOWER: retry nawigacji za 5s...")
                time.sleep(5)
            if stop_event.is_set():
                break

        # --- faza 2: czekaj na dołączenie do drużyny ---
        # Po przegranej (needs_reinvite) ZAWSZE czekaj na świeże zaproszenie
        if not needs_reinvite and _party_size(driver) > 0:
            log("✅ Kolos FOLLOWER: już jestem w drużynie")
        else:
            if needs_reinvite:
                log("🔄 Kolos FOLLOWER: czekam na nowe zaproszenie po przegranej...")
                needs_reinvite = False
            else:
                log("🔵 Kolos FOLLOWER: czekam na dołączenie do drużyny")
            while not stop_event.is_set():
                if _check_captcha(driver, log) and gathering_pos:
                    _click_minimap_pos(driver,
                                       gathering_pos.get("top", 0),
                                       gathering_pos.get("left", 0))

                if _party_size(driver) > 0:
                    log("✅ Kolos FOLLOWER: dołączyłem do drużyny")
                    break

                try:
                    for alert in driver.find_elements(By.CSS_SELECTOR, ".askAlert"):
                        try:
                            if "drużyn" in alert.text.lower() or "party" in alert.text.lower():
                                btn = alert.find_element(By.CSS_SELECTOR, ".alert-accept-hotkey")
                                if btn.is_displayed():
                                    btn.click()
                                    log("✅ Kolos FOLLOWER: dołączyłem do drużyny (alert)")
                                    time.sleep(1)
                        except Exception:
                            pass
                except Exception as e:
                    log(f"⚠️  Kolos FOLLOWER: {e}")

                time.sleep(3)

            if stop_event.is_set():
                break

        # --- faza 3: czekaj na min. liczbę graczy w drużynie ---
        log(f"⏳ Kolos FOLLOWER: czekam na {follower_min} graczy w drużynie...")
        while not stop_event.is_set():
            if _check_captcha(driver, log) and gathering_pos:
                _click_minimap_pos(driver,
                                   gathering_pos.get("top", 0),
                                   gathering_pos.get("left", 0))
            size = _party_size(driver)
            if size >= follower_min:
                log(f"✅ Kolos FOLLOWER: drużyna {size}/{follower_min} — ruszam do sali")
                break
            time.sleep(3)
        if stop_event.is_set():
            break

        # --- faza 4: guard — sprawdź grupę przed wejściem do sali ---
        if _party_size(driver) < 2:
            log("⚠️  Kolos FOLLOWER: utracono grupę przed wejściem do sali — wracam na zbiórkę")
            needs_reinvite = True
            continue

        # --- faza 4: nawigacja do sali walki ---
        if fight_loc:
            while not stop_event.is_set():
                _check_captcha(driver, log)
                if _is_colossus_done_today(driver):
                    _click_colossus_done_exit(driver, log)
                    _go_to_exit(driver, exit_location, stop_event, log)
                    log("⏸️  Kolos FOLLOWER: sala zablokowana — pauza (ukończono dziś)")
                    return "pause"
                if _go_to_map(driver, fight_loc, fight_pos, stop_event, log):
                    break
                if _is_colossus_done_today(driver):
                    _click_colossus_done_exit(driver, log)
                    _go_to_exit(driver, exit_location, stop_event, log)
                    log("⏸️  Kolos FOLLOWER: sala zablokowana — pauza (ukończono dziś)")
                    return "pause"
                log("🔄 Kolos FOLLOWER: retry nawigacji do sali za 5s...")
                time.sleep(5)
            if stop_event.is_set():
                break

        # --- faza 4b: guard — sprawdź grupę po przybyciu do sali ---
        if _party_size(driver) < 2:
            log("⚠️  Kolos FOLLOWER: brak grupy w sali — wracam do gathering")
            if gathering_loc:
                _go_to_map(driver, gathering_loc, gathering_pos, stop_event, log)
            needs_reinvite = True
            continue

        # --- faza 5: atakuj kolosusa ---
        log("🗡️  Kolos FOLLOWER: atakuję!")
        while not stop_event.is_set():
            _check_captcha(driver, log)
            if _colossus_dead_in_battle(driver):
                log("💀 Kolos FOLLOWER: kolosus zabity — opuszczam walkę")
                time.sleep(1.0)
                _click_leave_battle(driver, log)
                _go_to_exit(driver, exit_location, stop_event, log)
                log("⏸️  Kolos FOLLOWER: pauza po zabiciu kolosusa")
                return "killed"
            if not _colossus_visible(driver, colossus_cls):
                log("😵 Kolos FOLLOWER: walka przegrana — czekam na nowe zaproszenie")
                needs_reinvite = True
                break
            _press_key(driver, attack_key)
            time.sleep(3)

    log("🛑 Kolos FOLLOWER: stop")
    return None


# ---- LEADER helpers ----

def _ensure_who_is_here_open(driver) -> None:
    """Otwiera okno 'Gracze na mapie' jeśli nie jest widoczne (klik kompasu)."""
    try:
        win = driver.find_element(By.CSS_SELECTOR, ".whoishere-window")
        if win.is_displayed():
            return
    except Exception:
        pass
    try:
        btn = driver.find_element(By.CSS_SELECTOR, ".widget-button.widget-compass")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
    except Exception:
        pass


def _get_players_on_map(driver) -> set:
    """Zwraca zbiór nicków z okna 'Gracze na mapie'. Otwiera okno jeśli zamknięte."""
    _ensure_who_is_here_open(driver)
    names = set()
    try:
        els = driver.find_elements(
            By.CSS_SELECTOR,
            ".who-is-here .player-list .one-other .name .inner",
        )
        for el in els:
            n = (el.text or "").strip()
            if n:
                names.add(n)
    except Exception:
        pass
    return names


def _get_party_members(driver) -> list:
    """Zwraca listę {'name', 'kick_btn', 'is_leader'} dla każdego gracza w grupie."""
    members = []
    try:
        items = driver.find_elements(
            By.CSS_SELECTOR,
            ".party .party__list .party-member.tw-list-item",
        )
        for item in items:
            try:
                name = item.find_element(
                    By.CSS_SELECTOR, ".nickname .nickname-text"
                ).text.strip()
                kick_btn = None
                try:
                    kick_btn = item.find_element(
                        By.CSS_SELECTOR, ".kick-out-party.kick-out"
                    )
                except Exception:
                    pass
                is_leader = False
                try:
                    crown = item.find_element(By.CSS_SELECTOR, ".party__crown")
                    is_leader = crown.is_displayed()
                except Exception:
                    pass
                members.append({"name": name, "kick_btn": kick_btn, "is_leader": is_leader})
            except Exception:
                pass
    except Exception:
        pass
    return members


def _party_members_on_map_count(driver) -> int:
    """Ilu nie-liderów z grupy widocznych jest w oknie 'Gracze na mapie'."""
    on_map = _get_players_on_map(driver)
    return sum(
        1 for m in _get_party_members(driver)
        if not m["is_leader"] and m["name"] in on_map
    )


def _kick_present_party_members(driver, log) -> int:
    """Wyrzuca z grupy wszystkich (nie-liderów) widocznych w 'Gracze na mapie'. Re-fetchuje po każdym kicku."""
    kicked = 0
    while True:
        on_map   = _get_players_on_map(driver)
        members  = _get_party_members(driver)
        did_kick = False
        for m in members:
            if m["is_leader"]:
                continue
            name     = m["name"]
            kick_btn = m["kick_btn"]
            if not name or not kick_btn or name not in on_map:
                continue
            try:
                if kick_btn.is_displayed():
                    log(f"🚫 Kolos: wyrzucam '{name}' (nie weszli do sali)")
                    driver.execute_script("arguments[0].click();", kick_btn)
                    kicked += 1
                    did_kick = True
                    time.sleep(1.0)
                    break  # re-fetch po kicku — DOM grupy się odświeża
            except Exception:
                pass
        if not did_kick:
            break
    return kicked


def _kick_absent_party_members(driver, log) -> int:
    """Wyrzuca z grupy nie-liderów niewidocznych w 'Gracze na mapie'. Re-fetchuje po każdym kicku."""
    kicked = 0
    while True:
        on_map   = _get_players_on_map(driver)
        members  = _get_party_members(driver)
        did_kick = False
        for m in members:
            if m["is_leader"]:
                continue
            name     = m["name"]
            kick_btn = m["kick_btn"]
            if not name or not kick_btn or name in on_map:
                continue
            try:
                if kick_btn.is_displayed():
                    log(f"🚫 Kolos: wyrzucam '{name}' (nieobecny w sali)")
                    driver.execute_script("arguments[0].click();", kick_btn)
                    kicked += 1
                    did_kick = True
                    time.sleep(1.0)
                    break  # re-fetch po kicku
            except Exception:
                pass
        if not did_kick:
            break
    return kicked


def _approach_and_attack_colossus(driver, colossus_cls: str, attack_key: str,
                                   log, max_time_s: float = 60.0) -> bool:
    """
    Kliknij element kolosa na minimapie, poczekaj aż bohater podejdzie w zasięg,
    następnie naciśnij attack_key. Analogicznie do kill_object dla mobów.
    """
    from kill_object import _center_from_element, _in_attack_range

    sel = f".mmpMapObject.{colossus_cls}"

    def _find_colossus():
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        return els[0] if els else None

    def _click_col():
        el = _find_colossus()
        if el is None:
            return False
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False

    if not _click_col():
        log(f"⚠️  Kolos: brak {colossus_cls} na minimapie")
        return False

    log(f"🎯 Kolos: kliknięto {colossus_cls}, podchodzę...")
    t0 = time.time()
    last_pos  = None
    last_move = time.time()

    while time.time() - t0 < max_time_s:
        try:
            hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
            col  = _find_colossus()
            if col is None:
                log(f"ℹ️  Kolos: {colossus_cls} zniknął — zapewne walka już trwa")
                return True
            hx, hy, tile = _center_from_element(hero)
            cx, cy, _    = _center_from_element(col)
            if None in (hx, hy, cx, cy, tile):
                time.sleep(0.15)
                continue
            if _in_attack_range((hx, hy), (cx, cy), tile):
                log(f"⚔️  Kolos: w zasięgu → {attack_key.upper()}")
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(attack_key)
                except Exception:
                    pass
                return True
            # re-click gdy zablokowany
            now = time.time()
            if last_pos is None:
                last_pos  = (hx, hy)
                last_move = now
            else:
                moved = abs(hx - last_pos[0]) > 0.8 or abs(hy - last_pos[1]) > 0.8
                if moved:
                    last_pos  = (hx, hy)
                    last_move = now
                elif now - last_move >= 1.5:
                    _click_col()
                    last_move = now
                    log(f"🔁 Kolos: re-click {colossus_cls}")
        except Exception:
            pass
        time.sleep(0.15)

    log(f"⏱️  Kolos: timeout podejścia do {colossus_cls}")
    return False


def _click_auto_fight_party(driver, log) -> bool:
    """Kliknij 'Szybka walka', a następnie 'Drużyna' w dialogu wyboru."""
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "div.button.green.auto-fight-btn")
        driver.execute_script("arguments[0].click();", btn)
        log("⚔️  Kolos: kliknięto Szybka walka")
    except Exception as e:
        log(f"⚠️  Kolos: brak Szybka walka: {e}")
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
                    log("⚔️  Kolos: Szybka walka → Drużyna")
                    return True
        except Exception:
            pass
        time.sleep(0.2)

    log("⚠️  Kolos: dialog 'Drużyna' nie pojawił się — kontynuuję")
    return False


# ---- LEADER ----

def run_kolos_leader(driver, cfg: dict, stop_event, log) -> "str | None":
    """
    Leader loop:
      1. Nawigacja do gathering_location, zbieranie drużyny.
      2. Po pełnej drużynie — 10s oczekiwanie, potem czeka aż żaden członek
         grupy nie jest widoczny w 'Gracze na mapie' (wszyscy weszli do sali).
      3. Wejście do fight_location, weryfikacja składu, wyrzucenie nieobecnych.
      4. Szybka walka → Drużyna, atak.
      5. Kolos zabity → pauza; przegrana → restart cyklu.
    """
    gathering_loc = cfg.get("gathering_location", "")
    gathering_pos = cfg.get("gathering_position", {})
    fight_loc     = cfg.get("fight_location", "")
    fight_pos     = cfg.get("fight_position", {})
    colossus_cls  = cfg.get("colossus_class", "mmp-collosus")
    party_size    = int(cfg.get("party_size", 10))
    gather_key    = cfg.get("gather_key", "g")
    attack_key    = cfg.get("attack_key", "q")
    gather_ivl    = int(cfg.get("gather_interval_s", 10))
    exit_location = cfg.get("exit_location", "")

    needs_regather = False  # po przegranej rozwiąż drużynę i zbieraj od nowa

    log(f"🟡 Kolos LEADER: start | cel drużyny: {party_size}")

    while not stop_event.is_set():

        # --- faza 1: nawigacja do miejsca zbiórki ---
        if not _go_to_map(driver, gathering_loc, gathering_pos, stop_event, log):
            time.sleep(5)
            continue

        if stop_event.is_set():
            break

        # --- faza 2: zbiórka drużyny ---
        if needs_regather:
            _disband_party(driver, log)
            needs_regather = False
        log("🔔 Kolos: zbiórka — zapraszam do drużyny")
        gather_deadline = time.time() + 300
        last_gather = 0.0

        while time.time() < gather_deadline and not stop_event.is_set():
            if _check_captcha(driver, log) and gathering_pos:
                _click_minimap_pos(driver,
                                   gathering_pos.get("top", 0),
                                   gathering_pos.get("left", 0))
            size    = _party_size(driver)
            players = _count_map_players(driver)
            log(f"  drużyna: {size}/{party_size}  graczy na mapie: {players}")

            if size >= party_size:
                log("✅ Kolos: drużyna pełna!")
                break

            if time.time() - last_gather >= gather_ivl:
                _press_key(driver, gather_key)
                last_gather = time.time()

            time.sleep(5)

        if stop_event.is_set():
            break

        if _party_size(driver) < party_size:
            log(f"⏰ Kolos LEADER: timeout zbiórki ({_party_size(driver)}/{party_size}) — zaczynam od nowa")
            continue

        # --- faza 3: 10s okno na wejście, potem kick i weryfikacja ---
        log("⏳ Kolos LEADER: drużyna pełna — czekam 10s na wejście graczy...")
        for _ in range(10):
            if stop_event.is_set():
                break
            time.sleep(1)
        if stop_event.is_set():
            break

        stuck = _party_members_on_map_count(driver)
        if stuck > 0:
            log(f"⚡ Kolos LEADER: {stuck} graczy nie weszło po 10s — wyrzucam wszystkich")
            _kick_present_party_members(driver, log)
            time.sleep(1)

        size_now  = _party_size(driver)
        remaining = _party_members_on_map_count(driver)
        if size_now < party_size or remaining > 0:
            log(f"⚠️  Kolos LEADER: warunki nie spełnione ({size_now}/{party_size}, {remaining} w prędsionku) — restart za 5s")
            time.sleep(5)
            continue

        log("✅ Kolos LEADER: wszyscy w sali — wchodzę!")

        # --- faza 3b: guard — sprawdź grupę przed wejściem do sali ---
        if _party_size(driver) < 2:
            log("⚠️  Kolos LEADER: utracono grupę przed wejściem — zbieram od nowa")
            needs_regather = True
            continue

        # --- faza 4: nawigacja do sali walki ---
        if _is_colossus_done_today(driver):
            _click_colossus_done_exit(driver, log)
            _go_to_exit(driver, exit_location, stop_event, log)
            log("⏸️  Kolos LEADER: sala zablokowana — pauza (ukończono dziś)")
            return "pause"
        if not _go_to_map(driver, fight_loc, fight_pos, stop_event, log):
            if _is_colossus_done_today(driver):
                _click_colossus_done_exit(driver, log)
                _go_to_exit(driver, exit_location, stop_event, log)
                log("⏸️  Kolos LEADER: sala zablokowana — pauza (ukończono dziś)")
                return "pause"
            time.sleep(5)
            continue

        if stop_event.is_set():
            break

        # --- faza 5: czekaj aż wszyscy są w sali (minimap: mmp-other = party_size-1) ---
        if _party_size(driver) < 2:
            log("⚠️  Kolos LEADER: brak grupy w sali — wracam do gathering i zbieram od nowa")
            needs_regather = True
            _go_to_map(driver, gathering_loc, gathering_pos, stop_event, log)
            continue

        expected_others = party_size - 1  # np. 9 gdy party_size=10
        log(f"⏳ Kolos LEADER: czekam na {expected_others} graczy na minimapie sali...")
        from enable_map import enable_map
        t_wait = time.time()
        while time.time() - t_wait < 120.0 and not stop_event.is_set():
            try:
                enable_map(driver, enabled=True)
            except Exception:
                pass
            others = _count_mmp_others(driver)
            log(f"  minimap: {others}/{expected_others} innych graczy w sali")
            if others >= expected_others:
                break
            _check_captcha(driver, log)
            time.sleep(3)

        try:
            enable_map(driver, enabled=False)
        except Exception:
            pass

        if stop_event.is_set():
            break

        others = _count_mmp_others(driver)
        if others < expected_others:
            log(f"⚠️  Kolos LEADER: tylko {others}/{expected_others} graczy w sali po 120s — restart")
            needs_regather = True
            continue

        log(f"✅ Kolos LEADER: {others}/{expected_others} graczy w sali — atak!")

        # --- faza 6: uruchom Szybką walkę dla drużyny ---
        _click_auto_fight_party(driver, log)

        # --- faza 7: atak ---
        log("🗡️  Kolos LEADER: atakuję!")
        while not stop_event.is_set():
            _check_captcha(driver, log)
            if _colossus_dead_in_battle(driver):
                log("💀 Kolos LEADER: kolosus zabity — opuszczam walkę")
                time.sleep(1.0)
                _click_leave_battle(driver, log)
                _go_to_exit(driver, exit_location, stop_event, log)
                log("⏸️  Kolos LEADER: pauza po zabiciu kolosusa")
                return "killed"
            if _colossus_visible(driver, colossus_cls):
                _approach_and_attack_colossus(driver, colossus_cls, attack_key, log)
            else:
                log("😵 Kolos LEADER: walka przegrana — rozwiązuję drużynę i zbieram od nowa")
                needs_regather = True
                break
            time.sleep(1)

    log("🛑 Kolos LEADER: stop")
    return None
