#!/usr/bin/env bash
# Instalacja/aktualizacja Kraken API (panel + logi) jako demona systemd na Ubuntu/Debianie.
#   sudo ./install.sh --domain api.twojadomena.pl     # z HTTPS przez Caddy (certyfikat Let's Encrypt)
#   sudo ./install.sh                                 # sam serwer na 127.0.0.1:8787 (bez HTTPS)
# Bez własnej domeny: --domain <IP-z-kreskami>.sslip.io (np. 203-0-113-7.sslip.io wskazuje na 203.0.113.7).
set -euo pipefail
DOMAIN=""
while [ $# -gt 0 ]; do
  case "$1" in
    --domain) DOMAIN="${2:-}"; shift 2 ;;
    *) echo "Nieznana opcja: $1" >&2; exit 1 ;;
  esac
done
[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root: sudo ./install.sh" >&2; exit 1; }
command -v python3 >/dev/null || { apt-get update -qq && apt-get install -y -qq python3; }
command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git; }   # checkout danych bota (data_repo.py)
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || { echo "Potrzebny Python 3.8+" >&2; exit 1; }
cd "$(dirname "$0")"

# ── serwer ──
id kraken >/dev/null 2>&1 || useradd --system --home /var/lib/kraken-api --shell /usr/sbin/nologin kraken
install -d -o kraken -g kraken -m 750 /var/lib/kraken-api
install -d -m 755 /opt/kraken-api
install -m 644 server.py /opt/kraken-api/server.py
install -m 644 data_repo.py /opt/kraken-api/data_repo.py
install -d -m 750 -o root -g kraken /etc/kraken-api
if [ ! -f /etc/kraken-api/config.json ]; then
  install -m 640 -o root -g kraken config.example.json /etc/kraken-api/config.json
  echo "Utworzono /etc/kraken-api/config.json"
fi
install -m 644 kraken-api.service /etc/systemd/system/kraken-api.service
systemctl daemon-reload
systemctl enable --now kraken-api >/dev/null
systemctl restart kraken-api
PORT="$(python3 -c 'import json; print(json.load(open("/etc/kraken-api/config.json")).get("port", 8787))')"
for i in 1 2 3 4 5; do curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" && echo " ← kraken-api działa" || { echo "kraken-api nie odpowiada: journalctl -u kraken-api -e" >&2; exit 1; }

# ── HTTPS (Caddy) ──
if [ -n "$DOMAIN" ]; then
  if ! command -v caddy >/dev/null; then
    apt-get update -qq
    apt-get install -y -qq caddy
  fi
  cat > /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:${PORT}
}
CADDY
  systemctl enable --now caddy >/dev/null
  systemctl reload caddy || systemctl restart caddy
  # Firewall: SSH, HTTP (certyfikat), HTTPS
  if command -v ufw >/dev/null; then
    ufw allow 22/tcp >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
    ufw --force enable >/dev/null
  fi
  echo "Panel: https://$DOMAIN  (pierwsze logowanie: admin / admin – zmiana hasła wymagana)"
fi
