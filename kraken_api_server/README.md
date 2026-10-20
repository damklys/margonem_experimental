# Kraken API (panel + logi postaci)

Demon systemd: panel WWW z kontami użytkowników i API, na które bot Kraken (przeglądarka) i launcher wysyłają
logi postaci oraz sygnał „żyję”. Czysty Python 3.8+, bez zależności i bez Dockera; HTTPS przez Caddy.

## Instalacja na VPS (Ubuntu/Debian)

```bash
scp -r kraken_api_server root@SERWER:/root/
ssh root@SERWER 'cd /root/kraken_api_server && ./install.sh --domain api.twojadomena.pl'
```

Bez własnej domeny: `--domain 203-0-113-7.sslip.io` (IP z kreskami – sslip.io wskazuje na ten adres, Caddy
pobiera dla niego certyfikat Let's Encrypt). Instalator: użytkownik `kraken`, `/opt/kraken-api`,
`/etc/kraken-api/config.json`, usługa `kraken-api`, Caddy (HTTPS), ufw (22/80/443).
Aktualizacja: ten sam `install.sh` (dane i konfiguracja zostają).

- panel: `https://<domena>` – pierwsze logowanie **admin / admin**, potem wymuszona zmiana hasła
- dane: `/var/lib/kraken-api/users.json` (konta, hasła PBKDF2, tokeny), `/var/lib/kraken-api/users/<użytkownik>/logs/<świat>/<postać>.log`
- dziennik: `journalctl -u kraken-api -f`, `journalctl -u caddy -f`

## Panel

- **Token użytkownika** (kopiuj / wygeneruj nowy) – wpisuje się go w bocie i launcherze.
- **Sesje** – postacie z logami na tym koncie: online/offline (sygnał „żyję” w ostatnich 45 s), poziom, mapa, krok.
- **Podgląd sesji** – log postaci na żywo (odświeżanie co 1,5 s, kolory wg typu wpisu).

## Bot Kraken

⚙️ Ustawienia › 📡 Serwer: adres panelu (`https://…`) i token. Bot wysyła swoje logi co 3 s i sygnał „żyję” co 15 s;
pod polami widać stan połączenia. Ustawienie jest wspólne dla postaci w tej przeglądarce.

## Launcher

`kraken_host_launcher/api.json` (lokalny, poza gitem): `{"url": "https://…", "token": "…"}` – launcher wysyła
swoje logi sesji (`[launcher] …`), a logi bota z konsoli przeglądarki tylko wtedy, gdy bot nie ma tokenu (bez dubli).

## API

`Authorization: Bearer <token użytkownika>` (CORS otwarty dla stron gry):

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET | `/api/v1/health` | bez tokenu |
| GET | `/api/v1/me` | sprawdzenie tokenu |
| POST | `/api/v1/logs` | `{"source", "entries": [{"char", "world", "lines": [...]}]}` (opcjonalnie gzip) |
| POST | `/api/v1/heartbeat` | `{"char", "world", "version", "running", "map", "lvl", "step"}` |
