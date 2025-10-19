# Instrukcja Użytkownika ChemMan

Przewodnik dla użytkowników systemu ChemMan - zarządzanie substancjami chemicznymi.

---

## 📋 Spis treści

1. [Pierwsze kroki](#pierwsze-kroki)
2. [Przeglądanie substancji](#przeglądanie-substancji)
3. [Dodawanie substancji](#dodawanie-substancji)
4. [Edycja i usuwanie](#edycja-i-usuwanie)
5. [Zarządzanie lokalizacjami](#zarządzanie-lokalizacjami)
6. [Karty charakterystyki (SDS)](#karty-charakterystyki-sds)
7. [Eksport danych](#eksport-danych)
8. [Wyszukiwanie i filtrowanie](#wyszukiwanie-i-filtrowanie)
9. [Często zadawane pytania](#często-zadawane-pytania)

---

## Pierwsze kroki

### Logowanie do systemu

1. Otwórz przeglądarkę (zalecane: Chrome, Firefox, Edge)
2. Wpisz adres aplikacji: `http://[ADRES_SERWERA]:5000`
3. Wprowadź swoją **nazwę użytkownika** i **hasło**
4. Kliknij **"Zaloguj"**

![Ekran logowania](docs/images/login.png)

### Zmiana hasła po pierwszym logowaniu

**WAŻNE:** Po pierwszym logowaniu powinieneś zmienić hasło!

1. Kliknij **"Zmień hasło"** w górnym menu
2. Wprowadź **obecne hasło**
3. Wprowadź **nowe hasło** (min. 4 znaki, zalecane 8+)
4. Potwierdź nowe hasło
5. Kliknij **"Zmień Hasło"**

### Interfejs główny

Po zalogowaniu zobaczysz:
```
┌─────────────────────────────────────────┐
│  CHEM-MAN | LOKALIZACJE                 │
├─────────────────────────────────────────┤
│  [Menu nawigacji]                       │
│  Lista Lokalizacji | Wszystkie Subst.   │
│  | Zmień hasło | Wyloguj (jan.kowalski) │
├─────────────────────────────────────────┤
│  Istniejące lokalizacje:                │
│                                          │
│  📦 Magazyn A      [Edytuj] [Usuń]      │
│  📦 Laboratorium   [Edytuj] [Usuń]      │
│  📦 Magazyn B      [Edytuj] [Usuń]      │
│                                          │
│  [+ Dodaj nową lokalizację]             │
└─────────────────────────────────────────┘
```

---

## Przeglądanie substancji

### Widok lokalizacji

1. Na stronie głównej kliknij **nazwę lokalizacji** (np. "Magazyn A")
2. Zobaczysz tabelę z substancjami w tej lokalizacji:

| Nazwa chemiczna | Nr CAS | Nr WE | Klasyfikacja | Lokalizacja | Komentarz | Karta SDS | Akcje |
|----------------|--------|-------|--------------|-------------|-----------|-----------|-------|
| acetic acid<br>kwas octowy | 64-19-7 | 200-580-7 | Flam. Liq. 3 | Bieruń | 5L | Zobacz/Pobierz | Edytuj / Usuń |

### Oznaczenia substancji

- **🔴 CMR** - Substancja rakotwórcza, mutagenna lub działająca szkodliwie na rozrodczość
- **🟡 SVHC** - Substancja wzbudzająca szczególnie duże obawy (lista REACH)

**Przykład:**
```
bis(α,α-dimethylbenzyl) peroxide  [CMR] [SVHC]
nadtlenek bis(α,α-dimetylobenzylu)
```

### Nawigacja po stronach

Jeśli lokalizacja ma wiele substancji, zobaczysz paginację:
```
Wyświetlanie 25 z 150 substancji (Strona 1 z 6)

[<< Pierwsza] [< Poprzednia] [Strona 1] [Następna >] [Ostatnia >>]

Rekordów na stronę: [5] [10] [25] [50] [100]
```

---

## Dodawanie substancji

Masz **dwa sposoby** dodawania substancji:

### Sposób 1: Dodawanie z bazy (zalecane)

**Najlepszy dla substancji znanych, z bazy CLP lub SVHC**

1. W widoku lokalizacji przewiń do sekcji **"Dodaj z Bazy (Excel)"**
2. W polu wyszukiwania wpisz:
   - **Nazwę** (polską lub angielską): `kwas`, `acetic`
   - **Numer CAS**: `64-19-7`
   - **Numer EC**: `200-580-7`
3. Wybierz **lokalizację fizyczną** (Bieruń / Krupski Młyn) - opcjonalnie
4. Kliknij **"Szukaj"**
5. Pojawią się wyniki wyszukiwania:
```
✓ acetic acid ... % kwas octowy ... %
  CAS: 64-19-7 | EC: 200-580-7
  Klasyfikacja: Flam. Liq. 3, Skin Corr. 1A
  [Dodaj]
```

6. Kliknij **"Dodaj"** przy wybranej substancji
7. Substancja zostanie dodana do lokalizacji!

**Wskazówki wyszukiwania:**
- ✅ Wystarczą 2-3 znaki: `kwa` znajdzie wszystkie kwasy
- ✅ Szukaj po polsku lub angielsku: `acetic` = `kwas octowy`
- ✅ Możesz szukać po części numeru CAS: `64-19`
- ✅ Wyszukiwarka przeszukuje **obie bazy** (CLP i SVHC)

### Sposób 2: Dodawanie ręczne

**Dla mieszanin własnych lub substancji spoza bazy**

1. W widoku lokalizacji kliknij **"Dodaj mieszaninę/substancję ręcznie"**
2. Wypełnij formularz:

| Pole | Wymagane? | Opis |
|------|-----------|------|
| **Nazwa** | ✓ TAK | Nazwa substancji/mieszaniny |
| Nr CAS | Nie | Numer CAS (jeśli znany) |
| Nr WE | Nie | Numer WE/EC (jeśli znany) |
| Klasyfikacja | Nie | Np. "Flam. Liq. 3, Skin Corr. 1A" |
| Zwroty H | Nie | Np. "H226, H314" |
| Komentarz | Nie | Dodatkowe informacje |
| Lokalizacja fizyczna | Nie | Bieruń / Krupski Młyn |

3. Kliknij **"Zapisz"**

**Przykład - mieszanina własna:**
```
Nazwa: Mieszanina czyszcząca ABC
Klasyfikacja: Skin Irrit. 2, Eye Irrit. 2
Zwroty H: H315, H319
Komentarz: Mieszanina nr 5 z dnia 15.01.2025
Lokalizacja: Bieruń
```

---

## Edycja i usuwanie

### Edycja komentarza

**Najczęstsza operacja - dodawanie notatek do substancji**

1. W tabeli substancji kliknij **"Edytuj Kom."** przy wybranej substancji
2. Pojawi się pole tekstowe z komentarzem
3. Wprowadź zmiany (np. ilość, lokalizacja dokładna, termin ważności)
4. Kliknij **"Zapisz"** lub **"Anuluj"**

**Przykłady komentarzy:**
- `5L, półka 3, termin ważności: 2026-12`
- `Ostatnie opakowanie, zamówić więcej`
- `Nie używać, zanieczyszczone`

### Usuwanie substancji

**UWAGA:** Usunięcie jest trwałe!

1. Kliknij **"Usuń"** przy substancji
2. Potwierdź usunięcie w oknie dialogowym
3. Substancja zostanie usunięta z lokalizacji

**Wskazówka:** Zamiast usuwać, rozważ dodanie komentarza "ZUŻYTE" lub "DO UTYLIZACJI"

---

## Zarządzanie lokalizacjami

### Dodawanie lokalizacji

**Tylko dla użytkowników z uprawnieniami `can_add_location`**

1. Na stronie głównej przewiń do **"Dodaj nową lokalizację"**
2. Wprowadź nazwę lokalizacji (np. "Magazyn C", "Lab Analityczne")
3. Kliknij **"Dodaj Lokalizację"**

**Dobre praktyki nazewnictwa:**
- ✅ Opisowe: `Magazyn A - Substancje łatwopalne`
- ✅ Krótkie: `Lab 1`, `Mag B`
- ❌ Unikaj: `aaaaa`, `test123`

### Edycja nazwy lokalizacji

1. Na stronie głównej kliknij **"Edytuj"** przy lokalizacji
2. Wprowadź nową nazwę
3. Kliknij **"Zapisz"**

### Usuwanie lokalizacji

**UWAGA:** Usunięcie lokalizacji usuwa też WSZYSTKIE substancje w niej!

1. Kliknij **"Usuń"** przy lokalizacji
2. Potwierdź usunięcie (nazwa lokalizacji + liczba substancji)
3. Lokalizacja i jej zawartość zostaną usunięte

**Zalecenie:** Przed usunięciem lokalizacji, przenieś lub usuń substancje ręcznie.

---

## Karty charakterystyki (SDS)

### Dodawanie karty SDS

**Tylko dla użytkowników z uprawnieniami `can_upload_sds`**

1. W widoku lokalizacji znajdź substancję w tabeli
2. W kolumnie **"Karta SDS"**:
   - Jeśli brak karty, zobaczysz przycisk **"Załaduj SDS"**
   - Jeśli karta istnieje, zobaczysz link **"Zobacz/Pobierz"**
3. Kliknij **"Choose File"** / **"Wybierz plik"**
4. Wybierz plik PDF z kartą charakterystyki
5. Kliknij **"Załaduj SDS"**

**Wymagania:**
- ✅ Format: **PDF**
- ✅ Rozmiar: maksymalnie **16 MB**
- ❌ Inne formaty (Word, Excel) NIE są obsługiwane

### Przeglądanie karty SDS

1. Kliknij **"Zobacz/Pobierz"** w kolumnie "Karta SDS"
2. Plik PDF otworzy się w nowej karcie przeglądarki
3. Możesz go wydrukować lub zapisać na dysk

### Wymiana karty SDS

**Gdy masz nowszą wersję karty charakterystyki**

1. Kliknij **"Zmień"** przy istniejącej karcie
2. Pojawi się przycisk wyboru pliku
3. Wybierz nowy plik PDF
4. Kliknij **"OK"**
5. Stara karta zostanie zastąpiona nową

### Usuwanie karty SDS

1. Kliknij **"Usuń"** przy karcie SDS
2. Potwierdź usunięcie
3. Karta zostanie trwale usunięta

---

## Eksport danych

### Eksport substancji z lokalizacji

**Eksportuje wszystkie substancje z jednej lokalizacji do CSV**

1. W widoku lokalizacji kliknij **"⬇️ Eksportuj do CSV"** (prawy górny róg)
2. Plik zostanie pobrany: `ChemMan_lok_Magazyn_A_subst.csv`
3. Otwórz w Excel lub LibreOffice Calc

**Zawartość eksportu:**
- Nazwa chemiczna
- Nr CAS
- Klasyfikacja
- Zwroty H
- SCL/M-factor
- Komentarz
- Lokalizacja fizyczna

### Eksport wszystkich substancji

**Eksportuje substancje ze wszystkich lokalizacji**

1. W menu kliknij **"Wszystkie Substancje"**
2. Opcjonalnie zastosuj filtry (patrz: [Wyszukiwanie i filtrowanie](#wyszukiwanie-i-filtrowanie))
3. Kliknij **"⬇️ Eksportuj do CSV"** (prawy górny róg)
4. Plik zostanie pobrany:
   - Z filtrami: `ChemMan_substancje_filtrowane.csv`
   - Bez filtrów: `ChemMan_wszystkie_substancje.csv`

**Dodatkowe kolumny w globalnym eksporcie:**
- Nr WE
- CMR (Tak/Nie)
- SVHC (Tak/Nie)
- Użytkownik (nazwa lokalizacji)

### Otwieranie CSV w Excel

**Jeśli polskie znaki się nie wyświetlają:**

1. Otwórz Excel
2. **Dane** → **Z pliku tekstowego/CSV**
3. Wybierz pobrany plik
4. Ustaw **Kodowanie: UTF-8** lub **65001: Unicode (UTF-8)**
5. Kliknij **Załaduj**

---

## Wyszukiwanie i filtrowanie

### Widok "Wszystkie Substancje"

**Najpotężniejsze narzędzie do przeszukiwania całej bazy**

1. Kliknij **"Wszystkie Substancje"** w menu
2. Zobaczysz tabelę ze wszystkimi substancjami ze wszystkich lokalizacji

### Filtr tekstowy

W polu **"Filtruj (Nazwa, CAS, EC, Klasyfikacja, Lokalizacja...)"** możesz wpisać:

| Szukasz | Wpisz | Wynik |
|---------|-------|-------|
| Substancje z "kwas" w nazwie | `kwas` | Wszystkie kwasy |
| Konkretny CAS | `64-19-7` | Acetic acid |
| Wszystkie CMR | `CMR` | Tylko substancje CMR |
| Wszystkie SVHC | `SVHC` | Tylko substancje SVHC |
| Zwrot H | `H350` | Substancje z tym zwrotem |

**Przykłady:**
```
"kwas"        → znajdzie: kwas octowy, kwas solny, itp.
"flam"        → znajdzie: wszystkie łatwopalne
"CMR"         → tylko substancje CMR (czerwony badge)
"SVHC"        → tylko substancje SVHC (żółty badge)
"Magazyn A"   → wszystko w Magazynie A
```

### Zaawansowane filtry

Kliknij **"Pokaż zaawansowane filtry"** aby zobaczyć więcej opcji:

| Filtr | Opcje | Opis |
|-------|-------|------|
| **Lokalizacja fizyczna** | Wszystkie / Bieruń / Krupski Młyn | Filtruj po zakładzie |
| **Użytkownik** | Wszystkie / [lista lokalizacji] | Filtruj po lokalizacji bazodanowej |
| **Status CMR** | Wszystkie / Tak (CMR) / Nie | Pokaż tylko CMR lub nie-CMR |
| **Status SVHC** | Wszystkie / Tak (SVHC) / Nie | Pokaż tylko SVHC lub nie-SVHC |
| **Karta SDS** | Wszystkie / Posiada / Brak | Filtruj po posiadaniu karty |

**Przykład kombinacji filtrów:**
```
Tekst: "flam"
Lokalizacja fizyczna: Bieruń
Status SVHC: Tak (SVHC)

→ Wynik: Łatwopalne substancje SVHC w Bieruniu
```

### Czyszczenie filtrów

Kliknij **"Wyczyść filtry"** aby usunąć wszystkie zastosowane filtry i zobaczyć pełną listę.

---

## Operacje masowe

### Przenoszenie substancji

**Przenieś kilka substancji na raz do innej lokalizacji**

1. W widoku lokalizacji zaznacz checkboxy przy substancjach do przeniesienia
2. Pojawi się sekcja **"Wybrano: X substancji"**
3. Z listy **"Przenieś/Kopiuj do:"** wybierz docelową lokalizację
4. Kliknij **"Przenieś"**
5. Substancje znikną z obecnej lokalizacji i pojawią się w docelowej

### Kopiowanie substancji

**Skopiuj substancje do innej lokalizacji (oryginały pozostają)**

1. Zaznacz checkboxy przy substancjach
2. Wybierz lokalizację docelową z listy
3. Kliknij **"Kopiuj"**
4. Substancje zostaną skopiowane (duplikaty w obu lokalizacjach)

**Użycie:** Przydatne gdy ta sama substancja jest w kilku miejscach.

---

## Często zadawane pytania

### Ogólne

**Q: Jak często powinienem zmieniać hasło?**  
A: Zalecamy zmianę hasła co 3-6 miesięcy, lub natychmiast jeśli podejrzewasz wyciek.

**Q: Czy mogę pracować na telefonie/tablecie?**  
A: Tak, aplikacja działa w przeglądarce mobilnej, ale najwygodniej na komputerze.

**Q: Jak długo przechowywane są dane?**  
A: Wszystkie dane są przechowywane bezterminowo. System wykonuje automatyczne backupy.

### Substancje

**Q: Czym różni się "Dodaj z bazy" od "Dodaj ręcznie"?**  
A: 
- **Z bazy** - dane są automatycznie pobierane (klasyfikacja, H phrases, numery), CMR i SVHC oznaczane automatycznie
- **Ręcznie** - wszystko wpisujesz sam, dla substancji/mieszanin własnych

**Q: Dlaczego niektóre substancje mają dwie nazwy?**  
A: To nazwy dwujęzyczne - angielska (góra) i polska (dół) z bazy CLP.

**Q: Co oznacza badge CMR?**  
A: Substancja jest **rakotwórcza** (Carcinogenic), **mutagenna** (Mutagenic) lub **toksyczna dla rozrodczości** (Reprotoxic).

**Q: Co oznacza badge SVHC?**  
A: Substancja **Wzbudzająca Szczególnie Duże Obawy** - lista kandydacka REACH do objęcia wymogiem zezwolenia.

**Q: Czy mogę edytować nazwę lub CAS substancji?**  
A: Nie bezpośrednio. Musisz usunąć i dodać ponownie, lub skontaktować się z administratorem.

### Karty SDS

**Q: Czy plik SDS musi być w jakimś konkretnym formacie?**  
A: Tak, tylko **PDF**. Pliki Word, Excel, obrazy NIE są obsługiwane.

**Q: Jak duży może być plik SDS?**  
A: Maksymalnie **16 MB**. Jeśli plik jest większy, skompresuj go lub skontaktuj się z administratorem.

**Q: Co jeśli nie mam karty SDS?**  
A: To jest opcjonalne. Możesz pozostawić pole puste - substancja będzie miała status "Brak" w kolumnie SDS.

**Q: Czy mogę dodać kilka kart SDS do jednej substancji?**  
A: Nie, jedna substancja = jedna karta SDS. Jeśli masz kilka wersji, załaduj najnowszą.

### Eksport

**Q: Czy eksport zawiera również karty SDS?**  
A: Nie, eksport CSV zawiera tylko dane tekstowe. Karty SDS musisz pobierać osobno.

**Q: Czy mogę wyeksportować tylko wybrane substancje?**  
A: Tak, użyj filtrów w widoku "Wszystkie Substancje" przed eksportem.

**Q: W jakim programie otworzyć CSV?**  
A: Microsoft Excel, LibreOffice Calc, Google Sheets - dowolny program arkuszy kalkulacyjnych.

### Uprawnienia

**Q: Dlaczego nie widzę przycisku "Dodaj substancję"?**  
A: Nie masz uprawnienia `can_add`. Skontaktuj się z administratorem.

**Q: Dlaczego nie mogę usunąć lokalizacji?**  
A: Potrzebujesz uprawnienia `can_delete_location` lub statusu administratora.

**Q: Jak sprawdzić jakie mam uprawnienia?**  
A: Jeśli jesteś administratorem, możesz zobaczyć to w panelu "Zarządzaj Użytkownikami". W przeciwnym razie zapytaj swojego administratora.

### Problemy techniczne

**Q: Aplikacja nie działa, co robić?**  
A: 
1. Odśwież stronę (F5 lub Ctrl+R)
2. Wyczyść cache przeglądarki
3. Sprawdź połączenie z siecią
4. Skontaktuj się z administratorem

**Q: Widzę komunikat "Sesja wygasła"**  
A: Zaloguj się ponownie. Sesja wygasa po pewnym czasie nieaktywności (domyślnie kilka godzin).

**Q: Nie mogę załadować pliku SDS**  
A: Sprawdź:
- Czy plik jest w formacie PDF?
- Czy plik nie jest większy niż 16 MB?
- Czy masz uprawnienie `can_upload_sds`?

**Q: Polskie znaki w CSV wyświetlają się jako krzaki**  
A: Zobacz sekcję [Otwieranie CSV w Excel](#otwieranie-csv-w-excel) - ustaw kodowanie UTF-8.

---

## Wsparcie

Jeśli masz pytania lub problemy:

1. Sprawdź tę instrukcję
2. Zapytaj swojego administratora systemu
3. W przypadku błędów - zrób screenshot i prześlij administratorowi

---

**Wersja dokumentu:** 1.0  
**Data aktualizacji:** 2025-01-17