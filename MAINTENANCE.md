# Przewodnik Konserwacji ChemMan

Instrukcja dla administratorów systemu - codzienne operacje, backup, aktualizacje.

---

## 📋 Spis treści

1. [Codzienne zadania](#codzienne-zadania)
2. [Backup bazy danych](#backup-bazy-danych)
3. [Aktualizacja bazy substancji](#aktualizacja-bazy-substancji)
4. [Aktualizacja listy SVHC](#aktualizacja-listy-svhc)
5. [Zarządzanie użytkownikami](#zarządzanie-użytkownikami)
6. [Monitoring systemu](#monitoring-systemu)
7. [Procedury awaryjne](#procedury-awaryjne)

---

## Codzienne zadania

### Sprawdzenie logów
```bash
# Sprawdź logi aplikacji (jeśli są włączone)
cat logs/chem_man.log | tail -n 50

# Sprawdź ostatnie zmiany w dzienniku
# Panel admina → "Dziennik Zmian"
```

### Monitorowanie miejsca na dysku
```bash
# Windows
dir instance\uploads\sds

# Linux
du -sh instance/uploads/sds/
```

**Zalecane:** Regularnie archiwizuj stare pliki SDS (co kwartał).

---

## Backup bazy danych

### Automatyczny backup (zalecany)

**Skrypt `backup.py`:**
```python
import shutil
import os
from datetime import datetime

# Katalogi
DB_PATH = 'instance/chem_man.db'
BACKUP_DIR = 'backups'
SDS_DIR = 'instance/uploads/sds'

# Utwórz folder backupów
os.makedirs(BACKUP_DIR, exist_ok=True)

# Data dla nazwy pliku
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Backup bazy danych
db_backup = f'{BACKUP_DIR}/chem_man_db_{timestamp}.db'
shutil.copy2(DB_PATH, db_backup)
print(f'✓ Backup bazy danych: {db_backup}')

# Backup plików SDS (opcjonalnie - może być duży!)
sds_backup = f'{BACKUP_DIR}/sds_{timestamp}'
if os.path.exists(SDS_DIR):
    shutil.copytree(SDS_DIR, sds_backup)
    print(f'✓ Backup plików SDS: {sds_backup}')

print('✓ Backup zakończony!')
```

**Uruchomienie:**
```bash
python backup.py
```

### Harmonogram backupów (Windows - Task Scheduler)

1. Otwórz **Harmonogram zadań**
2. Utwórz zadanie podstawowe
3. **Nazwa:** ChemMan Backup
4. **Wyzwalacz:** Codziennie o 2:00
5. **Akcja:** Uruchom program
   - **Program:** `C:\ścieżka\do\venv\Scripts\python.exe`
   - **Argumenty:** `backup.py`
   - **Katalog:** `C:\ścieżka\do\chem-man`

### Harmonogram backupów (Linux - cron)
```bash
# Edytuj crontab
crontab -e

# Dodaj linię (backup codziennie o 2:00)
0 2 * * * cd /ścieżka/do/chem-man && /ścieżka/do/venv/bin/python backup.py
```

### Przywracanie z backupu
```bash
# 1. ZATRZYMAJ aplikację
# 2. Skopiuj backup
cp backups/chem_man_db_20250117_120000.db instance/chem_man.db

# 3. Przywróć pliki SDS (jeśli potrzeba)
rm -rf instance/uploads/sds
cp -r backups/sds_20250117_120000 instance/uploads/sds

# 4. Uruchom aplikację ponownie
```

---

## Aktualizacja bazy substancji CLP

**Częstotliwość:** Co 6-12 miesięcy (gdy ECHA opublikuje nową wersję)

### Przygotowanie

1. Pobierz najnowszą bazę CLP z ECHA
2. Zapisz jako `substancje_baza_NEW.xlsx`
3. **Sprawdź strukturę pliku Excel:**
```bash
python check_excel.py
```

Jeśli kolumny się zmieniły, zaktualizuj `import_excel.py`.

### Procedura aktualizacji
```bash
# 1. BACKUP OBECNEJ BAZY!
python backup.py

# 2. Usuń stare dane
python -c "from app import create_app, db, ExcelSourceSubstance; app=create_app(); app.app_context().push(); ExcelSourceSubstance.query.delete(); db.session.commit(); print('Stare dane usunięte')"

# 3. Zamień plik
mv substancje_baza.xlsx substancje_baza_OLD.xlsx
mv substancje_baza_NEW.xlsx substancje_baza.xlsx

# 4. Import nowych danych
python import_excel.py

# 5. Weryfikacja
python -c "from app import create_app, db, ExcelSourceSubstance; app=create_app(); app.app_context().push(); print(f'Zaimportowano {ExcelSourceSubstance.query.count()} substancji')"
```

### Aktualizacja flag CMR w istniejących substancjach

Po aktualizacji bazy CLP, zaktualizuj flagi CMR:

**Skrypt `update_cmr_flags.py`:**
```python
from app import create_app, db
from models import Substance
from utils import is_cmr_substance

app = create_app()

with app.app_context():
    substances = Substance.query.all()
    updated = 0
    
    for sub in substances:
        # Sprawdź czy jest CMR według nowej bazy
        is_cmr = is_cmr_substance(
            classification=sub.classification,
            h_phrases=sub.h_phrases
        )
        
        if sub.is_cmr != is_cmr:
            sub.is_cmr = is_cmr
            updated += 1
    
    db.session.commit()
    print(f'Zaktualizowano {updated} substancji')
```
```bash
python update_cmr_flags.py
```

---

## Aktualizacja listy SVHC

**Częstotliwość:** Co 6 miesięcy (ECHA publikuje nowe listy w czerwcu i grudniu)

### Procedura
```bash
# 1. Pobierz nową listę SVHC z ECHA
# Zapisz jako svhc_NEW.xlsx

# 2. BACKUP!
python backup.py

# 3. Sprawdź strukturę
python check_svhc.py

# 4. Zamień plik
mv svhc.xlsx svhc_OLD.xlsx
mv svhc_NEW.xlsx svhc.xlsx

# 5. Re-import
flask import-svhc

# 6. Weryfikacja
python -c "from app import create_app, db, SVHCSubstance; app=create_app(); app.app_context().push(); print(f'Lista SVHC: {SVHCSubstance.query.count()} substancji')"
```

### Aktualizacja flag SVHC w istniejących substancjach

**Skrypt `update_svhc_flags.py`:**
```python
from app import create_app, db
from models import Substance
from utils import is_svhc_substance

app = create_app()

with app.app_context():
    substances = Substance.query.all()
    updated = 0
    
    for sub in substances:
        svhc_reason = is_svhc_substance(
            cas=sub.cas,
            ec_number=sub.ec_number,
            name=sub.name
        )
        
        new_is_svhc = svhc_reason is not None
        
        if sub.is_svhc != new_is_svhc:
            sub.is_svhc = new_is_svhc
            updated += 1
    
    db.session.commit()
    print(f'Zaktualizowano {updated} substancji')
```
```bash
python update_svhc_flags.py
```

---

## Zarządzanie użytkownikami

### Dodawanie użytkownika przez CLI
```bash
python -c "
from app import create_app, db, User
app = create_app()
app.app_context().push()

user = User(
    username='jan.kowalski',
    is_admin=False,
    can_view=True,
    can_add=True,
    can_edit=False,
    can_delete=False,
    can_move=False,
    can_copy=False,
    can_upload_sds=True,
    can_add_location=False,
    can_delete_location=False
)
user.set_password('TymczasoweHaslo123!')
db.session.add(user)
db.session.commit()
print(f'Utworzono użytkownika: {user.username}')
"
```

### Reset hasła użytkownika
```bash
python -c "
from app import create_app, db, User
app = create_app()
app.app_context().push()

username = 'jan.kowalski'
new_password = 'NoweHaslo123!'

user = User.query.filter_by(username=username).first()
if user:
    user.set_password(new_password)
    db.session.commit()
    print(f'Hasło zmienione dla: {username}')
else:
    print(f'Nie znaleziono użytkownika: {username}')
"
```

### Usuwanie nieaktywnych użytkowników

**Panel admina → Zarządzaj użytkownikami → Usuń**

Lub przez CLI:
```bash
python -c "
from app import create_app, db, User
app = create_app()
app.app_context().push()

username = 'stary.user'
user = User.query.filter_by(username=username).first()
if user:
    db.session.delete(user)
    db.session.commit()
    print(f'Usunięto: {username}')
"
```

---

## Monitoring systemu

### Sprawdzanie rozmiaru bazy
```bash
# Windows
dir instance\chem_man.db

# Linux
ls -lh instance/chem_man.db
```

**Zalecane:** Jeśli baza przekracza 500MB, rozważ czyszczenie dziennika zmian.

### Czyszczenie starego dziennika zmian
```bash
python -c "
from app import create_app, db, AuditLog
from datetime import datetime, timedelta
app = create_app()
app.app_context().push()

# Usuń wpisy starsze niż 1 rok
cutoff = datetime.utcnow() - timedelta(days=365)
deleted = AuditLog.query.filter(AuditLog.timestamp < cutoff).delete()
db.session.commit()
print(f'Usunięto {deleted} starych wpisów z dziennika')
"
```

### Sprawdzanie liczby substancji
```bash
python -c "
from app import create_app, db
from models import Substance, Location, ExcelSourceSubstance, SVHCSubstance
app = create_app()
app.app_context().push()

print(f'Substancje w lokalizacjach: {Substance.query.count()}')
print(f'Lokalizacje: {Location.query.count()}')
print(f'Baza CLP: {ExcelSourceSubstance.query.count()}')
print(f'Lista SVHC: {SVHCSubstance.query.count()}')
"
```

---

## Procedury awaryjne

### Aplikacja nie startuje
```bash
# 1. Sprawdź logi błędów
python app.py

# 2. Sprawdź czy baza istnieje
ls instance/chem_man.db

# 3. Jeśli brak bazy, przywróć z backupu
cp backups/chem_man_db_[DATA].db instance/chem_man.db

# 4. Sprawdź uprawnienia do plików
# Windows: Właściwości → Zabezpieczenia
# Linux: chmod 644 instance/chem_man.db
```

### Uszkodzona baza danych
```bash
# 1. Sprawdź integralność
sqlite3 instance/chem_man.db "PRAGMA integrity_check;"

# 2. Jeśli uszkodzona, przywróć z backupu
mv instance/chem_man.db instance/chem_man_USZKODZONA.db
cp backups/chem_man_db_[DATA].db instance/chem_man.db

# 3. Jeśli brak backupu, spróbuj naprawić
sqlite3 instance/chem_man_USZKODZONA.db ".dump" | sqlite3 instance/chem_man_NAPRAWIONA.db
```

### Brak miejsca na dysku
```bash
# 1. Sprawdź rozmiar plików SDS
du -sh instance/uploads/sds/

# 2. Archiwizuj stare pliki SDS
tar -czf sds_archive_$(date +%Y%m%d).tar.gz instance/uploads/sds/
mv sds_archive_*.tar.gz /ścieżka/do/archiwum/

# 3. Opcjonalnie usuń oryginały (UWAGA!)
# rm instance/uploads/sds/*.pdf
```

### Zapomniałem hasła admina
```bash
# Reset hasła admina
python -c "
from app import create_app, db, User
app = create_app()
app.app_context().push()

admin = User.query.filter_by(username='admin').first()
admin.set_password('NoweHaslo123!')
db.session.commit()
print('Hasło admina zresetowane!')
"
```

---

## Checklist okresowej konserwacji

### Co tydzień
- [ ] Backup bazy danych
- [ ] Sprawdzenie logów błędów
- [ ] Monitorowanie miejsca na dysku

### Co miesiąc
- [ ] Przegląd dziennika zmian
- [ ] Sprawdzenie nieaktywnych użytkowników
- [ ] Test przywracania z backupu

### Co 6 miesięcy
- [ ] Aktualizacja listy SVHC
- [ ] Aktualizacja flag SVHC w substancjach
- [ ] Archiwizacja starych plików SDS
- [ ] Czyszczenie starego dziennika zmian (>1 rok)

### Co rok
- [ ] Aktualizacja bazy CLP
- [ ] Aktualizacja flag CMR w substancjach
- [ ] Przegląd uprawnień użytkowników
- [ ] Sprawdzenie integralności bazy danych

---

## Kontakt w razie problemów

Jeśli powyższe procedury nie rozwiązują problemu:

1. Sprawdź [BACKEND_GUIDE.md](BACKEND_GUIDE.md) - sekcja "Rozwiązywanie problemów"
2. Sprawdź logi: `logs/chem_man.log`
3. Zachowaj kopię błędu (screenshot/treść)