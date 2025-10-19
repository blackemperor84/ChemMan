import os
import traceback
from datetime import datetime
import pandas as pd
import pytz
from flask import current_app, flash, redirect, url_for, jsonify, request
from flask_login import current_user
from sqlalchemy import or_

from models import db, AuditLog, SVHCSubstance


def allowed_file(filename):
    """Sprawdza, czy rozszerzenie pliku jest dozwolone."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def log_action(action, target_type=None, target_id=None, details=None):
    """Zapisuje wpis do dziennika zmian i commituje go."""
    try:
        user_id_log = current_user.id if current_user.is_authenticated else None
        username_log = current_user.username if current_user.is_authenticated else 'System/Unknown'

        log_entry = AuditLog(
            timestamp=datetime.utcnow(),
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
        current_app.logger.error(f"KRYTYCZNY BŁĄD: Nie udało się zapisać wpisu do AuditLog dla akcji '{action}': {e}")
        traceback.print_exc()


def convert_utc_to_local(utc_timestamp):
    """Konwertuje czas UTC na lokalny czas Warsaw i formatuje go."""
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


def handle_exception(e, operation_name, redirect_url=None):
    """Obsługuje wyjątki w jednolity sposób."""
    db.session.rollback()
    error_message = f'Błąd podczas {operation_name}: {e}'
    current_app.logger.error(error_message)
    traceback.print_exc()
    flash(error_message, 'error')
    
    if redirect_url:
        return redirect(redirect_url)
    return jsonify({'status': 'error', 'message': error_message}), 500


# # W pliku utils.py, zaktualizuj funkcję search_substances_in_excel:

# def search_substances_in_excel(query):
#     """Wyszukuje substancje w pliku Excel."""
#     current_app.logger.info(f"Rozpoczynam przeszukiwanie Excela dla: '{query}'")
#     try:
#         if not os.path.exists(current_app.config['EXCEL_FILE_PATH']):
#             current_app.logger.error(f"BŁĄD KRYTYCZNY: Plik Excel nie istnieje: {current_app.config['EXCEL_FILE_PATH']}")
#             return []

#         # Odczyt pliku Excel
#         try:
#             df = pd.read_excel(current_app.config['EXCEL_FILE_PATH'], header=0)
#             current_app.logger.info(f"Wczytano plik Excel: {current_app.config['EXCEL_FILE_PATH']}")
#             current_app.logger.debug(f"Znalezione kolumny przez Pandas: {df.columns.tolist()}")
#         except Exception as read_e:
#             current_app.logger.error(f"BŁĄD KRYTYCZNY podczas odczytu pliku Excel: {read_e}")
#             traceback.print_exc()
#             return []

#         # Definicje nazw kolumn
#         name_col = 'International Chemical Identification'
#         cas_col = 'CAS No'
#         ec_col = 'EC No'  # Nazwa kolumny w Excelu
#         classification_col = 'Classification'
#         h_phrases_col = 'Unnamed: 5'  # Kolumna F
#         scl_m_col = 'Specific Conc. Limits, M-factors'
        
#         # Wypisujemy wszystkie kolumny w pliku Excel dla debugowania
#         current_app.logger.info(f"Dostępne kolumny w pliku Excel: {df.columns.tolist()}")
        
#         # Sprawdzamy, czy istnieje kolumna EC No
#         if ec_col in df.columns:
#             current_app.logger.info(f"Kolumna {ec_col} istnieje w pliku Excel")
#             # Wypisujemy kilka przykładowych wartości dla debugowania
#             current_app.logger.info(f"Przykładowe wartości EC No: {df[ec_col].head(5).tolist()}")
#         else:
#             current_app.logger.warning(f"Kolumna {ec_col} nie istnieje w pliku Excel")
#             # Sprawdźmy alternatywne nazwy kolumn
#             possible_ec_columns = [col for col in df.columns if 'ec' in col.lower() or 'we' in col.lower()]
#             if possible_ec_columns:
#                 current_app.logger.info(f"Możliwe alternatywne kolumny EC: {possible_ec_columns}")
#                 ec_col = possible_ec_columns[0]  # Używamy pierwszej znalezionej
#                 current_app.logger.info(f"Używam alternatywnej kolumny EC: {ec_col}")
        
#         # Filtrowanie 
#         mask = (df[name_col].astype(str).str.contains(query, case=False, na=False)) | \
#                (df[cas_col].astype(str).str.contains(query, case=False, na=False))
               
#         # Dodaj wyszukiwanie po EC No, ale tylko jeśli kolumna istnieje
#         if ec_col in df.columns:
#             mask = mask | (df[ec_col].astype(str).str.contains(query, case=False, na=False))
            
#         filtered_df = df[mask]
#         current_app.logger.info(f"Znaleziono {len(filtered_df)} pasujących wierszy w DataFrame.")

#         # Dla debugowania, wypisujemy pierwsze znalezione rekordy
#         if not filtered_df.empty:
#             current_app.logger.info(f"Pierwszy znaleziony rekord: {filtered_df.iloc[0].to_dict()}")
        
#         # Wybieramy kolumny, które istnieją
#         available_cols = []
#         for col in [name_col, cas_col, ec_col, classification_col, h_phrases_col, scl_m_col]:
#             if col in df.columns:
#                 available_cols.append(col)
#             else:
#                 current_app.logger.warning(f"Kolumna {col} nie istnieje w pliku Excel")
        
#         # Wybierz tylko dostępne kolumny
#         results_df = filtered_df[available_cols].copy()
#         results_df.fillna('', inplace=True)

#         # Zmień nazwy kolumn
#         rename_map = {
#             name_col: 'name', 
#             cas_col: 'cas',
#             classification_col: 'classification',
#             h_phrases_col: 'h_phrases', 
#             scl_m_col: 'scl_mfactor'
#         }
        
#         # Dodaj EC No do mapy, tylko jeśli kolumna istnieje
#         if ec_col in available_cols:
#             rename_map[ec_col] = 'ec_number'
#             current_app.logger.info(f"Mapowanie kolumny {ec_col} na pole ec_number")
        
#         # DODAĆ: Zastosuj mapowanie nazw kolumn
#         results_df = results_df.rename(columns=rename_map)
#         current_app.logger.info(f"Zastosowano mapowanie kolumn: {rename_map}")
#         current_app.logger.info(f"Nazwy kolumn po mapowaniu: {results_df.columns.tolist()}")

#         # Po przekształceniu wyników, dodaj dodatkowe debugowanie
#         results = results_df.to_dict('records')
#         if results:
#             # Sprawdź, czy 'ec_number' jest w wynikach
#             if 'ec_number' in results[0]:
#                 current_app.logger.info(f"EC number w wynikach: {results[0]['ec_number']}")
#             else:
#                 current_app.logger.warning("Brak pola ec_number w wynikach")
#                 # Wypisz wszystkie klucze pierwszego wyniku
#                 current_app.logger.info(f"Dostępne klucze: {list(results[0].keys())}")
            
#             # Sprawdź, czy 'name' jest w wynikach
#             if 'name' in results[0]:
#                 current_app.logger.info(f"Name w wynikach: {results[0]['name']}")
#             else:
#                 current_app.logger.warning("Brak pola name w wynikach")
        
#         # Dla debugowania, wypisujemy pierwszy przekształcony wynik
#         if results:
#             current_app.logger.info(f"Pierwszy przekształcony wynik: {results[0]}")
        
#         current_app.logger.info(f"Zwracam {len(results)} wyników jako słowniki.")
#         return results

#     except Exception as e:
#         current_app.logger.error(f"BŁĄD KRYTYCZNY podczas przetwarzania danych z Excela: {e}")
#         traceback.print_exc()
#         return []


def validate_json_data(required_fields):
    """Dekorator do walidacji danych JSON w request."""
    def decorator(f):
        def wrapped(*args, **kwargs):
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

def is_cmr_substance(h_phrases):
    """
    Sprawdza, czy substancja jest klasyfikowana jako CMR na podstawie zwrotów H.
    CMR to substancje: Carcenogenic, Mutagenic, Reprotoxic.
    
    Parametry:
    - h_phrases: string zawierający zwroty H (może być None)
    
    Zwraca:
    - bool: True jeśli substancja jest CMR, False w przeciwnym razie
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


def is_svhc_substance(cas=None, ec_number=None, name=None):
    """
    Sprawdza, czy substancja jest na liście SVHC i zwraca powód, jeśli tak.

    Parametry:
    - cas: Numer CAS substancji (opcjonalny)
    - ec_number: Numer EC substancji (opcjonalny)
    - name: Nazwa substancji (opcjonalna)

    Zwraca:
    - str | None: Powód włączenia na listę SVHC jako string, lub None jeśli nie znaleziono.
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
        current_app.logger.error(f"Błąd podczas sprawdzania SVHC: {e}")
        traceback.print_exc()
        return None # W razie błędu zwracamy None