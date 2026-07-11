from datetime import datetime, timezone
from typing import Optional, Any, Callable, List
import pytz
from flask import current_app, flash, redirect, jsonify, request
from flask_login import current_user
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


def log_action(action: str, target_type: Optional[str] = None, target_id: Optional[int] = None, details: Optional[str] = None) -> None:
    """
    Zapisuje wpis do dziennika zmian (audit log) i commituje go.

    Args:
        action: Opis wykonywanej akcji
        target_type: Typ obiektu docelowego (np. 'Substance', 'Location')
        target_id: ID obiektu docelowego
        details: Dodatkowe szczegóły akcji
    """
    try:
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
        db.session.add(log_entry)
        db.session.commit()
        current_app.logger.info(f"Zapisano log: {action} przez {username_log}")

    except Exception as e:
        current_app.logger.exception(f"KRYTYCZNY BŁĄD: Nie udało się zapisać wpisu do AuditLog dla akcji '{action}': {e}")


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

def is_cmr_substance(h_phrases: Optional[str]) -> bool:
    """
    Sprawdza, czy substancja jest klasyfikowana jako CMR na podstawie zwrotów H.
    CMR to substancje: Carcinogenic (rakotwórcze), Mutagenic (mutagenne), Reprotoxic (działające szkodliwie na rozrodczość).

    Sprawdza obecność następujących zwrotów H:
    - H340: Może powodować wady genetyczne (mutagenne)
    - H350: Może powodować raka (rakotwórcze)
    - H360: Może działać szkodliwie na płodność lub dziecko w łonie matki (reprotoksyczne)

    Args:
        h_phrases: String zawierający zwroty H (może być None)

    Returns:
        bool: True jeśli substancja jest CMR, False w przeciwnym razie
    """
    if not h_phrases:
        return False
        
    # Konwertuj na string i zamień na małe litery dla spójności
    h_phrases_lower = str(h_phrases).lower()
    
    # Lista głównych zwrotów CMR
    cmr_phrases = ['h340', 'h350', 'h360']
    
    # Sprawdź, czy którykolwiek ze zwrotów CMR występuje w h_phrases
    for phrase in cmr_phrases:
        if phrase in h_phrases_lower:
            return True
            
    # Sprawdź przypadki z dodatkowymi literami (H340A, H350i, itp.)
    for phrase in cmr_phrases:
        # Użyj regex, aby znaleźć zwroty z dodatkowymi literami
        import re
        pattern = re.compile(f"{phrase}[a-z]", re.IGNORECASE)
        if pattern.search(h_phrases_lower):
            return True
            
    return False


def is_svhc_substance(cas: Optional[str] = None, ec_number: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
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
        Optional[str]: Powód włączenia na listę SVHC jako string, lub None jeśli nie znaleziono.
    """
    try:
        if not cas and not ec_number and not name:
            # current_app.logger.warning("Brak danych do sprawdzenia SVHC") # Można odkomentować dla debugowania
            return None

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
            return None

        # Szukamy pasującego rekordu SVHC
        svhc_record = SVHCSubstance.query.filter(or_(*query_filters)).first()

        if svhc_record:
            # current_app.logger.info(f"Znaleziono SVHC: {svhc_record.name}. Powód: {svhc_record.reason}")
            return svhc_record.reason or "Brak informacji o powodzie w bazie danych" # <--- KLUCZOWE: Zwraca powód
        else:
            # current_app.logger.debug(f"Nie znaleziono SVHC dla: CAS={cas}, EC={ec_number}, Name={name}")
            return None

    except Exception as e:
        current_app.logger.exception(f"Błąd podczas sprawdzania SVHC: {e}")
        return None # W razie błędu zwracamy None