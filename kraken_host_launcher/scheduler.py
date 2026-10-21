"""Harmonogram launchera: wpisy (cel – grupa albo sesja, akcja, termin) i liczenie, kiedy wpis ma się wykonać.

Wpis (zapis w sessions_state.json, klucz "schedules"):
  id, enabled, target ("group" | "session"), world, group, session (uid sesji), session_name,
  action ("start" | "stop" | "create_session" – tylko grupa),
  kind ("daily" – codziennie o time w dni days; "interval" – co every minut w oknie from–to, pierwszy raz wg first:
        now – od razu, after – po odstępie, at – o first_at; "once" – date + time),
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
    "interval": "Co określony czas (odstęp)",
    "once": "Jednorazowo",
}
FIRST = {
    "now": "od razu po zapisaniu",
    "after": "po pierwszym odstępie",
    "at": "o godzinie",
}
DAYS = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
GRACE = 15 * 60     # termin „o godzinie” wykonuje się jeszcze do 15 min później (launcher włączony chwilę po czasie)


def new_entry(**kw) -> dict:
    e = {"id": uuid.uuid4().hex[:10], "enabled": True, "target": "group", "world": "", "group": "",
         "session": "", "session_name": "", "action": "start", "kind": "daily", "time": "11:00",
         "days": list(range(7)), "every": 60, "from": "", "to": "", "first": "after", "first_at": "", "date": "",
         "params": {"start": True, "disable_when_full": True}, "last_run": 0, "created": time.time()}
    e.update(kw)
    return e


def normalize(e: dict) -> dict:
    """Wpis z pliku/serwera uzupełniony o brakujące pola."""
    base = new_entry()
    base.update({k: v for k, v in (e or {}).items() if k in base})
    base["params"] = dict(new_entry()["params"], **((e or {}).get("params") or {}))
    if "first" not in (e or {}) and (e or {}).get("first_now"):      # wpisy sprzed wersji z „first”
        base["first"] = "now"
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
        if e.get("first") == "at" and not parse_hm(e.get("first_at")):
            return "Godzina pierwszego wykonania w formacie GG:MM."
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


def _first_slot(e: dict) -> float:
    """Pierwsze wykonanie wpisu „co odstęp” (gdy jeszcze nie było żadnego)."""
    created = e.get("created") or time.time()
    first = e.get("first") or "after"
    if first == "now":
        return created
    if first == "at":
        hm = parse_hm(e.get("first_at"))
        dt = datetime.datetime.fromtimestamp(created)
        slot = _slot(dt, hm)
        return slot if slot >= created else _slot(dt + datetime.timedelta(days=1), hm)
    return created + int(e["every"]) * 60


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
        if not last:
            return now >= _first_slot(e)
        return now - last >= int(e["every"]) * 60
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
        t = max(now, _first_slot(e) if not last else last + int(e["every"]) * 60)
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
        start = f", od {e['first_at']}" if e.get("first") == "at" else ""
        return f"co {fmt_every(e.get('every'))}{start}{win}"
    if kind == "once":
        return f"{e.get('date')} {e.get('time')}"
    return "?"


def describe_target(e: dict) -> str:
    if e.get("target") == "session":
        return f"sesja „{e.get('session_name') or e.get('session')}”"
    return f"grupa „{e.get('group')}” ({e.get('world')})"


def fmt_every(minutes) -> str:
    """60 → '1 godz.', 90 → '90 min'."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return f"{minutes} min"
    return f"{m // 60} godz." if m >= 60 and m % 60 == 0 else f"{m} min"
