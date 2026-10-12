from __future__ import annotations

from pathlib import Path


def play(
    driver,
    playbook: str,
    registry=None,
    stop_event=None,
    log_fn=print,
) -> None:
    """
    Uruchamia zagnieżdżony playbook z tym samym registry i stop_event.
    """
    from actions.executor import PlaybookExecutor, load_playbook

    pb_path = Path(__file__).parent.parent / "playbooks" / playbook
    if not pb_path.exists():
        pb_path = Path(playbook)

    log_fn(f"▶️  play: uruchamiam sub-playbook '{playbook}'…")
    data = load_playbook(pb_path)
    PlaybookExecutor(driver, registry=registry, stop_event=stop_event, log_fn=log_fn).run(data)
    log_fn(f"⏹️  play: sub-playbook '{playbook}' zakończony")


def load_from_json(cfg: dict) -> dict:
    return {"playbook": cfg["playbook"]}
