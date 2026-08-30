# Instrukcja Instalacji ChemMan

Pełna instrukcja instalacji, konfiguracji i uruchomienia aplikacji ChemMan od zera.

## Wymagania systemowe

- **System operacyjny:** Windows 10/11, Linux, macOS
- **Python:** 3.11 lub nowszy
- **PostgreSQL:** 14 lub nowszy (zalecane 18)
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

## Krok 2: Instalacja PostgreSQL

ChemMan wymaga PostgreSQL jako bazy danych dla środowiska produkcyjnego.

### Windows

1. Pobierz PostgreSQL z [postgresql.org](https://www.postgresql.org/download/windows/)
2. Zainstaluj PostgreSQL 18 (lub nowszy)
3. Podczas instalacji:
   - Ustaw hasło dla użytkownika `postgres` (zapamiętaj!)
   - Zaakceptuj domyślny port (5432)

4. Utwórz bazę danych i użytkownika:

```powershell
# Otwórz pgAdmin lub użyj psql
psql -U postgres

# W psql:
CREATE DATABASE chemman_dev;
CREATE USER chemman_user WITH PASSWORD 'twoje_silne_haslo';
GRANT ALL PRIVILEGES ON DATABASE chemman_dev TO chemman_user;
\q
```

### Linux (Ubuntu/Debian)

```bash
# Instalacja PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Uruchom PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Utwórz bazę danych i użytkownika
sudo -u postgres psql

# W psql:
CREATE DATABASE chemman_dev;
CREATE USER chemman_user WITH PASSWORD 'twoje_silne_haslo';
GRANT ALL PRIVILEGES ON DATABASE chemman_dev TO chemman_user;
\q
```

### macOS

```bash
# Instalacja przez Homebrew
brew install postgresql

# Uruchom PostgreSQL
brew services start postgresql

# Utwórz bazę danych i użytkownika
psql postgres

# W psql:
CREATE DATABASE chemman_dev;
CREATE USER chemman_user WITH PASSWORD 'twoje_silne_haslo';
GRANT ALL PRIVILEGES ON DATABASE chemman_dev TO chemman_user;
\q
```

---

## Krok 3: Pobranie aplikacji

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

## Krok 4: Konfiguracja aplikacji

### 4.1 Utwórz plik .env

Skopiuj przykładowy plik konfiguracji:

```bash
cp .env.example .env
```

### 4.2 Edytuj .env

Otwórz `.env` w edytorze tekstu i skonfiguruj:

```bash
# Database Configuration
DATABASE_URL=postgresql://chemman_user:twoje_silne_haslo@localhost:5432/chemman_dev

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=wygeneruj_losowy_klucz_tutaj
FLASK_DEBUG=1

# Admin User (first login) - brak wartości domyślnej, MUSISZ ustawić własne
CHEM_MAN_ADMIN_PASSWORD=
```

**Wygeneruj SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Skopiuj wynik do `SECRET_KEY` w pliku `.env`.

---

## Krok 5: Utworzenie środowiska wirtualnego

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

## Krok 6: Instalacja zależności

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

## Krok 7: Inicjalizacja bazy danych

Utwórz schemat bazy danych w PostgreSQL:

```bash
python -c "from app import create_app; from models import db; from config import DevelopmentConfig; app = create_app(DevelopmentConfig); app.app_context().push(); db.create_all(); print('✅ Tabele utworzone')"
```

**Oczekiwany wynik:**
```
✅ Tabele utworzone
```

---

## Krok 8: Utworzenie użytkownika administratora

Użyj dedykowanego skryptu do utworzenia użytkownika admin:

```bash
python create_admin.py
```

**Oczekiwany wynik:**
```
Hasło pobrano z: zmiennej CHEM_MAN_ADMIN_PASSWORD.
Tworzenie użytkownika 'admin'...
SUKCES: Utworzono użytkownika 'admin'.
        Nazwa użytkownika: admin
        Hasło: (takie, jakie podano powyżej)
```

**Hasło nie ma wartości domyślnej.** Skrypt pobierze je ze zmiennej
`CHEM_MAN_ADMIN_PASSWORD` (np. z pliku `.env`), a jeśli jej nie ustawisz -
zapyta interaktywnie. Bez hasła (i bez terminala, np. w CI) skrypt zakończy się błędem.

Minimalna długość hasła to 8 znaków. Hasło nigdy nie jest wypisywane na ekranie
ani do logów.

---

## Krok 9: Import danych - Baza CLP

Upewnij się że plik `substancje_baza.xlsx` jest w głównym katalogu projektu!

```bash
python import_excel.py
```

**Oczekiwany wynik:**
```
📊 Wczytywanie substancji z Excela...
📝 Wczytano 4400 wierszy
📥 Importowanie danych...
✅ Import CLP ukończony! Dodano 4400 substancji.
```

---

## Krok 10: Import danych - Lista SVHC

Upewnij się że plik `svhc.xlsx` jest w głównym katalogu projektu!

```bash
python import_svhc.py
```

**Oczekiwany wynik:**
```
📊 Wczytywanie SVHC z Excela...
📝 Wczytano 492 wierszy
📥 Importowanie SVHC...
✅ Import SVHC ukończony! Dodano 492 substancji SVHC.
```

---

## Krok 11: Uruchomienie aplikacji

### Tryb deweloperski (development)

```bash
python app.py
```

Powinieneś zobaczyć:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Otwórz przeglądarkę: `http://127.0.0.1:5000`

### Dostęp do aplikacji

- **URL:** `http://127.0.0.1:5000`
- **Login:** `admin`
- **Hasło:** to, które ustawiłeś w `CHEM_MAN_ADMIN_PASSWORD` (Krok 8)

### Testy (opcjonalnie)

Sprawdź czy wszystko działa poprawnie:

```bash
# Uruchom wszystkie testy
python -m pytest tests/ -v

# Oczekiwany wynik: 242 passed
```

Jeśli wszystkie testy przechodzą - aplikacja jest gotowa! ✅

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

**Data aktualizacji:** 22.10.2025

**Wersja:** 2.0.0 (PostgreSQL, testy automatyczne, production-ready)
