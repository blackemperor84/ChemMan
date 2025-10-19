# Historia Zmian ChemMan

Wszystkie istotne zmiany w projekcie ChemMan.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

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
- Email: [admin@example.com]
- GitHub Issues: [URL jeśli jest repo]

---

**Ostatnia aktualizacja:** 2025-01-17