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

- **Backend:** Flask (Python 3.8+)
- **Baza danych:** SQLite
- **Frontend:** HTML, CSS, JavaScript (vanilla)

## Szybki start

Zobacz [INSTALLATION.md](installation.md) dla szczegółowej instrukcji instalacji.
```bash
# Sklonuj repozytorium
git clone [URL]
cd chem-man

# Utwórz środowisko wirtualne
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Zainstaluj zależności
pip install -r requirements.txt

# Zainicjuj bazę danych
python -c "from app import create_app, db, User; app=create_app(); app.app_context().push(); db.create_all(); admin=User(username='admin', is_admin=True); admin.set_password('admin'); db.session.add(admin); db.session.commit()"

# Zaimportuj dane
python import_excel.py
python import_svhc.py

# Uruchom aplikację
python app.py
```

Domyślne logowanie: `admin` / `admin`

## Dokumentacja

- [📘 Instalacja i konfiguracja](installation.md)
- [🔧 Konserwacja i aktualizacje](maintenance.md)
- [⚙️ Przewodnik backendu](backend guide.md)
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

W razie problemów sprawdź [BACKEND_GUIDE.md](BACKEND_GUIDE.md) - sekcja "Rozwiązywanie problemów".

## Licencja

© 2025 NITROERG
