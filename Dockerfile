# ChemMan - obraz produkcyjny
#
# Budowanie:  docker build -t chemman:local .
# Uruchomienie: patrz docker-compose.yml
#
# Obraz zawiera aplikacje i wszystkie zaleznosci natywne (psycopg2, numpy,
# pandas, lxml, pillow, cryptography), dzieki czemu wdrozenie na serwerze nie
# wymaga kompilacji ani konkretnej wersji Pythona.

# ---------------------------------------------------------------------------
# Etap 1: budowanie zaleznosci w izolowanym virtualenv
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# build-essential jest potrzebny tylko wtedy, gdy dla ktorejs zaleznosci
# zabraknie gotowego kola manylinux. W etapie finalnym juz go nie ma.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-prod.txt

# ---------------------------------------------------------------------------
# Etap 2: obraz uruchomieniowy
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# libpq5 - biblioteka kliencka PostgreSQL wymagana przez psycopg2 w czasie pracy.
# curl - uzywany przez HEALTHCHECK ponizej.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Aplikacja nie potrzebuje roota. UID/GID sa stale, zeby prawa do wolumenow
# byly przewidywalne na hoscie.
RUN groupadd --gid 10001 chemman \
    && useradd --uid 10001 --gid chemman --create-home --shell /usr/sbin/nologin chemman

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    GUNICORN_BIND=0.0.0.0:8000

WORKDIR /app
COPY --chown=chemman:chemman . /app

# Katalogi trwale: zalaczniki SDS i logi. W docker-compose.yml sa podmontowane
# jako wolumeny — bez tego pliki znikaja przy kazdej aktualizacji obrazu.
RUN mkdir -p /app/instance/uploads/sds /app/logs \
    && chown -R chemman:chemman /app/instance /app/logs \
    && chmod +x /app/docker-entrypoint.sh

USER chemman

EXPOSE 8000

# Aplikacja nie ma dedykowanego /health, wiec sprawdzamy strone logowania —
# jej poprawne 200 oznacza dzialajacy Flask, szablony i sesje.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/login || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"]
