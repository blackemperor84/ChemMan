# ChemMan - Wersja Demo (Standalone)

**Wersja:** 2.1.0 Demo
**Data:** 2025-10-27
**Cel:** Prezentacja/demonstracja funkcjonalności aplikacji

---

## 🎯 Co to jest?

To jest **samodzielna wersja demonstracyjna** aplikacji ChemMan, która:
- ✅ Działa bez instalacji Python
- ✅ Działa bez instalacji PostgreSQL
- ✅ Zawiera pełną funkcjonalność
- ✅ Ma wstępnie załadowane dane (4400 CLP + 492 SVHC)
- ✅ Uruchamia się jednym kliknięciem
- ✅ Jest przenośna (można uruchomić z pendrive)

**Przeznaczenie:** Prezentacje dla zarządu, szkolenia, demonstracje przed wdrożeniem produkcyjnym.

---

## 🚀 Szybki Start

### Opcja 1: Uruchomienie z gotowego pakietu (najłatwiejsze)

Jeśli już masz spakowaną wersję demo:

1. Rozpakuj folder `ChemMan_Demo_v2.1.0.zip`
2. Wejdź do folderu `ChemMan_Demo`
3. Kliknij dwukrotnie `START_CHEMMAN_DEMO.bat`
4. Poczekaj aż otworzy się przeglądarka
5. Zaloguj się: **admin** / **Demo1234**

**To wszystko!** 🎉

### Opcja 2: Zbudowanie pakietu demo (dla developerów)

Jeśli chcesz zbudować pakiet demo od zera:

#### Krok 1: Zainstaluj PyInstaller

```bash
pip install pyinstaller
```

#### Krok 2: Przygotuj środowisko demo

```bash
# Ustaw tryb demo
set FLASK_ENV=demo
set DATABASE_URL=sqlite:///demo_chemman.db

# Utwórz bazę demo i zaimportuj dane
python build_demo.py
```

#### Krok 3: Zbuduj pakiet

```bash
# Windows
build_demo_package.bat

# Linux/Mac
bash build_demo_package.sh
```

#### Krok 4: Znajdź gotowy pakiet

Pakiet będzie w: `DEMO/dist/ChemMan_Demo/`

---

## 📦 Struktura Pakietu Demo

```
ChemMan_Demo/
├── START_CHEMMAN_DEMO.bat          # Główny plik startowy (Windows)
├── START_CHEMMAN_DEMO.sh           # Główny plik startowy (Linux/Mac)
├── chemman.exe                     # Główna aplikacja (Windows)
├── chemman                         # Główna aplikacja (Linux/Mac)
├── demo_chemman.db                 # Baza danych SQLite z danymi
├── static/                         # Pliki CSS, JS, obrazy
├── templates/                      # Szablony HTML
├── substancje_baza.xlsx            # Baza CLP (backup)
├── svhc.xlsx                       # Baza SVHC (backup)
└── README_DEMO.txt                 # Instrukcja

Rozmiar: ~150 MB
```

---

## 🔑 Domyślne Dane Logowania

**Demo:**
- **Login:** admin
- **Hasło:** Demo1234

**Uprawnienia:** Pełen dostęp (administrator)

---

## ✨ Funkcjonalność Demo

Wersja demo zawiera **wszystkie funkcje** wersji produkcyjnej:

### ✅ Dostępne funkcje:
- 📦 Zarządzanie komórkami organizacyjnymi i substancjami
- 🏢 System przypisywania użytkowników do komórek z kontrolą dostępu (v2.1.0)
- 🔍 Wyszukiwanie w bazach CLP (4400+) i SVHC (492)
- ⚠️ Detekcja CMR i SVHC
- 📄 Upload kart SDS (PDF)
- 📊 Eksport do CSV
- 👥 Zarządzanie użytkownikami
- 📜 Dziennik zmian (audit log)
- 🌍 Interfejs dwujęzyczny (PL/EN)

### ⚠️ Ograniczenia demo:
- ❌ Brak połączenia sieciowego (działa tylko lokalnie)
- ❌ Dane są usuwane po zamknięciu (można resetować)
- ⚠️ Nie nadaje się do produkcji (tylko demonstracja)

---

## 🎬 Scenariusze Prezentacji

### Scenariusz 1: Podstawowa demonstracja (5 min)

1. **Start:** Uruchom aplikację
2. **Login:** Zaloguj się jako admin
3. **Dodaj lokalizację:** "Magazyn Główny"
4. **Dodaj substancję:** Wyszukaj "Benzene", dodaj do magazynu
5. **Pokaż detekcję CMR:** Benzene automatycznie oznaczony jako CMR
6. **Upload SDS:** Dodaj kartę charakterystyki
7. **Eksport:** Wyeksportuj dane do CSV

### Scenariusz 2: Zaawansowana demonstracja (15 min)

1. **Wszystkie substancje:** Pokaż listę 4400+ substancji CLP
2. **Filtrowanie:** Filtruj po CMR, SVHC, lokalizacji
3. **Wyszukiwanie dwujęzyczne:** Szukaj po polsku i angielsku
4. **Operacje masowe:** Przenieś wiele substancji naraz
5. **Panel admina:** Zarządzanie użytkownikami
6. **Audit log:** Historia wszystkich zmian
7. **Bezpieczeństwo:** Pokaż rate limiting, uprawnienia

### Scenariusz 3: Prezentacja dla IT (30 min)

1. **Architektura:** Omów technologie (Flask, SQLite/PostgreSQL)
2. **Bezpieczeństwo:** Rate limiting, CSRF, bcrypt, MIME validation
3. **Testy:** Pokaż 242 testy, 80% pokrycia kodu
4. **Dokumentacja:** DEPLOYMENT_GUIDE.md
5. **Skalowalność:** Wytłumacz przejście SQLite → PostgreSQL
6. **Kod źródłowy:** Pokaż clean code, struktura projektu

---

## 🛠️ Troubleshooting

### Problem: "Antywirus blokuje aplikację"

**Rozwiązanie:**
- To normalne dla aplikacji spakowanych PyInstaller
- Dodaj wyjątek w antywirusie dla folderu `ChemMan_Demo`
- Lub użyj wersji podpisanej certyfikatem (produkcja)

### Problem: "Nie otwiera się przeglądarka"

**Rozwiązanie:**
1. Sprawdź czy aplikacja działa: `http://127.0.0.1:5000`
2. Otwórz ręcznie w przeglądarce
3. Sprawdź logi w `demo_chemman.log`

### Problem: "Port 5000 jest zajęty"

**Rozwiązanie:**
- Edytuj `START_CHEMMAN_DEMO.bat`
- Zmień port na inny (np. 5001, 5002)
- Lub zamknij aplikację która używa portu 5000

### Problem: "Brak danych w bazie"

**Rozwiązanie:**
1. Uruchom ponownie `build_demo.py`
2. Lub skopiuj `demo_chemman.db` z backupu

---

## 📤 Dystrybucja Wersji Demo

### Do kogoś wewnątrz firmy:

1. Spakuj folder `ChemMan_Demo/` do ZIP
2. Wyślij przez email / udostępnij na dysku sieciowym
3. Dołącz ten plik README

### Do klienta / partnera:

1. Spakuj folder + dodaj prezentację PowerPoint
2. Przygotuj video demo (opcjonalnie)
3. Wyślij wraz z DEPLOYMENT_GUIDE.md
4. Umów demo call do omówienia pytań

### Na prezentację w firmie:

1. Skopiuj na laptopa prezentacyjnego
2. Przetestuj dzień wcześniej
3. Przygotuj scenariusz prezentacji (powyżej)
4. Miej backup na pendrive

---

## 🔄 Aktualizacja Wersji Demo

Gdy pojawi się nowa wersja produkcyjna:

```bash
# 1. Pobierz najnowszy kod
git pull origin master

# 2. Przebuduj pakiet demo
cd DEMO
python build_demo.py
build_demo_package.bat

# 3. Nowy pakiet w dist/
```

---

## 🆚 Demo vs Produkcja

| Feature | Demo | Produkcja |
|---------|------|-----------|
| Instalacja | Nie wymagana | Python + PostgreSQL |
| Baza danych | SQLite (embedded) | PostgreSQL |
| Użytkownicy | 1 (admin) | Wielu |
| Dostęp sieciowy | Lokalny | Przez LAN/Internet |
| Backup | Ręczny | Automatyczny |
| SSL | Nie | Tak |
| Monitoring | Nie | Tak |
| Rozmiar | ~150 MB | ~50 MB (bez exe) |

---

## 📞 Wsparcie

Problemy z wersją demo?

1. **Sprawdź logi:** `demo_chemman.log`
2. **Sprawdź dokumentację:** `DEPLOYMENT_GUIDE.md`
3. **Przebuduj pakiet:** `build_demo.py`
4. **Kontakt IT:** [email IT support]

---

## 📜 Licencja

© 2025 NITROERG
Wersja Demo - tylko do celów prezentacyjnych/demonstracyjnych

---

**Miłej prezentacji!** 🎉
