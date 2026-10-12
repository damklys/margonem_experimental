from selenium.webdriver.common.by import By

def _get_xy(style):
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        return float(parts["left"]), float(parts["top"])
    except Exception:
        return None, None


def get_near_e2(driver):
    """
    Zwraca tip-id najbliższego obiektu mmp-elite2 względem hero.
    Obsługuje dynamiczny DOM i stale elements.
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

    # --- pobieramy elite2 w locie ---
    try:
        elites = driver.find_elements(By.CSS_SELECTOR, "div.mmpMapObject.mmp-elite2")
    except:
        return None

    for elite in elites:
        try:
            tip_id = elite.get_attribute("tip-id")
            style = elite.get_attribute("style")
            elite_xy = _get_xy(style)
        except:
            continue  # jeśli stale element → pomiń

        if not tip_id or None in elite_xy:
            continue

        dist = abs(hero_xy[0] - elite_xy[0]) + abs(hero_xy[1] - elite_xy[1])

        if nearest_dist is None or dist < nearest_dist:
            nearest_dist = dist
            nearest_tip_id = int(tip_id)

    return nearest_tip_id
