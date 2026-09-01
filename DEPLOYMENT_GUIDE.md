# Przewodnik Wdrozeniowy Chem-Man

Wdrozenie produkcyjne aplikacji Chem-Man. Serwer nie kompiluje niczego — pobiera
gotowy obraz z GitHub Container Registry i uruchamia go przez `docker compose`.

> **Instalacja bez Dockera (venv, gunicorn, reczna instalacja PostgreSQL) nie jest
> juz opisywana ani wspierana.** Do pracy deweloperskiej na wlasnej maszynie sluzy
> [INSTALLATION.md](INSTALLATION.md).

---

## Spis Tresci

1. [Wdrozenie przez Docker](#wdrozenie-przez-docker)
2. [Reverse proxy (nginx)](#reverse-proxy-nginx)
3. [SSL/TLS](#ssltls)
4. [Backup i przywracanie](#backup-i-przywracanie)
5. [Monitoring i utrzymanie](#monitoring-i-utrzymanie)
6. [Rozwiazywanie problemow](#rozwiazywanie-problemow)
7. [Listy kontrolne](#listy-kontrolne)

---

## Wdrozenie przez Docker

### Wymagania

- Docker Engine 24+ z wtyczka `docker compose`
- ok. 2 GB RAM i 5 GB miejsca na dysku
- nginx na hoscie (reverse proxy + TLS) — patrz [Reverse proxy](#reverse-proxy-nginx)

### Pierwsze uruchomienie

```bash
# 1. Pobierz pliki wdrozeniowe (wystarcza dwa)
mkdir -p /opt/chemman && cd /opt/chemman
curl -O https://raw.githubusercontent.com/blackemperor84/ChemMan/master/docker-compose.yml
curl -O https://raw.githubusercontent.com/blackemperor84/ChemMan/master/.env.docker.example

# 2. Przygotuj konfiguracje
cp .env.docker.example .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
nano .env          # uzupelnij POSTGRES_PASSWORD i CHEM_MAN_ADMIN_PASSWORD

# 3. Start
docker compose up -d

# 4. Sprawdz
docker compose ps
docker compose logs -f app
```

> **Uruchamiaj compose w osobnym katalogu (`/opt/chemman`), nigdy w kopii
> roboczej repozytorium.** `docker compose` czyta plik `.env` z katalogu
> biezacego, a w repozytorium lezy juz deweloperski `.env`. Compose po cichu
> uzyje go zamiast konfiguracji wdrozeniowej: bez `COMPOSE_PROFILES` nie wstana
> `db` ani `redis`, a `DATABASE_URL` z `localhost` w kontenerze wskazuje na sam
> kontener, nie na hosta. Krok 2 (`cp .env.docker.example .env`) nadpisalby
> przy okazji deweloperski `.env`.

Aplikacja slucha na `127.0.0.1:8000`. Skieruj na nia nginx z TLS —
patrz [Reverse proxy](#reverse-proxy-nginx) i [SSL/TLS](#ssltls).

> **Bez HTTPS nie zalogujesz sie.** W konfiguracji produkcyjnej
> `SESSION_COOKIE_SECURE=True`, wiec przegladarka nie odesle ciasteczka sesji
> po zwyklym HTTP.

Migracje bazy wykonuja sie automatycznie przy starcie kontenera. Konto `admin`
zakladane jest przy pierwszym uruchomieniu, jesli ustawiono
`CHEM_MAN_ADMIN_PASSWORD`.

> **Po pierwszym zalogowaniu usun `CHEM_MAN_ADMIN_PASSWORD` z `.env`.** Zmienna
> sluzy wylacznie do ZALOZENIA konta, nie do jego uzywania — aplikacja startuje
> i dziala normalnie bez niej. Kolejny `docker compose up -d` po prostu pominie
> krok zakladania konta.

### Import danych (CLP i SVHC)

**Wymagany krok — kontener sam tego nie robi.** Po pierwszym uruchomieniu baza
ma poprawna strukture, ale tabele CLP i SVHC sa puste, wiec wykrywanie CMR/SVHC
nie ma na czym pracowac. Pliki `substancje_baza.xlsx` i `svhc.xlsx` sa
w obrazie, wiec import uruchamia sie bez kopiowania czegokolwiek na serwer:

```bash
docker compose exec app python import_excel.py    # 4400 substancji CLP
docker compose exec app python import_svhc.py     # 1029 substancji SVHC
```

Weryfikacja:

```bash
docker compose exec -T db psql -U chemman -d chemman -tAc \
  "SELECT (SELECT count(*) FROM excel_source_substances) AS clp,
          (SELECT count(*) FROM svhc_substances) AS svhc,
          (SELECT count(*) FROM users) AS uzytkownicy"
```

Import jest idempotentny w tym sensie, ze mozna go powtorzyc po aktualizacji
list CLP/SVHC. Aktualizacje samych list opisuje `MAINTENANCE.md`.

### Aktualizacja

```bash
cd /opt/chemman
docker compose pull        # pobiera nowy obraz
docker compose up -d       # restart; migracje wykonaja sie same
```

Zrob backup bazy przed aktualizacja — patrz [Backup](#backup-i-przywracanie).
Aby przypiac konkretna wersje zamiast `latest`, ustaw w `docker-compose.yml`
`image: ghcr.io/blackemperor84/chemman:v2.4.1`.

### Zewnetrzne uslugi (wlasny PostgreSQL / Redis)

Uslugi `db` i `redis` naleza do profilu compose `bundled`, wlaczanego wpisem
`COMPOSE_PROFILES=bundled` w `.env`. Aby uzyc wlasnych serwerow:

1. usun (lub zakomentuj) `COMPOSE_PROFILES` w `.env`,
2. ustaw **obie** zmienne:

```
DATABASE_URL=postgresql://uzytkownik:haslo@host:5432/chemman
RATELIMIT_STORAGE_URL=redis://host:6379
```

3. uruchom normalnie — wystartuje wylacznie kontener aplikacji:

```bash
docker compose up -d
```

> **`RATELIMIT_STORAGE_URL` jest obowiazkowe przy wlasnej bazie.** Domyslna
> wartosc wskazuje na kontener `redis`, ktory bez profilu `bundled` nie istnieje.
> Gdy aplikacja nie moze polaczyc sie z Redisem, `flask-limiter` zwraca **500 przy
> kazdym zapytaniu objetym limitem — w tym na `/login`**, wiec logowanie przestaje
> dzialac. Kontener zatrzyma sie na starcie z czytelnym komunikatem, zamiast
> wystawiac niedzialajaca aplikacje.
>
> Nie masz Redisa? Ustaw `RATELIMIT_STORAGE_URL=memory://`. Dziala, ale kazdy
> worker gunicorna trzyma wlasne liczniki, wiec przy `GUNICORN_WORKERS=3`
> limit „10/min" zachowuje sie jak 30/min.

> **Baza zbudowana wczesniej przez `db.create_all()`** nie ma tabeli
> `alembic_version` i automatyczna migracja na niej padnie
> (`table locations already exists`). Trzeba ja raz oznaczyc `flask db stamp` —
> procedura w sekcji *Migracje bazy danych* w `MAINTENANCE.md`. Do czasu
> oznaczenia startuj z `RUN_MIGRATIONS=0`.

Przy zewnetrznej bazie polecenia z `docker compose exec db ...` w tym
przewodniku nie zadzialaja (uslugi `db` nie ma). Uzywaj `pg_dump`/`psql`
bezposrednio na swoim serwerze bazy.

### Dane trwale

Trzy wolumeny Dockera przezywaja aktualizacje obrazu:

| Wolumen w `docker-compose.yml` | Zawartosc | Punkt montowania |
|---|---|---|
| `chemman_pgdata` | baza PostgreSQL | `/var/lib/postgresql/data` |
| `chemman_uploads` | zalaczniki (karty SDS) | `/app/instance/uploads` |
| `chemman_logs` | logi aplikacji | `/app/logs` |

> Docker poprzedza nazwy wolumenow nazwa projektu, czyli nazwa katalogu.
> Przy wdrozeniu w `/opt/chemman` faktyczne nazwy to `chemman_chemman_pgdata`
> itd. Sprawdz swoje: `docker volume ls | grep chemman`.

### Przydatne polecenia

```bash
docker compose logs -f app                      # logi aplikacji
docker compose ps                               # stan uslug
docker compose restart app                      # restart samej aplikacji
docker compose exec app flask db current        # aktualna rewizja bazy
docker compose exec app python update_admin_password.py   # zmiana hasla admina
docker compose down                             # zatrzymanie (wolumeny zostaja)
```

> `docker compose down -v` **kasuje wolumeny razem z baza i zalacznikami.**
> Nie uzywaj go na produkcji.

---

## Reverse proxy (nginx)

Kontener wystawia aplikacje wylacznie na `127.0.0.1:8000`. Ruch z sieci ma isc
przez nginx na hoscie, ktory konczy TLS.

Utworz `/etc/nginx/sites-available/chemman`:

```nginx
# Przekierowanie HTTP na HTTPS
server {
    listen 80;
    server_name twoja-domena.com www.twoja-domena.com;

    return 301 https://$server_name$request_uri;
}

# Serwer HTTPS
server {
    listen 443 ssl http2;
    server_name twoja-domena.com www.twoja-domena.com;

    # Konfiguracja SSL (zaktualizuj sciezki do certyfikatow)
    ssl_certificate /etc/ssl/certs/twoja-domena.crt;
    ssl_certificate_key /etc/ssl/private/twoja-domena.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Nagłowki bezpieczenstwa
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    access_log /var/log/nginx/chemman_access.log;
    error_log /var/log/nginx/chemman_error.log;

    # Maksymalny rozmiar uploadu (karty SDS; aplikacja przyjmuje do 16 MB)
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

> **Nie dodawaj `location /static/` z `alias` na sciezke hosta.** Pliki statyczne
> sa w obrazie, a nie na dysku serwera — aplikacja serwuje je sama.

Wlaczenie:

```bash
sudo ln -s /etc/nginx/sites-available/chemman /etc/nginx/sites-enabled/
sudo nginx -t                  # test konfiguracji
sudo systemctl reload nginx
```

> **`X-Forwarded-For` a limity zapytan.** Compose ustawia
> `TRUSTED_PROXY_COUNT=1`, czyli „przede mna stoi dokladnie jeden proxy".
> Ta wartosc jest poprawna dla ukladu powyzej. Jesli wystawiasz port 8000
> bezposrednio do sieci, ustaw `TRUSTED_PROXY_COUNT=0` w `.env` — inaczej
> naglowek `X-Forwarded-For` mozna podrobic i obejsc limity logowania.
> Przy dwoch warstwach proxy (np. CDN + nginx) ustaw `2`.

---

## SSL/TLS

### Let's Encrypt (zalecane)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d twoja-domena.com -d www.twoja-domena.com

# Auto-odnowienie jest juz wlaczone przez certbot
sudo systemctl status certbot.timer
```

### Certyfikat komercyjny

1. Wygeneruj CSR:
   `openssl req -new -newkey rsa:2048 -nodes -keyout twoja-domena.key -out twoja-domena.csr`
2. Przeslij CSR do CA, odbierz certyfikat.
3. Wskaz pliki w `ssl_certificate` / `ssl_certificate_key` i przeladuj nginx.

---

## Backup i przywracanie

Do zabezpieczenia sa dwie rzeczy: **baza** i **zalaczniki SDS**. Obrazu ani
konfiguracji nie trzeba backupowac — obraz pobiera sie z rejestru, a `.env`
i `docker-compose.yml` to dwa male pliki (warto je trzymac w bezpiecznym miejscu,
bo `.env` zawiera hasla).

### Skrypt backupu

`/opt/chemman/backup.sh`:

```bash
#!/bin/bash
# Backup bazy i zalacznikow ChemMana. Uruchamiac z katalogu wdrozenia.
set -euo pipefail

BACKUP_DIR="/backups/chemman"
DEPLOY_DIR="/opt/chemman"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
cd "$DEPLOY_DIR"

# Baza danych
docker compose exec -T db pg_dump -U chemman chemman \
    | gzip > "$BACKUP_DIR/chemman_db_$DATE.sql.gz"

# Zalaczniki SDS (z wolumenu, przez kontener aplikacji)
docker compose exec -T app tar -czf - -C /app/instance/uploads . \
    > "$BACKUP_DIR/chemman_uploads_$DATE.tar.gz"

# Zachowaj ostatnie 30 dni
find "$BACKUP_DIR" -name 'chemman_*_*.gz' -mtime +30 -delete

echo "Backup ukonczony: $DATE"
```

```bash
chmod +x /opt/chemman/backup.sh

# Codziennie o 2:00
sudo crontab -e
# 0 2 * * * /opt/chemman/backup.sh >> /var/log/chemman-backup.log 2>&1
```

### Przywracanie

```bash
cd /opt/chemman

# Baza — UWAGA: nadpisuje biezace dane
gunzip -c /backups/chemman/chemman_db_20260901_020000.sql.gz \
    | docker compose exec -T db psql -U chemman -d chemman

# Zalaczniki
docker compose exec -T app tar -xzf - -C /app/instance/uploads \
    < /backups/chemman/chemman_uploads_20260901_020000.tar.gz

docker compose restart app
```

> **Przetestuj przywracanie zanim bedzie potrzebne.** Backup, ktorego nigdy nie
> odtworzono, jest zalozeniem, nie zabezpieczeniem.

---

## Monitoring i utrzymanie

### Logi

```bash
docker compose logs -f app          # biezace logi aplikacji
docker compose logs --tail=100 db   # logi PostgreSQL
docker compose ps                   # stan i restarty uslug
```

Logi aplikacji trafiaja rowniez do wolumenu `chemman_logs` (`/app/logs`
w kontenerze):

```bash
docker compose exec app tail -f /app/logs/chem_man.log
```

### Health check

Aplikacja odpowiada `200` na `/login` bez uwierzytelnienia — to najprostszy
sygnal, ze proces zyje i ma dostep do bazy oraz Redisa.

`/opt/chemman/health_check.sh`:

```bash
#!/bin/bash
CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/login || echo 000)
if [ "$CODE" != "200" ]; then
    echo "[$(date)] BLAD: /login zwrocilo $CODE"
    exit 1
fi
```

```bash
# Co 5 minut
*/5 * * * * /opt/chemman/health_check.sh >> /var/log/chemman-health.log 2>&1
```

> Kod `500` na `/login` przy dzialajacym kontenerze prawie zawsze oznacza
> niedostepny Redis — patrz [Rozwiazywanie problemow](#rozwiazywanie-problemow).

### Miejsce na dysku

```bash
docker system df                    # ile zajmuja obrazy i wolumeny
docker image prune -f               # usun nieuzywane warstwy po aktualizacjach
df -h /var/lib/docker
```

`docker image prune` jest bezpieczne — nie rusza wolumenow z danymi.

### Harmonogram

| Czestotliwosc | Czynnosc |
|---|---|
| Codziennie | Przejrzyj logi pod katem bledow; sprawdz miejsce na dysku |
| Co tydzien | Sprawdz, czy backupy powstaja i maja sensowny rozmiar; `docker compose pull` z aktualizacjami systemu hosta |
| Co miesiac | Przetestuj przywracanie z backupu; przejrzyj konta uzytkownikow |
| Co kwartal | Przeglad bezpieczenstwa; sprawdz waznosc certyfikatu (jesli nie auto-odnawiany) |

---

## Rozwiazywanie problemow

Pierwsze polecenie przy kazdym problemie:

```bash
docker compose logs --tail=50 app
```

### Kontener nie startuje

| Objaw w logach | Przyczyna | Rozwiazanie |
|---|---|---|
| `ustaw SECRET_KEY w pliku .env` | brak `SECRET_KEY` | uzupelnij `.env` |
| `table locations already exists` | baza z `db.create_all()`, bez `alembic_version` | `flask db stamp` — patrz `MAINTENANCE.md`; tymczasowo `RUN_MIGRATIONS=0` |
| kontener czeka w nieskonczonosc na baze | zly `DATABASE_URL` albo brak profilu `bundled` | sprawdz `.env` |
| wstal tylko `app`, brak `db`/`redis` | brak `COMPOSE_PROFILES=bundled` | dopisz do `.env` albo ustaw `DATABASE_URL` i `RATELIMIT_STORAGE_URL` |

Jesli compose zachowuje sie tak, jakby ignorowal `.env` — sprawdz, czy nie
uruchamiasz go w katalogu repozytorium zamiast w `/opt/chemman`.

### 500 na kazdej stronie z limitem (w tym `/login`)

Aplikacja nie ma polaczenia z Redisem. Sprawdz:

```bash
docker compose ps redis
docker compose exec app python -c "import os; print(os.environ['RATELIMIT_STORAGE_URL'])"
```

Przy wlasnej bazie `RATELIMIT_STORAGE_URL` jest obowiazkowe.

### Nie moge sie zalogowac, formularz „przeladowuje sie" bez bledu

Brak HTTPS. Produkcyjna konfiguracja ustawia `SESSION_COOKIE_SECURE=True`, wiec
przegladarka nie odsyla ciasteczka sesji po HTTP. Skonfiguruj TLS w nginx.

### Zapomniane haslo administratora

```bash
docker compose exec app python update_admin_password.py
```

### Wszyscy uzytkownicy dziela jeden limit zapytan

Aplikacja widzi adres proxy zamiast klienta. Sprawdz `TRUSTED_PROXY_COUNT`
(1 dla jednego nginxa) i czy nginx przekazuje `X-Forwarded-For`.

### Brak substancji CLP/SVHC w wyszukiwarce

Nie wykonano [importu danych](#import-danych-clp-i-svhc).

### Blad polaczenia z baza

```bash
docker compose exec db psql -U chemman -d chemman -c "SELECT version();"
docker compose exec app flask db current
```

---

## Listy kontrolne

### Bezpieczenstwo

- [ ] `SECRET_KEY` losowy, unikalny dla tego wdrozenia
- [ ] `.env` ma uprawnienia `600` i nie jest w repozytorium
- [ ] `CHEM_MAN_ADMIN_PASSWORD` usuniete z `.env` po pierwszym logowaniu
- [ ] HTTPS wymuszony, HTTP przekierowuje na HTTPS
- [ ] Certyfikat wazny i odnawiany automatycznie
- [ ] Port 8000 nie jest wystawiony poza `127.0.0.1`
- [ ] `TRUSTED_PROXY_COUNT` zgodne z faktyczna liczba proxy
- [ ] Firewall przepuszcza tylko 80/443
- [ ] Backupy dzialaja i przetestowano przywracanie
- [ ] Konta uzytkownikow maja uprawnienia adekwatne do roli

### Przed uruchomieniem produkcyjnym

- [ ] `docker compose ps` — wszystkie uslugi `running`
- [ ] Zaimportowano CLP (4400) i SVHC (1029)
- [ ] Logowanie kontem `admin` dziala przez domene po HTTPS
- [ ] Wyszukiwanie zwraca wyniki
- [ ] Eksport (CSV/XLSX) dziala
- [ ] Upload karty SDS dziala i plik przezywa `docker compose restart app`
- [ ] Backup wykonal sie co najmniej raz i da sie odtworzyc
- [ ] Health check zaplanowany w cronie

---

**Koniec przewodnika.** Utrzymanie biezace (migracje, aktualizacja list CLP/SVHC)
opisuje [MAINTENANCE.md](MAINTENANCE.md). Instalacja deweloperska —
[INSTALLATION.md](INSTALLATION.md).
