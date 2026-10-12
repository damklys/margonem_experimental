from __future__ import annotations


def anti_afk(driver, log_fn=print) -> bool:
    from anti_afk import check_interrupts
    handled = check_interrupts(driver, logger=log_fn)
    return handled


def load_from_json(cfg: dict) -> dict:
    return {}
