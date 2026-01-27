# ChemMan Demo - Szybki Start

## 🎯 Cel

Utworzenie **samodzielnego pakietu demo**, który działa bez instalacji.

---

## 🚀 Budowanie pakietu demo

### Wymagania wstępne

Potrzebujesz tylko:
- Python 3.11+ (już zainstalowany, jeśli uruchamiasz wersję deweloperską)
- Wszystkie zależności z `requirements.txt` (już zainstalowane)

### Krok po kroku budowania

#### Windows

```powershell
# 1. Przejdź do folderu DEMO
cd DEMO

# 2. Uruchom skrypt budowania
build_demo_package.bat

# 3. Poczekaj na zakończenie budowania (3-5 minut)

# 4. Pakiet gotowy w: dist\ChemMan_Demo\
```

#### Linux/Mac

```bash
# 1. Przejdź do folderu DEMO
cd DEMO

# 2. Nadaj uprawnienia wykonywania skryptowi
chmod +x build_demo_package.sh

# 3. Uruchom skrypt budowania
./build_demo_package.sh

# 4. Poczekaj na zakończenie budowania (3-5 minut)

# 5. Pakiet gotowy w: dist/ChemMan_Demo/
```

---

## 📦 Co zostanie utworzone

Po zbudowaniu będziesz mieć:

```
dist/ChemMan_Demo/
├── START_CHEMMAN_DEMO.bat     # ← Dwukrotnie kliknij, aby uruchomić (Windows)
├── START_CHEMMAN_DEMO.sh      # ← Uruchom na Linux/Mac
├── chemman_demo.exe           # Główny plik wykonywalny (Windows)
├── chemman_demo               # Główny plik wykonywalny (Linux/Mac)
├── demo_chemman.db            # Baza danych ze wszystkimi danymi
├── static/                    # Zasoby webowe
├── templates/                 # Szablony HTML
├── substancje_baza.xlsx       # Dane CLP (backup)
├── svhc.xlsx                  # Dane SVHC (backup)
├── README.txt                 # Instrukcje
└── [wiele plików DLL/SO]      # Zależności

Całkowity rozmiar: ~150 MB
```

---

## ✅ Testowanie demo

### Na Twoim komputerze (przed dystrybucją)

```bash
# 1. Przejdź do zbudowanego pakietu
cd dist/ChemMan_Demo

# 2. Windows: Dwukrotnie kliknij START_CHEMMAN_DEMO.bat
#    Linux/Mac: ./START_CHEMMAN_DEMO.sh

# 3. Przeglądarka otworzy się automatycznie na http://127.0.0.1:5000

# 4. Logowanie:
#    Nazwa użytkownika: admin
#    Hasło: Demo1234

# 5. Przetestuj wszystkie funkcje!
```

---

## 📤 Dystrybucja demo

### Opcja 1: Plik ZIP (zalecane)

```powershell
# Windows
Compress-Archive -Path dist\ChemMan_Demo -DestinationPath ChemMan_Demo_v2.0.0.zip

# Linux/Mac
tar -czf ChemMan_Demo_v2.0.0.tar.gz -C dist ChemMan_Demo
```

Wyślij ten plik ZIP do każdego:
- ✅ Nie wymaga instalacji
- ✅ Działa offline
- ✅ Przenośny (może działać z USB)

### Opcja 2: Udział sieciowy

Skopiuj folder `ChemMan_Demo/` do:
- Dysku sieciowego firmy
- SharePoint
- Pendrive USB

### Opcja 3: Przechowywanie w chmurze

Prześlij ZIP do:
- Google Drive
- OneDrive
- Serwera plików firmy

---

## 🎬 Scenariusze demo

### Szybkie demo (5 min)

1. Uruchom aplikację
2. Zaloguj się jako admin
3. Pokaż panel główny
4. Dodaj lokalizację
5. Wyszukaj "Benzen" i dodaj do lokalizacji
6. Pokaż automatyczną detekcję CMR
7. Eksportuj dane do CSV

### Pełne demo (15 min)

1. Wszystko powyżej, plus:
2. Pokaż wszystkie 4400+ substancji
3. Zademonstruj zaawansowane filtry
4. Prześlij plik SDS
5. Pokaż zarządzanie użytkownikami
6. Pokaż dziennik audytu
7. Zademonstruj dwujęzyczny interfejs

---

## 🛠️ Rozwiązywanie problemów z budowaniem

### Problem: "PyInstaller nie znaleziony"

**Rozwiązanie:**
```bash
pip install pyinstaller
```

### Problem: "ModuleNotFoundError podczas budowania"

**Rozwiązanie:**
```bash
# Przeinstaluj wszystkie zależności
cd ..
pip install -r requirements.txt
cd DEMO
```

### Problem: "substancje_baza.xlsx nie znaleziony"

**Rozwiązanie:**
- Upewnij się, że pliki Excel są w katalogu nadrzędnym
- Sprawdź, czy nazwy plików są dokładnie:
  - `substancje_baza.xlsx`
  - `svhc.xlsx`

### Problem: "Budowanie trwa zbyt długo (>10 min)"

**Rozwiązanie:**
- To normalne przy pierwszym budowaniu
- Kolejne budowania są szybsze
- Tymczasowo zamknij antywirus (spowalnia PyInstaller)

### Problem: "Plik wykonywalny się nie uruchamia"

**Rozwiązanie:**
1. Sprawdź antywirus - dodaj wyjątek dla folderu ChemMan_Demo
2. Uruchom z linii poleceń, aby zobaczyć komunikaty błędów
3. Sprawdź plik `demo_chemman.log`

---

## 🔄 Aktualizacja demo

Gdy aktualizujesz główną aplikację:

```bash
# 1. Pobierz najnowsze zmiany
git pull origin master

# 2. Przebuduj demo
cd DEMO
build_demo_package.bat  # lub .sh

# 3. Nowy pakiet gotowy w dist/
```

---

## ⚠️ Ważne uwagi

### Ograniczenia demo

- ❌ **Nie do użytku produkcyjnego!**
- ✅ Tylko do celów demo/prezentacyjnych
- ⚠️ Dane są trwałe (chyba że usuniesz bazę danych)
- ⚠️ Brak dostępu sieciowego (działa tylko lokalnie)

### Bezpieczeństwo

- Hasło demo jest **proste z założenia** (Demo1234 - spełnia wymaganie 8 znaków)
- Nie używaj pakietu demo do rzeczywistych danych
- Do produkcji użyj pełnego wdrożenia (DEPLOYMENT_GUIDE.md)

### Wydajność

- Pierwsze uruchomienie może być wolne (2-3 sekundy)
- Kolejne uruchomienia są szybsze
- SQLite jest wolniejsze niż PostgreSQL (oczekiwane)

---

## 📊 Szacowany czas budowania

| Zadanie | Czas |
|---------|------|
| Zainstaluj PyInstaller | 30 sek |
| Zbuduj bazę danych demo | 1 min |
| Budowanie PyInstaller | 2-5 min |
| **Razem** | **3-7 min** |

### Rozmiary plików

| Element | Rozmiar |
|---------|---------|
| Plik wykonywalny + DLL | ~100 MB |
| Baza danych | ~40 MB |
| Pliki statyczne | ~5 MB |
| **Pakiet całkowity** | **~150 MB** |
| **Plik ZIP** | **~50 MB** |

---

## ✅ Lista kontrolna przed dystrybucją

- [ ] Zbudowano pakiet pomyślnie
- [ ] Przetestowano skrypt startowy
- [ ] Zalogowano się danymi admin/Demo1234
- [ ] Przetestowano kluczowe funkcje (dodaj lokalizację, wyszukaj, eksportuj)
- [ ] Sprawdzono obecność danych w bazie (4400+ CLP, 492 SVHC)
- [ ] Spakowano do ZIP
- [ ] Dołączono README_DEMO.md
- [ ] Przygotowano scenariusz prezentacji/demo

---

## 🎉 Gotowe!

Twój samodzielny pakiet demo jest gotowy do:
- Pokazania zarządowi
- Prezentacji klientom
- Demonstracji na spotkaniach
- Wysłania do zdalnych użytkowników

**Powodzenia z prezentacją!** 🚀
