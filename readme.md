# ChemMan - System Zarządzania Substancjami Chemicznymi

System do zarządzania inwentaryzacją substancji chemicznych z obsługą baz CLP i SVHC.

## Funkcje

- 📦 Zarządzanie substancjami w komórkach organizacyjnych (jednostki/działy)
- 🏢 System przypisywania użytkowników do komórek organizacyjnych z kontrolą dostępu
- 🔍 Wyszukiwanie w bazie CLP (4400+ substancji) i SVHC (aktualna lista kandydacka ECHA)
- 🌍 Dwujęzyczne nazwy (angielski/polski)
- ⚠️ Automatyczne i ręczne oznaczanie CMR i SVHC
- 📄 Wiele kart SDS na substancję z informacją o producencie
- ✏️ Edycja inline wszystkich pól substancji bezpośrednio w tabeli
- 🗄️ Aktualizacja baz danych CLP/SVHC przez interfejs web (panel admina)
- 📊 Export do CSV
- 👥 System uprawnień użytkowników (10 poziomów) z kontrolą na poziomie komórek
- 📜 Dziennik zmian (audit log)

## Technologie

- **Backend:** Flask (Python 3.11+)
- **Baza danych:** PostgreSQL 14+ (produkcja), SQLite (testy)
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Testing:** pytest (363 testy, 84% pokrycia kodu)

## Szybki start (Development)

Zobacz [INSTALLATION.md](INSTALLATION.md) dla szczegółowej instrukcji instalacji.

### Wymagania wstępne
- Python 3.11+
- PostgreSQL 14+ (lub 18 zalecane)

### Instalacja
```bash
# Sklonuj repozytorium
git clone https://github.com/blackemperor84/ChemMan.git
cd ChemMan

# Utwórz środowisko wirtualne
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt

# Skonfiguruj bazę danych PostgreSQL
# (Zobacz INSTALLATION.md dla instrukcji PostgreSQL)

# Utwórz plik .env (skopiuj z .env.example)
cp .env.example .env
# Edytuj .env i ustaw DATABASE_URL

# Utwórz schemat bazy danych
python -c "from app import create_app; from models import db; from config import DevelopmentConfig; app = create_app(DevelopmentConfig); app.app_context().push(); db.create_all(); print('Tables created')"

# Zaimportuj dane referencyjne
python import_excel.py    # 4400 substancji CLP
python import_svhc.py     # aktualna lista SVHC ECHA (~1000 rekordów)

# Utwórz użytkownika admin
python create_admin.py

# Uruchom aplikację
python app.py
```

Logowanie: `admin` / hasło ustawione w `CHEM_MAN_ADMIN_PASSWORD` (lub podane
interaktywnie przy `create_admin.py`). Nie ma hasła domyślnego.

### Testy

```bash
# Uruchom wszystkie testy
python -m pytest tests/ -v

# Z pokryciem kodu
python -m pytest tests/ --cov=. --cov-report=html

# Oczekiwany wynik: 363 testy
```

## Co nowego w v2.4.1? 🎉

### 🔒 Poprawki po ponownym audycie
- ✅ Wstrzykniecie formul do CSV przez pola CAS/WE — identyfikatory sa teraz
  eksportowane jako zwykly tekst, nie jako konstrukcja `="..."`
- ✅ Nieudana weryfikacja SVHC nie zapisuje juz falszywego „nie SVHC” — zapis
  jest odrzucany zamiast zgadywany
- ✅ Odznaczony checkbox nie kasuje auto-detekcji CMR/SVHC (substancja z
  klasyfikacja `Carc. 1B` bez zwrotow H zapisywala sie jako nie-CMR)
- ✅ Sprzatanie po nieudanym uploadzie SDS nie kasuje juz pliku, ktorego wpis
  zostal poprawnie zapisany

## Co nowego w v2.4.0? 🎉

### 🔒 Wzmocnienie bezpieczeństwa (audyt zewnętrzny)
- ✅ Naprawiono trwały XSS — nowy filtr `nl2br` escapuje treść przed zamianą
  znaków nowej linii; usunięto wszystkie wystąpienia `|safe` z szablonów
- ✅ Kontrola dostępu do kart SDS — upload i usuwanie sprawdzają komórkę
  organizacyjną użytkownika (wcześniej nie sprawdzały jej wcale)
- ✅ Konfiguracja produkcyjna wybierana na podstawie `FLASK_ENV` + nowy `wsgi.py`
- ✅ Usunięto wbudowane hasła awaryjne administratora
- ✅ Wykrywanie CMR uwzględnia pole klasyfikacji (np. „Carc. 1B" bez zwrotów H)
- ✅ Nieudana weryfikacja SVHC jest odróżnialna od „nie znaleziono"
- ✅ Kopiowanie substancji zachowuje flagi „zawiera CMR/SVHC"
- ✅ Walidacja przekierowania `?next=` przy logowaniu (open redirect)
- ✅ Neutralizacja wstrzyknięcia formuł w eksporcie CSV
- ✅ Operacje na plikach SDS i bazie są spójne — brak osieroconych plików
  i martwych odnośników przy błędzie zapisu
- ✅ Uprawnienie `can_update_databases` wreszcie działa (patrz niżej)
- ✅ Atomowy import baz CLP/SVHC i uzupełniony łańcuch migracji
- ✅ Wszystkie 363 testy przechodzą

### 🔑 Naprawione uprawnienie „Aktualizacja baz"
Uprawnienie `can_update_databases`, ogłoszone w v2.3.0, nie działało — trasy
`/admin/databases` wymagały konta administratora, więc zaznaczenie tej opcji
nie dawało użytkownikowi żadnego dostępu. Teraz działa zgodnie z opisem:
uprawniona osoba widzi w menu „Bazy Danych" i może importować listy CLP/SVHC,
nie uzyskując przy tym dostępu do zarządzania użytkownikami ani dziennika zmian.

> **Aktualizujesz z wcześniejszej wersji?** Ta wersja zmienia sposób wdrożenia
> (`FLASK_ENV`, `wsgi.py`, wymagane `CHEM_MAN_ADMIN_PASSWORD`, nowy korzeń
> migracji). Przeczytaj sekcję *Uwagi do aktualizacji* w `CHANGELOG.md`.

### 📦 Poprzednie wersje

<details>
<summary>Co było nowego w v2.3.1</summary>

### 🛠️ Wzmocnienie importu, poprawki i porządki (patch)
- ✅ Import z zachowaniem danych (merge-preserve) — ponowny import nie nadpisuje
  ręcznie uzupełnionych SCL/M-factor, zwrotów H i klasyfikacji pustymi kolumnami
- ✅ Obsługa nowego formatu nagłówków ECHA CHEM dla listy SVHC
- ✅ Normalizacja pustych wartości (NaN/None → SQL NULL) — koniec wyników bez nazwy
- ✅ Poprawki bezpieczeństwa i błędów w trasach (admin, substancje, lokalizacje, eksport)
- ✅ Usunięto przestarzałe wywołania (`datetime.utcnow()`, `Model.query.get()`)
- ✅ Refaktoryzacja eksportu (–150 linii duplikacji) i naprawa problemu N+1
- ✅ Zaktualizowano listę SVHC do aktualnej listy kandydackiej ECHA (luty 2026)
- ✅ Wszystkie 242 testy przechodzą
</details>

<details>
<summary>Co było nowego w v2.3.0</summary>

### 🗄️ Aktualizacja baz danych przez interfejs web
- ✅ Nowa strona `/admin/databases` do zarządzania bazami substancji
- ✅ Upload i import bazy CLP (substancje_baza.xlsx) bezpośrednio przez przeglądarkę
- ✅ Upload i import listy SVHC (svhc.xlsx) bezpośrednio przez przeglądarkę
- ✅ Statystyki baz danych (liczba rekordów, data ostatniego importu)
- ✅ Walidacja plików Excel (rozszerzenie, MIME, struktura kolumn)
- ✅ Nowe uprawnienie `can_update_databases` dla wybranych użytkowników
- ✅ Poprawiono wyświetlanie wartości NaN i wyrównanie kolumn w tabelach
</details>

<details>
<summary>Co było nowego w v2.2.0 / v2.2.1</summary>

### 📁 Wiele kart SDS i zaawansowana edycja (v2.2.0)
- ✅ Wiele kart SDS na substancję z informacją o producencie
- ✅ Pełna edycja inline wszystkich pól substancji w wierszu tabeli
- ✅ Ręczne flagi CMR/SVHC (checkboxy "Jest CMR", "Zawiera SVHC" itp.)
- ✅ Liczniki substancji i kart SDS na komórkę organizacyjną

### 🐛 Poprawki (v2.2.1)
- ✅ Poprawiono wyszukiwanie CMR/SVHC w widoku globalnym
- ✅ Poprawiono formatowanie dialogu usuwania substancji
- ✅ Automatyczny rok w stopce
</details>

<details>
<summary>Co było nowego w v2.1.0</summary>

### 🏢 System komórek organizacyjnych
- ✅ Przypisywanie użytkowników do komórek organizacyjnych (działy/jednostki)
- ✅ Dwupoziomowa kontrola dostępu (VIEW/MODIFY)
- ✅ Użytkownicy mogą przeglądać wszystkie komórki, ale modyfikować tylko swoją
- ✅ Ograniczenie kopiowania/przenoszenia substancji do przypisanej komórki
- ✅ Klikalne wiersze w widoku "Wszystkie Substancje"
</details>

<details>
<summary>Co było nowego w v2.0.0</summary>

### Przejście na PostgreSQL
- ✅ Baza danych PostgreSQL (zamiast SQLite)
- ✅ Obsługa wielu użytkowników jednocześnie
- ✅ 363 testy automatyczne, 84% pokrycia kodu
- ✅ Kompletny przewodnik wdrożenia produkcyjnego
</details>

Zobacz [CHANGELOG.md](CHANGELOG.md) dla pełnej listy zmian.

## Wdrożenie produkcyjne

Wdrożenie produkcyjne odbywa się przez **Docker** — serwer nie kompiluje niczego,
tylko pobiera gotowy obraz z GitHub Container Registry:

```bash
mkdir -p /opt/chemman && cd /opt/chemman
curl -O https://raw.githubusercontent.com/blackemperor84/ChemMan/master/docker-compose.yml
curl -O https://raw.githubusercontent.com/blackemperor84/ChemMan/master/.env.docker.example
cp .env.docker.example .env    # uzupełnij SECRET_KEY, POSTGRES_PASSWORD, CHEM_MAN_ADMIN_PASSWORD
docker compose up -d
```

**[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - pełna instrukcja wdrożenia

Obejmuje:
- Uruchomienie przez `docker compose` (PostgreSQL i Redis w komplecie)
- Import danych CLP/SVHC do świeżej instalacji
- Reverse proxy (nginx) i certyfikaty SSL/TLS
- Kopie zapasowe bazy i załączników SDS
- Monitoring, health check i rozwiązywanie problemów

> Instalacja bez Dockera (venv + Gunicorn/Waitress) nie jest już wspierana
> produkcyjnie. Do pracy lokalnej służy [INSTALLATION.md](INSTALLATION.md).

## Dokumentacja

- [📘 Instalacja i konfiguracja](INSTALLATION.md)
- [🔧 Konserwacja i aktualizacje](MAINTENANCE.md)
- [⚙️ Przewodnik backendu](BACKEND_GUIDE.md)
- [👤 Instrukcja użytkownika](USER_GUIDE.md)

## Struktura projektu
```
chem-man/
├── app.py                 # Główny plik aplikacji
├── config.py              # Konfiguracja
├── models.py              # Modele bazy danych
├── decorators.py          # Dekoratory uprawnień
├── routes/                # Blueprinty Flask
│   ├── auth.py            # Logowanie/wylogowanie
│   ├── admin.py           # Panel admina (użytkownicy, bazy danych)
│   ├── locations.py       # Komórki organizacyjne
│   ├── substances.py      # CRUD substancji
│   ├── files.py           # Upload/download SDS
│   └── export.py          # Eksport CSV, widok globalny
├── utils/                 # Moduły pomocnicze
│   ├── __init__.py        # Audit log, klasyfikacja CMR/SVHC
│   ├── file_manager.py    # Zarządzanie plikami SDS
│   └── database_import.py # Import baz CLP/SVHC
├── static/                # CSS, JS
├── templates/             # Szablony HTML
├── tests/                 # Testy pytest (363 testy)
├── migrations/            # Migracje bazy danych (Alembic)
├── instance/              # Baza danych i pliki SDS
├── substancje_baza.xlsx   # Baza CLP
└── svhc.xlsx              # Lista SVHC
```

## Wsparcie

W razie problemów sprawdź [BACKEND_GUIDE.md](BACKEND_GUIDE.md) - sekcja "Rozwiązywanie problemów".

## Licencja

© 2025-2026 NITROERG
