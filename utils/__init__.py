import re
from datetime import datetime, timezone
from typing import Optional, Any, Callable, List, NamedTuple
from urllib.parse import urljoin, urlparse
import pytz
from flask import current_app, flash, redirect, jsonify, request
from flask_login import current_user
from markupsafe import Markup, escape
from sqlalchemy import or_

from models import db, AuditLog, SVHCSubstance


def utcnow() -> datetime:
    """Naive UTC datetime (matches existing DB timestamp storage).

    Replaces datetime.utcnow() which is deprecated in Python 3.12+.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def allowed_file(filename: str) -> bool:
    """
    Sprawdza, czy rozszerzenie pliku jest dozwolone.

    Args:
        filename: Nazwa pliku do sprawdzenia

    Returns:
        bool: True jeśli rozszerzenie jest dozwolone, False w przeciwnym razie
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def log_action(action: str, target_type: Optional[str] = None, target_id: Optional[int] = None,
               details: Optional[str] = None, commit: bool = True) -> None:
    """
    Zapisuje wpis do dziennika zmian (audit log).

    Args:
        action: Opis wykonywanej akcji
        target_type: Typ obiektu docelowego (np. 'Substance', 'Location')
        target_id: ID obiektu docelowego
        details: Dodatkowe szczegoly akcji
        commit: Gdy True (domyslnie) wpis jest commitowany od razu — tryb dla
                wywolan PO commicie wlasciwej operacji. Gdy False, wpis jest
                tylko dodawany do sesji i utrwala go commit wywolujacego, dzieki
                czemu operacja i jej slad w dzienniku sa jedna transakcja.

    Raises:
        Wyjatek zapisu jest propagowany tylko przy commit=False — wtedy transakcja
        wywolujacego jeszcze trwa i moze zostac wycofana w calosci. Przy commit=True
        operacja jest juz utrwalona, wiec blad dziennika jest logowany, a sesja
        wycofana, zeby nie zatruc kolejnych zapytan wywolujacego.
    """
    user_id_log = current_user.id if current_user.is_authenticated else None
    username_log = current_user.username if current_user.is_authenticated else 'System/Unknown'

    log_entry = AuditLog(
        timestamp=utcnow(),
        user_id=user_id_log,
        username=username_log,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )

    if not commit:
        # Transakcja wywolujacego obejmuje ten wpis — blad ma sie wydostac na zewnatrz.
        db.session.add(log_entry)
        return

    try:
        db.session.add(log_entry)
        db.session.commit()
        current_app.logger.info(f"Zapisano log: {action} przez {username_log}")
    except Exception as e:
        # Bez rollbacku sesja zostaje w stanie bledu i wywracaja sie kolejne zapytania
        # wywolujacego — mimo ze jego wlasna operacja zostala juz zatwierdzona.
        db.session.rollback()
        current_app.logger.exception(
            f"KRYTYCZNY BLAD: Nie udalo sie zapisac wpisu do AuditLog dla akcji '{action}': {e}"
        )


def nl2br(value: Any, separator: str = '<br>') -> Markup:
    """
    Zamienia znaki nowej linii na znacznik HTML, escapując najpierw treść.

    Zastępuje wzorzec `value|replace("\\n", "<br>")|safe`, który przepuszczał
    HTML wpisany przez użytkownika (podatność XSS typu stored).

    Args:
        value: Wartość do wyrenderowania (dowolny typ, None daje pusty wynik)
        separator: Znacznik HTML wstawiany w miejsce nowej linii.
                   Pochodzi z szablonu, nie od użytkownika, więc nie jest escapowany.

    Returns:
        Markup: Bezpieczny HTML - treść jest zescapowana, separator nie.
    """
    if value is None:
        return Markup('')

    return Markup(separator).join(escape(part) for part in str(value).split('\n'))


def convert_utc_to_local(utc_timestamp: Optional[datetime]) -> str:
    """
    Konwertuje czas UTC na lokalny czas Warsaw i formatuje go.

    Args:
        utc_timestamp: Timestamp w UTC (datetime object)

    Returns:
        str: Sformatowany czas lokalny (YYYY-MM-DD HH:MM) lub 'Brak danych'
    """
    if not utc_timestamp:
        return 'Brak danych'
    
    warsaw_tz = pytz.timezone(current_app.config['TIMEZONE'])
    # Upewnij się, że timestamp jest świadomy strefy czasowej (tzaware)
    if utc_timestamp.tzinfo is None:
        aware_utc_dt = pytz.utc.localize(utc_timestamp)
    else:
        aware_utc_dt = utc_timestamp
    
    local_dt = aware_utc_dt.astimezone(warsaw_tz)
    return local_dt.strftime('%Y-%m-%d %H:%M')


def handle_exception(e: Exception, operation_name: str, redirect_url: Optional[str] = None) -> Any:
    """
    Obsługuje wyjątki w jednolity sposób.

    Args:
        e: Wyjątek do obsługi
        operation_name: Nazwa operacji, która spowodowała wyjątek
        redirect_url: URL do przekierowania (opcjonalny)

    Returns:
        Response: Redirect lub JSON response z błędem
    """
    db.session.rollback()
    error_message = f'Błąd podczas {operation_name}: {e}'
    current_app.logger.exception(error_message)
    flash(error_message, 'error')
    
    if redirect_url:
        return redirect(redirect_url)
    return jsonify({'status': 'error', 'message': error_message}), 500


def validate_json_data(required_fields: List[str]) -> Callable:
    """
    Dekorator do walidacji danych JSON w request.

    Args:
        required_fields: Lista wymaganych pól w JSON

    Returns:
        Callable: Dekorator funkcji
    """
    def decorator(f: Callable) -> Callable:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Brak danych JSON.'}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    'status': 'error', 
                    'message': f'Brakujące pola: {", ".join(missing_fields)}'
                }), 400
                
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Zwroty H odpowiadające kategorii 1A/1B (polski rejestr czynników rakotwórczych
# lub mutagennych obejmuje wyłącznie kategorię 1A/1B — H341/H351/H361 to kategoria 2
# i celowo NIE są tu uwzględnione).
CMR_H_PHRASES = ('h340', 'h350', 'h360')

# Klasyfikacja tekstowa CLP w kategorii 1A/1B, np. "Carc. 1B", "Muta. 1A", "Repr. 1B".
# Kategoria 2 ("Carc. 2") celowo nie pasuje do tego wzorca.
_CMR_CLASSIFICATION_RE = re.compile(r'\b(?:carc|muta|repr)\.?\s*1\s*[ab]\b', re.IGNORECASE)

# Zwroty H z dodatkowymi literami, np. H360FD, H350i.
_CMR_H_PHRASE_RE = re.compile('|'.join(f'{p}[a-z]*' for p in CMR_H_PHRASES), re.IGNORECASE)


def is_cmr_substance(h_phrases: Optional[str], classification: Optional[str] = None) -> bool:
    """
    Sprawdza, czy substancja jest klasyfikowana jako CMR (kategoria 1A/1B).

    CMR to substancje: Carcinogenic (rakotwórcze), Mutagenic (mutagenne),
    Reprotoxic (działające szkodliwie na rozrodczość).

    Sprawdzane są dwa źródła, ponieważ karty charakterystyki bywają niekompletne
    — zdarzają się rekordy z klasyfikacją "Carc. 1B" i pustym polem zwrotów H:

    1. Zwroty H:
       - H340: Może powodować wady genetyczne (mutagenne)
       - H350: Może powodować raka (rakotwórcze)
       - H360: Może działać szkodliwie na płodność lub dziecko w łonie matki
    2. Klasyfikacja tekstowa CLP w kategorii 1A/1B, np. "Carc. 1B", "Muta. 1A".

    Kategoria 2 (H341/H351/H361, "Carc. 2") NIE jest traktowana jako CMR — polski
    rejestr czynników rakotwórczych lub mutagennych obejmuje tylko kategorię 1A/1B.

    Args:
        h_phrases: String zawierający zwroty H (może być None)
        classification: String z klasyfikacją CLP (może być None)

    Returns:
        bool: True jeśli substancja jest CMR, False w przeciwnym razie
    """
    if h_phrases and _CMR_H_PHRASE_RE.search(str(h_phrases)):
        return True

    if classification and _CMR_CLASSIFICATION_RE.search(str(classification)):
        return True

    return False


SVHC_FOUND = 'found'
SVHC_NOT_FOUND = 'not_found'
SVHC_UNKNOWN = 'unknown'


class SVHCResult(NamedTuple):
    """Wynik sprawdzenia listy SVHC.

    Rozróżnia "nie znaleziono na liście" od "nie udało się zweryfikować"
    (np. błąd bazy danych) — wcześniej oba przypadki zwracały None, przez co
    substancja mogła zostać cicho zapisana jako nie-SVHC mimo nieudanej weryfikacji.
    """

    status: str
    reason: Optional[str]

    @property
    def is_svhc(self) -> bool:
        """True tylko przy potwierdzonym trafieniu na liście SVHC."""
        return self.status == SVHC_FOUND

    @property
    def verified(self) -> bool:
        """False, jeśli weryfikacja się nie powiodła i wynik jest niewiarygodny."""
        return self.status != SVHC_UNKNOWN


def check_svhc_substance(cas: Optional[str] = None, ec_number: Optional[str] = None, name: Optional[str] = None) -> 'SVHCResult':
    """
    Sprawdza, czy substancja jest na liście SVHC (Substance of Very High Concern) i zwraca powód, jeśli tak.

    SVHC to substancje budzące szczególnie duże obawy zgodnie z rozporządzeniem REACH.

    Wyszukiwanie odbywa się według priorytetu:
    1. Numer CAS (dokładne dopasowanie lub bez separatorów)
    2. Numer EC (dokładne dopasowanie lub bez separatorów)
    3. Nazwa (częściowe dopasowanie, tylko jeśli brak CAS/EC)

    Args:
        cas: Numer CAS substancji (opcjonalny)
        ec_number: Numer EC substancji (opcjonalny)
        name: Nazwa substancji (opcjonalna)

    Returns:
        SVHCResult: status weryfikacji (found / not_found / unknown) oraz powód.
    """
    try:
        if not cas and not ec_number and not name:
            # current_app.logger.warning("Brak danych do sprawdzenia SVHC") # Można odkomentować dla debugowania
            return SVHCResult(SVHC_NOT_FOUND, None)

        query_filters = []
        if cas:
            cas = str(cas).strip()
            if cas:
                query_filters.append(SVHCSubstance.cas == cas)
                cas_clean = cas.replace('-', '').replace(' ', '')
                if cas_clean != cas:
                    query_filters.append(SVHCSubstance.cas.ilike(f"%{cas_clean}%"))

        if ec_number:
            ec_number = str(ec_number).strip()
            if ec_number:
                query_filters.append(SVHCSubstance.ec_number == ec_number)
                ec_clean = ec_number.replace('-', '').replace(' ', '')
                if ec_clean != ec_number:
                    query_filters.append(SVHCSubstance.ec_number.ilike(f"%{ec_clean}%"))

        # Sprawdzanie nazwy może być mniej precyzyjne, używamy go jako fallback
        # jeśli CAS i EC nie pasują, lub jako główny filtr, jeśli tylko nazwa jest podana
        if name and not cas and not ec_number: # Tylko jeśli nie ma CAS/EC
             name = str(name).strip()
             if name:
                 query_filters.append(SVHCSubstance.name.ilike(f"%{name}%"))

        if not query_filters:
            return SVHCResult(SVHC_NOT_FOUND, None)

        # Szukamy pasującego rekordu SVHC
        svhc_record = SVHCSubstance.query.filter(or_(*query_filters)).first()

        if svhc_record:
            # current_app.logger.info(f"Znaleziono SVHC: {svhc_record.name}. Powód: {svhc_record.reason}")
            return SVHCResult(SVHC_FOUND, svhc_record.reason or "Brak informacji o powodzie w bazie danych")
        else:
            # current_app.logger.debug(f"Nie znaleziono SVHC dla: CAS={cas}, EC={ec_number}, Name={name}")
            return SVHCResult(SVHC_NOT_FOUND, None)

    except Exception as e:
        current_app.logger.exception(f"Błąd podczas sprawdzania SVHC: {e}")
        # Weryfikacja się nie powiodła — to NIE jest to samo co "nie znaleziono".
        return SVHCResult(SVHC_UNKNOWN, None)


def is_svhc_substance(cas: Optional[str] = None, ec_number: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
    """
    Zwraca powód włączenia na listę SVHC albo None.

    Cienka nakładka na check_svhc_substance() zachowana dla zgodności z kodem
    wyświetlającym. UWAGA: None oznacza tu zarówno "nie znaleziono", jak i
    "weryfikacja nieudana". W ścieżkach zapisu używaj check_svhc_substance(),
    aby rozróżnić te przypadki.
    """
    return check_svhc_substance(cas=cas, ec_number=ec_number, name=name).reason


def is_safe_redirect_url(target: Optional[str]) -> bool:
    """
    Sprawdza, czy adres przekierowania wskazuje na tę samą aplikację.

    Chroni przed open redirect: parametr ?next= pochodzi od użytkownika i bez
    walidacji pozwalałby przekierować zalogowaną osobę na obcą domenę
    (np. na podrobioną stronę logowania).

    Args:
        target: Adres do sprawdzenia (może być None)

    Returns:
        bool: True jeśli adres jest lokalny i bezpieczny
    """
    if not target:
        return False

    # "//evil.com" i "\evil.com" są traktowane przez przeglądarki jak adres
    # bezwzględny, a urlparse nie zawsze je tak widzi — odrzucamy je wprost.
    if target.startswith('//') or target.startswith(chr(92)):
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def csv_safe(value: Any) -> str:
    """
    Neutralizuje wstrzyknięcie formuły w eksporcie CSV.

    Excel/LibreOffice traktują komórkę zaczynającą się od '=', '+', '-', '@'
    (a także tabulatora lub CR) jak formułę, więc dane wpisane przez użytkownika
    mogłyby wykonać kod po otwarciu pliku. Poprzedzamy taką komórkę apostrofem.

    Nie używaj tej funkcji do celowo tworzonych komórek typu ="0012-34-5",
    które wymuszają tekstowy format numerów CAS/WE.

    Args:
        value: Wartość komórki (dowolny typ, None -> pusty string)

    Returns:
        str: Bezpieczna zawartość komórki
    """
    if value is None:
        return ''

    text = str(value)
    if text and text[0] in ('=', '+', '-', '@', chr(9), chr(13)):
        return "'" + text

    return text
