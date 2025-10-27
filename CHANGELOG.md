# Historia Zmian ChemMan

Wszystkie istotne zmiany w projekcie ChemMan.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

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
| 2.1.0 | 2025-10-27 | System komórek organizacyjnych z kontrolą dostępu |
| 2.0.0 | 2025-10-22 | Przejście na PostgreSQL, testy automatyczne, dokumentacja |
| 1.0.0 | 2025-01-17 | Pierwsze wydanie |

---

## Kontakt

Zgłaszanie błędów i propozycji funkcji:
- Email: [l.wichary@nitroerg.pl]
- GitHub Issues: [https://github.com/blackemperor84/ChemMan/issues](https://github.com/blackemperor84/ChemMan/issues)

---

**Ostatnia aktualizacja:** 2025-10-27