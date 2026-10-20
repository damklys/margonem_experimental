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

- **Token użytkownika** (kopiuj / wygeneruj nowy) – wpisuje się go w launcherze (⚙️ Ustawienia) albo w bocie.
- **Hosty** – launchery z tym tokenem: online/offline, system, wersja, uruchomione sesje. Strona hosta: sesje launchera
  z przyciskami ▶ Start / ⏹ Stop (polecenie trafia do launchera przy jego następnym sygnale, do 10 s) i historia poleceń.
- **Sesje bota** – postacie z logami (z launchera albo uruchomione poza nim): online/offline, poziom, mapa, krok, host.
- **Podgląd sesji** – log postaci na żywo (odświeżanie co 1,5 s, kolory wg typu wpisu).
- **Ustawienia launcherów** – grupy, sesje i configi kont każdego hosta zapisują się na serwerze
  (`/var/lib/kraken-api/users/<użytkownik>/hosts/<host>.json`, uprawnienia 600 – zawierają loginy i hasła kont gry);
  launcher odtwarza je przyciskiem ⚙️ Ustawienia › ⬇ Odtwórz z serwera.

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
| POST | `/api/v1/host/heartbeat` | launcher: `{"host_id", "name", "platform", "version", "sessions", "results"}` → polecenia |
| POST | `/api/v1/host/state` | launcher: `{"host_id", "name", "state", "configs"}` – zapis ustawień |
| GET | `/api/v1/host/state?host_id=…` / `?list=1` | odczyt zapisanych ustawień / lista hostów |
