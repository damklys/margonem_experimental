from selenium.webdriver.common.by import By
import time

_ASYNC_MOB_LEVEL_JS = """
var callback = arguments[arguments.length - 1];
var tipId    = arguments[0];
var maxMs    = arguments[1];
var pollMs   = 50;

var el = document.querySelector('.mmpMapObject.mmp-mob[tip-id="' + tipId + '"]');
if (!el) { callback(null); return; }

var r = el.getBoundingClientRect();
var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
['pointerover','mouseover','mouseenter','mousemove'].forEach(function(t) {
    el.dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true,
                                        view:window, clientX:cx, clientY:cy}));
});
if (window.jQuery) window.jQuery(el).trigger('mouseenter').trigger('mouseover');

var elapsed = 0;
function readTip() {
    var tips = document.querySelectorAll('.tip-wrapper');
    for (var i = 0; i < tips.length; i++) {
        if (tips[i].offsetHeight > 0) {
            var c = tips[i].querySelector('.content') || tips[i];
            var span = c.querySelector('span');
            if (span) {
                var m = span.textContent.trim().match(/(\\d+)/);
                if (m) { callback(parseInt(m[1])); return; }
            }
        }
    }
    elapsed += pollMs;
    if (elapsed < maxMs) { setTimeout(readTip, pollMs); }
    else { callback(null); }
}
setTimeout(readTip, pollMs);
"""


def _get_mob_level(driver, mob_tip_id: int, hover_wait_ms: int = 500) -> "int | None":
    """
    Hover nad mobem przez JS async — przeglądarka czeka hover_wait_ms w swoim
    event-loop przed odczytem tooltipa (odpowiednik await setTimeout w konsoli).
    """
    try:
        raw = driver.execute_async_script(_ASYNC_MOB_LEVEL_JS,
                                          str(mob_tip_id), hover_wait_ms)
        print(f"[DBG] _get_mob_level({mob_tip_id}) raw={raw!r}")
        return int(raw) if raw is not None else None
    except Exception as e:
        print(f"[DBG] _get_mob_level({mob_tip_id}) exception={e}")
        return None


def _parse_style_xy(style: str):
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        return float(parts["left"]), float(parts["top"])
    except Exception:
        return None, None


def _center_from_element(el):
    """
    Zwraca (cx, cy, tile) bazując na:
    - left/top ze style
    - width/height z rect
    tile = max(width,height)
    """
    style = el.get_attribute("style") or ""
    left, top = _parse_style_xy(style)
    if left is None or top is None:
        return None, None, None

    r = el.rect
    w = float(r.get("width") or 0)
    h = float(r.get("height") or 0)
    tile = max(w, h) if max(w, h) > 0 else 11.0

    cx = left + w / 2.0
    cy = top + h / 2.0
    return cx, cy, tile


def _in_attack_range(hero_c, mob_c, tile):
    """
    Zasięg ataku: obok + po przekątnej.
    Chebyshev distance <= 1 kafelek (+ tolerancja).
    """
    hx, hy = hero_c
    mx, my = mob_c

    dx = abs(hx - mx) / tile
    dy = abs(hy - my) / tile

    tol = 0.25  # trochę większa tolerancja, bo UI bywa "pływające"
    return max(dx, dy) <= 1.0 + tol


def _find_hero(driver):
    return driver.find_element(By.CSS_SELECTOR, "div.mmpMapObject.mmp-hero")


def _find_mob(driver, mob_tip_id):
    return driver.find_element(By.CSS_SELECTOR, f'div.mmpMapObject.mmp-mob[tip-id="{mob_tip_id}"]')


def _safe_get_snapshot(driver, mob_tip_id):
    """
    Snapshot: (hero_center, mob_center, tile) albo None jeśli brak/DOM się zmienia.
    """
    try:
        hero = _find_hero(driver)
        mob = _find_mob(driver, mob_tip_id)
        hx, hy, tile = _center_from_element(hero)
        mx, my, _ = _center_from_element(mob)
    except Exception:
        return None

    if None in (hx, hy, mx, my, tile):
        return None

    return (hx, hy), (mx, my), tile


# -------- GLOBALNY LIMITER Q (ważne!) --------

def _can_press_q(driver, cooldown_s: float) -> bool:
    """
    Globalny cooldown Q zapisany w driverze.
    Dzięki temu Q nie spamuje między kolejnymi wywołaniami kill_object().
    """
    now = time.time()
    last = getattr(driver, "_last_q_time", 0.0)
    if now - last >= cooldown_s:
        setattr(driver, "_last_q_time", now)
        return True
    return False


def _press_q(driver):
    driver.find_element(By.TAG_NAME, "body").send_keys("q")


# -------- refresh helpers --------

def _wait_dom_ready(driver, timeout_s: float = 12.0, poll: float = 0.10) -> bool:
    """Czeka aż document.readyState == 'complete'."""
    t0 = time.time()
    while time.time() - t0 <= timeout_s:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(poll)
    return False


def _refresh_page(driver, wait_s: float = 12.0):
    try:
        driver.refresh()
    except Exception:
        return
    _wait_dom_ready(driver, timeout_s=wait_s)
    # mały debounce po załadowaniu, żeby elementy mapy zdążyły się pojawić
    time.sleep(0.35)


def kill_object(
    driver,
    mob_tip_id: int,
    char_level: "int | None" = None,
    poll: float = 0.12,
    max_time_s: float = 12.0,
    repath_if_stuck_s: float = 1.2,
    q_cooldown_s: float = 1.0,
    repath_refresh_after: int = 5,
):
    # --- sprawdzenie poziomu moba ---
    if char_level is not None:
        mob_level = None
        for _attempt in range(2):
            mob_level = _get_mob_level(driver, mob_tip_id)
            if mob_level is not None:
                break

        if mob_level is None:
            print(f"⏭️ Mob {mob_tip_id}: nie udało się odczytać poziomu (3 próby), ignoruję")
            return "IGNORED"

        lo = char_level - 13
        hi = char_level + 25
        if mob_level < lo or mob_level > hi:
            print(f"⏭️ Mob {mob_tip_id} lvl={mob_level} poza zakresem [{lo}–{hi}], ignoruję")
            return "IGNORED"

        print(f"✅ Mob {mob_tip_id} lvl={mob_level} w zakresie [{lo}–{hi}], atakuję")

    t0 = time.time()

    def _click_mob_or_fail(stage: str) -> bool:
        try:
            mob = _find_mob(driver, mob_tip_id)
            driver.execute_script("arguments[0].click();", mob)
            print(f"🎯 Klik mob {mob_tip_id}" if stage == "start" else f"🎯 Klik mob {mob_tip_id} ({stage})")
            return True
        except Exception:
            print(f"❌ Mob nie istnieje ({stage})")
            return False

    # początkowy klik
    if not _click_mob_or_fail("start"):
        return False

    last_hero_pos = None
    last_move_time = time.time()
    last_repath_time = 0.0

    repath_count = 0  # <-- NOWE: licznik re-path bez skutku

    while True:
        if time.time() - t0 > max_time_s:
            print(f"⏱️ Timeout podejścia do moba {mob_tip_id}")
            return False

        snap = _safe_get_snapshot(driver, mob_tip_id)
        if snap is None:
            # sprawdź czy mob jeszcze istnieje
            try:
                _ = _find_mob(driver, mob_tip_id)
            except Exception:
                print(f"⚰️ Mob {mob_tip_id} zniknął")
                return False

            time.sleep(poll)
            continue

        hero_c, mob_c, tile = snap

        # --- jeśli w zasięgu -> Q, ale globalnie max 1/sek ---
        if _in_attack_range(hero_c, mob_c, tile):
            if _can_press_q(driver, q_cooldown_s):
                print(f"⚔️ Zasięg OK (tile={tile:.1f}) -> Q")
                _press_q(driver)
                return True
            else:
                # jesteśmy w zasięgu, ale cooldown blokuje Q -> czekamy
                time.sleep(poll)
                continue

        # --- wykrywanie "stuck" (hero nie rusza się) + re-path ---
        now = time.time()
        if last_hero_pos is None:
            last_hero_pos = hero_c
            last_move_time = now
        else:
            moved = (abs(hero_c[0] - last_hero_pos[0]) > 0.8) or (abs(hero_c[1] - last_hero_pos[1]) > 0.8)
            if moved:
                last_hero_pos = hero_c
                last_move_time = now
                repath_count = 0  # <-- NOWE: jak ruszył, resetujemy licznik re-path
            else:
                # stoi
                if (now - last_move_time >= repath_if_stuck_s) and (now - last_repath_time >= 0.8):
                    try:
                        mob = _find_mob(driver, mob_tip_id)
                        driver.execute_script("arguments[0].click();", mob)
                        print(f"🔁 Re-path klik mob {mob_tip_id}")
                        last_repath_time = now
                        last_move_time = now  # reset "stuck timer"

                        # <-- NOWE: zliczanie re-path i refresh po limicie
                        repath_count += 1
                        if repath_count >= repath_refresh_after:
                            print(f"🔄 Re-path x{repath_count} dla mob {mob_tip_id} -> refresh strony")
                            _refresh_page(driver)

                            # po refresh: reset lokalnych timerów i próbujemy ponownie "zaczepić" moba
                            repath_count = 0
                            last_hero_pos = None
                            last_move_time = time.time()
                            last_repath_time = 0.0

                            # jeśli mob po refreshu zniknął — kończymy
                            if not _click_mob_or_fail("po refresh"):
                                return False

                    except Exception:
                        print(f"⚰️ Mob {mob_tip_id} zniknął przy re-path")
                        return False

        time.sleep(poll)


