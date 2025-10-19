# Instrukcja Instalacji ChemMan

## Wymagania systemowe

- **System operacyjny:** Windows 10/11, Linux, macOS
- **Python:** 3.8 lub nowszy
- **Pamięć RAM:** minimum 2GB
- **Miejsce na dysku:** minimum 500MB
- **Przeglądarka:** Chrome, Firefox, Edge (najnowsze wersje)

## Krok 1: Instalacja Python

### Windows

1. Pobierz Python z [python.org](https://www.python.org/downloads/)
2. **WAŻNE:** Zaznacz "Add Python to PATH" podczas instalacji
3. Sprawdź instalację:
```powershell
python --version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## Krok 2: Pobranie aplikacji
```bash
# Jeśli używasz Git
git clone [URL_REPOZYTORIUM]
cd chem-man

# Lub rozpakuj archiwum ZIP
```

## Krok 3: Utworzenie środowiska wirtualnego

### Windows (PowerShell)
```powershell
# Utwórz środowisko
python -m venv venv

# Aktywuj
.\venv\Scripts\Activate.ps1

# Jeśli błąd ExecutionPolicy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
```

## Krok 4: Instalacja zależności
```bash
pip install -r requirements.txt
```

**Zawartość `requirements.txt`:**
```
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-Bcrypt==1.0.1
pandas==2.1.4
openpyxl==3.1.2
python-dateutil==2.8.2
```

## Krok 5: Konfiguracja

### Plik `.env` (opcjonalnie)

Utwórz plik `.env` w głównym katalogu:
```bash
SECRET_KEY=twoj-super-tajny-klucz-min-32-znaki
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/chem_man.db
CHEM_MAN_ADMIN_PASSWORD=bezpieczne-haslo-admina
```

**Generowanie SECRET_KEY:**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Krok 6: Inicjalizacja bazy danych

### Metoda 1: Komenda Python (szybka)
```bash
python -c "from app import create_app, db, User; app=create_app(); app.app_context().push(); db.create_all(); admin=User(username='admin', is_admin=True, can_view=True, can_add=True, can_edit=True, can_delete=True, can_move=True, can_copy=True, can_upload_sds=True, can_add_location=True, can_delete_location=True); admin.set_password('admin'); db.session.add(admin); db.session.commit(); print('Baza utworzona!')"
```

### Metoda 2: Flask CLI (zalecana dla produkcji)
```bash
$env:FLASK_APP="app"  # Windows
export FLASK_APP=app  # Linux/Mac

flask init-db
```

## Krok 7: Import danych

### Import bazy CLP

**Upewnij się, że masz plik `substancje_baza.xlsx`!**
```bash
python import_excel.py
```

Oczekiwany wynik:
```
Rozpoczynam import...
Wczytano 4400 wierszy z Excel
Gotowe! Zaimportowano 4400 substancji!
```

### Import listy SVHC

**Upewnij się, że masz plik `svhc.xlsx`!**
```bash
python import_svhc.py
```

Lub przez Flask CLI:
```bash
flask import-svhc
```

## Krok 8: Uruchomienie aplikacji

### Tryb deweloperski
```bash
python app.py
```

Aplikacja uruchomi się na: `http://127.0.0.1:5000`

### Tryb produkcyjny (z Gunicorn - Linux)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Krok 9: Pierwsze logowanie

1. Otwórz przeglądarkę: `http://127.0.0.1:5000`
2. Zaloguj się:
   - **Użytkownik:** `admin`
   - **Hasło:** `admin` (lub hasło z pliku `.env`)
3. **WAŻNE:** Zmień hasło admina natychmiast po pierwszym logowaniu!

## Weryfikacja instalacji

### Test działania
```bash
python -c "from app import create_app; from models import ExcelSourceSubstance, SVHCSubstance; app=create_app(); app.app_context().push(); print(f'CLP: {ExcelSourceSubstance.query.count()} substancji'); print(f'SVHC: {SVHCSubstance.query.count()} substancji')"
```

Oczekiwany wynik:
```
CLP: 4400 substancji
SVHC: 492 substancji
```

## Rozwiązywanie problemów instalacji

### Błąd: "Python nie jest rozpoznawany"

**Windows:**
- Dodaj Python do PATH ręcznie
- Panel sterowania → Zmienne środowiskowe
- Dodaj: `C:\Users\[USER]\AppData\Local\Programs\Python\Python3X`

### Błąd: "pip nie jest rozpoznawany"
```bash
python -m pip install --upgrade pip
```

### Błąd: "Brak modułu Flask"
```bash
pip install --force-reinstall -r requirements.txt
```

### Błąd: "Nie można otworzyć pliku Excel"

Sprawdź czy pliki `substancje_baza.xlsx` i `svhc.xlsx` są w głównym katalogu projektu.

## Następne kroki

- [📘 Konserwacja i aktualizacje](MAINTENANCE.md)
- [⚙️ Przewodnik backendu](BACKEND_GUIDE.md)