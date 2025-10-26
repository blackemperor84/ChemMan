# ChemMan - System Zarządzania Substancjami Chemicznymi

System do zarządzania inwentaryzacją substancji chemicznych z obsługą baz CLP i SVHC.

## Funkcje

- 📦 Zarządzanie substancjami w różnych lokalizacjach
- 🔍 Wyszukiwanie w bazie CLP (4400+ substancji) i SVHC (490+ substancji)
- 🌍 Dwujęzyczne nazwy (angielski/polski)
- ⚠️ Automatyczne oznaczanie CMR i SVHC
- 📄 Upload i zarządzanie kartami SDS (PDF)
- 📊 Export do CSV
- 👥 System uprawnień użytkowników
- 📜 Dziennik zmian (audit log)

## Technologie

- **Backend:** Flask (Python 3.11+)
- **Baza danych:** PostgreSQL 14+ (produkcja), SQLite (testy)
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Testing:** pytest (242 testy, 80% pokrycia kodu)

## Szybki start (Development)

Zobacz [installation.md](installation.md) dla szczegółowej instrukcji instalacji.

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
python import_svhc.py     # 492 substancji SVHC

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

## Co nowego w v2.0.0? 🎉

### Przejście na PostgreSQL
- ✅ Baza danych PostgreSQL (zamiast SQLite)
- ✅ Obsługa wielu użytkowników jednocześnie
- ✅ Brak błędów "database locked"
- ✅ Gotowe do produkcji

### Testy automatyczne
- ✅ 242 testy automatyczne
- ✅ 80% pokrycia kodu
- ✅ Testowane bezpieczeństwo, uprawnienia, pliki

### Ulepszenia bezpieczeństwa
- ✅ Ulepszone limitowanie prędkości (rate limiting)
- ✅ Lepsze sprawdzanie typów plików
- ✅ Ulepszona walidacja danych

### Dokumentacja
- ✅ Kompletny przewodnik wdrożenia produkcyjnego
- ✅ Instrukcje dla Linux i Windows
- ✅ Konfiguracja SSL, kopie zapasowe, monitoring

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

- [📘 Instalacja i konfiguracja](installation.md)
- [🔧 Konserwacja i aktualizacje](maintenance.md)
- [⚙️ Przewodnik backendu](backend_guide.md)
- [👤 Instrukcja użytkownika](user_guide.md)

## Struktura projektu
```
chem-man/
├── app.py                 # Główny plik aplikacji
├── config.py             # Konfiguracja
├── models.py             # Modele bazy danych
├── commands.py           # Komendy Flask CLI
├── routes/               # Blueprinty Flask
│   ├── auth.py
│   ├── locations.py
│   ├── export.py
│   └── ...
├── static/               # CSS, JS
├── templates/            # Szablony HTML
├── instance/             # Baza danych i pliki SDS
├── substancje_baza.xlsx  # Baza CLP
└── svhc.xlsx            # Lista SVHC
```

## Wsparcie

W razie problemów sprawdź [backend_guide.md](backend_guide.md) - sekcja "Rozwiązywanie problemów".

## Licencja

© 2025 NITROERG
