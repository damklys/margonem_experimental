# Kraken API (serwer logów)

Demon systemd zbierający logi postaci z launcherów (`kraken_host_launcher`). Czysty Python 3.8+, bez zależności i bez Dockera.

## Instalacja na VPS

```bash
# skopiuj katalog kraken_api_server na serwer, potem:
cd kraken_api_server
sudo ./install.sh          # użytkownik kraken, /opt/kraken-api, /etc/kraken-api/config.json (nowy token), systemd
```

Aktualizacja: ponownie `sudo ./install.sh` (config i logi zostają).

- logi postaci: `/var/lib/kraken-api/logs/<świat>/<postać>.log` (rotacja co 50 MB, 5 starszych plików)
- dziennik serwera: `journalctl -u kraken-api -f`
- sterowanie: `systemctl status|restart|stop kraken-api`

## HTTPS (zalecane)

Serwer domyślnie słucha tylko na `127.0.0.1:8787` – na zewnątrz wystaw go przez reverse proxy z HTTPS,
żeby token nie szedł otwartym tekstem. Najprościej Caddy (sam pobiera certyfikat):

```
# /etc/caddy/Caddyfile
api.twojadomena.pl {
    reverse_proxy 127.0.0.1:8787
}
```

Bez domeny / proxy: w `/etc/kraken-api/config.json` ustaw `"host": "0.0.0.0"`, otwórz port w firewallu
(`ufw allow 8787/tcp`) i w launcherze użyj `http://IP:8787` (token jawnym tekstem – tylko na próbę).

## API

Nagłówek `Authorization: Bearer <token>` (tokeny w `config.json` → `tokens`).

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET | `/api/v1/health` | bez tokenu – czy serwer żyje |
| POST | `/api/v1/logs` | `{"source": "...", "entries": [{"char": "Nick", "world": "gordion", "lines": ["..."]}]}`, opcjonalnie gzip |
| GET | `/api/v1/chars` | lista postaci z logami |
| GET | `/api/v1/logs?world=gordion&char=Nick&tail=200` | ostatnie linie postaci |

```bash
curl -H "Authorization: Bearer $TOKEN" "https://api.twojadomena.pl/api/v1/logs?world=gordion&char=Nick&tail=50"
```

## Launcher

W `kraken_host_launcher/api.json` (plik lokalny, poza gitem):

```json
{ "url": "https://api.twojadomena.pl", "token": "TOKEN-Z-INSTALACJI" }
```

Launcher wysyła wtedy w tle logi każdej sesji: własne (logowanie, captcha…) i logi bota Kraken z przeglądarki.
Bez tego pliku nic nie wysyła.
