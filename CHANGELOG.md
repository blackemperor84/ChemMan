# Historia Zmian ChemMan

Wszystkie istotne zmiany w projekcie ChemMan.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

---

## [2.3.1] - 2026-08-16

### 🛠️ Wzmocnienie Importu, Poprawki i Porządki - Patch Release

Wydanie utrzymaniowe skupione na niezawodności importu baz CLP/SVHC, poprawkach
błędów, usunięciu przestarzałych wywołań (deprecations) oraz uporządkowaniu kodu.
Bez zmian w interfejsie użytkownika. Wszystkie 242 testy przechodzą.

#### 🐛 Poprawiono

**Import baz danych (`utils/database_import.py`):**
- Import z zachowaniem danych (merge-preserve): przy ponownym imporcie istniejące
  wartości `scl_mfactor` / `h_phrases` / `classification` (CLP) oraz `reason` /
  `date_inclusion` (SVHC) są zachowywane, gdy nowy plik ma te kolumny puste.
  Priorytet dopasowania: CAS → EC → dokładna nazwa. Chroni ręcznie uzupełnione
  dane SCL/M-factor przed nadpisaniem przez eksporty ECHA CHEM, które pomijają te kolumny.
- Obsługa nowego formatu nagłówków ECHA CHEM dla listy SVHC (dopasowanie po
  słowach kluczowych zamiast dokładnego dopasowania z końcową spacją). Jawny błąd,
  gdy nie znaleziono kolumny z nazwą substancji.
- Normalizacja pustych wartości: NaN / 'nan' / 'None' / białe znaki są zapisywane
  jako prawdziwy SQL NULL. Naprawia stare rekordy, w których literał 'NaN'
  powodował wyniki wyszukiwania bez nazwy.

**Trasy (routes):**
- `substances.py`: usunięto podwójne `db.session.add/flush`; dodano zabezpieczenia
  None przy wyszukiwaniu lokalizacji.
- `admin.py`: usunięto obejście `username == 'admin'`, które omijało `is_admin`;
  dodano `functools.wraps` do dekoratora `admin_required`.
- `locations.py`: zastąpiono błędne użycie `accept_mimetypes.accept_json` funkcją
  pomocniczą `_wants_json()`; naprawiono wywołanie `handle_exception`.
- `export.py`: API wyszukiwania odfiltrowuje rekordy z pustą nazwą i usuwa
  duplikaty wewnątrz listy SVHC (źródło powiela każdy wpis dla pod-substancji).

#### 🔧 Zmieniono

**Usunięto przestarzałe wywołania (deprecations):**
- `datetime.utcnow()` → nowa funkcja pomocnicza `utcnow()` (bezpieczna dla Python 3.12+).
- `Model.query.get()` → `db.session.get()` w kodzie produkcyjnym.
- `traceback.print_exc()` → `logger.exception()`.
- `commands.py`: surowy SQL opakowany w `text()` (zgodność z SQLAlchemy 2.x) + jawny commit.

**Refaktoryzacja:**
- Wyodrębniono `_build_substance_query()` w `routes/export.py`, eliminując ~150
  linii zduplikowanych między `export_all_csv` a `view_all_substances`.
- Dodano `joinedload(Substance.sds_files)` w widokach lokalizacji i wszystkich
  substancji (naprawa problemu N+1 przy leniwym ładowaniu relacji SDS).
- CLI `import-excel` / `import-svhc` korzystają teraz ze wspólnych funkcji z
  `utils.database_import` zamiast duplikować logikę mapowania.

#### 🗄️ Dane

- Zaktualizowano `svhc.xlsx` do aktualnej listy kandydackiej SVHC ECHA
  (aktualizacja luty 2026): 1029 rekordów (poprzednio 492), obejmujących wpisy
  wraz z pod-substancjami/solami. Wyszukiwarka automatycznie usuwa duplikaty.

#### 🧹 Porządki

- Usunięto `config_backup.py`, zbłąkany `chem_man.log` w katalogu głównym, martwą
  funkcję `configure_logging()` oraz ~100 linii zakomentowanego kodu
  `search_substances_in_excel`.
- Oczyszczono `requirements.txt` z niepotrzebnych pakietów (nodejs, react,
  PyQt5*, distlib, virtualenv itp.); dodano brakujący `Flask-Limiter`.

#### 🎬 Demo

- `DEMO/build_demo.py` korzysta ze wspólnych funkcji importu, więc budowanie demo
  automatycznie dziedziczy wszystkie poprawki. Automatyczne wykrywanie źródła
  `svhc.xlsx` (lub `svhc__current.xlsx`).

---

## [2.3.0] - 2026-01-28

### 🗄️ Aktualizacja Baz Danych przez Interfejs - New Feature!

#### ✨ Dodano

**Zarządzanie Bazami Danych przez Web:**
- Nowa strona administracyjna `/admin/databases` do zarządzania bazami substancji
- Upload i import bazy CLP (substancje_baza.xlsx) bezpośrednio przez przeglądarkę
- Upload i import listy SVHC (svhc.xlsx) bezpośrednio przez przeglądarkę
- Wyświetlanie statystyk baz danych (liczba rekordów CLP i SVHC)
- Informacje o ostatnim imporcie (data, użytkownik)
- Modal potwierdzenia przed importem z ostrzeżeniem o nadpisaniu danych

**Nowe uprawnienie użytkownika:**
- Dodano uprawnienie `can_update_databases` do modelu User
- Administratorzy mają domyślnie dostęp do funkcji aktualizacji baz
- Możliwość nadania uprawnienia wybranym użytkownikom przez panel admina
- Checkbox w formularzu dodawania/edycji użytkownika

**Walidacja plików Excel:**
- Sprawdzanie rozszerzenia pliku (.xlsx, .xls)
- Walidacja MIME type (magic bytes) dla plików Excel
- Walidacja struktury kolumn przed importem
- Limit rozmiaru pliku (16 MB)
- Obsługa wartości NaN - automatyczna konwersja na puste wartości

**Nawigacja:**
- Link "Bazy Danych" w menu administratora (base.html)

#### 🔧 Zmieniono

**Wyświetlanie danych:**
- Poprawiono wyświetlanie wartości "NaN" w tabelach - teraz wyświetlane jako puste pola
- Poprawiono wyrównanie pionowe i poziome w kolumnach Klasyfikacja, Zwroty H, SCL/M-factor
- Poprawiono wyrównanie przycisków akcji w tabeli substancji

#### 📦 Techniczne

**Nowe pliki:**
- `utils/database_import.py` - serwis importu z funkcjami walidacji i importu
- `templates/admin/manage_databases.html` - szablon strony zarządzania bazami
- `static/css/manage_databases.css` - style dla strony zarządzania bazami
- `migrations/versions/add_can_update_databases_permission.py` - migracja bazy danych

**Zmodyfikowane pliki:**
- `models.py` - dodano pole `can_update_databases` do modelu User
- `decorators.py` - dodano dekorator `update_databases_permission_required`
- `routes/admin.py` - dodano trasy `/databases`, `/databases/upload/clp`, `/databases/upload/svhc`
- `templates/base.html` - dodano link do zarządzania bazami w menu admina
- `templates/admin/manage_users.html` - dodano checkbox dla nowego uprawnienia
- `templates/location_detail.html` - poprawiono filtrowanie wartości NaN
- `templates/all_substances.html` - poprawiono filtrowanie wartości NaN
- `static/css/location_detail.css` - poprawiono style wyrównania kolumn

**Audit logging:**
- Nowe typy akcji: `IMPORT_CLP_DATABASE`, `IMPORT_SVHC_DATABASE`
- Logowanie: nazwa pliku, liczba zaimportowanych rekordów, użytkownik

---

## [2.2.1] - 2026-01-18

### 🐛 Poprawki Błędów - Patch Release

#### 🐛 Naprawiono

**Wyszukiwanie CMR/SVHC:**
- Wyszukiwanie "CMR" w widoku globalnym teraz znajduje zarówno substancje oznaczone jako CMR (`is_cmr`) jak i mieszaniny zawierające CMR (`contains_cmr`)
- Wyszukiwanie "SVHC" w widoku globalnym teraz znajduje zarówno substancje oznaczone jako SVHC (`is_svhc`) jak i mieszaniny zawierające SVHC (`contains_svhc`)
- Zaawansowane filtry (dropdowny CMR/SVHC) również uwzględniają obie flagi
- Eksport CSV respektuje te same zasady filtrowania

**Dialog Usuwania:**
- Poprawiono formatowanie okna potwierdzenia usunięcia substancji
- Dialog teraz pokazuje tylko nazwę substancji (oczyszczoną, max 60 znaków) zamiast całej zawartości komórki z odznakami i flagami
- Lepsza czytelność komunikatu potwierdzenia

**Stopka:**
- Rok w stopce (© 2025) teraz aktualizuje się automatycznie do aktualnego roku
- Używa `{{ now().year }}` w szablonie Jinja2 zamiast zakodowanej wartości

#### 📦 Techniczne

**Lokalizacje zmian:**
- `routes/export.py`: Zaktualizowano logikę filtrowania tekstowego i dropdown'ów (używa `or_()` dla `is_*/contains_*`)
- `static/js/location_detail.js`: Pobieranie nazwy substancji z `.substance-name` div, czyszczenie whitespace, ograniczenie długości
- `templates/base.html`: Stopka używa `{{ now().year }}` zamiast zakodowanego roku

---

## [2.2.0] - 2026-01-18

### 📁 Wiele Kart SDS i Zaawansowana Edycja - Major Feature Update!

#### ✨ Dodano

**Wiele Kart SDS na Substancję:**
- Każda substancja może mieć wiele kart SDS od różnych producentów
- Pole "Producent" do śledzenia źródła karty SDS
- Wyświetlanie oryginalnej nazwy pliku w kolumnie SDS
- Śledzenie znacznika czasu przesłania dla każdej karty SDS
- Możliwość dodawania, przeglądania i usuwania wielu kart SDS
- Wyświetlanie wszystkich kart SDS w widoku lokalizacji i widoku globalnym

**Liczniki Substancji i Kart SDS:**
- Widok szczegółów komórki organizacyjnej: liczba substancji i kart SDS na komórkę
- Widok globalny: całkowita liczba substancji i kart SDS we wszystkich komórkach
- Liczniki aktualizują się dynamicznie po dodaniu/usunięciu substancji lub kart SDS
- Wyświetlanie w stylizowanych sekcjach z ikonami

**Ręczne Flagi CMR/SVHC:**
- Substancje czyste: checkboxy "Jest CMR" / "Jest SVHC"
- Mieszaniny: checkboxy "Zawiera CMR" / "Zawiera SVHC"
- Flagi można ustawić podczas ręcznego dodawania lub edycji inline
- Ręczne flagi nadpisują autodetekcję, gdy są wyraźnie ustawione
- Autodetekcja nadal działa dla substancji bez ręcznych flag
- Wizualne odznaki dla wszystkich flag (czerwone dla CMR, żółte dla SVHC, złote dla flag mieszanin)

**Pełna Edycja Inline:**
- Wszystkie pola substancji edytowalne bezpośrednio w wierszu tabeli
- Pola edytowalne: nazwa, CAS, EC, klasyfikacja, zwroty H, SCL/M-factor, lokalizacja fizyczna, komentarz
- Flagi CMR/SVHC edytowalne inline
- Przyciski Zapisz/Anuluj w każdym wierszu
- Tryb widoku/edycji z przełączaniem za pomocą przycisków
- Pola edycyjne dopasowane do szerokości kolumn

**Ulepszenia UI:**
- Poprawione wyrównanie checkboxów w trybie edycji i formularzu ręcznego dodawania
- Fieldset flag CMR/SVHC zajmuje pełną szerokość formularza
- Pola edycyjne z ograniczoną szerokością dopasowaną do kolumn
- Responsywny układ formularza (2-kolumnowy grid)
- Lepsze marginesy i odstępy w formularzach

#### 🔧 Zmieniono

**Schemat Bazy Danych:**
- Dodano model `SDSFile` dla relacji jeden-do-wielu z substancjami
- Tabela `sds_files`: kolumny: id, substance_id, filename, original_filename, manufacturer, upload_timestamp
- Dodano pola `contains_cmr` i `contains_svhc` Boolean do modelu `Substance`
- Zachowano pole `sds_filename` dla kompatybilności wstecznej

**API i Backend:**
- Zaktualizowano endpoint `/substance/<id>/edit` aby przyjmował wszystkie pola włącznie z flagami CMR/SVHC
- Zaktualizowano endpoint `/location/<id>/add_manual` aby przyjmował flagi CMR/SVHC
- Zaktualizowano endpoint `/substance/<id>/upload_sds` dla wielu plików z danymi producenta
- Zaktualizowano endpoint `/sds/delete` aby przyjmował parametr `sds_file_id`
- Dodano logikę liczników w `routes/locations.py` i `routes/export.py`
- Ulepszona obsługa relacji SQLAlchemy dla wielu kart SDS

**Frontend:**
- Refaktoryzacja edycji z modalnej na edycję inline w wierszach
- Zaktualizowano `templates/location_detail.html` z trybem widoku/edycji inline
- Zaktualizowano `templates/all_substances.html` do wyświetlania wielu kart SDS
- Dodano checkboxy CMR/SVHC do formularza ręcznego dodawania
- Zaktualizowano `static/js/location_detail.js` z obsługą edycji inline
- CSS: `static/css/base.css` - układ formularza i style checkboxów
- CSS: `static/css/location_detail.css` - tryb edycji i ograniczenia szerokości pól

#### 🐛 Naprawiono

- Szerokość pól edycyjnych teraz dopasowana do szerokości kolumn tabeli
- Wyrównanie checkboxów CMR/SVHC w trybie edycji i formularzu ręcznego dodawania
- Szerokość fieldset w formularzu ręcznego dodawania zajmuje pełną szerokość formularza (grid-column: 1 / 3)
- Wiele kart SDS teraz wyświetla się poprawnie w widoku globalnym
- Poprawiono style flexbox dla etykiet i checkboxów
- Poprawiono układy grid dla spójności formularzy

#### 📦 Techniczne

**Migracja Bazy Danych:**
- Skrypt migracyjny: `migrate_to_multi_sds.py`
- Migruje stare pole `sds_filename` do nowego modelu `SDSFile`
- Bezpieczna migracja bez utraty danych
- Automatyczne tworzenie rekordów `SDSFile` z istniejących kart SDS

**Lokalizacje Plików:**
- Modele: `models.py` (linie: SDSFile model, Substance.contains_cmr/contains_svhc)
- Routy substancji: `routes/substances.py:update_substance()`, `add_manual_substance()`
- Routy plików: `routes/files.py:upload_sds()`, `delete_sds()`
- Routy lokalizacji: `routes/locations.py:view_location()` (liczniki i lista kart SDS)
- Routy eksportu: `routes/export.py:view_all_substances()` (globalne liczniki)
- Szablony: `templates/location_detail.html`, `templates/all_substances.html`
- JavaScript: `static/js/location_detail.js` (obsługa edycji inline)
- CSS: `static/css/base.css` (linie 390-414), `static/css/location_detail.css`

---

## [2.1.0] - 2025-10-27

### 🏢 System Komórek Organizacyjnych - Major Feature Update!

#### ✨ Dodano

**Zarządzanie Komórkami Organizacyjnymi:**
- Zmieniono terminologię: "Lokalizacja" → "Komórka Organizacyjna"
- Rozróżnienie między komórkami organizacyjnymi (działy/jednostki) a lokalizacjami fizycznymi (Bieruń/Krupski Młyn)
- System przypisywania użytkowników do konkretnych komórek organizacyjnych
- Dwupoziomowy model kontroli dostępu:
  - **Przeglądanie (VIEW)**: Wszyscy użytkownicy z przypisaną komórką mogą przeglądać wszystkie komórki
  - **Modyfikacja (MODIFY)**: Użytkownicy mogą modyfikować tylko swoją przypisaną komórkę
- Ograniczenie kopiowania/przenoszenia substancji tylko do przypisanej komórki organizacyjnej

**Funkcje nawigacyjne:**
- Klikalne wiersze w widoku "Wszystkie Substancje" - kliknięcie substancji przekierowuje do komórki organizacyjnej, w której jest przechowywana
- Inteligentna obsługa kliknięć: linki (np. do SDS) działają normalnie, kliknięcie w dowolną część wiersza przekierowuje do komórki
- Wizualna informacja o klikalności (kursor pointer na hoverze)

**Baza danych:**
- Nowa kolumna `organizational_unit_id` w tabeli `users`
- Foreign key do tabeli `locations` (komórek organizacyjnych)
- Relacja `users` w modelu `Location`

**Model dostępu:**
- `has_access_to_organizational_unit()` - sprawdza dostęp do przeglądania
- `can_modify_organizational_unit()` - sprawdza dostęp do modyfikacji
- Walidacja na poziomie backendu dla wszystkich operacji CRUD
- Filtrowanie dropdown'ów kopiowania/przenoszenia na podstawie przypisanej komórki

**Panel administratora:**
- Możliwość przypisywania użytkowników do komórek organizacyjnych
- Wyświetlanie przypisanej komórki dla każdego użytkownika
- Dropdown wyboru komórki organizacyjnej w formularzach użytkownika

#### 🔧 Zmieniono

**Interfejs:**
- `templates/base.html`: "Lista Lokalizacji" → "Komórki Organizacyjne"
- `templates/locations.html`: Zaktualizowano terminologię i warunkowe wyświetlanie przycisków edycji
- `templates/location_detail.html`: Warunkowe wyświetlanie kontrolek edycji na podstawie `can_modify_this_unit`
- `templates/admin/manage_users.html`: Dodano selektor komórki organizacyjnej

**Backend:**
- `models.py`: Dodano metody `has_access_to_organizational_unit()` i `can_modify_organizational_unit()`
- `routes/locations.py`:
  - `index()` - wszyscy użytkownicy z przypisaniem widzą wszystkie komórki
  - `view_location()` - dodano flagę `can_modify` i filtrowanie `other_locations`
  - Walidacja uprawnień używa `can_modify_organizational_unit()`
- `routes/substances.py`: Wszystkie trasy modyfikacji sprawdzają `can_modify_organizational_unit()`
- `routes/admin.py`: Obsługa `organizational_unit_id` w formularzach użytkownika

#### 🧪 Testy

**Zaktualizowano:**
- `tests/conftest.py`: Fixture `test_user` przypisuje użytkownika do `test_location`
- `tests/test_routes_substances.py`: Zaktualizowano test `test_add_manual_location_not_found` (403 zamiast 404)
- `tests/test_routes_locations.py`: Zaktualizowano test `test_delete_location_protected_admin_location`
- ✅ Wszystkie 242 testy przechodzą pomyślnie

#### 📚 Dokumentacja

**Dodano:**
- `ORGANIZATIONAL_UNITS_UPDATE.md`: Dokumentacja początkowej implementacji
- `ACCESS_CONTROL_UPDATE.md`: Dokumentacja zaktualizowanego modelu dostępu (v1.2.0)
- `COPY_RESTRICTION_FIX.md`: Dokumentacja ograniczeń kopiowania (v1.2.1)
- Zaktualizowano `TESTING_GUIDE.md`: Nowe scenariusze testowe dla kontroli dostępu

#### 🔒 Bezpieczeństwo

**Ulepszone:**
- Walidacja uprawnień na poziomie backendu dla wszystkich operacji
- Filtrowanie UI oparte na uprawnieniach (nie tylko ukrywanie przycisków)
- Ochrona przed bezpośrednim dostępem przez API
- Komunikaty błędów 403 przy próbach nieupoważnionych operacji

#### ⚠️ Breaking Changes

**Dla istniejących użytkowników:**
1. Terminologia w interfejsie zmieniona na "Komórka Organizacyjna"
2. Użytkownicy bez przypisanej komórki organizacyjnej nie mają dostępu do żadnych danych
3. Użytkownicy mogą modyfikować tylko swoją przypisaną komórkę

#### 🔄 Instrukcje migracji

Dla istniejących instalacji:

1. Dodaj kolumnę do bazy danych:
```sql
ALTER TABLE users ADD COLUMN organizational_unit_id INTEGER;
ALTER TABLE users ADD CONSTRAINT fk_users_organizational_unit_id
    FOREIGN KEY (organizational_unit_id) REFERENCES locations(id);
```

Lub użyj skryptu:
```bash
python add_org_unit_column.py
```

2. Przypisz użytkowników do komórek organizacyjnych:
   - Zaloguj się jako administrator
   - Przejdź do "Zarządzaj Użytkownikami"
   - Dla każdego użytkownika wybierz "Komórka organizacyjna"
   - Zapisz zmiany

3. Restart aplikacji

**Zachowanie administratorów:**
- Administratorzy zachowują pełny dostęp do wszystkich komórek organizacyjnych
- Brak zmian w funkcjonalności dla kont administratorów

---

## [2.0.0] - 2025-10-22

### 🎉 Wersja gotowa do produkcji - Major Update!

#### 💾 Przejście na PostgreSQL (Breaking Change)

**Dodano:**
- PostgreSQL jako główna baza danych (zamiast SQLite)
- Obsługa wielu użytkowników jednocześnie
- Kolumny TEXT dla długich danych (CAS, EC, nazwy do 2048 znaków)
- Automatyczne tworzenie użytkownika admin (`create_admin.py`)

**Zmieniono:**
- `models.py`: Zmieniono VARCHAR na TEXT dla `name`, `cas`, `ec_number`
- `config.py`: Dodano wsparcie PostgreSQL przez DATABASE_URL
- `requirements.txt`: Dodano `psycopg2-binary==2.9.11`

**Naprawiono:**
- `import_excel.py`: Poprawiono konwersję typów danych (pandas → PostgreSQL)
- `import_svhc.py`: Poprawiono konwersję typów danych
- Usunięto błędy "database locked" przy wielu użytkownikach

#### 🧪 Infrastruktura testowa (242 testy, 80% pokrycia)

**Dodano:**
- Kompletną infrastrukturę testową z pytest
- 242 testy automatyczne:
  - 29 testów autentykacji (97% pokrycia)
  - 41 testów substancji (90% pokrycia)
  - 40 testów lokalizacji (87% pokrycia)
  - 25 testów plików (86% pokrycia)
  - 26 testów admina (85% pokrycia)
  - 20 testów eksportu (28% pokrycia)
  - 31 testów detekcji CMR
  - 30 testów detekcji SVHC
- 80% całkowitego pokrycia kodu
- Testy izolacji uprawnień użytkowników
- Testy bezpieczeństwa plików (MIME validation)

**Pliki testowe:**
- `tests/conftest.py`: Fixtures i konfiguracja pytest
- `tests/test_routes_auth.py`: Testy autentykacji
- `tests/test_routes_substances.py`: Testy CRUD substancji
- `tests/test_routes_locations.py`: Testy lokalizacji
- `tests/test_routes_files.py`: Testy uploadu plików
- `tests/test_routes_admin.py`: Testy panelu admin
- `tests/test_routes_export.py`: Testy eksportu
- `tests/test_cmr_detection.py`: Testy detekcji CMR
- `tests/test_svhc_detection.py`: Testy detekcji SVHC

#### 🔒 Ulepszenia bezpieczeństwa

**Dodano:**
- Ulepszone limitowanie prędkości (rate limiting) z osobnym modułem
- Lepsze sprawdzanie typów MIME dla plików PDF
- Ulepszona walidacja danych wejściowych
- Wymuszenie zmiany domyślnego hasła admina

**Zmieniono:**
- `limiter.py`: Wydzielono do osobnego modułu
- `routes/auth.py`: Poprawiono obsługę błędów logowania
- `routes/files.py`: Ulepszona walidacja MIME plików

#### 📚 Dokumentacja

**Dodano:**
- `DEPLOYMENT_GUIDE.md`: Kompletny przewodnik wdrożenia produkcyjnego (500+ linii)
  - Instrukcje dla Linux i Windows
  - Konfiguracja PostgreSQL
  - Serwery WSGI (Gunicorn/Waitress)
  - Reverse proxy (nginx/Apache)
  - Certyfikaty SSL/TLS
  - Automatyczne kopie zapasowe
  - Monitoring i utrzymanie
  - Troubleshooting
- `TODO.md`: Roadmap i postępy projektu
- `SESSION_SUMMARY_*.md`: Dokumentacja sesji rozwojowych
- `.env.example`: Przykładowa konfiguracja
- `.gitignore`: Ignorowanie plików środowiskowych

**Zaktualizowano:**
- `readme.md`: Dodano informacje o PostgreSQL i testach
- `installation.md`: Dodano instrukcje instalacji PostgreSQL
- `changelog.md`: Ten plik

#### 🗂️ Struktura projektu

**Dodano:**
- `deployment/`: Skrypty migracji i konfiguracji
  - `setup_postgresql.py`: Automatyczna konfiguracja bazy
  - `migrate_to_postgresql.py`: Skrypt migracji danych
  - `check_data_lengths.py`: Diagnostyka długości danych
- `create_admin.py`: Skrypt tworzenia admina

**Usunięto:**
- `routes/auth_backup.py`: Niepotrzebna kopia zapasowa
- `routes/files_backup.py`: Niepotrzebna kopia zapasowa

#### 🔧 Poprawki techniczne

**Poprawiono:**
- Obsługę NaN w pandas podczas importu danych
- Batch commits w importach (co 100/50 rekordów)
- Izolację testów (fixture `db_session`)
- Konflikty nazw użytkowników w testach
- Pętle przekierowań w testach uprawnień

#### 📊 Statystyki

- **Testy:** 242 (+242)
- **Pokrycie kodu:** 80% (+80%)
- **Linie kodu testów:** ~2500
- **Dokumentacja:** ~1500 linii
- **Bezpieczeństwo:** Rate limiting, MIME validation, input validation
- **Gotowość produkcyjna:** ✅

#### ⚠️ Breaking Changes

1. **Baza danych:** Wymagana migracja z SQLite na PostgreSQL
2. **Python:** Minimalna wersja 3.11+ (poprzednio 3.8+)
3. **Zależności:** Wymagany `psycopg2-binary`
4. **Konfiguracja:** Wymagany plik `.env` z `DATABASE_URL`

#### 🔄 Instrukcje migracji

Dla użytkowników migrujących z v1.0.0:

1. Zainstaluj PostgreSQL 14+
2. Utwórz bazę danych i użytkownika
3. Zaktualizuj kod: `git pull origin main`
4. Zainstaluj zależności: `pip install -r requirements.txt`
5. Skonfiguruj `.env` (skopiuj z `.env.example`)
6. Utwórz schemat: `db.create_all()`
7. Zaimportuj dane: `python import_excel.py && python import_svhc.py`
8. Utwórz admina: `python create_admin.py`
9. Uruchom testy: `pytest tests/`

Zobacz [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) dla szczegółów.

---

## [1.0.0] - 2025-01-17

### 🎉 Wydanie początkowe

Pierwsza stabilna wersja systemu ChemMan.

#### ✨ Dodano

**Podstawowe funkcje:**
- System logowania i autentykacji użytkowników
- Zarządzanie lokalizacjami (dodawanie, edycja, usuwanie)
- Zarządzanie substancjami w lokalizacjach
- System uprawnień użytkowników (9 poziomów uprawnień)
- Panel administratora

**Bazy danych:**
- Import bazy CLP (4400+ substancji z ECHA)
- Import listy SVHC (492 substancje)
- Automatyczne oznaczanie substancji CMR
- Automatyczne oznaczanie substancji SVHC
- Dwujęzyczne nazwy substancji (angielski/polski)

**Wyszukiwanie:**
- Wyszukiwanie substancji w bazie CLP
- Wyszukiwanie substancji w bazie SVHC
- Wyszukiwanie dwujęzyczne (polski i angielski)
- Globalny widok wszystkich substancji z filtrowaniem
- Zaawansowane filtry (lokalizacja, CMR, SVHC, SDS)

**Karty charakterystyki (SDS):**
- Upload plików PDF (max 16 MB)
- Podgląd i pobieranie kart SDS
- Wymiana kart SDS na nowsze wersje
- Timestamp ostatniej aktualizacji

**Eksport danych:**
- Eksport substancji z lokalizacji do CSV
- Eksport wszystkich substancji do CSV
- Eksport z zastosowanymi filtrami
- Format zgodny z Excel (UTF-8 BOM)

**Operacje masowe:**
- Przenoszenie wielu substancji między lokalizacjami
- Kopiowanie substancji do innych lokalizacji
- Zaznaczanie wielu substancji checkboxami

**Audit log:**
- Dziennik wszystkich zmian w systemie
- Zapisywanie: kto, kiedy, co zmienił
- Widok dziennika w panelu admina

**Interfejs:**
- Responsywny design (desktop/tablet/mobile)
- Toast notifications (powiadomienia)
- Paginacja po stronie serwera
- Przyjazny interfejs użytkownika

#### 🔧 Szczegóły techniczne

**Backend:**
- Flask 3.0.0
- SQLAlchemy ORM
- SQLite database
- Flask-Login authentication
- Bcrypt password hashing

**Frontend:**
- Vanilla JavaScript (bez frameworków)
- CSS Grid i Flexbox
- AJAX requests
- Dynamiczne ładowanie danych

**Bezpieczeństwo:**
- CSRF protection
- Password hashing (bcrypt)
- Session management
- Permission-based access control

---

## Typy zmian

- **✨ Dodano** - nowe funkcje
- **🔧 Zmieniono** - zmiany w istniejących funkcjach
- **🐛 Naprawiono** - poprawki błędów
- **🗑️ Usunięto** - usunięte funkcje
- **⚠️ Wycofano** - funkcje oznaczone do usunięcia
- **🔒 Bezpieczeństwo** - poprawki bezpieczeństwa

---

## Wersjonowanie

Projekt stosuje [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x) - zmiany niezgodne wstecz
- **MINOR** (x.1.x) - nowe funkcje, zgodne wstecz
- **PATCH** (x.x.1) - poprawki błędów, zgodne wstecz

---

## Historia wydań

| Wersja | Data | Główne zmiany |
|--------|------|---------------|
| 2.3.1 | 2026-08-16 | Wzmocnienie importu (merge-preserve), poprawki, porządki, aktualizacja listy SVHC |
| 2.3.0 | 2026-01-28 | Aktualizacja baz danych CLP/SVHC przez interfejs web |
| 2.2.1 | 2026-01-18 | Poprawki wyszukiwania CMR/SVHC, dialog usuwania |
| 2.2.0 | 2026-01-18 | Wiele kart SDS, edycja inline, flagi CMR/SVHC |
| 2.1.0 | 2025-10-27 | System komórek organizacyjnych z kontrolą dostępu |
| 2.0.0 | 2025-10-22 | Przejście na PostgreSQL, testy automatyczne, dokumentacja |
| 1.0.0 | 2025-01-17 | Pierwsze wydanie |

---

## Kontakt

Zgłaszanie błędów i propozycji funkcji:
- Email: [l.wichary@nitroerg.pl]
- GitHub Issues: [https://github.com/blackemperor84/ChemMan/issues](https://github.com/blackemperor84/ChemMan/issues)

---

**Ostatnia aktualizacja:** 2026-01-28