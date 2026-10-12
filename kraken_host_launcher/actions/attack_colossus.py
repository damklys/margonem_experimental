from __future__ import annotations

from selenium.webdriver.common.by import By


def attack_colossus(driver, colossus_class: str = "mmp-collosus", stop_event=None, log_fn=print) -> bool:
    """
    Klika obiekt kolosusa na minimapie by otworzyć menu walki.
    """
    from anti_afk import check_interrupts

    check_interrupts(driver, logger=log_fn)

    try:
        els = driver.find_elements(By.CSS_SELECTOR, f".mmpMapObject.{colossus_class}")
        if not els:
            log_fn(f"⚠️  attack_colossus: nie znaleziono .{colossus_class} na minimapie")
            return False

        log_fn(f"⚔️  attack_colossus: klikam kolosusa ({len(els)} obiektów)…")
        for el in els:
            try:
                rect = driver.execute_script(
                    "var r=arguments[0].getBoundingClientRect();"
                    "return {left:r.left,top:r.top,width:r.width,height:r.height};",
                    el,
                )
                cx = rect["left"] + rect["width"]  / 2
                cy = rect["top"]  + rect["height"] / 2
                mmap = driver.find_element(By.CSS_SELECTOR, ".mmpMap")
                driver.execute_script(
                    """
                    var el = arguments[0], cx = arguments[1], cy = arguments[2];
                    ['mousedown','mouseup','click'].forEach(function(t) {
                        el.dispatchEvent(new MouseEvent(t, {
                            bubbles:true, cancelable:true, view:window,
                            clientX:cx, clientY:cy
                        }));
                    });
                    """,
                    mmap, cx, cy,
                )
                log_fn("✅ attack_colossus: kliknięto")
                return True
            except Exception:
                pass
    except Exception as e:
        log_fn(f"⚠️  attack_colossus: błąd — {e}")

    return False


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("colossus_class",) if k in cfg}
