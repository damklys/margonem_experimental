"""Harmonogram launchera: wpisy (cel – grupa albo sesja, akcja, termin) i liczenie, kiedy wpis ma się wykonać.

Wpis (zapis w sessions_state.json, klucz "schedules"):
  id, enabled, target ("group" | "session"), world, group, session (uid sesji), session_name,
  action ("start" | "stop" | "create_session" – tylko grupa),
  kind ("daily" – codziennie o time w dni days; "interval" – co every minut w oknie from–to; "once" – date + time),
  params (dla create_session: prof, server, browser, template, program, start, disable_when_full),
  last_run, created.
"""
import datetime
import time
import uuid

ACTIONS = {
    "start": "▶ Start",
    "stop": "⏹ Stop",
    "create_session": "＋ Nowa sesja z nowym configiem",
}
KINDS = {
    "daily": "Codziennie o godzinie",
    "interval": "Co N minut",
    "once": "Jednorazowo",
}
DAYS = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
GRACE = 15 * 60     # termin „o godzinie” wykonuje się jeszcze do 15 min później (launcher włączony chwilę po czasie)


def new_entry(**kw) -> dict:
    e = {"id": uuid.uuid4().hex[:10], "enabled": True, "target": "group", "world": "", "group": "",
         "session": "", "session_name": "", "action": "start", "kind": "daily", "time": "11:00",
         "days": list(range(7)), "every": 60, "from": "", "to": "", "first_now": False, "date": "",
         "params": {"start": True, "disable_when_full": True}, "last_run": 0, "created": time.time()}
    e.update(kw)
    return e


def normalize(e: dict) -> dict:
    """Wpis z pliku/serwera uzupełniony o brakujące pola."""
    base = new_entry()
    base.update({k: v for k, v in (e or {}).items() if k in base})
    base["params"] = dict(new_entry()["params"], **((e or {}).get("params") or {}))
    return base


def parse_hm(s: str):
    """'11:00' → (11, 0); błędny format → None."""
    try:
        h, m = str(s).strip().split(":")
        h, m = int(h), int(m)
        return (h, m) if 0 <= h < 24 and 0 <= m < 60 else None
    except (ValueError, AttributeError):
        return None


def parse_date(s: str):
    try:
        return datetime.datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def validate(e: dict) -> str:
    """'' = wpis poprawny, inaczej opis błędu."""
    if e["target"] == "group" and not e.get("group"):
        return "Wybierz grupę."
    if e["target"] == "session" and not e.get("session"):
        return "Wybierz sesję."
    if e["target"] == "session" and e["action"] == "create_session":
        return "Nową sesję tworzy tylko wpis grupy."
    if e["kind"] in ("daily", "once") and not parse_hm(e.get("time")):
        return "Godzina w formacie GG:MM, np. 11:00."
    if e["kind"] == "daily" and not e.get("days"):
        return "Zaznacz co najmniej jeden dzień."
    if e["kind"] == "once" and not parse_date(e.get("date")):
        return "Data w formacie RRRR-MM-DD."
    if e["kind"] == "interval":
        try:
            if int(e.get("every")) < 1:
                raise ValueError
        except (TypeError, ValueError):
            return "Odstęp w minutach (liczba ≥ 1)."
        for k in ("from", "to"):
            if e.get(k) and not parse_hm(e[k]):
                return "Okno godzin w formacie GG:MM (albo puste)."
    return ""


def in_window(e: dict, dt: datetime.datetime) -> bool:
    """Okno godzin wpisu „co N minut” (puste = cała doba; 22:00–06:00 przechodzi przez północ)."""
    a, b = parse_hm(e.get("from") or ""), parse_hm(e.get("to") or "")
    if not a or not b:
        return True
    cur, a, b = dt.hour * 60 + dt.minute, a[0] * 60 + a[1], b[0] * 60 + b[1]
    return a <= cur < b if a <= b else (cur >= a or cur < b)


def _slot(dt: datetime.datetime, hm) -> float:
    return dt.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0).timestamp()


def due(e: dict, now: float = None) -> bool:
    if not e.get("enabled") or validate(e):
        return False
    now = time.time() if now is None else now
    dt = datetime.datetime.fromtimestamp(now)
    last = e.get("last_run") or 0
    kind = e.get("kind")
    if kind == "daily":
        if dt.weekday() not in e.get("days", []):
            return False
        slot = _slot(dt, parse_hm(e["time"]))
        return slot <= now < slot + GRACE and last < slot
    if kind == "once":
        d = parse_date(e["date"])
        slot = _slot(datetime.datetime.combine(d, datetime.time()), parse_hm(e["time"]))
        return slot <= now < slot + GRACE and last < slot
    if kind == "interval":
        if not in_window(e, dt):
            return False
        if not last and e.get("first_now"):
            return True
        return now - (last or e.get("created") or now) >= int(e["every"]) * 60
    return False


def next_run(e: dict, now: float = None):
    """Najbliższy termin (timestamp) albo None – do podglądu w oknie harmonogramu."""
    if not e.get("enabled") or validate(e):
        return None
    now = time.time() if now is None else now
    kind = e.get("kind")
    if kind == "daily":
        hm, dt = parse_hm(e["time"]), datetime.datetime.fromtimestamp(now)
        for i in range(8):
            day = dt + datetime.timedelta(days=i)
            slot = _slot(day, hm)
            if day.weekday() in e["days"] and slot > (e.get("last_run") or 0) and slot + GRACE > now:
                return max(slot, now)
        return None
    if kind == "once":
        slot = _slot(datetime.datetime.combine(parse_date(e["date"]), datetime.time()), parse_hm(e["time"]))
        return slot if slot + GRACE > now and (e.get("last_run") or 0) < slot else None
    if kind == "interval":
        last = e.get("last_run") or 0
        if not last and e.get("first_now"):
            t = now
        else:
            t = max(now, (last or e.get("created") or now) + int(e["every"]) * 60)
        # poza oknem godzin – szukamy pierwszej minuty w oknie (do doby naprzód)
        for _ in range(24 * 60):
            if in_window(e, datetime.datetime.fromtimestamp(t)):
                return t
            t += 60
        return None
    return None


def describe_when(e: dict) -> str:
    kind = e.get("kind")
    if kind == "daily":
        days = e.get("days") or []
        d = "codziennie" if len(days) == 7 else ", ".join(DAYS[i] for i in sorted(days))
        return f"{d} o {e.get('time')}"
    if kind == "interval":
        win = f", {e['from']}–{e['to']}" if e.get("from") and e.get("to") else ""
        return f"co {e.get('every')} min{win}"
    if kind == "once":
        return f"{e.get('date')} {e.get('time')}"
    return "?"


def describe_target(e: dict) -> str:
    if e.get("target") == "session":
        return f"sesja „{e.get('session_name') or e.get('session')}”"
    return f"grupa „{e.get('group')}” ({e.get('world')})"
