from __future__ import annotations

from anti_afk import check_interrupts


def checkout_group(driver, party_size: int = 10, stop_event=None, log_fn=print) -> int:
    """
    Leader (w sali walki): wyrzuca z grupy tych NIEwidocznych na tej mapie.
    Zwraca aktualny rozmiar grupy.
    """
    from kolos_mode import _party_size, _kick_absent_party_members

    check_interrupts(driver, logger=log_fn)
    log_fn("🔍 checkout_group: sprawdzam skład w sali…")
    kicked = _kick_absent_party_members(driver, log_fn)
    if kicked:
        log_fn(f"🚫 checkout_group: wyrzucono {kicked} nieobecnych")
    current = _party_size(driver)
    log_fn(f"{'✅' if current >= party_size else '⚠️ '} checkout_group: drużyna {current}/{party_size}")
    return current


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("party_size",) if k in cfg}
