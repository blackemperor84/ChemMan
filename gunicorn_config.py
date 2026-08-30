"""
Konfiguracja gunicorna dla ChemMana.

Uzycie:
    gunicorn -c gunicorn_config.py wsgi:app

Plik byl juz opisany w DEPLOYMENT_GUIDE.md i w docstringu wsgi.py, ale nie
istnial w repozytorium — jednostka systemd z przewodnika nie wystartowalaby.
"""
import multiprocessing
import os

# --- Adres nasluchu ---------------------------------------------------------
# Domyslnie tylko localhost: ruch z zewnatrz ma isc przez nginx.
# W kontenerze ustaw GUNICORN_BIND=0.0.0.0:8000 (robi to docker-compose.yml).
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')

# --- Procesy robocze --------------------------------------------------------
# Rekomendacja gunicorna: (2 x rdzenie) + 1. Mozna nadpisac zmienna srodowiskowa,
# bo w kontenerze liczba rdzeni hosta bywa wieksza niz przydzielony limit CPU.
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
threads = int(os.environ.get('GUNICORN_THREADS', '2'))

# Import aplikacji przed forkiem — mniejsze zuzycie pamieci i szybszy start.
preload_app = True

# --- Limity czasu -----------------------------------------------------------
# Import baz CLP/SVHC (4400+ rekordow z pliku Excel) potrafi trwac dlugo,
# dlatego timeout jest wyrazie wiekszy niz domyslne 30 s.
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
graceful_timeout = 30
keepalive = 5

# --- Recykling workerow -----------------------------------------------------
# Ogranicza skutki ewentualnych wyciekow pamieci (pandas/openpyxl przy imporcie).
max_requests = 1000
max_requests_jitter = 100

# --- Logi -------------------------------------------------------------------
# '-' kieruje logi na stdout/stderr, co jest wlasciwe dla kontenerow i systemd.
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# X-Forwarded-* przyjmujemy tylko od proxy; wlasciwa obsluga adresu klienta
# jest w app.py pod zmienna TRUSTED_PROXY_COUNT.
forwarded_allow_ips = os.environ.get('GUNICORN_FORWARDED_ALLOW_IPS', '127.0.0.1')

proc_name = 'chemman'
