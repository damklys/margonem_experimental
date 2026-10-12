from __future__ import annotations

from anti_afk import check_interrupts


def check_afk_members(driver, party_size: int = 10, stop_event=None, log_fn=print) -> bool:
    """
    Leader (przy zbiórce): wyrzuca z grupy tych wciąż widocznych na tej mapie
    (nie weszli jeszcze do sali walki).
    Zwraca True gdy rozmiar grupy == party_size (wszyscy weszli).
    """
    from kolos_mode import _party_size, _kick_present_party_members, _party_members_on_map_count

    check_interrupts(driver, logger=log_fn)

    stuck = _party_members_on_map_count(driver)
    if stuck > 0:
        log_fn(f"⚡ check_afk_members: {stuck} graczy wciąż na zbiórce — wyrzucam…")
        kicked = _kick_present_party_members(driver, log_fn)
        log_fn(f"🚫 check_afk_members: wyrzucono {kicked} graczy")
    else:
        log_fn("✅ check_afk_members: wszyscy weszli do sali")

    current = _party_size(driver)
    ready   = current >= party_size
    log_fn(f"{'✅' if ready else '🔄'} check_afk_members: drużyna {current}/{party_size} → {'gotowi' if ready else 'wróć do zbiórki'}")
    return ready


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("party_size",) if k in cfg}
