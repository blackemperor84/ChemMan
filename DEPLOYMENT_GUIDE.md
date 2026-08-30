# Przewodnik Wdrożeniowy Chem-Man

Kompletny przewodnik wdrażania aplikacji do zarządzania substancjami chemicznymi Chem-Man w środowisku produkcyjnym.

---

## Spis Treści

0. [Wdrożenie przez Docker (zalecane)](#wdrozenie-przez-docker-zalecane)
1. [Wymagania Wstępne](#wymagania-wstępne)
2. [Konfiguracja Serwera](#konfiguracja-serwera)
3. [Instalacja Bazy Danych (PostgreSQL)](#instalacja-bazy-danych-postgresql)
4. [Instalacja Aplikacji](#instalacja-aplikacji)
5. [Konfiguracja](#konfiguracja)
6. [Import Danych](#import-danych)
7. [Wdrożenie Produkcyjne (Serwer WSGI)](#wdrożenie-produkcyjne-serwer-wsgi)
8. [Konfiguracja Reverse Proxy (nginx/Apache)](#konfiguracja-reverse-proxy)
9. [Konfiguracja SSL/TLS](#konfiguracja-ssltls)
10. [Strategia Backupu](#strategia-backupu)
11. [Monitoring i Utrzymanie](#monitoring-i-utrzymanie)
12. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

---

## Wdrozenie przez Docker (zalecane)

Najszybsza sciezka wdrozenia. Serwer nie kompiluje niczego — pobiera gotowy obraz
z GitHub Container Registry. Rozdzialy 2-7 ponizej opisuja instalacje reczna
(bez Dockera) i przy tym wariancie mozna je pominac; nadal potrzebne sa
[reverse proxy](#konfiguracja-reverse-proxy), [SSL/TLS](#konfiguracja-ssltls)
i [backup](#strategia-backupu).

### Wymagania

- Docker Engine 24+ z wtyczka `docker compose`
- ok. 2 GB RAM i 5 GB miejsca na dysku

### Pierwsze uruchomienie

```bash
# 1. Pobierz pliki wdrozeniowe (wystarcza trzy)
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

Aplikacja slucha na `127.0.0.1:8000`. Skieruj na nia nginx z TLS —
patrz [Reverse Proxy](#konfiguracja-reverse-proxy) i [SSL/TLS](#konfiguracja-ssltls).

> **Bez HTTPS nie zalogujesz sie.** W konfiguracji produkcyjnej
> `SESSION_COOKIE_SECURE=True`, wiec przegladarka nie odesle ciasteczka sesji
> po zwyklym HTTP.

Migracje bazy wykonuja sie automatycznie przy starcie kontenera. Konto `admin`
zakladane jest przy pierwszym uruchomieniu, jesli ustawiono
`CHEM_MAN_ADMIN_PASSWORD`. **Po pierwszym zalogowaniu usun te zmienna z `.env`.**

### Aktualizacja

```bash
cd /opt/chemman
docker compose pull        # pobiera nowy obraz
docker compose up -d       # restart; migracje wykonaja sie same
```

Zrob backup bazy przed aktualizacja — patrz [Strategia Backupu](#strategia-backupu).
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

### Dane trwale

Trzy wolumeny Dockera przezywaja aktualizacje obrazu:

| Wolumen | Zawartosc |
|---|---|
| `chemman_pgdata` | baza PostgreSQL |
| `chemman_uploads` | zalaczniki (karty SDS) |
| `chemman_logs` | logi aplikacji |

Backup bazy z dzialajacego zestawu:

```bash
docker compose exec -T db pg_dump -U chemman chemman > backup_$(date +%F).sql
```

### Przydatne polecenia

```bash
docker compose logs -f app                      # logi aplikacji
docker compose restart app                      # restart samej aplikacji
docker compose exec app flask db current        # aktualna rewizja bazy
docker compose exec app python update_admin_password.py   # zmiana hasla admina
docker compose down                             # zatrzymanie (wolumeny zostaja)
```

---

## Wymagania Wstępne

### Wymagania Serwerowe

- **System Operacyjny:** Windows Server 2019/2022 lub Linux (Ubuntu 20.04/22.04, CentOS 8+)
- **RAM:** Minimum 4GB, zalecane 8GB
- **Dysk:** Minimum 20GB (włącznie z bazą danych i logami)
- **CPU:** Minimum 2 rdzenie, zalecane 4 rdzenie

### Wymagania Oprogramowania

- **Python:** 3.11 lub wyższy
- **PostgreSQL:** 14 lub wyższy (zalecane 18)
- **pip:** Najnowsza wersja
- **virtualenv:** Do izolacji środowiska Python

### Wymagania Sieciowe

- **Port 5432:** Baza danych PostgreSQL (tylko wewnętrzny)
- **Port 80:** HTTP (przekierowanie na HTTPS)
- **Port 443:** HTTPS (dostęp publiczny)
- **Port 5000:** Serwer deweloperski Flask (tylko wewnętrzny, nie dla produkcji)

---

## Konfiguracja Serwera

### 1. Aktualizacja Systemu (Linux)

```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# LUB
sudo yum update -y  # CentOS/RHEL
```

### 2. Instalacja Zależności Systemowych

#### Ubuntu/Debian:
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx
```

#### CentOS/RHEL:
```bash
sudo yum install -y python3 python3-pip postgresql-server postgresql-contrib nginx
```

#### Windows Server:
- Pobierz i zainstaluj Python 3.13+ z [python.org](https://www.python.org/downloads/)
- Pobierz i zainstaluj PostgreSQL 18 z [postgresql.org](https://www.postgresql.org/download/windows/)
- Pobierz i zainstaluj nginx z [nginx.org](http://nginx.org/en/download.html)

---

## Instalacja Bazy Danych (PostgreSQL)

### Instalacja Linux

#### 1. Inicjalizacja PostgreSQL (tylko przy pierwszej instalacji)

```bash
# Ubuntu/Debian - automatycznie zainicjalizowane podczas instalacji
sudo systemctl start postgresql
sudo systemctl enable postgresql

# CentOS/RHEL - wymagana ręczna inicjalizacja
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Utworzenie Bazy Danych i Użytkownika

```bash
sudo -u postgres psql

# W terminalu PostgreSQL:
CREATE DATABASE chemman_prod;
CREATE USER chemman_user WITH PASSWORD 'SILNE_HASŁO_TUTAJ';
GRANT ALL PRIVILEGES ON DATABASE chemman_prod TO chemman_user;
\q
```

### Instalacja Windows

#### 1. Instalacja PostgreSQL

- Uruchom instalator PostgreSQL
- Ustaw silne hasło dla superużytkownika `postgres`
- Zaakceptuj domyślny port (5432)

#### 2. Utworzenie Bazy Danych i Użytkownika

Używając pgAdmin lub linii poleceń:

```sql
-- Otwórz okno zapytania SQL i wykonaj:
CREATE DATABASE chemman_prod;
CREATE USER chemman_user WITH PASSWORD 'SILNE_HASŁO_TUTAJ';
GRANT ALL PRIVILEGES ON DATABASE chemman_prod TO chemman_user;
```

### Zabezpieczenie Bazy Danych

Edytuj pliki `postgresql.conf` i `pg_hba.conf`:

```bash
# Linux:
sudo nano /etc/postgresql/18/main/postgresql.conf

# Ustaw:
listen_addresses = 'localhost'  # Akceptuj tylko połączenia lokalne
max_connections = 100
```

Edytuj `pg_hba.conf`:
```
# TYP   BAZA DANYCH     UŻYTKOWNIK      ADRES                   METODA
local   chemman_prod    chemman_user                            md5
host    chemman_prod    chemman_user    127.0.0.1/32            md5
```

Zrestartuj PostgreSQL:
```bash
sudo systemctl restart postgresql  # Linux
# Windows: Zrestartuj usługę przez Panel Usług
```

---

## Instalacja Aplikacji

### 1. Utworzenie Użytkownika Aplikacji (tylko Linux)

```bash
sudo useradd -m -s /bin/bash chemman
sudo su - chemman
```

### 2. Skopiowanie Plików Aplikacji

```bash
# Utwórz katalog
mkdir -p /opt/chemman  # Linux
# LUB
mkdir C:\chemman  # Windows

# Skopiuj wszystkie pliki aplikacji do tego katalogu
cd /opt/chemman  # Linux
cd C:\chemman  # Windows
```

### 3. Utworzenie Wirtualnego Środowiska Python

```bash
python3 -m venv venv

# Aktywuj środowisko
source venv/bin/activate  # Linux
venv\Scripts\activate  # Windows
```

### 4. Instalacja Zależności Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Konfiguracja

### 1. Utworzenie Pliku Konfiguracyjnego Produkcyjnego

Utwórz plik `.env` w głównym katalogu aplikacji:

```bash
# Konfiguracja Bazy Danych
DATABASE_URL=postgresql://chemman_user:SILNE_HASŁO_TUTAJ@localhost:5432/chemman_prod

# Konfiguracja Flask
FLASK_ENV=production
SECRET_KEY=WYGENERUJ_LOSOWY_KLUCZ_TUTAJ
FLASK_DEBUG=0

# Użytkownik Admin (pierwsze logowanie)
CHEM_MAN_ADMIN_PASSWORD=ZMIEŃ_TO_NATYCHMIAST

# Rate Limiting
# Wspoldzielony magazyn licznikow. Bez tego kazdy worker gunicorna ma wlasne
# liczniki i faktyczny limit jest ich wielokrotnoscia.
RATELIMIT_STORAGE_URL=redis://localhost:6379

# Liczba zaufanych odwrotnych proxy (nginx). Bez tego aplikacja widzi adres
# proxy zamiast klienta i WSZYSCY uzytkownicy dziela jeden limit zapytan.
# Ustaw 1 dla typowej konfiguracji z jednym nginx-em.
# UWAGA: nie ustawiaj > 0, jesli aplikacja jest wystawiona bezposrednio —
# naglowek X-Forwarded-For mozna wtedy podrobic.
TRUSTED_PROXY_COUNT=1

# Nagłówki Bezpieczeństwa
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### 2. Generowanie Klucza Sekretnego

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Skopiuj wynik do `SECRET_KEY` w pliku `.env`.

### 3. Ustawienie Uprawnień Plików (Linux)

```bash
chmod 600 .env  # Tylko właściciel może odczytać
chown chemman:chemman .env
```

---

## Import Danych

### 1. Utworzenie Tabel w Bazie Danych

```bash
python -c "from app import create_app; from models import db; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); db.create_all(); print('Tabele utworzone')"
```

### 2. Import Bazy CLP (4400 substancji)

```bash
python import_excel.py
```

Oczekiwany wynik: `Gotowe! Zaimportowano 4400 substancji!`

### 3. Import Bazy SVHC (492 substancje)

```bash
python import_svhc.py
```

Oczekiwany wynik: `Gotowe! Zaimportowano 492 substancji SVHC!`

### 4. Utworzenie Użytkownika Admin

```bash
python create_admin.py
```

Oczekiwany wynik: `Admin user created successfully!`

### 5. Weryfikacja Importu

```bash
python -c "from app import create_app; from models import db, ExcelSourceSubstance, SVHCSubstance, User; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); print(f'CLP: {ExcelSourceSubstance.query.count()}'); print(f'SVHC: {SVHCSubstance.query.count()}'); print(f'Użytkownicy: {User.query.count()}')"
```

Oczekiwany wynik:
```
CLP: 4400
SVHC: 492
Użytkownicy: 1
```

---

## Wdrożenie Produkcyjne (Serwer WSGI)

### Opcja 1: Gunicorn (Linux - Zalecane)

#### 1. Instalacja zaleznosci produkcyjnych

```bash
pip install -r requirements-prod.txt
```

Plik `requirements-prod.txt` zaciaga cale `requirements.txt` oraz dwie zaleznosci
potrzebne wylacznie na serwerze: `gunicorn` i `redis` (klient dla
`RATELIMIT_STORAGE_URL`). Sa trzymane osobno, bo gunicorn nie dziala na Windows,
a srodowisko deweloperskie tego projektu jest windowsowe.

> **Nie instaluj gunicorna recznie** (`pip install gunicorn`). Wersja bylaby
> nieprzypieta i nieodtwarzalna. Uwaga takze na `redis`: `flask-limiter`
> wymaga `redis<7.0.0`, dlatego wersja jest przypieta w pliku.

#### 2. Konfiguracja Gunicorn

Repozytorium zawiera gotowy `gunicorn_config.py` w katalogu glownym — ponizszy
listing opisuje jego zawartosc i mozna go uzyc bez zmian. Wartosci sterowane sa
zmiennymi srodowiskowymi (`GUNICORN_WORKERS`, `GUNICORN_BIND`, `GUNICORN_TIMEOUT`).

<details>
<summary>Alternatywnie: wlasny plik konfiguracyjny</summary>

Utwórz plik `gunicorn_config.py`:

```python
# Plik konfiguracyjny Gunicorn
bind = "127.0.0.1:8000"
workers = 4  # (2 x liczba rdzeni CPU) + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logowanie
accesslog = "/var/log/chemman/access.log"
errorlog = "/var/log/chemman/error.log"
loglevel = "info"

# Bezpieczeństwo
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```
</details>

> **WAŻNE - punkt wejścia WSGI**
>
> Uruchamiaj gunicorna przez `wsgi:app`, nie przez `app:create_app()`.
> Moduł `wsgi.py` gwarantuje, że konfiguracja zostanie wybrana na podstawie
> `FLASK_ENV`. Upewnij się też, że `FLASK_ENV=production` jest widoczne dla
> procesu (w `.env` w katalogu roboczym albo w `Environment=` w usłudze systemd) -
> bez tego aplikacja wystartuje na `DevelopmentConfig`, czyli m.in. bez
> `SESSION_COOKIE_SECURE`. Przy starcie w logu pojawi się ostrzeżenie, jeśli
> `FLASK_ENV` nie jest ustawione na `production`.

#### 3. Utworzenie Usługi Systemd

Utwórz plik `/etc/systemd/system/chemman.service`:

```ini
[Unit]
Description=Aplikacja Chem-Man do Zarządzania Substancjami Chemicznymi
After=network.target postgresql.service

[Service]
Type=notify
User=chemman
Group=chemman
WorkingDirectory=/opt/chemman
Environment="PATH=/opt/chemman/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/chemman/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. Uruchomienie i Włączenie Usługi

```bash
sudo systemctl daemon-reload
sudo systemctl start chemman
sudo systemctl enable chemman
sudo systemctl status chemman
```

### Opcja 2: Waitress (Windows - Zalecane)

#### 1. Instalacja Waitress

```bash
pip install waitress
```

#### 2. Utworzenie Skryptu Startowego

Utwórz plik `start_production.py`:

```python
"""Skrypt startowy serwera produkcyjnego używający Waitress"""
from waitress import serve
from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    print("Uruchamianie Chem-Man na http://localhost:8000")
    serve(app, host='127.0.0.1', port=8000, threads=4)
```

#### 3. Utworzenie Usługi Windows

Zainstaluj NSSM (Non-Sucking Service Manager):
```bash
# Pobierz z https://nssm.cc/download
nssm install ChemMan "C:\chemman\venv\Scripts\python.exe" "C:\chemman\start_production.py"
nssm set ChemMan AppDirectory "C:\chemman"
nssm start ChemMan
```

---

## Konfiguracja Reverse Proxy

### Konfiguracja nginx (Linux i Windows)

#### 1. Utworzenie Konfiguracji nginx

Utwórz plik `/etc/nginx/sites-available/chemman` (Linux) lub `C:\nginx\conf\chemman.conf` (Windows):

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

    # Konfiguracja SSL (zaktualizuj ścieżki do certyfikatów)
    ssl_certificate /etc/ssl/certs/twoja-domena.crt;
    ssl_certificate_key /etc/ssl/private/twoja-domena.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Nagłówki Bezpieczeństwa
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logowanie
    access_log /var/log/nginx/chemman_access.log;
    error_log /var/log/nginx/chemman_error.log;

    # Maksymalny rozmiar uploadu (dla plików SDS)
    client_max_body_size 20M;

    # Proxy do Gunicorn/Waitress
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Limity czasowe
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Pliki statyczne (jeśli serwowane oddzielnie)
    location /static/ {
        alias /opt/chemman/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 2. Włączenie Strony (Linux)

```bash
sudo ln -s /etc/nginx/sites-available/chemman /etc/nginx/sites-enabled/
sudo nginx -t  # Testowanie konfiguracji
sudo systemctl restart nginx
```

#### 3. Uruchomienie nginx (Windows)

```bash
cd C:\nginx
start nginx
```

### Konfiguracja Apache (Alternatywa)

Utwórz plik `/etc/apache2/sites-available/chemman.conf`:

```apache
<VirtualHost *:80>
    ServerName twoja-domena.com
    Redirect permanent / https://twoja-domena.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName twoja-domena.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/twoja-domena.crt
    SSLCertificateKeyFile /etc/ssl/private/twoja-domena.key

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

Włącz moduły i stronę:
```bash
sudo a2enmod proxy proxy_http ssl
sudo a2ensite chemman
sudo systemctl restart apache2
```

---

## Konfiguracja SSL/TLS

### Opcja 1: Let's Encrypt (Darmowe, tylko Linux)

```bash
# Instalacja Certbot
sudo apt install certbot python3-certbot-nginx

# Uzyskanie certyfikatu
sudo certbot --nginx -d twoja-domena.com -d www.twoja-domena.com

# Auto-odnowienie (już włączone przez certbot)
sudo systemctl status certbot.timer
```

### Opcja 2: Certyfikat Komercyjny

1. Kup certyfikat SSL od CA (Comodo, DigiCert, itp.)
2. Wygeneruj CSR: `openssl req -new -newkey rsa:2048 -nodes -keyout twoja-domena.key -out twoja-domena.csr`
3. Prześlij CSR do CA, otrzymaj certyfikat
4. Zainstaluj certyfikat w konfiguracji nginx/Apache (patrz wyżej)

---

## Strategia Backupu

### 1. Backup Bazy Danych

Utwórz plik `/opt/chemman/backup_db.sh`:

```bash
#!/bin/bash
# Skrypt backupu PostgreSQL

BACKUP_DIR="/backups/chemman"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="chemman_prod"
DB_USER="chemman_user"

mkdir -p $BACKUP_DIR

# Utworzenie backupu
PGPASSWORD="SILNE_HASŁO_TUTAJ" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/chemman_$DATE.sql.gz

# Zachowaj tylko ostatnie 30 dni
find $BACKUP_DIR -name "chemman_*.sql.gz" -mtime +30 -delete

echo "Backup ukończony: chemman_$DATE.sql.gz"
```

Nadaj uprawnienia wykonywania i zaplanuj:
```bash
chmod +x /opt/chemman/backup_db.sh

# Dodaj do crona (codziennie o 2:00)
sudo crontab -e
# Dodaj linię:
0 2 * * * /opt/chemman/backup_db.sh >> /var/log/chemman/backup.log 2>&1
```

### 2. Backup Plików Aplikacji

```bash
#!/bin/bash
# Backup plików aplikacji

BACKUP_DIR="/backups/chemman"
DATE=$(date +%Y%m%d)
APP_DIR="/opt/chemman"

tar -czf $BACKUP_DIR/chemman_files_$DATE.tar.gz $APP_DIR --exclude='venv' --exclude='__pycache__' --exclude='*.pyc'

# Zachowaj tylko ostatnie 7 dni
find $BACKUP_DIR -name "chemman_files_*.tar.gz" -mtime +7 -delete
```

### 3. Przywracanie z Backupu

```bash
# Przywróć bazę danych
gunzip -c /backups/chemman/chemman_20251022.sql.gz | PGPASSWORD="HASŁO" psql -U chemman_user -h localhost chemman_prod

# Przywróć pliki
tar -xzf /backups/chemman/chemman_files_20251022.tar.gz -C /
```

---

## Monitoring i Utrzymanie

### 1. Monitoring Logów

Logi aplikacji:
- **Lokalizacja:** `/var/log/chemman/` (Linux) lub `C:\chemman\logs\` (Windows)
- **Pliki:** `chem_man.log`, `access.log`, `error.log`

Monitorowanie logów:
```bash
tail -f /var/log/chemman/chem_man.log
tail -f /var/log/chemman/error.log
```

### 2. Skrypt Health Check

Utwórz plik `health_check.py`:

```python
"""Skrypt health check dla aplikacji Chem-Man"""
import requests
import sys
from datetime import datetime

def check_health():
    try:
        # Sprawdź czy aplikacja odpowiada
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code in [200, 302]:  # 302 = przekierowanie do loginu
            print(f"[{datetime.now()}] OK: Aplikacja odpowiada")
            return 0
        else:
            print(f"[{datetime.now()}] BŁĄD: Nieoczekiwany kod statusu {response.status_code}")
            return 1
    except Exception as e:
        print(f"[{datetime.now()}] BŁĄD: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(check_health())
```

Zaplanuj health checki:
```bash
# Dodaj do crona (co 5 minut)
*/5 * * * * /opt/chemman/venv/bin/python /opt/chemman/health_check.py >> /var/log/chemman/health.log 2>&1
```

### 3. Monitoring Przestrzeni Dyskowej

```bash
# Sprawdź przestrzeń dyskową co tydzień
df -h | grep -E 'Filesystem|/$' | mail -s "Raport Przestrzeni Dyskowej" admin@twoja-domena.com
```

### 4. Monitoring Wydajności

Zainstaluj i skonfiguruj:
- **PostgreSQL:** pg_stat_statements do monitorowania zapytań
- **nginx:** Monitoruj czasy odpowiedzi poprzez logi dostępu
- **Aplikacja:** Użyj Flask-Monitor lub własnych metryk

---

## Rozwiązywanie Problemów

### Aplikacja Nie Uruchamia Się

1. **Sprawdź logi:**
   ```bash
   tail -50 /var/log/chemman/error.log
   sudo journalctl -u chemman -n 50
   ```

2. **Zweryfikuj połączenie z bazą danych:**
   ```bash
   python -c "from app import create_app; from config import ProductionConfig; app = create_app(ProductionConfig); print('Połączenie z bazą OK')"
   ```

3. **Sprawdź uprawnienia:**
   ```bash
   ls -la /opt/chemman
   # Upewnij się, że użytkownik chemman jest właścicielem plików
   ```

### Błędy Połączenia z Bazą Danych

1. **Sprawdź czy PostgreSQL działa:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Sprawdź connection string w `.env`:**
   ```bash
   grep DATABASE_URL .env
   ```

3. **Przetestuj połączenie ręcznie:**
   ```bash
   PGPASSWORD="HASŁO" psql -U chemman_user -h localhost chemman_prod -c "SELECT version();"
   ```

### Błędy nginx/Apache

1. **Sprawdź konfigurację:**
   ```bash
   sudo nginx -t
   # LUB
   sudo apache2ctl configtest
   ```

2. **Sprawdź logi błędów:**
   ```bash
   tail -50 /var/log/nginx/error.log
   ```

3. **Zweryfikuj czy proxy działa:**
   ```bash
   curl -I http://localhost:8000
   ```

### Błędy Importu

1. **Sprawdź uprawnienia plików Excel:**
   ```bash
   ls -la substancje_baza.xlsx svhc.xlsx
   ```

2. **Zweryfikuj czy tabele istnieją:**
   ```bash
   python -c "from app import create_app; from models import db; from config import ProductionConfig; app = create_app(ProductionConfig); app.app_context().push(); print(db.engine.table_names())"
   ```

---

## Lista Kontrolna Bezpieczeństwa

- [ ] PostgreSQL akceptuje tylko połączenia lokalne
- [ ] Silne hasła dla użytkownika bazy danych i konta admin
- [ ] SECRET_KEY jest losowy i bezpieczny
- [ ] HTTPS jest wymuszony (HTTP przekierowuje na HTTPS)
- [ ] Certyfikat SSL jest ważny i aktualny
- [ ] Nagłówki bezpieczeństwa skonfigurowane w nginx
- [ ] Uprawnienia plików są restrykcyjne (600 dla .env, 644 dla kodu)
- [ ] Aplikacja działa jako użytkownik bez uprawnień roota (Linux)
- [ ] Backupy bazy danych są skonfigurowane i przetestowane
- [ ] Logi są regularnie monitorowane
- [ ] Rate limiting jest włączony
- [ ] Reguły firewalla są skonfigurowane (tylko porty 80/443 otwarte)

---

## Harmonogram Utrzymania

### Codziennie
- Monitoruj logi pod kątem błędów
- Sprawdź przestrzeń dyskową

### Co tydzień
- Przejrzyj logi dostępu
- Sprawdź integralność backupów
- Aktualizuj pakiety systemowe

### Co miesiąc
- Aktualizuj zależności Python (`pip list --outdated`)
- Przejrzyj konta użytkowników
- Przetestuj przywracanie z backupu

### Co kwartał
- Audit bezpieczeństwa
- Przegląd wydajności
- Aktualizacja certyfikatów SSL (jeśli nie auto-odnawiane)

---

## Wsparcie i Aktualizacje

### Aktualizacja Aplikacji

```bash
# Zatrzymaj aplikację
sudo systemctl stop chemman  # Linux
nssm stop ChemMan  # Windows

# Backup obecnej wersji
cd /opt/chemman
tar -czf ../chemman_backup_$(date +%Y%m%d).tar.gz .

# Pobierz/skopiuj nowy kod
git pull  # jeśli używasz git

# Aktualizuj zależności
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Uruchom migracje (jeśli są)
# python migrate.py

# Zrestartuj aplikację
sudo systemctl start chemman  # Linux
nssm start ChemMan  # Windows
```

### Uzyskiwanie Pomocy

- **Logi aplikacji:** `/var/log/chemman/chem_man.log`
- **Logi PostgreSQL:** `/var/log/postgresql/`
- **Logi nginx:** `/var/log/nginx/`

---

## Lista Kontrolna Produkcyjna

Przed uruchomieniem produkcyjnym, zweryfikuj:

- [ ] Baza danych to PostgreSQL (nie SQLite)
- [ ] Zaimportowano 4400 substancji CLP
- [ ] Zaimportowano 492 substancje SVHC
- [ ] Utworzono użytkownika admin
- [ ] HTTPS działa
- [ ] Backupy są skonfigurowane
- [ ] Logi są zapisywane
- [ ] Health checki są zaplanowane
- [ ] Wszystkie testy przechodzą (`pytest tests/`)
- [ ] Aplikacja dostępna przez nazwę domeny
- [ ] Logowanie działa z danymi admin
- [ ] Funkcja wyszukiwania działa
- [ ] Funkcja eksportu działa
- [ ] Upload plików SDS działa

---

**Koniec Przewodnika Wdrożeniowego**

W razie pytań lub problemów, sprawdź logi i skonsultuj się z sekcją rozwiązywania problemów w tym przewodniku.
