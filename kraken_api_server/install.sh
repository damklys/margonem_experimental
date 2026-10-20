#!/usr/bin/env bash
# Instalacja/aktualizacja Kraken API jako demona systemd (Debian/Ubuntu/…; potrzebny python3 ≥ 3.8).
# Użycie (na VPS, w katalogu kraken_api_server):  sudo ./install.sh
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root: sudo ./install.sh" >&2; exit 1; }
command -v python3 >/dev/null || { echo "Brak python3 (apt install python3)" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || { echo "Potrzebny Python 3.8+" >&2; exit 1; }

cd "$(dirname "$0")"
id kraken >/dev/null 2>&1 || useradd --system --home /var/lib/kraken-api --shell /usr/sbin/nologin kraken
install -d -o kraken -g kraken -m 750 /var/lib/kraken-api
install -d -m 755 /opt/kraken-api
install -m 644 server.py /opt/kraken-api/server.py
install -d -m 750 -o root -g kraken /etc/kraken-api

if [ ! -f /etc/kraken-api/config.json ]; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  sed "s/WSTAW-TU-TOKEN/$TOKEN/" config.example.json > /etc/kraken-api/config.json
  chmod 640 /etc/kraken-api/config.json
  chgrp kraken /etc/kraken-api/config.json
  echo "Utworzono /etc/kraken-api/config.json z nowym tokenem:"
  echo "  $TOKEN"
  echo "(wpisz go w launcherze: kraken_host_launcher/api.json)"
else
  echo "Config /etc/kraken-api/config.json bez zmian."
fi

install -m 644 kraken-api.service /etc/systemd/system/kraken-api.service
systemctl daemon-reload
systemctl enable --now kraken-api
systemctl restart kraken-api
sleep 1
systemctl --no-pager --lines=5 status kraken-api || true
PORT="$(python3 -c 'import json; print(json.load(open("/etc/kraken-api/config.json")).get("port", 8787))')"
curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" && echo || echo "⚠️  /api/v1/health nie odpowiada – sprawdź: journalctl -u kraken-api -e"
