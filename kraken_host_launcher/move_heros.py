from selenium.webdriver.common.by import By
import time

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
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_current_map_name(driver):
    """
    Pobiera nazwę aktualnej mapy z elementu .map-data .location
    """
    try:
        location_element = driver.find_element(By.CSS_SELECTOR, ".map-data .location")
        map_name = location_element.text.strip()
        return map_name
    except Exception as e:
        print(f"⚠️ Nie można pobrać nazwy mapy: {e}")
        return None


def click_gw(driver, gw_coords, expected_map_name=None, timeout=40, tolerance=30):
    """
    Klika w przejście (GW) na podstawie koordynatów.
    Czeka aż postać przejdzie na nową mapę (weryfikacja po nazwie mapy).
    
    Args:
        driver: WebDriver
        gw_coords: tuple (left, top) - koordynaty GW
        expected_map_name: str - oczekiwana nazwa mapy po przejściu (opcjonalne)
        timeout: int - maksymalny czas oczekiwania na przejście (sekundy)
        tolerance: int - tolerancja odległości do GW (piksele)
    """
    # Pobierz aktualną nazwę mapy przed przejściem
    current_map = get_current_map_name(driver)
    print(f"📍 Aktualna mapa: {current_map}")
    
    try:
        gw_elements = driver.find_elements(By.CSS_SELECTOR, "div.mmpMapObject.mmp-gw")
    except:
        print("❌ Nie znaleziono żadnych GW")
        return False

    # Znajdź GW najbliższe podanym koordynatom
    target_gw = None
    min_dist = float('inf')

    for gw in gw_elements:
        try:
            style = gw.get_attribute("style")
            gw_xy = _get_xy(style)
            if None in gw_xy:
                continue

            dist = _distance(gw_coords, (gw_xy[0], gw_xy[1]))
            if dist < min_dist and dist < tolerance:
                min_dist = dist
                target_gw = gw
        except:
            continue

    if target_gw is None:
        print(f"❌ Nie znaleziono GW w pobliżu ({gw_coords}) w promieniu {tolerance}px")
        print(f"   Dostępne GW na mapie:")
        for gw in gw_elements:
            try:
                style = gw.get_attribute("style")
                gw_xy = _get_xy(style)
                if None not in gw_xy:
                    dist = _distance(gw_coords, (gw_xy[0], gw_xy[1]))
                    print(f"   - GW: ({gw_xy[0]}, {gw_xy[1]}) - odległość: {dist:.1f}px")
            except:
                pass
        return False

    print(f"✅ Znaleziono GW w odległości {min_dist:.1f}px od ({gw_coords})")

    # Kliknij w GW
    try:
        driver.execute_script("arguments[0].click();", target_gw)
        print(f"🚪 Klik w GW ({gw_coords})")
    except Exception as e:
        print(f"❌ Błąd kliknięcia GW: {e}")
        return False

    # Czekaj na załadowanie nowej mapy (timeout 15s)
    start_time = time.time()
    last_check_time = start_time
    
    while time.time() - start_time < timeout:
        time.sleep(0.5)
        
        # Sprawdzaj nazwę mapy co 0.5s
        if time.time() - last_check_time >= 0.5:
            new_map = get_current_map_name(driver)
            last_check_time = time.time()
            
            if new_map and new_map != current_map:
                print(f"✅ Przeszedłem na mapę: {new_map}")
                
                # Jeśli podano oczekiwaną nazwę, zweryfikuj
                if expected_map_name and new_map != expected_map_name:
                    print(f"⚠️ Oczekiwano: {expected_map_name}, otrzymano: {new_map}")
                
                time.sleep(1)  # Dodatkowy bufor na załadowanie
                return True
    
    print(f"⏱️ Timeout przejścia przez GW ({timeout}s)")
    print(f"   Aktualna mapa: {get_current_map_name(driver)}")
    return False