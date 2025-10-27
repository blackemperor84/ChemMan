import io
import csv
from flask import Blueprint, request, flash, redirect, url_for, Response, jsonify, render_template, current_app
import traceback
from flask_login import login_required
from decorators import view_permission_required
from sqlalchemy import or_
import urllib.parse
import re # Import modułu re do wyrażeń regularnych

from models import db, Location, Substance, ExcelSourceSubstance, SVHCSubstance

# Zakładając, że handle_exception i is_svhc_substance są w utils
# Pamiętaj, aby upewnić się, że utils.__init__.py zawiera te funkcje
from utils import handle_exception, is_svhc_substance


from models import db, ExcelSourceSubstance # Dodaj import nowego modelu
# from utils import is_svhc_substance # Ta linia jest teraz wyżej, można ją usunąć jeśli była zdublowana

# Utworzenie blueprintu dla eksportu danych
export_bp = Blueprint('export', __name__)


@export_bp.route('/search_substances')
@login_required
@view_permission_required
def search_substances_api():
    """API do wyszukiwania substancji w tabeli zaimportowanej z Excela ORAZ w SVHC."""
    current_app.logger.debug("Obsługa trasy /search_substances (API - Baza Danych)")
    query_param = request.args.get('query', '').strip()
    results = []

    if len(query_param) >= 2:
        current_app.logger.info(f"Zapytanie API (Baza) o substancję: '{query_param}'")
        search_term = f"%{query_param}%"

        try:
            # 1. Wyszukaj w bazie CLP
            found_substances = ExcelSourceSubstance.query.filter(
                or_(
                    ExcelSourceSubstance.name.ilike(search_term),
                    ExcelSourceSubstance.cas.ilike(search_term),
                    ExcelSourceSubstance.ec_number.ilike(search_term)
                )
            ).limit(50).all()

            for sub in found_substances:
                results.append({
                    'name': sub.name,
                    'cas': sub.cas,
                    'ec_number': sub.ec_number,
                    'classification': sub.classification,
                    'h_phrases': sub.h_phrases,
                    'scl_mfactor': sub.scl_mfactor,
                    'source': 'CLP'  # Oznacz źródło
                })

            # 2. Wyszukaj w bazie SVHC
            found_svhc = SVHCSubstance.query.filter(
                or_(
                    SVHCSubstance.name.ilike(search_term),
                    SVHCSubstance.cas.ilike(search_term),
                    SVHCSubstance.ec_number.ilike(search_term)
                )
            ).limit(50).all()

            for sub in found_svhc:
                # Sprawdź czy już nie ma w wynikach (z bazy CLP)
                already_exists = any(
                    r['cas'] == sub.cas and sub.cas 
                    for r in results
                )
                
                if not already_exists:
                    results.append({
                        'name': sub.name,
                        'cas': sub.cas or '',
                        'ec_number': sub.ec_number or '',
                        'classification': '',  # SVHC nie ma klasyfikacji
                        'h_phrases': '',
                        'scl_mfactor': '',
                        'source': 'SVHC'  # Oznacz źródło
                    })

            current_app.logger.info(f"Wyszukiwanie zwróciło {len(results)} wyników (CLP + SVHC).")

        except Exception as e:
            current_app.logger.error(f"Błąd podczas wyszukiwania: {e}")
            traceback.print_exc()
            return jsonify([])
    else:
        current_app.logger.info("Zapytanie API (Baza) zbyt krótkie.")

    return jsonify(results)


@export_bp.route('/export/location/<int:location_id>/csv')
@login_required
@view_permission_required
def export_location_csv(location_id):
    """Eksportuje substancje dla danej lokalizacji do CSV."""
    current_app.logger.debug(f"Eksport CSV dla lokacji ID: {location_id}")
    try:
        location = Location.query.get_or_404(location_id)
        # Pobieramy substancje dla tej lokalizacji, sortujemy np. po lokalizacji fizycznej, a potem nazwie
        substances = Substance.query.filter_by(location_id=location.id).order_by(Substance.physical_location, Substance.name).all()

        # Przygotowanie pliku CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Nagłówek - DODANO 'Lokalizacja fizyczna'
        header = ['Nazwa chemiczna', 'Nr CAS', 'Klasyfikacja', 'Zwroty H', 'SCL/M-factor', 'Lokalizacja', 'Komentarz']
        writer.writerow(header)

        # Dane
        for sub in substances:
            cas_val = sub.cas or ''
            # Formatowanie CAS jako tekst w Excelu (zapobiega konwersji na liczbę/datę)
            excel_cas = f'="{cas_val}"' if cas_val else ''

            # DODANO sub.physical_location, używamy 'Nieznana' jeśli brak wartości
            writer.writerow([
                sub.name,
                excel_cas,
                sub.classification or '',
                sub.h_phrases or '',
                sub.scl_mfactor or '',
                sub.physical_location or 'Nieznana', # Lokalizacja na pozycji 6
                sub.comment or '', # Komentarz na pozycji 7
            ])

        # Finalizacja i przygotowanie odpowiedzi
        csv_data = output.getvalue()
        # Bezpieczna nazwa pliku
        safe_name = "".join(c if c.isalnum() else "_" for c in location.name)
        filename = f"ChemMan_lok_{safe_name}_subst.csv"

        # Użyj RFC 5987 dla nazw plików z nie-ASCII (lepsza kompatybilność)
        filename_header = "attachment; filename*=UTF-8''{}".format(
            urllib.parse.quote(filename, encoding='utf-8')
        )

        response = Response(
            csv_data.encode('utf-8-sig'), # Używamy utf-8-sig dla poprawnego otwierania w Excel
            mimetype='text/csv',
            headers={"Content-Disposition": filename_header}
        )

        current_app.logger.info(f"Zakończono CSV dla lokacji: {filename}")
        return response

    except Exception as e:
        # Używamy istniejącej funkcji do obsługi błędów
        return handle_exception(
            e,
            "eksportu CSV lokacji",
            url_for('locations.view_location', location_id=location_id)
        )


@export_bp.route('/export/all/csv')
@login_required
@view_permission_required
def export_all_csv():
    """Eksportuje wszystkie (lub filtrowane) substancje do CSV."""
    current_app.logger.debug("Globalny eksport CSV")

     # Pobierz parametry filtrowania
    filter_query = request.args.get('filter', '').strip()
    physical_location = request.args.get('physical_location', '').strip()
    user_location = request.args.get('user_location', '').strip()
    is_cmr = request.args.get('is_cmr', '').strip()
    is_svhc_param = request.args.get('is_svhc', '').strip() # Zmieniona nazwa zmiennej
    has_sds = request.args.get('has_sds', '').strip()

    current_app.logger.info(f"Filtr tekstowy: '{filter_query}', Lokalizacja fizyczna: '{physical_location}', " +
                            f"Użytkownik: '{user_location}', CMR (param): '{is_cmr}', SVHC (param): '{is_svhc_param}', SDS (param): '{has_sds}'")

    try:
        # Przygotowanie zapytania
        # Zaczynamy od Substance i zawsze joinujemy Location
        query = db.session.query(Substance).join(Location)

        # Zastosowanie filtrów
        filters_applied = False

        # Filtr tekstowy (zmodyfikowany)
        if filter_query:
            search_term = f"%{filter_query}%"
            # Przekształć zapytanie na małe litery do porównania
            filter_query_lower = filter_query.lower()

            # Warunek bazowy dla wyszukiwania tekstowego
            text_filter_condition = or_(
                Location.name.ilike(search_term),
                Substance.name.ilike(search_term),
                Substance.cas.ilike(search_term),
                Substance.ec_number.ilike(search_term),
                Substance.classification.ilike(search_term),
                Substance.h_phrases.ilike(search_term),
                Substance.physical_location.ilike(search_term),
                Substance.comment.ilike(search_term)
            )

            # Dodaj warunek dla 'svhc' w filtrze tekstowym
            svhc_text_condition = None
            # Użyj regex, aby znaleźć "svhc" jako pełne słowo lub jego część,
            # ale nie jako podciąg w dłuższych słowach, chyba że jest na początku/końcu/samodzielnie
            # Poprawiony regex: szuka "svhc" otoczonego przez granice słów (początek, koniec, spacja itp.)
            # lub gdy jest na początku/końcu całego ciągu.
            if re.search(r'(^|\W)svhc($|\W)', filter_query_lower):
                # Sprawdź, czy substancja jest SVHC
                svhc_text_condition = Substance.is_svhc == True
            # Dodaj warunek dla 'cmr' w filtrze tekstowym
            cmr_text_condition = None
            if re.search(r'(^|\W)cmr($|\W)', filter_query_lower):
                cmr_text_condition = Substance.is_cmr == True

            # Połącz warunki
            combined_conditions = []
            if svhc_text_condition is not None:
                combined_conditions.append(svhc_text_condition)
            if cmr_text_condition is not None:
                combined_conditions.append(cmr_text_condition)

            if combined_conditions:
                if filter_query_lower.strip() in ['svhc', 'cmr']:
                    query = query.filter(or_(*combined_conditions))
                else:
                    query = query.filter(or_(text_filter_condition, *combined_conditions))
            else:
                query = query.filter(text_filter_condition)

            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr tekstowy: '{filter_query}' (uwzględniono SVHC jeśli pasuje).")


        # Filtr lokalizacji fizycznej (bez zmian)
        if physical_location:
            query = query.filter(Substance.physical_location == physical_location)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr lokalizacji fizycznej: {physical_location}")

        # Filtr użytkownika (lokalizacja bazodanowa) (bez zmian)
        if user_location:
            # Location jest już zjoinowane na początku, więc można filtrować bezpośrednio
            query = query.filter(Location.name == user_location)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr użytkownika: {user_location}")

        # Filtr substancji CMR (bez zmian)
        if is_cmr:
            is_cmr_bool = is_cmr.lower() == 'true'
            query = query.filter(Substance.is_cmr == is_cmr_bool)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr CMR: {is_cmr}")

        # Filtr substancji SVHC z parametru URL (bez zmian, używamy zmiennej is_svhc_param)
        if is_svhc_param:
            # Ten filtr działa tylko jeśli parametr is_svhc='true' lub 'false' jest jawnie podany
            # Niezależnie od filtra tekstowego
            is_svhc_bool = is_svhc_param.lower() == 'true'
            query = query.filter(Substance.is_svhc == is_svhc_bool)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr SVHC (parametr URL): {is_svhc_param}")


        # Filtr posiadania karty SDS (bez zmian)
        if has_sds:
            has_sds_bool = has_sds.lower() == 'true'
            if has_sds_bool:
                query = query.filter(Substance.sds_filename.isnot(None))
            else:
                query = query.filter(Substance.sds_filename.is_(None))
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr SDS: {has_sds}")


        # Sortowanie
        # Location jest już zjoinowane na początku, więc można sortować bezpośrednio
        query = query.order_by(Location.name, Substance.name).all() # .all() pobiera wszystkie wyniki do eksportu


        # Sprawdź czy są wyniki
        if not query: # Zmieniono substances_to_export na query, bo .all() zostało wyżej
            filters_msg = "pasujących do filtrów" if filters_applied else ""
            flash(f'Brak substancji {filters_msg} do eksportu.', 'warning')
            # Przekieruj z zachowaniem parametrów filtra
            url_with_params = url_for('export.view_all_substances')
            if request.query_string:
                 url_with_params += '?' + request.query_string.decode('utf-8')
            return redirect(url_with_params)

        substances_to_export = query # Używamy pobranych wyników po .all()


        # Przygotowanie pliku CSV
        import io
        import csv
        import urllib.parse
        from datetime import datetime # Upewnij się, że datetime jest zaimportowany

        output = io.StringIO()
        writer = csv.writer(output)

        # Nagłówek z dodanym numerem WE
        header = ['Nazwa chemiczna', 'Nr CAS', 'Nr WE',
          'Klasyfikacja', 'Zwroty H', 'SCL/M-factor', 'CMR', 'SVHC', 'Komentarz', 'Użytkownik', 'Lokalizacja']

        writer.writerow(header)

        # Dane
        for sub in substances_to_export:
            cas_val = sub.cas or ''
            ec_val = sub.ec_number or ''
            excel_cas = f'="{cas_val}"' if cas_val else ''
            excel_ec = f'="{ec_val}"' if ec_val else ''

            writer.writerow([
            sub.name,                               # Nazwa chemiczna
            excel_cas,                              # Nr CAS
            excel_ec,                               # Nr WE
            sub.classification or '',               # Klasyfikacja
            sub.h_phrases or '',                    # Zwroty H
            sub.scl_mfactor or '',                  # SCL/M-factor
            'Tak' if sub.is_cmr else 'Nie',         # CMR
            'Tak' if sub.is_svhc else 'Nie',        # SVHC
            sub.comment or '',                      # Komentarz
            sub.location.name,                      # Użytkownik
            sub.physical_location or 'Nieznana',    # Lokalizacja
        ])

        # Finalizacja i przygotowanie odpowiedzi
        csv_data = output.getvalue()

        # Nazwa pliku zależy od filtru
        if filters_applied:
            filename = "ChemMan_substancje_filtrowane.csv"
        else:
            filename = "ChemMan_wszystkie_substancje.csv"

        # Użyj RFC 5987 dla nazw plików z nie-ASCII
        filename_header = "attachment; filename*=UTF-8''{}".format(
            urllib.parse.quote(filename, encoding='utf-8')
        )

        response = Response(
            csv_data.encode('utf-8-sig'),
            mimetype='text/csv',
            headers={"Content-Disposition": filename_header}
        )

        current_app.logger.info(f"Zakończono globalny CSV: {filename}")
        return response

    except Exception as e:
        # Przekazujemy url_for z argumentami, aby powrócić do widoku z zachowanymi filtrami
        return handle_exception(
            e,
            "globalnego eksportu CSV",
            url_for('export.view_all_substances') + (f'?{request.query_string.decode("utf-8")}' if request.query_string else '')
        )


@export_bp.route('/substances/all')
@login_required
@view_permission_required
def view_all_substances():
    """Wyświetla stronę ze wszystkimi substancjami, z paginacją po stronie serwera."""
    current_app.logger.debug("Obsługa trasy /substances/all (z paginacją po stronie serwera)")
    try:
        # Pobierz parametry paginacji
        page = request.args.get('page', 1, type=int)
        # Używamy wartości z configa jako domyślnej, ale pozwalamy na nadpisanie z URL
        per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
        # Limit liczby rekordów na stronę dla bezpieczeństwa
        if per_page > 100:
            per_page = 100

        # Pobieramy wszystkie lokalizacje dla listy filtrowania
        locations = Location.query.order_by(Location.name).all()

        # Przygotowanie zapytania
        # Zaczynamy od Substance i zawsze joinujemy Location
        query = db.session.query(Substance).join(Location)

        # Zastosuj filtrowanie, jeśli podano parametry
        filter_query = request.args.get('filter', '').strip()
        physical_location = request.args.get('physical_location', '').strip()
        user_location = request.args.get('user_location', '').strip()
        is_cmr = request.args.get('is_cmr', '').strip()
        is_svhc_param = request.args.get('is_svhc', '').strip() # Zmieniona nazwa zmiennej
        has_sds = request.args.get('has_sds', '').strip()

        current_app.logger.info(f"Filtr tekstowy: '{filter_query}', Lokalizacja fizyczna: '{physical_location}', " +
                                f"Użytkownik: '{user_location}', CMR (param): '{is_cmr}', SVHC (param): '{is_svhc_param}', SDS (param): '{has_sds}'")


        # Filtr tekstowy (zmodyfikowany)
        if filter_query:
            search_term = f"%{filter_query}%"
            # Przekształć zapytanie na małe litery do porównania
            filter_query_lower = filter_query.lower()

            # Warunek bazowy dla wyszukiwania tekstowego
            text_filter_condition = or_(
                Location.name.ilike(search_term),
                Substance.name.ilike(search_term),
                Substance.cas.ilike(search_term),
                Substance.ec_number.ilike(search_term),
                Substance.classification.ilike(search_term),
                Substance.h_phrases.ilike(search_term),
                Substance.physical_location.ilike(search_term),
                Substance.comment.ilike(search_term)
            )

            # Dodaj warunek dla 'svhc' w filtrze tekstowym
            svhc_text_condition = None
            # Użyj regex, aby znaleźć "svhc" jako pełne słowo lub jego część,
            # otoczone przez granice słów (początek, koniec, spacja, znak interpunkcyjny itp.)
            # Dodatkowe warunki dla samego 'svhc' lub 'svhc.' itp.
            if re.search(r'(^|\W)svhc($|\W)', filter_query_lower) or filter_query_lower == 'svhc':
                 # Sprawdź, czy substancja jest SVHC
                 svhc_text_condition = Substance.is_svhc == True
            # Dodaj warunek dla 'cmr' w filtrze tekstowym
            cmr_text_condition = None
            if re.search(r'(^|\W)cmr($|\W)', filter_query_lower):
                cmr_text_condition = Substance.is_cmr == True


            # Połącz warunki
            combined_conditions = []
            if svhc_text_condition is not None:
                combined_conditions.append(svhc_text_condition)
            if cmr_text_condition is not None:
                combined_conditions.append(cmr_text_condition)

            if combined_conditions:
                if filter_query_lower.strip() in ['svhc', 'cmr']:
                    query = query.filter(or_(*combined_conditions))
                else:
                    query = query.filter(or_(text_filter_condition, *combined_conditions))
            else:
                query = query.filter(text_filter_condition)

            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr tekstowy: '{filter_query}' (uwzględniono SVHC jeśli pasuje).")


        # Filtr lokalizacji fizycznej
        if physical_location:
            query = query.filter(Substance.physical_location == physical_location)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr lokalizacji fizycznej: {physical_location}")

        # Filtr użytkownika (lokalizacja bazodanowa)
        if user_location:
            # Location jest już zjoinowane na początku, więc można filtrować bezpośrednio
            query = query.filter(Location.name == user_location)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr użytkownika: {user_location}")

        # Filtr substancji CMR
        if is_cmr:
            is_cmr_bool = is_cmr.lower() == 'true'
            query = query.filter(Substance.is_cmr == is_cmr_bool)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr CMR: {is_cmr}")

        # Filtr substancji SVHC z parametru URL
        if is_svhc_param:
            # Ten filtr działa tylko jeśli parametr is_svhc='true' lub 'false' jest jawnie podany
            # Niezależnie od filtra tekstowego
            is_svhc_bool = is_svhc_param.lower() == 'true'
            query = query.filter(Substance.is_svhc == is_svhc_bool)
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr SVHC (parametr URL): {is_svhc_param}")

        # Filtr posiadania karty SDS
        if has_sds:
            has_sds_bool = has_sds.lower() == 'true'
            if has_sds_bool:
                query = query.filter(Substance.sds_filename.isnot(None))
            else:
                query = query.filter(Substance.sds_filename.is_(None))
            filters_applied = True
            current_app.logger.info(f"Zastosowano filtr SDS: {has_sds}")

        # Sortowanie
        # Location jest już zjoinowane na początku, więc można sortować bezpośrednio
        query = query.order_by(Location.name, Substance.name)


        # Wykonaj zapytanie z paginacją
        paginated_substances = query.paginate(page=page, per_page=per_page, error_out=False)

        # Przygotuj listę danych dla szablonu
        from utils import convert_utc_to_local
        # Upewnij się, że is_svhc_substance jest zaimportowane z utils
        # from utils import is_svhc_substance # Sprawdzić, czy jest w utils.__init__.py

        all_substances_data_for_template = []

        for sub in paginated_substances.items:
            # Konwersja czasu UTC na czas lokalny
            local_timestamp_str = convert_utc_to_local(sub.sds_upload_timestamp)

            # When building the substances_data_for_template dictionary
            svhc_reason = None
            if sub.is_svhc:
                # Użyj funkcji z utils
                svhc_reason = is_svhc_substance(cas=sub.cas, ec_number=sub.ec_number, name=sub.name)

            all_substances_data_for_template.append({
                'id': sub.id,
                'location_id': sub.location_id,
                'location_name': sub.location.name,
                'name': sub.name,
                'cas': sub.cas,
                'ec_number': sub.ec_number,
                'classification': sub.classification,
                'h_phrases': sub.h_phrases,
                'comment': sub.comment,
                'sds_filename': sub.sds_filename,
                'sds_upload_timestamp_local': local_timestamp_str,
                'scl_mfactor': sub.scl_mfactor or '',
                'physical_location': sub.physical_location or 'Nieznana',
                'is_cmr': sub.is_cmr,
                'is_svhc': sub.is_svhc,
                'svhc_reason': svhc_reason or ''
            })

        current_app.logger.info(f"Znaleziono {paginated_substances.total} substancji, wyświetlanie strony {page} ({len(all_substances_data_for_template)} rekordów) z filtrem '{filter_query}'")

        # Upewnij się, że lista lokalizacji jest zawsze dostępna dla filtra
        locations = Location.query.order_by(Location.name).all()

        # Przekazujemy listę słowników, lokalizacje i informacje o paginacji do szablonu
        return render_template('all_substances.html',
                               all_substances_data=all_substances_data_for_template,
                               locations=locations,
                               pagination=paginated_substances,
                               filter_query=filter_query, # Przekazujemy aktualne parametry filtra
                               physical_location=physical_location,
                               user_location=user_location,
                               is_cmr=is_cmr,
                               is_svhc=is_svhc_param, # Przekazujemy parametr SVHC
                               has_sds=has_sds)


    except Exception as e:
        # Przekazujemy url_for z argumentami, aby powrócić do widoku z zachowanymi filtrami
        return handle_exception(
            e,
            "pobierania wszystkich substancji",
            url_for('export.view_all_substances') + (f'?{request.query_string.decode("utf-8")}' if request.query_string else '')
        )