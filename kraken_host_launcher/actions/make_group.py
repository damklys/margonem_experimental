from __future__ import annotations

import time
from typing import Optional


def make_group(
    driver,
    party_size: int = 10,
    gather_key: str = "g",
    gather_interval_s: int = 10,
    position: Optional[dict] = None,
    timeout_s: float = 300.0,
    stop_event=None,
    log_fn=print,
) -> int:
    """
    Leader: zaprasza graczy klawiszem gather_key aż rozmiar grupy == party_size lub timeout.
    Repositioning only after stasis/captcha handling (jak oryginał kolos_mode).
    """
    from kolos_mode import _party_size, _click_minimap_pos, _count_map_players
    from anti_afk import check_interrupts
    from selenium.webdriver.common.action_chains import ActionChains

    def _press_gather():
        try:
            ActionChains(driver).key_down(gather_key).pause(0.15).key_up(gather_key).perform()
        except Exception:
            pass

    log_fn(f"🔔 make_group: zbieram drużynę do {party_size} graczy…")
    t0          = time.time()
    last_gather = 0.0
    last_log    = 0.0

    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            break

        # Reposition tylko gdy check_interrupts coś obsłużył (staza/captcha)
        interrupted = check_interrupts(driver, logger=log_fn)
        if interrupted and position:
            _click_minimap_pos(driver, float(position["top"]), float(position["left"]))

        size   = _party_size(driver)
        on_map = _count_map_players(driver)

        if size >= party_size:
            log_fn(f"✅ make_group: drużyna pełna ({size}/{party_size})")
            return size

        if time.time() - last_log >= 15:
            elapsed = int(time.time() - t0)
            log_fn(f"🔔 make_group: drużyna {size}/{party_size}, graczy na mapie: {on_map} ({elapsed}s)")
            last_log = time.time()

        if time.time() - last_gather >= gather_interval_s:
            _press_gather()
            last_gather = time.time()

        time.sleep(3)

    size = _party_size(driver)
    log_fn(f"⏰ make_group: timeout — drużyna {size}/{party_size}")
    return size


def load_from_json(cfg: dict) -> dict:
    return {k: cfg[k] for k in ("party_size", "gather_key", "gather_interval_s", "position", "timeout_s") if k in cfg}
