from selenium.webdriver.common.by import By
import json
import time
import re

def _get_xy(style):
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        return float(parts["left"]), float(parts["top"])
    except Exception:
        return None, None


def _distance(pos1, pos2):
    """Oblicza odległość Manhattan między dwoma punktami"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def find_nearest_heros_resp(driver, target_coords, tolerance=20):
    """
    Znajduje najbliższy mmp-heros-resp względem podanych koordynatów.
    Zwraca tip_id jeśli znaleziono w promieniu tolerance.
    """
    try:
        respawns = driver.find_elements(By.CSS_SELECTOR, "div.mmpMapObject.mmp-heros-resp")
    except:
        return None

    nearest_tip_id = None
    nearest_dist = float('inf')

    for resp in respawns:
        try:
            tip_id = resp.get_attribute("tip-id")
            style = resp.get_attribute("style")
            resp_xy = _get_xy(style)
            
            if not tip_id or None in resp_xy:
                continue

            dist = _distance(target_coords, (resp_xy[0], resp_xy[1]))
            
            if dist < tolerance and dist < nearest_dist:
                nearest_dist = dist
                nearest_tip_id = int(tip_id)
        except:
            continue

    return nearest_tip_id


def find_heros_on_map(driver):
    """
    Znajduje najbliższego herosa (mmp-heros) na mapie względem bohatera.
    Zwraca tip_id.
    """
    try:
        hero = driver.find_element(By.CSS_SELECTOR, "div.mmpMapObject.mmp-hero")
        hero_xy = _get_xy(hero.get_attribute("style"))
        if None in hero_xy:
            return None
    except:
        return None

    nearest_tip_id = None
    nearest_dist = None

    try:
        heros_elements = driver.find_elements(By.CSS_SELECTOR, "div.mmpMapObject.mmp-heros")
    except:
        return None

    for heros_el in heros_elements:
        try:
            tip_id = heros_el.get_attribute("tip-id")
            style = heros_el.get_attribute("style")
            heros_xy = _get_xy(style)
        except:
            continue

        if not tip_id or None in heros_xy:
            continue

        dist = _distance(hero_xy, heros_xy)
        if nearest_dist is None or dist < nearest_dist:
            nearest_dist = dist
            nearest_tip_id = int(tip_id)

    return nearest_tip_id


def check_heros_detector_window(driver, discord_webhook=None):
    """
    Sprawdza czy pojawił się wykrywacz herosa.
    Jeśli tak, zwraca True, klika 'Podejdź' i wysyła powiadomienie na Discord.
    """
    try:
        # Szukamy okna wykrywacza
        window = driver.find_element(
            By.CSS_SELECTOR,
            "div.border-window .heros-detector"
        )
        
        print("🎉 Znaleziono herosa!!!")
        
        # Pobierz informacje o herosie
        heros_info = {}
        try:
            name_element = window.find_element(By.CSS_SELECTOR, ".name-label")
            heros_info['name'] = name_element.text.strip()
        except:
            heros_info['name'] = "Nieznany heros"
        
        try:
            map_element = window.find_element(By.CSS_SELECTOR, ".map-label")
            map_text = map_element.text.strip()
            heros_info['map'] = map_text
            
            # Wyciągnij koordynaty z tekstu np. "Przeklęty Zamek (11,5)"
            coords_match = re.search(r'\((\d+),(\d+)\)', map_text)
            if coords_match:
                heros_info['coords'] = (coords_match.group(1), coords_match.group(2))
            else:
                heros_info['coords'] = None
        except:
            heros_info['map'] = "Nieznana mapa"
            heros_info['coords'] = None
        
        # Wyślij powiadomienie Discord
        if discord_webhook:
            discord_webhook.send_heros_alert(
                heros_name=heros_info.get('name'),
                map_name=heros_info.get('map'),
                coords=heros_info.get('coords')
            )
        
        # Klikamy przycisk "Podejdź"
        approach_btn = window.find_element(
            By.XPATH,
            ".//div[contains(@class, 'button') and .//div[text()='Podejdź']]"
        )
        
        driver.execute_script("arguments[0].click();", approach_btn)
        print("✅ Kliknięto 'Podejdź'")
        
        time.sleep(1)
        
        # Zamknij okno
        try:
            close_btn = driver.find_element(
                By.CSS_SELECTOR,
                "div.border-window .close-button"
            )
            driver.execute_script("arguments[0].click();", close_btn)
            print("🔒 Zamknięto okno wykrywacza")
        except:
            pass
        
        return True
        
    except:
        return False


def click_heros_resp(driver, resp_tip_id, timeout=40, discord_webhook=None):
    """
    Klika w respawn herosa i czeka aż postać dotrze na miejsce.
    Zwraca True jeśli znaleziono herosa (wykrywacz się pojawił).
    """
    try:
        resp = driver.find_element(
            By.CSS_SELECTOR,
            f'div.mmpMapObject.mmp-heros-resp[tip-id="{resp_tip_id}"]'
        )
        driver.execute_script("arguments[0].click();", resp)
        print(f"📍 Klik w respawn herosa (tip-id={resp_tip_id})")
    except Exception as e:
        print(f"❌ Nie można kliknąć respawnu: {e}")
        return False

    # Czekaj aż postać dotrze (max timeout)
    start_time = time.time()
    last_pos = None

    while time.time() - start_time < timeout:
        time.sleep(0.3)
        
        # Sprawdź wykrywacz herosa (przekaż discord_webhook)
        if check_heros_detector_window(driver, discord_webhook):
            return True

        # Sprawdź czy postać dotarła (przestała się ruszać)
        try:
            hero = driver.find_element(By.CSS_SELECTOR, "div.mmpMapObject.mmp-hero")
            hero_xy = _get_xy(hero.get_attribute("style"))
            
            if last_pos is None:
                last_pos = hero_xy
            else:
                if _distance(last_pos, hero_xy) < 2:  # prawie nie rusza się
                    time.sleep(0.5)
                    # Ostatnia szansa na wykrywacz
                    if check_heros_detector_window(driver, discord_webhook):
                        return True
                    return False
                last_pos = hero_xy
        except:
            pass

    print("⏱️ Timeout podejścia do respawnu")
    return False