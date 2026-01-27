# Aktualizacja: Komórki Organizacyjne i Kontrola Dostępu

## Podsumowanie Zmian

### 1. Zmiana Nazewnictwa: "Lokalizacja" → "Komórka Organizacyjna"

**Problem:** Termin "Lokalizacja" był używany w dwóch różnych kontekstach:
- Jako miejsce przechowywania substancji (dział/jednostka organizacyjna)
- Jako fizyczna lokalizacja (Bieruń lub Krupski Młyn)

**Rozwiązanie:**
- **"Komórka organizacyjna"** - teraz oznacza dział/jednostkę organizacyjną (np. Laboratorium, Produkcja)
- **"Lokalizacja fizyczna"** - pozostała bez zmian, oznacza miejsce fizyczne (Bieruń, Krupski Młyn)

### 2. Przypisywanie Użytkowników do Komórek Organizacyjnych

**Nowa funkcjonalność:**
- Administratorzy mogą teraz przypisać użytkowników do konkretnych komórek organizacyjnych
- Użytkownicy mają dostęp **tylko** do substancji w przypisanej im komórce organizacyjnej
- Administratorzy zachowują pełny dostęp do wszystkich komórek

## Szczegóły Implementacji

### Zmiany w Bazie Danych

**Nowa kolumna w tabeli `users`:**
```sql
organizational_unit_id INTEGER NULLABLE
FOREIGN KEY -> locations(id)
```

### Kontrola Dostępu

**Nowa metoda w modelu User:**
```python
def has_access_to_organizational_unit(self, location_id: int) -> bool:
    """
    Sprawdza, czy użytkownik ma dostęp do danej komórki organizacyjnej.
    - Admin: dostęp do wszystkich komórek
    - Użytkownik: dostęp tylko do przypisanej komórki
    """
```

**Zabezpieczenia:**
- Wszystkie trasy sprawdzają dostęp przed operacjami
- Użytkownicy bez przypisanej komórki nie widzą żadnych substancji
- Blokada przenoszenia/kopiowania między komórkami dla zwykłych użytkowników

### Interfejs Administracyjny

**Zarządzanie użytkownikami** (`/admin/users`):
- Przy dodawaniu nowego użytkownika można wybrać komórkę organizacyjną
- Przy edycji uprawnień można zmienić przypisanie do komórki
- Lista użytkowników pokazuje, do której komórki jest przypisany każdy użytkownik

### Zmiany w UI

**Zaktualizowane etykiety:**
- "Lokalizacje" → "Komórki organizacyjne"
- "Użytkownik" (w filtrach) → "Komórka organizacyjna"
- Dodano informację o przypisaniu w panelu administracyjnym

## Instrukcja Wdrożenia

### Krok 1: Backup Bazy Danych
```bash
# PostgreSQL
pg_dump chemman_dev > backup_before_org_units.sql
```

### Krok 2: Zastosuj Migrację
```bash
cd "C:\Users\HP\Desktop\chem-man app"
call venv\Scripts\activate.bat
flask db upgrade
```

Jeśli wystąpią problemy z automatyczną migracją, użyj ręcznego skryptu SQL:
```sql
-- Dodaj kolumnę do tabeli users
ALTER TABLE users ADD COLUMN organizational_unit_id INTEGER;

-- Dodaj klucz obcy
ALTER TABLE users
ADD CONSTRAINT fk_users_organizational_unit_id
FOREIGN KEY (organizational_unit_id)
REFERENCES locations(id);
```

### Krok 3: Przypisz Użytkowników do Komórek

1. Zaloguj się jako administrator
2. Przejdź do **Zarządzanie Użytkownikami** (`/admin/users`)
3. Dla każdego użytkownika:
   - Kliknij "Edytuj uprawnienia"
   - Wybierz odpowiednią komórkę organizacyjną z listy rozwijanej
   - Kliknij "Zapisz"

### Krok 4: Testowanie

**Sprawdź:**
- ✓ Administrator widzi wszystkie komórki organizacyjne
- ✓ Użytkownik z przypisaną komórką widzi tylko swoją komórkę
- ✓ Użytkownik bez przypisanej komórki widzi komunikat o braku dostępu
- ✓ Użytkownik nie może przenosić substancji między komórkami
- ✓ Użytkownik nie może edytować substancji w innych komórkach

## Pliki Zmodyfikowane

### Backend:
- `models.py` - Dodano relację User ↔ Location, metodę `has_access_to_organizational_unit()`
- `routes/locations.py` - Dodano kontrolę dostępu do wszystkich endpointów
- `routes/substances.py` - Dodano kontrolę dostępu do operacji na substancjach
- `routes/admin.py` - Dodano obsługę przypisywania komórek organizacyjnych
- `migrations/versions/add_organizational_unit_id_to_users.py` - Nowa migracja

### Frontend:
- `templates/locations.html` - Zmieniono etykiety na "Komórki organizacyjne"
- `templates/location_detail.html` - Zmieniono etykiety
- `templates/all_substances.html` - Zmieniono filtry
- `templates/admin/manage_users.html` - Dodano dropdown do wyboru komórki organizacyjnej

## Uwagi Ważne

1. **Użytkownicy bez przypisania:** Jeśli użytkownik nie ma przypisanej komórki organizacyjnej (organizational_unit_id = NULL), nie będzie miał dostępu do żadnych substancji. Administrator musi przypisać każdego użytkownika do komórki.

2. **Administrator:** Konto administratora (is_admin=True) ma dostęp do wszystkich komórek niezależnie od przypisania.

3. **Bezpieczeństwo:** Wszystkie operacje (dodawanie, edycja, usuwanie, przenoszenie) sprawdzają dostęp użytkownika do komórki organizacyjnej przed wykonaniem akcji.

4. **Kompatybilność wsteczna:** Istniejące dane nie są zmieniane. Kolumna `organizational_unit_id` jest nullable, więc istniejący użytkownicy mogą działać (ale będą potrzebować przypisania do komórki).

## Przykładowe Scenariusze Użycia

### Scenariusz 1: Laboratorium i Produkcja
- Komórka "Laboratorium" - użytkownicy: jan.kowalski, anna.nowak
- Komórka "Produkcja" - użytkownicy: piotr.wisniewski

Jan i Anna widzą tylko substancje w Laboratorium. Piotr widzi tylko substancje w Produkcji.

### Scenariusz 2: Fizyczne Lokalizacje
W ramach komórki "Laboratorium" mogą być substancje w:
- Lokalizacja fizyczna: Bieruń
- Lokalizacja fizyczna: Krupski Młyn

Użytkownicy przypisani do "Laboratorium" widzą substancje z obu fizycznych lokalizacji.

## Kontakt i Pomoc

W razie pytań lub problemów:
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Dokumentacja: README.md, USER_GUIDE.md

---
**Data wdrożenia:** 2025-10-27
**Wersja:** 1.1.0
**Autor zmian:** Claude Code
