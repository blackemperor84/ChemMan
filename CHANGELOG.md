# Historia Zmian ChemMan

Wszystkie istotne zmiany w projekcie ChemMan.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

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

## [Niezwydane] - W przygotowaniu

### 🔮 Planowane funkcje

**v1.1.0 (Q2 2025):**
- [ ] Filtrowanie po dacie dodania substancji
- [ ] Historia zmian dla pojedynczej substancji
- [ ] Eksport do Excel (XLSX) zamiast CSV
- [ ] Powiadomienia email dla administratorów
- [ ] Integracja z zewnętrznym API ECHA (aktualizacje)

**v1.2.0 (Q3 2025):**
- [ ] Moduł raportowania (raporty PDF)
- [ ] Zaawansowane statystyki i wykresy
- [ ] Multi-tenancy (wiele firm w jednej instancji)
- [ ] REST API dla integracji z innymi systemami
- [ ] Import substancji z CSV

**v2.0.0 (Q4 2025):**
- [ ] Przeprojektowanie UI (nowoczesny framework)
- [ ] Migracja z SQLite na PostgreSQL
- [ ] System powiadomień wewnętrznych
- [ ] Moduł zarządzania terminami ważności
- [ ] Skanowanie kodów QR/kreskowych

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
| 1.0.0 | 2025-01-17 | Pierwsze wydanie |

---

## Kontakt

Zgłaszanie błędów i propozycji funkcji:
- Email: [l.wichary@nitroerg.pl]
- GitHub Issues: [URL jeśli jest repo]

---

**Ostatnia aktualizacja:** 2025-01-17