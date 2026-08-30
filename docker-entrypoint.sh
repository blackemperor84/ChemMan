#!/bin/sh
# Punkt wejscia kontenera ChemMan.
#
# 1. czeka na baze danych,
# 2. wykonuje migracje,
# 3. opcjonalnie zaklada konto administratora,
# 4. oddaje sterowanie polecenu z CMD (domyslnie gunicorn).
set -eu

echo "[entrypoint] ChemMan - start"

if [ "${FLASK_ENV:-}" != "production" ]; then
    echo "[entrypoint] UWAGA: FLASK_ENV=${FLASK_ENV:-<puste>} — konfiguracja NIE jest produkcyjna."
fi

# --- 1. Czekanie na baze ---------------------------------------------------
# Bez tego pierwszy start obok swiezego kontenera PostgreSQL wywala sie na
# wyscigu: aplikacja startuje szybciej, niz baza przyjmuje polaczenia.
if [ -n "${DATABASE_URL:-}" ]; then
    echo "[entrypoint] Czekam na baze danych..."
    python <<'PYWAIT'
import os, sys, time
import sqlalchemy

url = os.environ['DATABASE_URL']
deadline = time.time() + float(os.environ.get('DB_WAIT_SECONDS', '60'))
last = None
while time.time() < deadline:
    try:
        engine = sqlalchemy.create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))
        print('[entrypoint] Baza odpowiada.')
        sys.exit(0)
    except Exception as exc:
        last = exc
        time.sleep(2)

print('[entrypoint] BLAD: baza nie odpowiedziala w wyznaczonym czasie: %s' % last,
      file=sys.stderr)
sys.exit(1)
PYWAIT
fi

# --- 1b. Czekanie na Redis -------------------------------------------------
# Nieosiagalny Redis nie psuje startu aplikacji, tylko kazde zapytanie objete
# limitem — flask-limiter zwraca wtedy 500, takze na /login. Lepiej zatrzymac
# sie tutaj z czytelnym komunikatem niz wystawic aplikacje, ktora nie pozwala
# sie zalogowac.
case "${RATELIMIT_STORAGE_URL:-}" in
  redis://*|rediss://*)
    echo "[entrypoint] Czekam na Redis..."
    python <<'PYREDIS'
import os, sys, time
import redis

url = os.environ['RATELIMIT_STORAGE_URL']
deadline = time.time() + float(os.environ.get('REDIS_WAIT_SECONDS', '30'))
last = None
while time.time() < deadline:
    try:
        redis.Redis.from_url(url, socket_connect_timeout=3).ping()
        print('[entrypoint] Redis odpowiada.')
        sys.exit(0)
    except Exception as exc:
        last = exc
        time.sleep(2)

print('[entrypoint] BLAD: Redis (%s) nie odpowiada: %s' % (url, last), file=sys.stderr)
print('[entrypoint] Ustaw RATELIMIT_STORAGE_URL=memory:// albo uruchom Redisa.',
      file=sys.stderr)
sys.exit(1)
PYREDIS
    ;;
  *)
    echo "[entrypoint] RATELIMIT_STORAGE_URL=${RATELIMIT_STORAGE_URL:-<puste>} — pomijam sprawdzenie Redisa."
    ;;
esac

# --- 2. Migracje -----------------------------------------------------------
# Pusta baza zostanie zbudowana od migracji bazowej `chemman_baseline`.
# UWAGA: baza zbudowana wczesniej przez db.create_all() NIE ma tabeli
# alembic_version i `upgrade` na niej padnie ("table locations already exists").
# Taka baze trzeba raz oznaczyc: flask db stamp <rewizja> — patrz MAINTENANCE.md.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[entrypoint] Migracje bazy danych..."
    flask db upgrade
    echo "[entrypoint] Migracje zakonczone."
else
    echo "[entrypoint] Pominieto migracje (RUN_MIGRATIONS=0)."
fi

# --- 3. Konto administratora ----------------------------------------------
# Uruchamiane tylko, gdy podano haslo. create_admin.py sam sprawdza, czy konto
# juz istnieje, i wtedy niczego nie zmienia — mozna to trzymac wlaczone.
if [ -n "${CHEM_MAN_ADMIN_PASSWORD:-}" ]; then
    echo "[entrypoint] Sprawdzam konto administratora..."
    python create_admin.py || echo "[entrypoint] create_admin.py zglosil blad — pomijam."
fi

echo "[entrypoint] Uruchamiam: $*"
exec "$@"
