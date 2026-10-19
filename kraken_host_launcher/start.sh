#!/usr/bin/env bash
# Kraken – start launchera na Linuksie i macOS: .venv z zależnościami (przy pierwszym uruchomieniu) i main_v3.py.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
  done
fi
if [ -z "$PY" ]; then
  echo "Brak Pythona 3.10+ (zainstaluj python3; Linux: też python3-venv i python3-tk)." >&2
  exit 1
fi
"$PY" - <<'PYCHK' || { echo "Potrzebny Python 3.10 lub nowszy (jest: $("$PY" --version))." >&2; exit 1; }
import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)
PYCHK
"$PY" -c "import tkinter" 2>/dev/null || {
  echo "Brak tkinter. Linux: sudo apt install python3-tk (Debian/Ubuntu) / sudo dnf install python3-tkinter (Fedora); macOS: brew install python-tk." >&2
  exit 1
}

if [ ! -x .venv/bin/python ]; then
  echo "Tworzę środowisko .venv…"
  "$PY" -m venv .venv
fi
# Zależności – tylko gdy requirements.txt się zmienił od ostatniej instalacji.
if ! cmp -s requirements.txt .venv/.requirements.installed 2>/dev/null; then
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt
  cp requirements.txt .venv/.requirements.installed
fi
exec .venv/bin/python main_v3.py "$@"
