from __future__ import annotations


def check_group_size(driver, stop_event=None, log_fn=print) -> int:
    """
    Zwraca aktualny rozmiar grupy (1 = gracz solo, nie w grupie).
    Nie ma efektów ubocznych — nie zaprasza, nie wyrzuca.
    """
    from kolos_mode import _party_size

    size = _party_size(driver)
    log_fn(f"👥 check_group_size: {size}")
    return size


def load_from_json(cfg: dict) -> dict:
    return {}
