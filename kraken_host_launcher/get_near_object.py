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


def _is_excluded(mob_xy, excluded):
    """Zwraca True jeśli mob dokładnie pasuje do wpisu w excluded po top/left."""
    for ex in excluded:
        if "left" not in ex or "top" not in ex:
            continue
        if mob_xy[0] == float(ex["left"]) and mob_xy[1] == float(ex["top"]):
            return True
    return False


def get_near_object(driver, excluded=None, ignored_tip_ids=None):
    """
    Zwraca tip-id najbliższego mob-a względem hero.
    excluded: lista {"top": float, "left": float, "tip_id": str} – moby pomijane.
    ignored_tip_ids: set[int] – tip-id mobów zignorowanych (zły poziom).
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
        mobs = driver.find_elements(By.CSS_SELECTOR, "div.mmpMapObject.mmp-mob")
    except:
        return None

    for mob in mobs:
        try:
            tip_id = mob.get_attribute("tip-id")
            style  = mob.get_attribute("style")
            mob_xy = _get_xy(style)
        except:
            continue

        if not tip_id or None in mob_xy:
            continue

        if excluded and _is_excluded(mob_xy, excluded):
            print(f"[EXCL] skip mob tip-id={tip_id} pos=(top={mob_xy[1]:.1f}, left={mob_xy[0]:.1f})")
            continue

        if ignored_tip_ids and int(tip_id) in ignored_tip_ids:
            continue

        dist = abs(hero_xy[0] - mob_xy[0]) + abs(hero_xy[1] - mob_xy[1])

        if nearest_dist is None or dist < nearest_dist:
            nearest_dist   = dist
            nearest_tip_id = int(tip_id)

    return nearest_tip_id


def wait_for_mob(driver, excluded=None, ignored_tip_ids=None,
                 timeout_s: float = 2.0, poll: float = 0.12):
    """
    Polluje get_near_object przez max timeout_s.
    Zwraca tip-id gdy mob się pojawi, lub None gdy upłynie czas.
    Używane zaraz po zmianie mapy, zanim DOM w pełni się załaduje.
    """
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        mob_id = get_near_object(driver, excluded=excluded,
                                 ignored_tip_ids=ignored_tip_ids)
        if mob_id is not None:
            return mob_id
        time.sleep(poll)
    return None
