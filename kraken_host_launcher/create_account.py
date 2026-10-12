import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ── Słowniki do generowania nicków ────────────────────────────────────────────

ADJECTIVES = [
    "gotowany", "smażony", "pieczony", "wędzony", "grillowany", "duszony", "blanszowany",
    "karmelizowany", "marynowany", "solony", "kwaszony", "fermentowany", "suszony", "liofilizowany",
    "kandyzowany", "glazurowany", "panierowany", "frytowany", "parowany", "prażony",
    "podsmażony", "zrumieniony", "podpieczony", "podsuszony", "konfitowany", "peklowany",
    "kiszony", "moczony", "deglasowany", "flambowany", "zredukowany", "przetarty",
    "sklarowany", "emulgowany", "spieniony", "ucierany", "ubity", "zagęszczony",
    "roztopiony", "kruszony", "siekany", "blendowany", "tarty", "podwędzony",
    "pieklowany", "obtoczony", "schłodzony", "podgrzewany", "sous-vide",
]

NOUNS = [
    "łosoś", "dorsz", "tuńczyk", "śledź", "karp", "pstrąg", "sum", "sandacz", "okoń", "węgorz",
    "mintaj", "halibut", "morszczuk", "flądra", "szprot", "makrela", "amur", "leszcz",
    "kurczak", "indyk", "królik", "gołąb", "bażant", "kaczor", "gęsior",
    "szponder", "boczek", "mostek", "udziec", "antrykot", "polędwik", "schab", "karczek",
    "ogórek", "pomidor", "por", "seler", "burak", "szparag", "groszek", "bób", "jarmuż",
    "borowik", "podgrzybek", "kurk", "maślak", "rydz", "smardz", "grzyb", "pieczark",
]


_ORDINALS = [
    "pierwszy", "drugi", "trzeci", "czwarty", "piąty",
    "szósty", "siódmy", "ósmy", "dziewiąty", "dziesiąty",
]


def _ordinal(n: int) -> str:
    return _ORDINALS[(n - 1) % len(_ORDINALS)]


def generate_login() -> str:
    length = random.randint(8, 12)
    pool = string.ascii_lowercase + string.digits
    return random.choice(string.ascii_lowercase) + "".join(random.choices(pool, k=length - 1))


def generate_password() -> str:
    pool = string.ascii_letters + string.digits + "!@#$%"
    return "".join(random.choices(pool, k=12))


def generate_nick() -> str:
    for _ in range(20):
        adj  = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        num  = _ordinal(random.randint(1, 10))
        nick = f"{adj.capitalize()} {noun.capitalize()} {num.capitalize()}"
        if len(nick) <= 21:
            return nick
    return (adj.capitalize() + " " + noun.capitalize())[:21]


# ── Pomocnicze funkcje Selenium ───────────────────────────────────────────────

def _find(driver, by, sel):
    try:
        els = driver.find_elements(by, sel)
        return els[0] if els else None
    except Exception:
        return None


def _wait_for(driver, by, sel, timeout=30.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        el = _find(driver, by, sel)
        if el:
            return el
        time.sleep(0.3)
    return None


def _send(driver, by, sel, text: str) -> None:
    el = _find(driver, by, sel)
    if el:
        try:
            el.clear()
            el.send_keys(text)
        except Exception:
            pass
        time.sleep(0.2)


def _get_location(driver) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, "span.location").text.strip()
    except Exception:
        return ""


def _get_hero_rect(driver) -> dict | None:
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        return driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();"
            "return {left:r.left,top:r.top,width:r.width,height:r.height};",
            hero,
        )
    except Exception:
        return None


def _click_mmap_element(driver, el) -> bool:
    """Kliknij element minimapy w jego centrum (via mmpMap offset)."""
    try:
        rect = driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();"
            "return {left:r.left,top:r.top,width:r.width,height:r.height};",
            el,
        )
        tx = rect["left"] + rect["width"]  / 2
        ty = rect["top"]  + rect["height"] / 2
        mmap = driver.find_element(By.CSS_SELECTOR, ".mmpMap")
        mr = driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();return {left:r.left,top:r.top};",
            mmap,
        )
        ActionChains(driver).move_to_element_with_offset(
            mmap, int(tx - mr["left"]), int(ty - mr["top"])
        ).click().perform()
        return True
    except Exception as e:
        print(f"⚠️  _click_mmap_element: {e}")
        return False


def _find_nearest(driver, css_class: str):
    """
    Zwraca element .mmpMapObject.<css_class> najbliższy mmp-hero.
    Nie używa tip-id — działa niezależnie od rotacyjnych ID.
    """
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        hr = driver.execute_script(
            "var r=arguments[0].getBoundingClientRect();"
            "return {left:r.left,top:r.top,width:r.width,height:r.height};",
            hero,
        )
        hcx = hr["left"] + hr["width"]  / 2
        hcy = hr["top"]  + hr["height"] / 2

        els = driver.find_elements(By.CSS_SELECTOR, f".mmpMapObject.{css_class}")
        best, best_dist = None, float("inf")
        for el in els:
            try:
                r = driver.execute_script(
                    "var r=arguments[0].getBoundingClientRect();"
                    "return {left:r.left,top:r.top,width:r.width,height:r.height};", el)
                cx = r["left"] + r["width"]  / 2
                cy = r["top"]  + r["height"] / 2
                d  = ((cx - hcx) ** 2 + (cy - hcy) ** 2) ** 0.5
                if d < best_dist:
                    best, best_dist = el, d
            except Exception:
                continue
        return best
    except Exception:
        return None


def _wait_for_mmap_hero(driver, timeout: float = 30) -> bool:
    """Czeka aż mmp-hero pojawi się na minimapie (mapa w pełni załadowana)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if driver.find_elements(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero"):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _hero_moved(driver, prev_rect: dict, tolerance: float = 5) -> bool:
    """Zwraca True gdy hero przesunął się względem prev_rect."""
    cur = _get_hero_rect(driver)
    if not cur or not prev_rect:
        return False
    return (abs(cur["left"] - prev_rect["left"]) > tolerance or
            abs(cur["top"]  - prev_rect["top"])  > tolerance)


def _click_gw_loop(driver, target_substr: str,
                   interval: float = 3.0, timeout: float = 60.0) -> bool:
    """
    Klikaj najbliższy mmp-gw co interval sekund aż lokacja zawiera target_substr.
    Nie używa tip-id.
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        if target_substr in _get_location(driver):
            return True
        gw = _find_nearest(driver, "mmp-gw")
        if gw:
            _click_mmap_element(driver, gw)
        time.sleep(interval)
    return target_substr in _get_location(driver)


# ── Etapy procesu ─────────────────────────────────────────────────────────────

def _human_type(driver, by, sel, text: str) -> None:
    """Wpisuje tekst znak po znaku z losowymi opóźnieniami."""
    el = _find(driver, by, sel)
    if not el:
        return
    try:
        el.clear()
        time.sleep(random.uniform(0.3, 0.6))
        for ch in text:
            el.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.18))
    except Exception:
        pass


def step_register(driver, logger, login: str, password: str) -> None:
    """Wypełnia i wysyła formularz rejestracji na margonem.pl/intro."""
    logger("📋 Czekam na formularz rejestracji...")
    if not _wait_for(driver, By.ID, "popup-create-account-login", timeout=45):
        raise RuntimeError("Brak formularza rejestracji (timeout 45s)")

    time.sleep(random.uniform(1.2, 2.5))
    _human_type(driver, By.ID, "popup-create-account-login", login)
    time.sleep(random.uniform(0.8, 1.6))
    _human_type(driver, By.ID, "popup-create-account-password", password)
    time.sleep(random.uniform(0.5, 1.0))
    _human_type(driver, By.ID, "popup-create-account-password2", password)
    time.sleep(random.uniform(0.6, 1.2))

    chk = _find(driver, By.ID, "popup-create-account-checkbox")
    if chk and not chk.is_selected():
        driver.execute_script("arguments[0].click();", chk)
    time.sleep(random.uniform(1.0, 2.0))

    btn = _find(driver, By.CSS_SELECTOR, "button.button-register")
    if btn:
        driver.execute_script("arguments[0].click();", btn)
    logger(f"✅ Rejestracja wysłana: {login}")


def step_create_character(driver, logger, nick: str, server: str = "gordion") -> None:
    """Wypełnia formularz tworzenia postaci."""
    logger("🧙 Czekam na formularz postaci...")
    if not _wait_for(driver, By.ID, "add-character-form", timeout=45):
        raise RuntimeError("Brak formularza tworzenia postaci (timeout 45s)")

    time.sleep(random.uniform(1.0, 2.0))
    radio = _find(driver, By.ID, f"world-select-input-{server.lower()}")
    if radio:
        driver.execute_script("arguments[0].click();", radio)
    time.sleep(random.uniform(0.8, 1.4))

    _human_type(driver, By.ID, "add-character-nick", nick)
    time.sleep(random.uniform(1.0, 2.0))

    btn = _find(driver, By.CSS_SELECTOR, "button.js-create-character-button")
    if btn:
        driver.execute_script("arguments[0].click();", btn)
    logger(f"✅ Postać wysłana: nick={nick}, serwer={server}")


def step_wait_canvas(driver, logger, timeout: float = 120) -> None:
    logger("⏳ Czekam na GAME_CANVAS...")
    t0 = time.time()
    while time.time() - t0 < timeout:
        if driver.find_elements(By.CSS_SELECTOR, "canvas#GAME_CANVAS"):
            logger("✅ Gra załadowana!")
            return
        time.sleep(1)
    raise RuntimeError("Timeout: GAME_CANVAS nie pojawiło się!")


def step_tutorial(driver, logger, stop_flag) -> None:
    """Tutorial: ruch inicjalizacyjny → NPC → broń → moby → GW → mapy."""

    # 1. Czekaj na minimapę
    logger("⏳ Czekam na minimapę...")
    if not _wait_for_mmap_hero(driver, timeout=30):
        logger("⚠️  mmp-hero nie pojawił się (timeout 30s)")

    # 2. Ruch inicjalizacyjny strzałkami
    logger("🕹️  Ruch inicjalizacyjny (strzałki)...")
    time.sleep(1.5)
    try:
        ActionChains(driver).key_down(Keys.ARROW_RIGHT).pause(0.6).key_up(Keys.ARROW_RIGHT).perform()
        time.sleep(0.4)
        ActionChains(driver).key_down(Keys.ARROW_LEFT).pause(0.6).key_up(Keys.ARROW_LEFT).perform()
        time.sleep(0.5)
    except Exception as e:
        logger(f"⚠️  Ruch inicjalizacyjny: {e}")

    # 3. Kliknij najbliższy NPC
    logger("🗺️  Klikam NPC...")
    prev_rect = _get_hero_rect(driver)
    npc = _find_nearest(driver, "mmp-npc")
    if npc:
        _click_mmap_element(driver, npc)
    else:
        logger("⚠️  Brak NPC na minimapie")

    # Czekaj aż hero ruszy (max 8s)
    t0 = time.time()
    while time.time() - t0 < 8 and not stop_flag():
        if _hero_moved(driver, prev_rect):
            logger("✅ Hero ruszył do NPC")
            break
        time.sleep(0.5)

    # Czekaj aż hero się zatrzyma przy NPC (max 15s stabilności)
    time.sleep(2)
    t0 = time.time()
    stable_start = time.time()
    last_rect = _get_hero_rect(driver)
    while time.time() - t0 < 15 and not stop_flag():
        if _hero_moved(driver, last_rect, tolerance=3):
            last_rect = _get_hero_rect(driver)
            stable_start = time.time()
        elif time.time() - stable_start > 1.5:
            logger("✅ Hero przy NPC (zatrzymał się)")
            break
        time.sleep(0.4)

    # 4. Sekwencja dialogowa klawiszem N
    logger("💬 Sekwencja dialogowa (N × 10)...")
    for _ in range(10):
        if stop_flag():
            return
        try:
            ActionChains(driver).key_down("n").key_up("n").perform()
        except Exception:
            pass
        time.sleep(0.7)

    # 5. Ekwipuj przedmiot z inwentarza (PPM → Ekwipuj)
    logger("🎒 Szukam przedmiotu w inwentarzu...")
    equipped = False
    t0 = time.time()
    while time.time() - t0 < 20 and not stop_flag():
        item = _find(driver, By.CSS_SELECTOR, ".inventory-item")
        if item:
            try:
                ActionChains(driver).context_click(item).perform()
                time.sleep(0.5)
                equip_btn = _find(driver, By.XPATH,
                                  "//div[@class='menu-item' and text()='Ekwipuj']")
                if equip_btn:
                    equip_btn.click()
                    logger("⚔️  Przedmiot ekwipowany!")
                    equipped = True
                else:
                    ActionChains(driver).key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()
            except Exception as e:
                logger(f"⚠️  Ekwipowanie: {e}")
            if equipped:
                break
        time.sleep(1)

    if not equipped:
        logger("⚠️  Nie znaleziono przedmiotu do ekwipowania")

    # 6. Zabijaj moby, aż znikną — wtedy kliknij GW
    logger("⚔️  Zabijam moby (mapa startowa)...")
    t0 = time.time()
    while time.time() - t0 < 240 and not stop_flag():
        mob = _find_nearest(driver, "mmp-mob")
        if mob:
            _click_mmap_element(driver, mob)
            time.sleep(2.5)
        else:
            gw = _find_nearest(driver, "mmp-gw")
            if gw:
                logger("🚪 Brak mobów — klikam GW...")
                _click_mmap_element(driver, gw)
                time.sleep(3)
                break
            time.sleep(1)

    if stop_flag():
        return

    # 7. Czekaj na mapę podziemia p.1 sala 2
    logger("⏳ Czekam na Podziemia p.1 sala 2...")
    t0 = time.time()
    while time.time() - t0 < 60 and not stop_flag():
        loc = _get_location(driver)
        if "podziemia p.1" in loc and "sala 2" in loc:
            logger(f"✅ {loc}")
            break
        time.sleep(1)

    if stop_flag():
        return

    # 8. GW → podziemia p.0 (co 3s)
    logger("🚪 Klikam GW co 3s → podziemia p.0...")
    _click_gw_loop(driver, "podziemia p.0", interval=3.0, timeout=60)
    logger(f"  Lokacja: {_get_location(driver)}")

    if stop_flag():
        return

    # 9. GW → Ruiny (co 3s)
    logger("🚪 Klikam GW co 3s → Ruiny...")
    _click_gw_loop(driver, "Ruiny", interval=3.0, timeout=60)
    logger(f"  Lokacja: {_get_location(driver)}")

    if stop_flag():
        return

    # 10. Klawisz 1 co 3s → Ruiny Szabrowników
    logger("⌨️  Klikam 1 co 3s → Ruiny Szabrowników...")
    t0 = time.time()
    while time.time() - t0 < 120 and not stop_flag():
        if "Ruiny Szabrowników" in _get_location(driver):
            logger("🎉 Dotarłem do Ruin Szabrowników!")
            break
        try:
            ActionChains(driver).key_down("1").key_up("1").perform()
        except Exception:
            pass
        time.sleep(3)


# ── Punkt wejściowy ───────────────────────────────────────────────────────────

def run_full(driver, logger, login: str, password: str,
             server: str = "gordion", stop_flag=None, nick: str = None) -> str:
    """
    Pełny proces: rejestracja → postać → tutorial.
    Zwraca użyty nick lub "" jeśli przerwano.
    stop_flag: callable() → bool
    nick: jeśli podany, użyty zamiast losowego
    """
    if stop_flag is None:
        stop_flag = lambda: False

    nick = nick if nick else generate_nick()
    logger(f"🔑 Login: {login}  |  Hasło: {password}  |  Nick: {nick}")

    step_register(driver, logger, login, password)
    if stop_flag():
        return ""

    step_create_character(driver, logger, nick, server=server)
    if stop_flag():
        return ""

    step_wait_canvas(driver, logger)
    if stop_flag():
        return ""

    step_tutorial(driver, logger, stop_flag)
    logger("✅ Konto gotowe!")
    return nick
