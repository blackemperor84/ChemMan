# Przewodnik Konserwacji ChemMan

Instrukcja dla administratorów - codzienne operacje, backup, aktualizacje list
CLP/SVHC, migracje.

**Zakłada wdrożenie produkcyjne w Dockerze** (patrz
[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)). Wszystkie polecenia uruchamiaj
z katalogu wdrożenia, czyli tam, gdzie leży `docker-compose.yml` i `.env`
(np. `/opt/chemman`).

> **Pracujesz lokalnie, bez Dockera?** Pomiń przedrostek
> `docker compose exec app` i uruchamiaj polecenia z katalogu projektu przy
> aktywnym `venv`. Instalację lokalną opisuje [INSTALLATION.md](INSTALLATION.md).

---

## 📋 Spis treści

1. [Codzienne zadania](#codzienne-zadania)
2. [Backup i przywracanie](#backup-i-przywracanie)
3. [Aktualizacja bazy CLP](#aktualizacja-bazy-clp)
4. [Aktualizacja listy SVHC](#aktualizacja-listy-svhc)
5. [Flagi CMR/SVHC w istniejących substancjach](#flagi-cmrsvhc-w-istniejacych-substancjach)
6. [Zarządzanie użytkownikami](#zarzadzanie-uzytkownikami)
7. [Monitoring systemu](#monitoring-systemu)
8. [Migracje bazy danych](#migracje-bazy-danych)
9. [Procedury awaryjne](#procedury-awaryjne)
10. [Checklist okresowej konserwacji](#checklist-okresowej-konserwacji)

---

## Codzienne zadania

### Sprawdzenie logów

```bash
docker compose logs --tail=100 app     # log kontenera
docker compose ps                      # czy coś się restartuje w kółko
```

Log aplikacji trafia też do wolumenu `chemman_logs`:

```bash
docker compose exec app tail -n 50 /app/logs/chem_man.log
```

Dziennik zmian użytkowników: **Panel admina → „Dziennik Zmian"**.

### Monitorowanie miejsca na dysku

```bash
docker system df                       # obrazy, kontenery, wolumeny
df -h /var/lib/docker                  # dysk hosta pod Dockerem
docker compose exec app du -sh /app/instance/uploads/sds
```

**Zalecane:** archiwizuj stare karty SDS co kwartał — patrz
[Procedury awaryjne](#procedury-awaryjne).

---

## Backup i przywracanie

Pełna procedura wraz z gotowym skryptem i wpisem do crona jest w
[DEPLOYMENT_GUIDE.md → Backup i przywracanie](DEPLOYMENT_GUIDE.md#backup-i-przywracanie).
Tu skrót do użycia „na już", np. przed aktualizacją list:

```bash
# Baza
docker compose exec -T db pg_dump -U chemman chemman | gzip > backup_$(date +%F).sql.gz

# Załączniki SDS
docker compose exec -T app tar -czf - -C /app/instance/uploads . > uploads_$(date +%F).tar.gz
```

> **Zrób backup przed każdą aktualizacją list CLP/SVHC i przed migracją.**
> Import nadpisuje całą tabelę referencyjną.

---

## Aktualizacja bazy CLP

**Częstotliwość:** co 6-12 miesięcy, gdy ECHA opublikuje nową wersję.

### Metoda 1: przez interfejs web (zalecana, od v2.3.0)

1. Pobierz najnowszą bazę CLP z ECHA (plik `.xlsx`).
2. Zaloguj się jako administrator.
3. Przejdź do **Bazy Danych** w menu nawigacji.
4. W sekcji „Aktualizacja Bazy CLP" wskaż pobrany plik.
5. Kliknij **„Importuj bazę CLP"** i potwierdź.
6. Zweryfikuj licznik rekordów na stronie.

Ta droga nie wymaga dostępu do serwera ani restartu kontenera.

### Metoda 2: z linii poleceń

Komenda `flask import-excel` importuje plik wskazany przez `EXCEL_FILE_PATH`
(domyślnie `substancje_baza.xlsx` w obrazie). Aby zaimportować **nowszy** plik,
trzeba go najpierw skopiować do kontenera:

```bash
# 1. BACKUP (patrz wyzej)

# 2. Wgraj nowy plik do dzialajacego kontenera
docker compose cp substancje_baza_NEW.xlsx app:/app/substancje_baza.xlsx

# 3. Import (nadpisuje tabele referencyjna CLP)
docker compose exec app flask import-excel

# 4. Weryfikacja
docker compose exec -T db psql -U chemman -d chemman -tAc \
  "SELECT count(*) FROM excel_source_substances"
```

> **Plik skopiowany przez `docker compose cp` znika przy odtworzeniu
> kontenera** (`docker compose up -d` po `pull`). Sama zaimportowana treść
> zostaje — siedzi w bazie, a nie w pliku. Przy kolejnej aktualizacji obrazu
> powtórz kopiowanie tylko wtedy, gdy znów importujesz.

Aktualnie w bazie: **4400** rekordów CLP.

---

## Aktualizacja listy SVHC

**Częstotliwość:** co ok. 6 miesięcy (ECHA publikuje aktualizacje listy
kandydackiej zwykle w czerwcu i grudniu).

### Metoda 1: przez interfejs web (zalecana, od v2.3.0)

1. Pobierz najnowszą listę SVHC z ECHA (plik `.xlsx`).
2. Zaloguj się jako administrator.
3. Przejdź do **Bazy Danych**.
4. W sekcji „Aktualizacja Listy SVHC" wskaż pobrany plik.
5. Kliknij **„Importuj listę SVHC"** i potwierdź.
6. Zweryfikuj licznik rekordów.

### Metoda 2: z linii poleceń

```bash
# 1. BACKUP

# 2. Wgraj nowa liste
docker compose cp svhc_NEW.xlsx app:/app/svhc.xlsx

# 3. Import
docker compose exec app flask import-svhc

# 4. Weryfikacja
docker compose exec -T db psql -U chemman -d chemman -tAc \
  "SELECT count(*) FROM svhc_substances"
```

Aktualnie w bazie: **1029** rekordów SVHC.

> Po podmianie listy przeczytaj następny rozdział — **flagi przy już
> wprowadzonych substancjach nie aktualizują się same.**

---

## Flagi CMR/SVHC w istniejacych substancjach

Import list CLP i SVHC podmienia **tabele referencyjne**. Nie przelicza pól
`is_cmr` / `is_svhc` przy substancjach już wprowadzonych do lokalizacji — te
wartości zapisano w chwili dodawania substancji. Po aktualizacji listy mogą
więc być nieaktualne: substancja dopisana do listy kandydackiej nadal ma
`is_svhc = false`.

### Dlaczego nie ma skryptu „przelicz wszystko"

Nie jest to przeoczenie, tylko świadome ograniczenie:

1. **Nie da się odróżnić decyzji ręcznej od automatycznej.** Model
   `Substance` ma jedno pole `is_svhc`. Jeśli administrator ustawił flagę
   sam (formularz na to pozwala), masowe przeliczenie nadpisze jego decyzję,
   bo nic w bazie nie zapamiętało, że była ręczna.
2. **Nieudana weryfikacja nie może cicho oznaczyć „nie SVHC".** Aplikacja
   wprost tego pilnuje (`check_svhc_substance` zwraca `verified`, a zapis jest
   odrzucany, gdy weryfikacja się nie powiodła). Skrypt lecący po całej tabeli
   musiałby to obejść — a fałszywe „nie SVHC" w rejestrze substancji jest
   groźniejsze niż brak aktualizacji.

### Zalecana procedura

Po każdej aktualizacji listy:

1. Wypisz substancje, których dotyczy zmiana — porównaj listę przed i po
   imporcie (kopia z backupu) albo przejrzyj nowo dodane pozycje ECHA.
2. Dla każdej z nich otwórz substancję w aplikacji i zapisz ponownie —
   zapis uruchamia pełną, tę samą ścieżkę detekcji co przy dodawaniu.
3. Odnotuj przegląd w dzienniku zmian.

Substancje wprowadzone **po** imporcie są klasyfikowane już wobec nowej listy.

Ile substancji ma dziś ustawione flagi:

```bash
docker compose exec -T db psql -U chemman -d chemman -tAc \
  "SELECT count(*) FILTER (WHERE is_cmr)  AS cmr,
          count(*) FILTER (WHERE is_svhc) AS svhc,
          count(*)                        AS wszystkie
   FROM substances"
```

---

## Zarzadzanie uzytkownikami

Codzienne operacje rób w **Panelu admina → Zarządzaj użytkownikami** (dodawanie,
uprawnienia, usuwanie). Poniżej tylko to, czego panel nie obejmuje.

### Reset hasła administratora

```bash
docker compose exec app python update_admin_password.py
```

Skrypt pyta o hasło bez wyświetlania go (minimum 8 znaków). Można też podać je
zmienną `CHEM_MAN_ADMIN_PASSWORD`.

### Odtworzenie konta admin (gdy zostało usunięte)

```bash
docker compose exec app python create_admin.py
```

Skrypt zapyta o hasło i jego powtórzenie, nie wyświetlając go na ekranie.
Nic nie zmienia, jeśli konto `admin` już istnieje.

> **Nie podawaj hasła w wierszu poleceń** (`-e CHEM_MAN_ADMIN_PASSWORD=...`).
> Trafia wtedy do historii powłoki i do listy procesów. Zmiennej używaj
> wyłącznie tam, gdzie nie ma terminala — przy pierwszym uruchomieniu
> kontenera czyta ją z pliku `.env`, który ma uprawnienia `600`.

### Przegląd kont z uprawnieniami administratora

```bash
docker compose exec -T db psql -U chemman -d chemman -c \
  "SELECT username, is_admin, can_delete, can_delete_location FROM users ORDER BY username"
```

---

## Monitoring systemu

### Rozmiar bazy

```bash
docker compose exec -T db psql -U chemman -d chemman -tAc \
  "SELECT pg_size_pretty(pg_database_size('chemman'))"
```

### Liczba rekordów

```bash
docker compose exec -T db psql -U chemman -d chemman -c \
  "SELECT
     (SELECT count(*) FROM substances)               AS substancje,
     (SELECT count(*) FROM locations)                AS lokalizacje,
     (SELECT count(*) FROM excel_source_substances)  AS clp,
     (SELECT count(*) FROM svhc_substances)          AS svhc,
     (SELECT count(*) FROM users)                    AS uzytkownicy,
     (SELECT count(*) FROM audit_log)                AS dziennik"
```

### Czyszczenie starego dziennika zmian

Dziennik rośnie w nieskończoność. Gdy zajmuje zbyt dużo miejsca, usuń wpisy
starsze niż rok:

```bash
# NAJPIERW backup, potem:
docker compose exec -T db psql -U chemman -d chemman -c \
  "DELETE FROM audit_log WHERE timestamp < now() - interval '1 year'"
```

> Sprawdź wcześniej, jak długo musisz przechowywać dziennik na potrzeby
> audytu BHP — usunięcie jest nieodwracalne.

---

## Migracje bazy danych

### Nowa instalacja (pusta baza)

Cały schemat da się zbudować z samych migracji — kontener robi to sam przy
starcie (`RUN_MIGRATIONS=1`, domyślnie). Ręcznie:

```bash
docker compose exec app flask db upgrade
```

Łańcuch startuje od rewizji `chemman_baseline`, która tworzy tabele
`locations`, `users`, `substances`, `sds_files` i `audit_log`. Kolejne rewizje
dokładają tabele referencyjne (CLP, SVHC) oraz późniejsze kolumny.

> **Uwaga historyczna:** do sierpnia 2026 łańcuch migracji nie zawierał tych
> podstawowych tabel - powstawały przez `db.create_all()`. `flask db upgrade`
> na pustej bazie kończył się błędem `no such table: substances`.

### Istniejąca baza założona przez `db.create_all()`

**To dotyczy wszystkich instalacji sprzed sierpnia 2026.** Taka baza ma komplet
tabel, ale nie ma tabeli `alembic_version`, więc Alembic uzna ją za pustą i
spróbuje utworzyć tabele od nowa:

```
psycopg2.errors.DuplicateTable: relation "locations" already exists
```

Kontener zatrzyma się na tym błędzie. Wystartuj go z `RUN_MIGRATIONS=0`
w `.env`, przeprowadź procedurę, potem usuń tę zmienną.

```bash
# 1. BACKUP (obowiazkowo)

# 2. Sprawdz, jakie tabele sa w bazie
docker compose exec -T db psql -U chemman -d chemman -c '\dt'

# 3a. Komplet tabel i kolumn jest na miejscu - oznacz baze jako aktualna:
docker compose exec app flask db stamp head

# 3b. Czegos brakuje (np. tabeli sds_files) - oznacz rewizja SPRZED
#     brakujacej zmiany i dograj reszte migracjami:
docker compose exec app flask db stamp chemman_baseline
docker compose exec app flask db upgrade
```

Po `flask db stamp head` kolejne aktualizacje działają już normalnie.

### Sprawdzenie stanu

```bash
docker compose exec app flask db current   # rewizja zapisana w bazie
docker compose exec app flask db heads     # najnowsza dostepna (powinna byc jedna)
```

Jeżeli `flask db heads` pokazuje więcej niż jedną pozycję, łańcuch się rozgałęził
i `upgrade` nie zadziała - trzeba scalić gałęzie (`flask db merge`).

### Testy migracji

Zestaw testów zawiera smoke test, który uruchamia `flask db upgrade` na pustej
bazie i porównuje wynikowy schemat z modelami (uruchamiany z repozytorium, nie
z wdrożenia):

```bash
python -m pytest tests/test_migrations.py -v
```

---

## Procedury awaryjne

### Kontener nie startuje

```bash
docker compose logs --tail=50 app
```

Najczęstsze przyczyny i rozwiązania zebrano w
[DEPLOYMENT_GUIDE.md → Rozwiązywanie problemów](DEPLOYMENT_GUIDE.md#rozwiazywanie-problemow).

### Uszkodzona baza danych

PostgreSQL nie ma odpowiednika `PRAGMA integrity_check`. Podstawowa weryfikacja
to pełny zrzut - jeśli przechodzi bez błędu, dane są czytelne:

```bash
docker compose exec -T db pg_dump -U chemman chemman > /dev/null && echo "zrzut OK"
```

Przy podejrzeniu uszkodzenia przywróć z backupu — procedura w
[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#backup-i-przywracanie).

### Brak miejsca na dysku

```bash
# 1. Co zajmuje miejsce po stronie Dockera
docker system df

# 2. Usun nieuzywane warstwy obrazow (nie rusza wolumenow z danymi)
docker image prune -f

# 3. Rozmiar zalacznikow SDS
docker compose exec app du -sh /app/instance/uploads/sds

# 4. Archiwizacja starych kart SDS
docker compose exec -T app tar -czf - -C /app/instance/uploads/sds . \
  > sds_archiwum_$(date +%Y%m%d).tar.gz
```

> Usuwanie plików SDS z wolumenu rozspójnia je z rekordami w bazie —
> aplikacja będzie pokazywać załącznik, którego nie ma. Usuwaj tylko
> załączniki substancji, które również usunięto z rejestru.

### Zapomniane hasło administratora

```bash
docker compose exec app python update_admin_password.py
```

---

## Checklist okresowej konserwacji

### Co tydzień
- [ ] Backup bazy wykonał się i ma sensowny rozmiar
- [ ] Przegląd logów pod kątem błędów
- [ ] Miejsce na dysku hosta

### Co miesiąc
- [ ] Przegląd dziennika zmian
- [ ] Przegląd kont użytkowników i uprawnień
- [ ] Test przywracania z backupu

### Co 6 miesięcy
- [ ] Aktualizacja listy SVHC (ECHA)
- [ ] Przegląd flag SVHC przy substancjach objętych zmianą
- [ ] Archiwizacja starych kart SDS
- [ ] Czyszczenie dziennika zmian starszego niż rok

### Co rok
- [ ] Aktualizacja bazy CLP (ECHA)
- [ ] Przegląd flag CMR przy substancjach objętych zmianą
- [ ] Przegląd uprawnień i kont administratorów
- [ ] Weryfikacja, że backup da się odtworzyć na czystym środowisku

---

## Kontakt w razie problemów

1. [DEPLOYMENT_GUIDE.md → Rozwiązywanie problemów](DEPLOYMENT_GUIDE.md#rozwiazywanie-problemow)
2. [BACKEND_GUIDE.md](BACKEND_GUIDE.md) - sekcja „Rozwiązywanie problemów"
3. Logi: `docker compose logs app` oraz `/app/logs/chem_man.log` w kontenerze
