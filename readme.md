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
- **Testing:** pytest (242 testy, 80% pokrycia kodu)

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

Domyślne logowanie: `admin` / `F23pADFE!` (zmień po pierwszym logowaniu!)

### Testy

```bash
# Uruchom wszystkie testy
python -m pytest tests/ -v

# Z pokryciem kodu
python -m pytest tests/ --cov=. --cov-report=html

# Oczekiwany wynik: 242 testy, 80% pokrycia
```

## Co nowego w v2.3.1? 🎉

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

### 📦 Poprzednie wersje

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
- ✅ 242 testy automatyczne, 80% pokrycia kodu
- ✅ Kompletny przewodnik wdrożenia produkcyjnego
</details>

Zobacz [CHANGELOG.md](CHANGELOG.md) dla pełnej listy zmian.

## Wdrożenie produkcyjne

Dla wdrożenia produkcyjnego na serwerze, zobacz kompletny przewodnik:

**[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Pełna instrukcja wdrożenia produkcyjnego

Obejmuje:
- Instalację PostgreSQL na Windows/Linux
- Konfigurację serwera WSGI (Gunicorn/Waitress)
- Reverse proxy (nginx/Apache)
- Certyfikaty SSL/TLS
- Automatyczne kopie zapasowe
- Monitoring i utrzymanie

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
├── tests/                 # Testy pytest (242 testy)
├── migrations/            # Migracje bazy danych (Alembic)
├── instance/              # Baza danych i pliki SDS
├── substancje_baza.xlsx   # Baza CLP
└── svhc.xlsx              # Lista SVHC
```

## Wsparcie

W razie problemów sprawdź [BACKEND_GUIDE.md](BACKEND_GUIDE.md) - sekcja "Rozwiązywanie problemów".

## Licencja

© 2025-2026 NITROERG
