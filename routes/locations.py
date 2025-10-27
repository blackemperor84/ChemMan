from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from decorators import view_permission_required, add_permission_required, edit_permission_required, delete_permission_required, add_location_permission_required, delete_location_permission_required
from werkzeug.exceptions import NotFound # Dodaj import NotFound

from models import db, Location, Substance
from utils import log_action, convert_utc_to_local, handle_exception, is_svhc_substance

from datetime import datetime

# Utworzenie blueprintu dla lokalizacji
locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/')
@login_required
@view_permission_required
def index():
    """Wyświetla listę komórek organizacyjnych. Wszyscy użytkownicy z przypisaniem widzą wszystkie komórki."""
    current_app.logger.debug("Obsługa trasy / (index)")
    try:
        # Użytkownicy z przypisaną komórką widzą wszystkie komórki (mogą przeglądać)
        if current_user.is_admin or current_user.organizational_unit_id:
            locations = Location.query.order_by(Location.name).all()
        # Użytkownik bez przypisanej komórki nie widzi nic
        else:
            locations = []
            flash('Nie masz przypisanej komórki organizacyjnej. Skontaktuj się z administratorem.', 'warning')

        return render_template('locations.html', locations=locations)
    except Exception as e:
        flash(f'Błąd odczytu komórek organizacyjnych z bazy danych: {e}', 'error')
        current_app.logger.error(f"Błąd odczytu komórek organizacyjnych z DB: {e}")
        return render_template('locations.html', locations=[])


@locations_bp.route('/add_location', methods=['POST'])
@login_required
@add_location_permission_required  # Poprawiono dekorator na add_permission_required
def add_location():
    """Obsługuje dodawanie nowej lokalizacji."""
    current_app.logger.debug("Obsługa trasy /add_location (POST)")
    location_name = request.form.get('location_name', '').strip()
    
    if not location_name:
        flash('Nazwa lokalizacji nie może być pusta!', 'error')
        return redirect(url_for('locations.index'))
    
    # Sprawdź istnienie (ignorując wielkość liter)
    existing_location = Location.query.filter(
        db.func.lower(Location.name) == db.func.lower(location_name)
    ).first()
    
    if existing_location:
        flash(f'Lokalizacja "{location_name}" już istnieje!', 'error')
        return redirect(url_for('locations.index'))
    
    # Dodaj nową lokalizację
    try:
        new_loc = Location(name=location_name)
        db.session.add(new_loc)
        db.session.flush()  # Uzyskaj ID przed logowaniem
        
        log_action(
            'CREATE_LOCATION', 
            target_type='Location', 
            target_id=new_loc.id, 
            details=f"Nazwa: {new_loc.name}"
        )
        
        db.session.commit()
        flash(f'Lokalizacja "{location_name}" została dodana.', 'success')
        current_app.logger.info(f"Dodano lokalizację: {location_name}")
    except Exception as e:
        return handle_exception(e, "dodawania lokalizacji", url_for('locations.index'))
    
    return redirect(url_for('locations.index'))

# W pliku routes/locations.py - To jest POPRAWNY kod funkcji view_location
@locations_bp.route('/location/<int:location_id>')
@login_required
@view_permission_required
def view_location(location_id):
    try:
        # Sprawdź, czy użytkownik ma dostęp do przeglądania tej komórki organizacyjnej
        if not current_user.has_access_to_organizational_unit(location_id):
            flash('Nie masz dostępu do tej komórki organizacyjnej.', 'error')
            current_app.logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do komórki ID: {location_id}")
            return redirect(url_for('locations.index'))

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        if per_page > 100: per_page = 100

        db.session.expire_all()
        location = Location.query.get_or_404(location_id)

        # Sprawdź, czy użytkownik może modyfikować tę komórkę
        can_modify = current_user.can_modify_organizational_unit(location_id)

        paginated_substances = Substance.query.filter_by(location_id=location_id).order_by(
            Substance.name
        ).paginate(page=page, per_page=per_page, error_out=False)

        # Użytkownicy mogą kopiować/przenosić tylko do swojej przypisanej komórki
        if current_user.is_admin:
            # Admin widzi wszystkie inne komórki jako cele
            other_locations = Location.query.filter(Location.id != location_id).order_by(Location.name).all()
        elif current_user.organizational_unit_id and current_user.organizational_unit_id != location_id:
            # Użytkownik widzi tylko swoją przypisaną komórkę jako cel (jeśli nie jest to aktualna komórka)
            other_locations = Location.query.filter_by(id=current_user.organizational_unit_id).all()
        else:
            # Jeśli użytkownik przegląda swoją własną komórkę, nie ma innych celów (lub nie ma przypisania)
            other_locations = []

        substances_data_for_template = []
        for sub in paginated_substances.items:
            local_timestamp_str = convert_utc_to_local(sub.sds_upload_timestamp)

            # --- DODANA LOGIKA POBIERANIA POWODU SVHC ---
            svhc_reason = None
            if sub.is_svhc:
                # Wywołujemy zmodyfikowaną funkcję z __init__.py
                svhc_reason = is_svhc_substance(cas=sub.cas, ec_number=sub.ec_number, name=sub.name)
            # --- KONIEC DODANEJ LOGIKI ---

            substances_data_for_template.append({
                'id': sub.id,
                'name': sub.name,'cas': sub.cas, 'ec_number': sub.ec_number,
                'classification': sub.classification, 'h_phrases': sub.h_phrases,
                'comment': sub.comment, 'sds_filename': sub.sds_filename,
                'sds_upload_timestamp_local': local_timestamp_str,
                'scl_mfactor': sub.scl_mfactor or '',
                'physical_location': sub.physical_location or 'Nieznana',
                'is_cmr': sub.is_cmr,
                'is_svhc': sub.is_svhc,
                'svhc_reason': svhc_reason or '' # DODANE: Przekazujemy powód do szablonu (lub pusty string)
            })

        current_app.logger.info(f"Znaleziono lokalizację: {location.name}, wyświetlanie strony {page} z {paginated_substances.pages} ({len(substances_data_for_template)} substancji)")

        return render_template(
                'location_detail.html',
                location=location,
                substances_data=substances_data_for_template,
                other_locations=other_locations,
                pagination=paginated_substances,
                can_modify_this_unit=can_modify
            )
    except Exception as e:
        return handle_exception(e, "pobierania szczegółów lokalizacji", url_for('locations.index'))

@locations_bp.route('/location/<int:location_id>/edit', methods=['POST'])
@login_required
@edit_permission_required
def update_location_name(location_id):
    """Obsługuje aktualizację nazwy komórki organizacyjnej (przez AJAX/fetch)."""
    current_app.logger.debug(f"Otrzymano POST na /location/{location_id}/edit")

    # Sprawdź czy użytkownik może modyfikować tę komórkę organizacyjną
    if not current_user.can_modify_organizational_unit(location_id):
        current_app.logger.error(f"BŁĄD: Użytkownik {current_user.username} nie może modyfikować komórki ID: {location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz edytować tylko substancje w swojej komórce organizacyjnej.'}), 403

    # Pobierz lokalizację LUB zwróć błąd 404 jeśli nie istnieje
    location = Location.query.get_or_404(location_id)
    location.last_modified = datetime.utcnow()
    # Zapamiętaj starą nazwę PRZED próbą zmiany
    old_name = location.name

    data = request.get_json()
    if not data or 'name' not in data:
        current_app.logger.error("BŁĄD: Brak danych JSON lub klucza 'name'")
        return jsonify({'status': 'error', 'message': 'Nieprawidłowe dane żądania.'}), 400

    new_name = data['name'].strip()
    current_app.logger.debug(f"Otrzymano nową nazwę: '{new_name}' dla ID: {location_id}")

    # Walidacja: Czy nowa nazwa nie jest pusta?
    if not new_name:
        return jsonify({'status': 'error', 'message': 'Nazwa lokalizacji nie może być pusta.'}), 400

    # Sprawdź, czy nazwa (case-sensitive) się nie zmieniła - jeśli nie, zwróć sukces bez zapisu
    if new_name == old_name:
        current_app.logger.info("INFO: Nazwa lokalizacji bez zmian.")
        return jsonify({'status': 'success', 'message': 'Nazwa lokalizacji bez zmian.', 'new_name': old_name})

    # Walidacja: Czy inna lokalizacja o tej nazwie już istnieje (ignorujemy wielkość liter)?
    existing = Location.query.filter(
        Location.id != location_id,  # Wyklucz samą siebie
        db.func.lower(Location.name) == db.func.lower(new_name)  # Porównaj case-insensitive
    ).first()

    if existing:
        current_app.logger.error(f"BŁĄD: Lokalizacja o nazwie '{new_name}' (ignorując wielkość liter) już istnieje.")
        return jsonify({'status': 'error', 
                        'message': f'Lokalizacja o nazwie "{new_name}" (lub podobnej) już istnieje.'}), 409  # Conflict

    # Jeśli walidacja przeszła, aktualizuj nazwę
    try:
        location.name = new_name  # Ustaw nową nazwę
        # Logowanie akcji (teraz mamy old_name i new_name)
        log_action(
            'UPDATE_LOCATION', 
            target_type='Location', 
            target_id=location_id, 
            details=f"Zmieniono nazwę z '{old_name}' na '{new_name}'"
        )
        db.session.commit()  # Zapisuje zmianę nazwy i log
        current_app.logger.info(f"Pomyślnie zaktualizowano nazwę lokalizacji ID: {location_id} na '{new_name}'")
        return jsonify({
            'status': 'success', 
            'message': 'Nazwa lokalizacji zaktualizowana.', 
            'new_name': location.name
        })  # Zwracamy nową nazwę
    except Exception as e:
        db.session.rollback()  # Wycofaj zmiany w razie błędu zapisu
        current_app.logger.error(f"BŁĄD podczas aktualizacji nazwy lokalizacji (ID: {location_id}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Wystąpił wewnętrzny błąd serwera: {e}'}), 500


@locations_bp.route('/location/<int:location_id>/delete', methods=['POST'])
@login_required
@delete_location_permission_required
def delete_location(location_id):
    """Obsługuje usuwanie komórki organizacyjnej i jej zawartości."""
    current_app.logger.info(f"Otrzymano POST na /location/{location_id}/delete")
    try:
        # Sprawdź czy użytkownik może modyfikować tę komórkę organizacyjną
        if not current_user.can_modify_organizational_unit(location_id):
            current_app.logger.warning(f"Użytkownik {current_user.username} próbował usunąć komórkę bez uprawnień ID: {location_id}")
            if request.accept_mimetypes.accept_json or request.content_type == 'application/json':
                return jsonify({'status': 'error', 'message': 'Możesz usuwać tylko komórki organizacyjne przypisane do Ciebie.'}), 403
            flash('Możesz usuwać tylko komórki organizacyjne przypisane do Ciebie.', 'error')
            return redirect(url_for('locations.index'))

        location_to_delete = Location.query.get_or_404(location_id)
        location_name = location_to_delete.name
        loc_id = location_to_delete.id # Zapisz ID przed usunięciem

        # Dodatkowe zabezpieczenie - uniemożliwienie usunięcia lokalizacji "admin" lub ID 1
        if (location_name.lower() == 'admin' or location_id == 1) and not current_user.is_admin:
            current_app.logger.warning(f"Użytkownik {current_user.username} próbował usunąć chronioną lokalizację ID: {location_id}")
            flash('Nie można usunąć chronionej lokalizacji "admin".', 'error')
            # Sprawdź, czy żądanie oczekuje JSON
            if request.accept_mimetypes.accept_json or request.content_type == 'application/json':
                 return jsonify({'status': 'error', 'message': 'Nie można usunąć chronionej lokalizacji "admin".'}), 403
            return redirect(url_for('locations.index'))

        log_action(
            'DELETE_LOCATION',
            target_type='Location',
            target_id=loc_id,
            details=f"Nazwa: {location_name}"
        )

        # Cascade='all, delete-orphan' w modelu powinien usunąć powiązane substancje
        db.session.delete(location_to_delete)
        db.session.commit()
        current_app.logger.info(f"Usunięto lokalizację: {location_name} (ID: {location_id})")

        # Zwróć JSON lub przekieruj - **POPRAWIONY WARUNEK**
        # Sprawdź, czy klient akceptuje JSON lub wysłał JSON
        if request.accept_mimetypes.accept_json or request.content_type == 'application/json':
            return jsonify({
                'status': 'success',
                'message': f'Lokalizacja "{location_name}" (oraz jej zawartość) została usunięta.'
            })
        # Jeśli to zwykłe żądanie POST (np. z formularza bez JS), przekieruj z komunikatem
        flash(f'Lokalizacja "{location_name}" (oraz jej zawartość) została usunięta.', 'success')
        return redirect(url_for('locations.index'))

    except NotFound as e: # Specyficzna obsługa błędu 404
        db.session.rollback()
        current_app.logger.warning(f"Próba usunięcia nieistniejącej lokalizacji ID: {location_id}")
         # Sprawdź, czy klient akceptuje JSON lub wysłał JSON - **POPRAWIONY WARUNEK**
        if request.accept_mimetypes.accept_json or request.content_type == 'application/json':
            return jsonify({'status': 'error', 'message': f'Lokalizacja o ID {location_id} nie została znaleziona.'}), 404
        flash(f'Lokalizacja o ID {location_id} nie została znaleziona.', 'error')
        return redirect(url_for('locations.index'))

    except Exception as e: # Ogólna obsługa innych błędów
        db.session.rollback()
        # Logowanie błędu przez handle_exception
        return handle_exception(e, f"usuwania lokalizacji ID: {location_id}",
                                redirect_url=url_for('locations.index'),
                                return_json= (request.accept_mimetypes.accept_json or request.content_type == 'application/json') # Przekaż informację, czy zwrócić JSON
                               )