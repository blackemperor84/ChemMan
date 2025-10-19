# Instrukcja Instalacji ChemMan

Pełna instrukcja instalacji, konfiguracji i uruchomienia aplikacji ChemMan od zera.

## Wymagania systemowe

- **System operacyjny:** Windows 10/11, Linux, macOS
- **Python:** 3.8 lub nowszy
- **Pamięć RAM:** minimum 2GB
- **Miejsce na dysku:** minimum 1GB
- **Przeglądarka:** Chrome, Firefox, Edge (najnowsze wersje)

---

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

### macOS

```bash
brew install python3
```

---

## Krok 2: Pobranie aplikacji

### Opcja A: Z GitHub (jeśli masz Git)

```bash
git clone https://github.com/blackemperor84/ChemMan.git
cd ChemMan
```

### Opcja B: Z archiwum ZIP

1. Pobierz plik ZIP
2. Rozpakuj go
3. Wejdź do folderu

---

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

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

**Weryfikacja:** Powinna pojawić się `(venv)` na początku wiersza poleceń.

---

## Krok 4: Instalacja zależności

Z aktywnym `venv`:

```bash
pip install -r requirements.txt
```

**Zawartość `requirements.txt`:**
```
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-Bcrypt==1.0.1
Flask-WTF==1.2.1
Flask-Limiter==4.0.0
pandas==2.1.4
openpyxl==3.1.2
python-dateutil==2.8.2
Werkzeug==3.1.3
```

**Sprawdzenie:**
```bash
pip list | findstr flask  # Windows
pip list | grep flask     # Linux/Mac
```

---

## Krok 5: Inicjalizacja bazy danych

Baza danych nie istnieje na starcie. Musisz ją utworzyć:

### Windows (PowerShell)

```powershell
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Baza danych utworzona!')"
```

### Linux/macOS

```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Baza danych utworzona!')"
```

**Oczekiwany wynik:**
```
✅ Baza danych utworzona!
```

---

## Krok 6: Utworzenie użytkownika administratora

### Automatyczne (szybkie)

```powershell
# Windows
python -c "
from app import create_app
from models import db, User

app = create_app()
ctx = app.app_context()
ctx.push()

admin_password = 'admin'  # Zmień to na bezpieczne hasło!
admin = User(
    username='admin',
    is_admin=True,
    can_view=True,
    can_add=True,
    can_edit=True,
    can_delete=True,
    can_move=True,
    can_copy=True,
    can_upload_sds=True,
    can_add_location=True,
    can_delete_location=True
)
admin.set_password(admin_password)
db.session.add(admin)
db.session.commit()
print(f'✅ Admin user created! Username: admin, Password: {admin_password}')
"
```

**Oczekiwany wynik:**
```
✅ Admin user created! Username: admin, Password: admin
```

**Zmień hasło admina!** Użyj hasła zawierającego:
- Co najmniej 8 znaków
- Wielkie i małe litery
- Cyfry
- Znaki specjalne (!@#$%^&*)

---

## Krok 7: Import danych - Baza CLP

Upewnij się że plik `substancje_baza.xlsx` jest w głównym katalogu projektu!

### Import substancji z Excela

```powershell
# Windows
python -c "
from app import create_app
from models import db, ExcelSourceSubstance
import pandas as pd
import os

app = create_app()
ctx = app.app_context()
ctx.push()

excel_path = os.path.join(os.getcwd(), 'substancje_baza.xlsx')

if not os.path.exists(excel_path):
    print(f'❌ Błąd: Plik {excel_path} nie istnieje')
else:
    print('📊 Wczytywanie substancji z Excela...')
    df = pd.read_excel(excel_path, header=0, skiprows=[1])
    print(f'📝 Wczytano {len(df)} wierszy')
    
    column_map = {
        'International Chemical Identification': 'name',
        'CAS No': 'cas',
        'EC No': 'ec_number',
        'Classification': 'classification',
        'Unnamed: 5': 'h_phrases',
        'Specific Conc. Limits, M-factors': 'scl_mfactor'
    }
    
    df.rename(columns=column_map, inplace=True)
    df = df[list(column_map.values())]
    
    print('🗑️ Czyszczenie starej bazy...')
    db.session.query(ExcelSourceSubstance).delete()
    db.session.commit()
    
    print('📥 Importowanie nowych danych...')
    data = df.to_dict(orient='records')
    db.session.bulk_insert_mappings(ExcelSourceSubstance, data)
    db.session.commit()
    
    print(f'✅ Import CLP ukończony! Dodano {len(data)} substancji.')
"
```

**Oczekiwany wynik:**
```
📊 Wczytywanie substancji z Excela...
📝 Wczytano 4400 wierszy
🗑️ Czyszczenie starej bazy...
📥 Importowanie nowych danych...
✅ Import CLP ukończony! Dodano 4400 substancji.
```

---

## Krok 8: Import danych - Lista SVHC

Upewnij się że plik `svhc.xlsx` jest w głównym katalogu projektu!

### Import SVHC

```powershell
# Windows
python -c "
from app import create_app
from models import db, SVHCSubstance
import pandas as pd
import os

app = create_app()
ctx = app.app_context()
ctx.push()

svhc_path = os.path.join(os.getcwd(), 'svhc.xlsx')

if not os.path.exists(svhc_path):
    print(f'❌ Błąd: Plik {svhc_path} nie istnieje')
else:
    print('📊 Wczytywanie SVHC z Excela...')
    df = pd.read_excel(svhc_path, header=0)
    print(f'📝 Wczytano {len(df)} wierszy')
    
    column_map = {
        'Nazwa substancji ': 'name',
        'Nr WE': 'ec_number',
        'Nr CAS': 'cas',
        'Powód włączenia ': 'reason',
        'Data włączenia ': 'date_inclusion'
    }
    
    df.rename(columns=column_map, inplace=True)
    
    for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
        if col not in df.columns:
            df[col] = None
    
    df = df[['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]
    
    print('🗑️ Czyszczenie starej listy SVHC...')
    db.session.query(SVHCSubstance).delete()
    db.session.commit()
    
    print('📥 Importowanie SVHC...')
    data = df.to_dict(orient='records')
    db.session.bulk_insert_mappings(SVHCSubstance, data)
    db.session.commit()
    
    print(f'✅ Import SVHC ukończony! Dodano {len(data)} substancji SVHC.')
"
```

**Oczekiwany wynik:**
```
📊 Wczytywanie SVHC z Excela...
📝 Wczytano 492 wierszy
🗑️ Czyszczenie starej listy SVHC...
📥 Importowanie SVHC...
✅ Import SVHC ukończony! Dodano 492 substancji SVHC.
```

---

## Krok 9: Uruchomienie aplikacji

### Tryb deweloperski (development)

```powershell
python app.py
```

Powinieneś zobaczyć:

```
UWAGA: Wygenerowano tymczasowy SECRET_KEY dla środowiska developerskiego.
 * Running on http://127.0.0.1:5000
```

Otwórz przeglądarkę: `http://127.0.0.1:5000`

### Dostęp do aplikacji

- **URL:** `http://127.0.0.1:5000`
- **Login:** `admin`
- **Hasło:** to hasło które ustawiłeś w Kroku 6

---

## Weryfikacja poprawnej instalacji

### Test 1: Zaloguj się

1. Wejdź na `http://127.0.0.1:5000`
2. Zaloguj się jako `admin` z hasłem
3. Powinieneś zobaczyć dashbord

### Test 2: Sprawdź czy substancje są zaimportowane

W panelu admina:
1. Kliknij "Wszystkie Substancje"
2. Powinno być ~4400 substancji CLP
3. Możesz filtrować po "SVHC"

### Test 3: Dodaj lokalizację i substancję

1. Kliknij "Zarządzaj Lokalizacjami"
2. Dodaj nową lokalizację
3. Dodaj substancję do lokalizacji
4. Wyszukaj "Anthracene" - powinno znaleźć

### Test 4: Sprawdź zabezpieczenia

1. Spróbuj zalogować się 6 razy z błędnym hasłem
2. Po 5 prób powinno pokazać: "429 Too Many Requests"
3. Czekaj 1 minutę
4. Powinieneś móc zalogować się ponownie

---

## Konfiguracja dla produkcji

### Ustawienie bezpiecznego hasła admina

Przed wdrożeniem w produkcji ustawiłeś bezpieczne hasło dla administratora.

#### Windows (PowerShell)

```powershell
$env:CHEM_MAN_ADMIN_PASSWORD = "TwojeNoweBezpieczneHaslo123!@#"
$env:FLASK_ENV = "production"
python app.py
```

#### Linux/macOS

```bash
export CHEM_MAN_ADMIN_PASSWORD="TwojeNoweBezpieczneHaslo123!@#"
export FLASK_ENV="production"
python app.py
```

**Ważne:** W produkcji aplikacja **nie uruchomi się** bez ustawienia zmiennej `CHEM_MAN_ADMIN_PASSWORD`!

---

## Rozwiązywanie problemów instalacji

### Problem: "Python nie jest rozpoznawany"

**Rozwiązanie (Windows):**
1. Panel sterowania → Zmienne środowiskowe
2. Dodaj ścieżkę do Python: `C:\Users\[TWOJE_IMIĘ]\AppData\Local\Programs\Python\Python311`
3. Zrestartuj terminal

### Problem: "Plik substancje_baza.xlsx nie istnieje"

**Rozwiązanie:**
1. Upewnij się że plik jest w głównym katalogu projektu
2. Sprawdź pisownię nazwy pliku
3. Plik musi być w formacie `.xlsx` (nie `.xls`)

### Problem: "Baza danych nie została utworzona"

**Rozwiązanie:**
1. Sprawdź czy folder `instance/` istnieje
2. Jeśli nie, utwórz go: `mkdir instance`
3. Powtórz Krok 5

### Problem: "Błąd przy logowaniu (500 error)"

**Rozwiązanie:**
1. Sprawdź czy admin user został utworzony (Krok 6)
2. Jeśli nie, powtórz Krok 6
3. Sprawdź logi: `logs/chem_man.log` (jeśli istnieje)

### Problem: "Nie mogę znaleźć substancji w wyszukiwarce"

**Rozwiązanie:**
1. Sprawdź czy import CLP został ukończony (Krok 7)
2. Sprawdź czy liczba substancji = 4400
3. Czekaj kilka sekund, indeksy bazy się budują
4. Przeładuj stronę (F5)

### Problem: "Wygenerowano tymczasowe hasło admina" po każdym restarcie

**Przyczyna:** Aplikacja w trybie development - normalnie!

**Rozwiązanie dla produkcji:**
```bash
$env:FLASK_ENV = "production"
$env:CHEM_MAN_ADMIN_PASSWORD = "TwojeHaslo"
python app.py
```

---

## Następne kroki

- [📘 Instrukcja użytkownika](USER_GUIDE.md) - jak korzystać z aplikacji
- [🔧 Przewodnik konserwacji](MAINTENANCE.md) - backup, aktualizacje, monitoring
- [⚙️ Przewodnik backendu](BACKEND_GUIDE.md) - architektura, rozszerzenia
- [🔐 Zabezpieczenia](INSTRUKCJA_BEZPIECZENSTWA.md) - rate limiting, walidacja

---

## Szybka pomoc

### Jeśli coś pójdzie nie tak:

1. **Przeczytaj komunikat błędu** - najczęściej mówi co nie tak
2. **Sprawdź czy venv jest aktywny** - powinna być `(venv)` na początku wiersza
3. **Restartuj aplikację** - Ctrl+C i `python app.py`
4. **Przejrzyj logi** - `logs/chem_man.log`
5. **Sprawdź dokumentację** - [BACKEND_GUIDE.md](BACKEND_GUIDE.md)

### Kontakt

W razie trwałych problemów zachowaj:
- Screenshot błędu
- Treść wiadomości błędu
- Zawartość `logs/chem_man.log`
- Wersję Python (`python --version`)

---

**Data aktualizacji:** 19.10.2025

**Wersja:** 2.0 (z zabezpieczeniami i rate limitingiem)
