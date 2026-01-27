# 🔐 INSTRUKCJA WDRAŻANIA ZABEZPIECZEŃ W CHEMMAN

## Podsumowanie zmian:

1. ✅ **DEFAULT_ADMIN_PASSWORD** - wymuszenie bezpiecznego hasła
2. ✅ **RATE LIMITING** - ochrona przed brute force atakami
3. ✅ **VALIDACJA INPUTU** - sprawdzenie długości i zawartości
4. ✅ **MIME TYPE VALIDATION** - sprawdzenie typu pliku PDF
5. ✅ **PATH TRAVERSAL PROTECTION** - ochrona przed dostępem do plików

---

## KROK 1: Instalacja Flask-Limiter

W terminalu (z aktywnym venv):

```bash
pip install flask-limiter
```

Sprawdzenie:
```bash
pip list | grep limiter
```

---

## KROK 2: Aktualizacja plików

Zastąp trzy pliki:

### A. config.py
- Skopiuj zawartość z `config_fixed.py`
- W `routes/config.py` zamień zawartość

### B. routes/auth.py
- Skopiuj zawartość z `auth_fixed.py`
- W `routes/auth.py` zamień zawartość

### C. routes/files.py
- Skopiuj zawartość z `files_fixed.py`
- W `routes/files.py` zamień zawartość

---

## KROK 3: Inicjalizacja Rate Limiter w app.py

**Dodaj na górze app.py (po importach):**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicjalizacja Rate Limiter (DODAJ TĘ LINIĘ!)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

**Potem w funkcji głównej (gdzie tworzysz app):**

```python
app = Flask(__name__)
app.config.from_object(config_type)

# DODAJ TĘ LINIĘ:
limiter.init_app(app)

# Rest of your code...
```

---

## KROK 4: Ustawienie hasła administratora (KRYTYCZNE!)

### W DEVELOPMENCIE:
Gdy uruchomisz aplikację, zobaczysz:
```
⚠️  DEVELOPMENT: Wygenerowano tymczasowe hasło admina: xxxxxxxxxxxxxx
```
Skopiuj to hasło i użyj do logowania!

### W PRODUKCJI:
**Musisz ustawić zmienną środowiskową PRZED uruchomieniem aplikacji:**

#### Windows (PowerShell):
```powershell
$env:CHEM_MAN_ADMIN_PASSWORD = "TwojeNoweBezpieczneHasło123!@#"
$env:FLASK_ENV = "production"
python app.py
```

#### Linux/Mac:
```bash
export CHEM_MAN_ADMIN_PASSWORD="TwojeNoweBezpieczneHasło123!@#"
export FLASK_ENV="production"
python app.py
```

#### Lub na Windowsie (CMD):
```cmd
set CHEM_MAN_ADMIN_PASSWORD=TwojeNoweBezpieczneHasło123!@#
set FLASK_ENV=production
python app.py
```

⚠️ **WAŻNE:** Jeśli nie ustawisz `CHEM_MAN_ADMIN_PASSWORD` w produkcji, aplikacja NIE URUCHOMI SIĘ!

---

## KROK 5: Testowanie

### Test 1: Rate Limiting na login
1. Wejdź na stronę logowania
2. Spróbuj zalogować się 6 razy z błędnym hasłem
3. Powinno pokazać: "429 Too Many Requests"

### Test 2: Walidacja inputu
1. Spróbuj zalogować się z hasłem 1 znakowym
2. Powinno pokazać: "Hasło jest za krótkie"

### Test 3: PDF Upload Validation
1. Spróbuj wrzucić plik txt zamiast PDF
2. Powinno pokazać: "Plik nie jest prawidłowym plikiem PDF"

### Test 4: Default password
1. Zaloguj się z domyślnym hasłem (takim jakie wygenerował system)
2. Powinno zadziałać
3. Zmień hasło natychmiast!

---

## KROK 6: Wdrożenie na GitHub

Po zmianach:

```bash
git add .
git commit -m "Security update: Add rate limiting, input validation, MIME type checking"
git push
```

---

## PODSUMOWANIE ZABEZPIECZEŃ:

| Funkcja | Status | Opis |
|---------|--------|------|
| Default password 'admin' | ✅ NAPRAWIONE | Wymuszenie zmiennej env |
| Brute force ochrona | ✅ DODANE | Rate limiting 5/min |
| Input validation | ✅ WZMOCNIONE | Min/max długość |
| File MIME validation | ✅ DODANE | Magic number check |
| Path traversal | ✅ CHRONIONE | Sprawdzanie '..' w nazwach |

---

## ⚠️ WAŻNE UWAGI:

1. **Hasło musi być silne!** Używaj co najmniej:
   - 12 znaków
   - Wielkie i małe litery
   - Cyfry
   - Znaki specjalne: !@#$%^&*

2. **Przechowywanie hasła:**
   - NIE wpisuj na stałe w kodzie
   - Użyj zmiennych środowiskowych
   - Na serwerze - przechowuj w `.env` lub systemowych zmiennych

3. **Rate limiting:**
   - Domyślnie: 5 prób/minutę na login
   - Możesz zmienić w `@limiter.limit("5 per minute")`
   - Dla Intranetu możesz zwiększyć na np. 10 per minute

---

## JEŚLI COŚ NIE DZIAŁA:

1. **"ModuleNotFoundError: No module named 'flask_limiter'"**
   - Zapomniano zainstalować: `pip install flask-limiter`

2. **"Musisz ustawić zmienną środowiskową 'CHEM_MAN_ADMIN_PASSWORD'"**
   - Aplikacja wymaga ENV var w produkcji - ustaw ją!

3. **Rate limiting nie działa**
   - Upewnij się że zainicjalizowałeś `limiter.init_app(app)` w app.py

4. **PDF upload zawsze mówi "nieprawidłowy plik"**
   - Upewnij się że nie uploadujesz skorumpowany PDF
   - Spróbuj innego pliku PDF

---

Gotowe! Twoja aplikacja ChemMan ma teraz solidne zabezpieczenia! 🔐
