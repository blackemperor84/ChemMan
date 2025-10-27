# Przewodnik Techniczny Backend - ChemMan

Szczegółowa dokumentacja techniczna dla programistów i administratorów systemu.

---

## 📋 Spis treści

1. [Architektura systemu](#architektura-systemu)
2. [Struktura bazy danych](#struktura-bazy-danych)
3. [Kluczowe pliki i funkcje](#kluczowe-pliki-i-funkcje)
4. [API i endpointy](#api-i-endpointy)
5. [Mechanizm wyszukiwania](#mechanizm-wyszukiwania)
6. [System uprawnień](#system-uprawnień)
7. [Obsługa plików Excel](#obsługa-plików-excel)
8. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Architektura systemu

### Diagram komponentów
```
┌─────────────────────────────────────────┐
│          Frontend (Browser)             │
│  HTML + CSS + Vanilla JavaScript        │
└──────────────┬──────────────────────────┘
               │ HTTP/AJAX
┌──────────────▼──────────────────────────┐
│         Flask Application               │
│  ┌──────────────────────────────────┐   │
│  │      Blueprints (Routes)         │   │
│  │  • auth.py                       │   │
│  │  • locations.py                  │   │
│  │  • export.py                     │   │
│  │  • admin.py                      │   │
│  └──────────────┬───────────────────┘   │
│                 │                        │
│  ┌──────────────▼───────────────────┐   │
│  │      Business Logic (utils)      │   │
│  │  • is_cmr_substance()            │   │
│  │  • is_svhc_substance()           │   │
│  │  • convert_utc_to_local()        │   │
│  └──────────────┬───────────────────┘   │
│                 │                        │
│  ┌──────────────▼───────────────────┐   │
│  │    Models (SQLAlchemy ORM)       │   │
│  │  • User, Location, Substance     │   │
│  │  • ExcelSourceSubstance, SVHC    │   │
│  └──────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         SQLite Database                 │
│    instance/chem_man.db                 │
└─────────────────────────────────────────┘
```

### Stack technologiczny

| Warstwa | Technologia | Wersja |
|---------|-------------|--------|
| Backend Framework | Flask | 3.0.0 |
| ORM | SQLAlchemy | 3.1.1 |
| Autentykacja | Flask-Login | 0.6.3 |
| Hashowanie | Flask-Bcrypt | 1.0.1 |
| Baza danych | SQLite | 3.x |
| Excel Processing | pandas + openpyxl | 2.1.4 + 3.1.2 |
| Frontend | Vanilla JS | - |

---

## Struktura bazy danych

### Diagram ER
```
┌──────────────┐
│    Users     │
├──────────────┤
│ id (PK)      │
│ username     │
│ password_hash│
│ is_admin     │
│ can_view     │
│ can_add      │
│ ...          │
└──────────────┘
       │ 1
       │
       │ * (logs)
       │
┌──────▼───────┐
│  AuditLog    │
├──────────────┤
│ id (PK)      │
│ user_id (FK) │
│ action       │
│ timestamp    │
│ details      │
└──────────────┘

┌──────────────────┐
│    Locations     │
├──────────────────┤
│ id (PK)          │
│ name             │
│ last_modified    │
└────────┬─────────┘
         │ 1
         │
         │ * (substances)
         │
┌────────▼──────────────────┐
│      Substances           │
├───────────────────────────┤
│ id (PK)                   │
│ location_id (FK)          │
│ name                      │
│ cas                       │
│ ec_number                 │
│ classification            │
│ h_phrases                 │
│ scl_mfactor               │
│ comment                   │
│ is_cmr                    │
│ is_svhc                   │
│ physical_location         │
│ sds_filename              │
│ sds_upload_timestamp      │
└───────────────────────────┘

┌───────────────────────────┐
│  ExcelSourceSubstance     │
│  (Baza CLP)               │
├───────────────────────────┤
│ id (PK)                   │
│ name                      │
│ cas                       │
│ ec_number                 │
│ classification            │
│ h_phrases                 │
│ scl_mfactor               │
└───────────────────────────┘

┌───────────────────────────┐
│    SVHCSubstance          │
│    (Lista SVHC)           │
├───────────────────────────┤
│ id (PK)                   │
│ name                      │
│ cas                       │
│ ec_number                 │
│ reason                    │
│ date_inclusion            │
└───────────────────────────┘
```

### Modele szczegółowo

#### User
```python
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Uprawnienia
    can_view = db.Column(db.Boolean, default=True)
    can_add = db.Column(db.Boolean, default=False)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_move = db.Column(db.Boolean, default=False)
    can_copy = db.Column(db.Boolean, default=False)
    can_upload_sds = db.Column(db.Boolean, default=False)
    can_add_location = db.Column(db.Boolean, default=False)
    can_delete_location = db.Column(db.Boolean, default=False)
```

#### Substance
```python
class Substance(db.Model):
    __tablename__ = 'substances'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    cas = db.Column(db.String(20), nullable=True)
    ec_number = db.Column(db.String(20), nullable=True)
    classification = db.Column(db.Text, nullable=True)
    h_phrases = db.Column(db.Text, nullable=True)
    scl_mfactor = db.Column(db.Text, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    
    # Flagi
    is_cmr = db.Column(db.Boolean, default=False)
    is_svhc = db.Column(db.Boolean, default=False)
    
    # SDS
    sds_filename = db.Column(db.String(255), nullable=True)
    sds_upload_timestamp = db.Column(db.DateTime, nullable=True)
    
    # Lokalizacje
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    physical_location = db.Column(db.String(50), nullable=True)  # Bieruń/Krupski Młyn
```

---

## Kluczowe pliki i funkcje

### Struktura plików
```
chem-man/
├── app.py                      # Główna aplikacja Flask
├── config.py                   # Konfiguracja (Config classes)
├── models.py                   # Modele SQLAlchemy
├── commands.py                 # Flask CLI commands
├── utils.py                    # Funkcje pomocnicze
├── decorators.py               # Dekoratory uprawnień
│
├── routes/                     # Blueprinty
│   ├── __init__.py
│   ├── auth.py                 # Logowanie, rejestracja, zmiana hasła
│   ├── locations.py            # CRUD lokalizacji
│   ├── substances.py           # CRUD substancji
│   ├── export.py               # Wyszukiwanie, eksport CSV
│   ├── files.py                # Upload/download SDS
│   └── admin.py                # Panel admina
│
├── static/
│   ├── css/
│   │   ├── base.css
│   │   ├── location_detail.css
│   │   └── ...
│   └── js/
│       ├── base.js
│       ├── location_detail.js
│       └── ...
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── locations.html
│   ├── location_detail.html
│   ├── all_substances.html
│   └── ...
│
├── instance/                   # Instancyjne dane (gitignored)
│   ├── chem_man.db            # Baza SQLite
│   └── uploads/
│       └── sds/               # Pliki PDF SDS
│
├── substancje_baza.xlsx        # Baza CLP (4400 substancji)
├── svhc.xlsx                   # Lista SVHC (492 substancji)
├── import_excel.py             # Skrypt importu CLP
└── import_svhc.py              # Skrypt importu SVHC
```

### Kluczowe funkcje w `utils.py`

#### `is_cmr_substance()`

Sprawdza czy substancja jest CMR na podstawie klasyfikacji i zwrotów H.
```python
def is_cmr_substance(classification=None, h_phrases=None):
    """
    Zwraca True jeśli substancja zawiera:
    - Zwroty H: H340, H350, H360 (lub warianty)
    - Klasyfikację: Carc., Muta., Repr.
    """
    # Implementacja: regex pattern matching
```

**Przykłady:**
- `H350` → Może powodować raka → CMR
- `Carc. 1A` → Rakotwórczość kat. 1A → CMR
- `Repr. 2` → Toksyczność rozrodcza kat. 2 → CMR

#### `is_svhc_substance()`

Sprawdza czy substancja jest na liście SVHC.
```python
def is_svhc_substance(cas=None, ec_number=None, name=None):
    """
    Wyszukuje substancję w tabeli SVHCSubstance.
    Zwraca 'reason' (powód włączenia) lub None.
    
    Priorytet dopasowania:
    1. CAS number (najdokładniejsze)
    2. EC number
    3. Nazwa (fuzzy matching)
    """
```

**Przykład:**
```python
reason = is_svhc_substance(cas='80-43-3')
# Zwraca: "Reproductive toxicity (Article 57c)"
```

#### `convert_utc_to_local()`

Konwertuje czas UTC z bazy na czas lokalny (Europe/Warsaw).
```python
def convert_utc_to_local(utc_dt):
    """
    Input: datetime object (UTC)
    Output: string formatted as "DD-MM-YYYY HH:MM"
    """
```

---

## API i endpointy

### Główne endpointy

| Metoda | Endpoint | Funkcja | Uprawnienie |
|--------|----------|---------|-------------|
| GET | `/` | Lista lokalizacji | `can_view` |
| GET | `/login` | Formularz logowania | - |
| POST | `/login` | Logowanie | - |
| GET | `/logout` | Wylogowanie | - |
| GET | `/location/<id>` | Szczegóły lokalizacji | `can_view` |
| POST | `/add_location` | Dodaj lokalizację | `can_add_location` |
| POST | `/edit_location/<id>` | Edytuj lokalizację | `can_edit` |
| POST | `/delete_location/<id>` | Usuń lokalizację | `can_delete_location` |
| POST | `/add_substance` | Dodaj substancję | `can_add` |
| POST | `/edit_substance/<id>` | Edytuj substancję | `can_edit` |
| POST | `/delete_substance/<id>` | Usuń substancję | `can_delete` |
| GET | `/search_substances` | API wyszukiwania | `can_view` |
| GET | `/substances/all` | Wszystkie substancje | `can_view` |
| GET | `/export/all/csv` | Eksport CSV | `can_view` |
| POST | `/upload_sds/<id>` | Upload pliku SDS | `can_upload_sds` |
| GET | `/download_sds/<filename>` | Pobierz SDS | `can_view` |

### API wyszukiwania - `/search_substances`

**Request:**
```
GET /search_substances?query=kwas
```

**Response:**
```json
[
  {
    "name": "acetic acid\nkwas octowy",
    "cas": "64-19-7",
    "ec_number": "200-580-7",
    "classification": "Flam. Liq. 3...",
    "h_phrases": "H226, H314",
    "scl_mfactor": "",
    "source": "CLP"
  },
  {
    "name": "Perfluamine",
    "cas": "338-83-0",
    "ec_number": "206-420-2",
    "classification": "",
    "h_phrases": "",
    "scl_mfactor": "",
    "source": "SVHC"
  }
]
```

**Mechanizm wyszukiwania:**
1. Przeszukuje `ExcelSourceSubstance` (baza CLP)
2. Przeszukuje `SVHCSubstance` (lista SVHC)
3. Usuwa duplikaty (po numerze CAS)
4. Limit: 50 wyników

---

## Mechanizm wyszukiwania

### Wyszukiwanie w lokalizacji

**Plik:** `static/js/location_detail.js`
```javascript
// 1. Użytkownik wpisuje frazę (min. 2 znaki)
// 2. AJAX request do /search_substances?query=...
// 3. Backend przeszukuje obie bazy (CLP + SVHC)
// 4. JavaScript wyświetla wyniki
// 5. Po kliknięciu "Dodaj" → POST /add_substance
```

### Wyszukiwanie globalne (filtrowanie)

**Plik:** `routes/export.py` → `view_all_substances()`

**Parametry URL:**
- `filter` - tekst wyszukiwania
- `physical_location` - Bieruń/Krupski Młyn
- `user_location` - nazwa lokalizacji
- `is_cmr` - true/false
- `is_svhc` - true/false
- `has_sds` - true/false
- `page` - numer strony
- `per_page` - rekordów na stronę

**Przykład:**
```
/substances/all?filter=kwas&is_cmr=true&page=2&per_page=25
```

**Algorytm:**
```python
# 1. Buduj zapytanie SQLAlchemy
query = db.session.query(Substance).join(Location)

# 2. Filtr tekstowy
if filter_query:
    # Szukaj w: nazwa, CAS, EC, klasyfikacja, H phrases
    # PLUS specjalna logika dla "CMR" i "SVHC"
    if filter_query.lower() == 'cmr':
        query = query.filter(Substance.is_cmr == True)
    elif filter_query.lower() == 'svhc':
        query = query.filter(Substance.is_svhc == True)

# 3. Filtry dropdown
if is_cmr == 'true':
    query = query.filter(Substance.is_cmr == True)

# 4. Paginacja
paginated = query.paginate(page=page, per_page=per_page)
```

---

## System uprawnień

### Dekoratory

**Plik:** `decorators.py`
```python
def view_permission_required(f):
    """Wymaga can_view lub is_admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin or current_user.can_view):
            flash('Brak uprawnień', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
```

**Użycie:**
```python
@locations_bp.route('/location/<int:location_id>')
@login_required
@view_permission_required  # Sprawdza uprawnienie
def view_location(location_id):
    # ...
```

### Macierz uprawnień

| Akcja | `is_admin` | `can_view` | `can_add` | `can_edit` | `can_delete` | `can_upload_sds` |
|-------|-----------|-----------|----------|-----------|-------------|-----------------|
| Przeglądanie | ✓ | ✓ | - | - | - | - |
| Dodaj substancję | ✓ | - | ✓ | - | - | - |
| Edytuj komentarz | ✓ | - | - | ✓ | - | - |
| Usuń substancję | ✓ | - | - | - | ✓ | - |
| Upload SDS | ✓ | - | - | - | - | ✓ |
| Zarządzaj użytkownikami | ✓ | - | - | - | - | - |

### Kontrola dostępu na poziomie komórek organizacyjnych (v2.1.0+)

**Model dostępu:** Dwupoziomowa kontrola - VIEW (przeglądanie) vs MODIFY (modyfikacja)

**Plik:** `models.py`
```python
class User:
    organizational_unit_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    def has_access_to_organizational_unit(self, location_id: int) -> bool:
        """
        Sprawdza dostęp do PRZEGLĄDANIA komórki organizacyjnej.
        - Admin: dostęp do wszystkich komórek
        - Użytkownik z przypisaniem: może przeglądać wszystkie komórki (read-only)
        - Użytkownik bez przypisania: brak dostępu
        """
        if self.is_admin:
            return True
        if self.organizational_unit_id is not None:
            return True
        return False

    def can_modify_organizational_unit(self, location_id: int) -> bool:
        """
        Sprawdza dostęp do MODYFIKACJI komórki organizacyjnej.
        - Admin: może modyfikować wszystkie komórki
        - Użytkownik: może modyfikować TYLKO swoją przypisaną komórkę
        """
        if self.is_admin:
            return True
        if self.organizational_unit_id is None:
            return False
        return self.organizational_unit_id == location_id
```

**Zastosowanie w trasach:**
```python
# routes/substances.py
@substances_bp.route('/location/<int:location_id>/add_substance', methods=['POST'])
def add_substance_to_location(location_id):
    # Sprawdź czy użytkownik może modyfikować tę komórkę
    if not current_user.can_modify_organizational_unit(location_id):
        return jsonify({
            'status': 'error',
            'message': 'Możesz dodawać substancje tylko do swojej komórki organizacyjnej.'
        }), 403
    # ... reszta logiki
```

**Macierz dostępu:**

| Rola | VIEW wszystkich komórek | MODIFY wszystkich komórek | COPY do innych komórek |
|------|-------------------------|---------------------------|------------------------|
| Administrator | ✓ Tak | ✓ Tak | ✓ Tak |
| User (z przypisaniem) | ✓ Tak (read-only) | ✗ Tylko własna komórka | ✗ Tylko do własnej komórki |
| User (bez przypisania) | ✗ Nie | ✗ Nie | ✗ Nie |

**Przykład użycia:**
```python
# Użytkownik przypisany do Laboratorium (ID: 1)

# Przeglądanie RBR-K (ID: 2)
current_user.has_access_to_organizational_unit(2)  # True - może przeglądać

# Dodawanie substancji do RBR-K
current_user.can_modify_organizational_unit(2)  # False - nie może modyfikować

# Dodawanie substancji do Laboratorium
current_user.can_modify_organizational_unit(1)  # True - może modyfikować swoją komórkę
```

**Pliki zmodyfikowane:**
- `models.py`: Dodano `organizational_unit_id` i metody dostępu
- `routes/locations.py`: Walidacja dostępu w wszystkich trasach
- `routes/substances.py`: Walidacja `can_modify_organizational_unit()` przed operacjami CRUD
- `routes/admin.py`: Obsługa przypisywania użytkowników do komórek
- `templates/location_detail.html`: Warunkowe wyświetlanie kontrolek na podstawie `can_modify_this_unit`

---

## Obsługa plików Excel

### Import bazy CLP

**Plik:** `import_excel.py`
```python
import pandas as pd
from app import create_app, db, ExcelSourceSubstance

# 1. Wczytaj Excel (pomiń pierwszy pusty wiersz!)
df = pd.read_excel('substancje_baza.xlsx', header=0, skiprows=[1])

# 2. Mapuj kolumny
column_map = {
    'International Chemical Identification': 'name',
    'CAS No': 'cas',
    'EC No': 'ec_number',
    'Classification': 'classification',
    'Unnamed: 5': 'h_phrases',
    'Specific Conc. Limits, M-factors': 'scl_mfactor'
}
df.rename(columns=column_map, inplace=True)

# 3. Import do bazy
for idx, row in df.iterrows():
    substance = ExcelSourceSubstance(
        name=row['name'],
        cas=row['cas'],
        # ...
    )
    db.session.add(substance)

db.session.commit()
```

**KRYTYCZNE:** `skiprows=[1]` pomija pierwszy pusty wiersz!

### Import listy SVHC

**Plik:** `app.py` → Flask CLI command
```python
@app.cli.command('import-svhc')
def import_svhc_command():
    df = pd.read_excel('svhc.xlsx', header=0)
    
    # Kolumny (UWAGA: mają spacje na końcu!)
    for idx, row in df.iterrows():
        substance = SVHCSubstance(
            name=str(row['Nazwa substancji ']).strip(),
            cas=str(row['Nr CAS']).strip(),
            ec_number=str(row['Nr WE']).strip(),
            reason=str(row['Powód włączenia ']).strip(),
            date_inclusion=str(row['Data włączenia ']).strip()
        )
        db.session.add(substance)
    
    db.session.commit()
```

---

## Rozwiązywanie problemów

### Problem: Substancje nie mają nazw polskich

**Przyczyna:** Nieprawidłowy import - nie pominięto pustego wiersza.

**Rozwiązanie:**
```bash
# 1. Sprawdź strukturę pliku
python check_excel.py

# 2. Upewnij się że w import_excel.py jest: skiprows=[1]
# 3. Re-import
python import_excel.py
```

### Problem: SVHC nie są oznaczane

**Przyczyna:** Nie zaimportowano listy SVHC lub flagi nie są aktualizowane.

**Diagnoza:**
```bash
python -c "from app import create_app, db, SVHCSubstance; app=create_app(); app.app_context().push(); print(SVHCSubstance.query.count())"
```

**Rozwiązanie:**
```bash
# Jeśli 0 - import SVHC
flask import-svhc

# Aktualizuj flagi w istniejących substancjach
python update_svhc_flags.py
```

### Problem: Wyszukiwarka nie znajduje substancji

**Przyczyna:** Baza CLP jest pusta.

**Diagnoza:**
```bash
python -c "from app import create_app, db, ExcelSourceSubstance; app=create_app(); app.app_context().push(); print(ExcelSourceSubstance.query.count())"
```

**Rozwiązanie:**
```bash
python import_excel.py
```

### Problem: Błąd "Flask app not found"

**Przyczyna:** Zmienna środowiskowa FLASK_APP nie jest ustawiona.

**Rozwiązanie:**
```bash
# Windows PowerShell
$env:FLASK_APP="app"

# Linux/Mac
export FLASK_APP=app

# Lub uruchom bezpośrednio
python app.py
```

### Problem: Błąd uprawnień do plików (Linux)

**Rozwiązanie:**
```bash
# Ustaw prawidłowe uprawnienia
chmod 644 instance/chem_man.db
chmod 755 instance/uploads/sds/
chmod 644 instance/uploads/sds/*.pdf
```

### Problem: Import CSV w Excelu nie pokazuje polskich znaków

**Przyczyna:** Excel nie rozpoznaje kodowania UTF-8.

**Rozwiązanie:** 
- Aplikacja używa `utf-8-sig` (BOM)
- W Excelu: Dane → Z pliku tekstowego → Kodowanie: UTF-8

### Problem: Pliki SDS zajmują za dużo miejsca

**Rozwiązanie:**
```bash
# Kompresuj stare pliki
cd instance/uploads/sds/
tar -czf ../sds_archive_$(date +%Y%m%d).tar.gz *.pdf

# Przenieś archiwum
mv ../sds_archive_*.tar.gz /backup/location/

# Usuń oryginały (UWAGA! Upewnij się że masz backup!)
# rm *.pdf
```

---

## Performance i optymalizacja

### Indeksy bazy danych

Indeksy są automatycznie tworzone przez SQLAlchemy:
```python
# models.py - przykład
name = db.Column(db.String(255), index=True)  # Indeks na name
cas = db.Column(db.String(20), index=True)     # Indeks na CAS
```

### Paginacja

**Domyślnie:** 25 rekordów na stronę (konfigurowalny w `config.py`)
```python
ITEMS_PER_PAGE = 25
```

### Cache

**Obecnie:** Brak cache - SQLite jest wystarczająco szybkie dla małych/średnich baz.

**Przyszłość:** Rozważ Redis dla >10,000 substancji w lokalizacjach.

---

## Deployment produkcyjny

### Gunicorn (Linux)
```bash
# Instalacja
pip install gunicorn

# Uruchomienie
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Z logowaniem
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile logs/access.log --error-logfile logs/error.log app:app
```

### Nginx (reverse proxy)
```nginx
server {
    listen 80;
    server_name chemman.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd service (autostart)
```ini
# /etc/systemd/system/chemman.service
[Unit]
Description=ChemMan Flask Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/chemman
ExecStart=/var/www/chemman/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable chemman
sudo systemctl start chemman
```

---

## Testowanie

### Unit testy (przygotowane do implementacji)
```python
# tests/test_utils.py
def test_is_cmr_substance():
    assert is_cmr_substance(h_phrases="H350") == True
    assert is_cmr_substance(h_phrases="H226") == False

def test_is_svhc_substance():
    # Wymaga działającej bazy
    pass
```

**Uruchomienie:**
```bash
pytest tests/
```

---

## Kontakt i wsparcie

Jeśli dokumentacja nie rozwiązuje Twojego problemu:

1. Sprawdź logi: `logs/chem_man.log`
2. Sprawdź [MAINTENANCE.md](MAINTENANCE.md) - procedury awaryjne
3. Zachowaj pełny tekst błędu + kroki do odtworzenia

---

**Aktualizacja:** 2025-01-17  
**Wersja:** 1.0
