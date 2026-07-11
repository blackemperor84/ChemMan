from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from decorators import add_permission_required, edit_permission_required, delete_permission_required, move_permission_required, copy_permission_required

from models import db, Substance, Location
from utils import log_action, handle_exception, utcnow
from datetime import datetime

# Utworzenie blueprintu dla substancji
substances_bp = Blueprint('substances', __name__)


@substances_bp.route('/location/<int:location_id>/add_substance', methods=['POST'])
@login_required
@add_permission_required
def add_substance_to_location(location_id):
    """Obsługuje dodawanie substancji znalezionej przez wyszukiwanie w Excelu."""
    current_app.logger.debug(f"Otrzymano POST na /location/{location_id}/add_substance")

    # Sprawdź czy użytkownik może modyfikować tę komórkę organizacyjną
    if not current_user.can_modify_organizational_unit(location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował dodać substancję do komórki bez uprawnień ID: {location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz dodawać substancje tylko do swojej komórki organizacyjnej.'}), 403

    location = db.session.get(Location, location_id)
    if not location:
        return jsonify({'status': 'error', 'message': 'Lokalizacja nie istnieje.'}), 404
    location.last_modified = utcnow()

    data = request.get_json()
    current_app.logger.debug(f"Otrzymano dane JSON: {data}")

    if not data:
        return jsonify({'status': 'error', 'message': 'Brak danych JSON.'}), 400

    name = data.get('name')
    cas = data.get('cas')
    ec_number = data.get('ec_number')  # Dodany numer WE
    classification = data.get('classification')
    h_phrases = data.get('h_phrases')
    scl_mfactor = data.get('scl_mfactor')
    physical_location = data.get('physical_location')
    
    current_app.logger.debug(f"Odczytano scl_mfactor z JSON: '{scl_mfactor}' (Typ: {type(scl_mfactor)})")

    if not name:
        return jsonify({'status': 'error', 'message': 'Nazwa substancji jest wymagana.'}), 400

    # Sprawdź duplikat - MODYFIKACJA ZAPYTANIA
    existing = Substance.query.filter_by(
        location_id=location_id,
        name=name,
        cas=cas,
        physical_location=physical_location # <-- DODANO physical_location
    ).first()

    if existing:
        # Zaktualizuj komunikat błędu
        return jsonify({
            'status': 'error',
            'message': f'Substancja "{name}" ({cas or "brak CAS"}) już istnieje w lokalizacji "{location.name}" DLA fizycznej lokalizacji "{physical_location}".'
        }), 409

    try:
        # Sprawdź, czy substancja jest CMR na podstawie zwrotów H
        from utils import is_cmr_substance, is_svhc_substance
        is_cmr = is_cmr_substance(h_phrases)
        
        # Sprawdź, czy substancja jest na liście SVHC
        svhc_reason = is_svhc_substance(cas=cas, ec_number=ec_number, name=name)
        is_svhc = svhc_reason is not None
        
        # Stwórz obiekt
        new_substance = Substance(
            location_id=location_id, 
            name=name, 
            cas=cas,
            ec_number=ec_number,  # Dodany numer WE
            classification=classification, 
            h_phrases=h_phrases,
            scl_mfactor=scl_mfactor,
            physical_location=physical_location,
            is_cmr=is_cmr,  # Dodana flaga CMR
            is_svhc=is_svhc  # Dodana flaga SVHC
        )
        
        current_app.logger.debug(f"Utworzony obiekt new_substance przed dodaniem do sesji:")
        current_app.logger.debug(f"  - name: {new_substance.name}")
        current_app.logger.debug(f"  - cas: {new_substance.cas}")
        current_app.logger.debug(f"  - ec_number: {new_substance.ec_number}")
        current_app.logger.debug(f"  - is_cmr: {new_substance.is_cmr}")
        current_app.logger.debug(f"  - is_svhc: {new_substance.is_svhc}")
        current_app.logger.debug(f"  - scl_mfactor: {new_substance.scl_mfactor}")

        db.session.add(new_substance)
        db.session.flush()  # Uzyskaj ID
        current_app.logger.debug(f"ID nowej substancji po flush: {new_substance.id}")

        # Logowanie akcji
        log_action(
            'ADD_SUBSTANCE',
            target_type='Substance',
            target_id=new_substance.id,
            details=f"Nazwa: {name}, CAS: {cas}, EC: {ec_number}, CMR: {'Tak' if is_cmr else 'Nie'}, SVHC: {'Tak' if is_svhc else 'Nie'}, LokID: {location_id}, Źródło: Excel"
        )

        db.session.commit()  # Zapisz substancję i log
        current_app.logger.info(f"Dodano substancję '{name}' do lokacji ID {location_id} z Excela")
        return jsonify({'status': 'success', 'message': f'Substancja "{name}" dodana do "{location.name}".'})

    except Exception as e:
        return handle_exception(e, f"dodawania substancji z Excela", None)
    
    
@substances_bp.route('/location/<int:location_id>/add_manual', methods=['POST'])
@login_required
@add_permission_required
def add_manual_substance(location_id):
    """Obsługuje dodawanie substancji/mieszaniny wprowadzonej ręcznie."""
    current_app.logger.debug(f"Otrzymano POST na /location/{location_id}/add_manual")

    # Sprawdź czy użytkownik może modyfikować tę komórkę organizacyjną
    if not current_user.can_modify_organizational_unit(location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował dodać substancję ręcznie do komórki bez uprawnień ID: {location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz dodawać substancje tylko do swojej komórki organizacyjnej.'}), 403

    # Sprawdź czy lokalizacja istnieje
    location = db.session.get(Location, location_id)
    if not location:
        return jsonify({'status': 'error', 'message': 'Lokalizacja nie istnieje.'}), 404
    location.last_modified = utcnow()

    data = request.get_json()
    if not data: 
        return jsonify({'status': 'error', 'message': 'Brak danych JSON.'}), 400

    name = data.get('name', '').strip()
    cas = data.get('cas', '').strip()
    ec_number = data.get('ec_number', '').strip()  # Dodany numer WE
    classification = data.get('classification', '').strip()
    h_phrases = data.get('h_phrases', '').strip()
    comment = data.get('comment', '').strip()
    physical_location = data.get('physical_location', '').strip()

    # Pobierz flagi CMR/SVHC z formularza (mogą nadpisać auto-detekcję)
    manual_is_cmr = data.get('is_cmr', None)  # None oznacza brak flagi, False oznacza odznaczony checkbox
    manual_is_svhc = data.get('is_svhc', None)
    manual_contains_cmr = data.get('contains_cmr', False)
    manual_contains_svhc = data.get('contains_svhc', False)

    if not name:
        return jsonify({'status': 'error', 'message': 'Nazwa jest wymagana.'}), 400

    # Sprawdź duplikat w tej lokalizacji - MODYFIKACJA ZAPYTANIA
    if cas:
        existing = Substance.query.filter_by(
            location_id=location_id,
            name=name,
            cas=cas,
            physical_location=physical_location # <-- DODANO physical_location
        ).first()
    else:
        # Obsługa przypadków bez CAS (np. mieszaniny)
        existing = Substance.query.filter_by(
            location_id=location_id,
            name=name,
            cas=None,
            physical_location=physical_location # <-- DODANO physical_location
        ).first()

    if existing:
        # Zaktualizuj komunikat błędu
        message = f'Pozycja "{name}"' + (f' (CAS: {cas})' if cas else '') + f' już istnieje w lokalizacji "{location.name}" DLA fizycznej lokalizacji "{physical_location}".'
        current_app.logger.warning(f"Duplikat (manual): {message}")
        return jsonify({'status': 'error', 'message': message}), 409

    try:
        # Sprawdź, czy substancja jest CMR na podstawie zwrotów H (auto-detekcja)
        from utils import is_cmr_substance, is_svhc_substance
        auto_is_cmr = is_cmr_substance(h_phrases)

        # Sprawdź, czy substancja jest na liście SVHC (auto-detekcja)
        svhc_reason = is_svhc_substance(
            cas=cas if cas else None,
            ec_number=ec_number if ec_number else None,
            name=name
        )
        auto_is_svhc = svhc_reason is not None

        # Użyj flag ręcznych jeśli podane, w przeciwnym razie użyj auto-detekcji
        final_is_cmr = manual_is_cmr if manual_is_cmr is not None else auto_is_cmr
        final_is_svhc = manual_is_svhc if manual_is_svhc is not None else auto_is_svhc

        new_substance = Substance(
            location_id=location_id,
            name=name,
            cas=cas if cas else None,
            ec_number=ec_number if ec_number else None,  # Dodany numer WE
            classification=classification,
            h_phrases=h_phrases,
            comment=comment,
            physical_location=physical_location,
            is_cmr=final_is_cmr,  # Status CMR (auto lub ręczny)
            is_svhc=final_is_svhc,  # Status SVHC (auto lub ręczny)
            contains_cmr=manual_contains_cmr,  # Flaga mieszanin zawierająca CMR
            contains_svhc=manual_contains_svhc  # Flaga mieszanin zawierająca SVHC
        )
        db.session.add(new_substance)
        db.session.flush()  # Uzyskaj ID

        log_action(
            'ADD_SUBSTANCE',
            target_type='Substance',
            target_id=new_substance.id,
            details=f"Nazwa: {name}, CAS: {cas}, EC: {ec_number}, CMR: {'Tak' if final_is_cmr else 'Nie'}, SVHC: {'Tak' if final_is_svhc else 'Nie'}, Zaw.CMR: {'Tak' if manual_contains_cmr else 'Nie'}, Zaw.SVHC: {'Tak' if manual_contains_svhc else 'Nie'}, LokID: {location_id}, Źródło: Ręczne"
        )
        
        db.session.commit()
        current_app.logger.info(f"Dodano ręcznie: '{name}' do lokacji ID {location_id}")
        return jsonify({'status': 'success', 'message': f'Dodano ręcznie "{name}" do "{location.name}".'})
    except Exception as e:
        return handle_exception(e, "dodawania ręcznego substancji", None)

@substances_bp.route('/substance/<int:substance_id>', methods=['DELETE'])
@login_required
@delete_permission_required
def delete_substance(substance_id):
    """Obsługuje usuwanie pojedynczej substancji."""
    current_app.logger.debug(f"Otrzymano DELETE na /substance/{substance_id}")
    try:
        from models import Location  # Import Location model
        substance = Substance.query.get_or_404(substance_id)

        # Sprawdź czy użytkownik może modyfikować komórkę organizacyjną substancji
        if not current_user.can_modify_organizational_unit(substance.location_id):
            current_app.logger.warning(f"Użytkownik {current_user.username} próbował usunąć substancję bez uprawnień do komórki ID: {substance.location_id}")
            return jsonify({'status': 'error', 'message': 'Możesz usuwać substancje tylko z swojej komórki organizacyjnej.'}), 403

        # Zapamiętaj dane PRZED usunięciem, aby użyć ich w logu i komunikacie
        sub_id = substance.id
        substance_name = substance.name
        sub_loc_id = substance.location_id
        sub_loc_name = substance.location.name  # Pobierzmy też nazwę lokalizacji dla logu

        # Zaktualizuj datę ostatniej modyfikacji lokalizacji
        location = db.session.get(Location, sub_loc_id)
        if location:
            location.last_modified = utcnow()
        
        # Usuń obiekt z sesji
        db.session.delete(substance)

        # Logowanie akcji (przed commitem, bo potrzebujemy danych obiektu)
        log_action(
            action='DELETE_SUBSTANCE',
            target_type='Substance',
            target_id=sub_id,
            details=f"Usunięto: '{substance_name}', Lok.: '{sub_loc_name}' (ID: {sub_loc_id})"
        )

        # Zatwierdź zmiany (usunięcie i log)
        db.session.commit()

        current_app.logger.info(f"Usunięto substancję: {substance_name} (ID: {sub_id})")
        return jsonify({'status': 'success', 'message': f'Substancja "{substance_name}" usunięta.'})

    except Exception as e:
        return handle_exception(e, "usuwania substancji", None)


@substances_bp.route('/substance/<int:substance_id>/comment', methods=['POST'])
@login_required
@edit_permission_required
def update_substance_comment(substance_id):
    """Obsługuje aktualizację komentarza dla substancji i loguje akcję."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/comment przez {current_user.username}")
    substance = Substance.query.get_or_404(substance_id)

    # Sprawdź czy użytkownik może modyfikować komórkę organizacyjną substancji
    if not current_user.can_modify_organizational_unit(substance.location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował edytować substancję bez uprawnień do komórki ID: {substance.location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz edytować substancje tylko w swojej komórce organizacyjnej.'}), 403

    data = request.get_json()
    if data is None or 'comment' not in data:
        current_app.logger.error(f"BŁĄD: Brak JSON lub klucza 'comment' dla sub ID: {substance_id}")
        return jsonify({'status': 'error', 'message': 'Nieprawidłowe dane żądania.'}), 400

    new_comment = data['comment'].strip()

    try:
        # Aktualizuj komentarz w obiekcie SQLAlchemy
        substance.comment = new_comment
        # Zatwierdź zmianę w bazie danych
        db.session.commit()
        current_app.logger.info(f"Pomyślnie zaktualizowano komentarz dla substancji ID: {substance_id}")

        # Logowanie akcji - po udanym zapisie do bazy
        try:
            log_action(
                action='UPDATE_COMMENT',
                target_type='Substance',
                target_id=substance_id,
                # Logujemy fragment dla zwięzłości
                details=f"Zmieniono kom. dla '{substance.name}'. Nowy (fragm.): {new_comment[:50]}{'...' if len(new_comment)>50 else ''}"
            )
        except Exception as log_e:
            current_app.logger.warning(f"OSTRZEŻENIE: Nie udało się zapisać logu dla UPDATE_COMMENT: {log_e}")

        # Zwróć odpowiedź o sukcesie
        return jsonify({'status': 'success', 'message': 'Komentarz zaktualizowany.', 'new_comment': new_comment})

    except Exception as e:
        return handle_exception(e, "aktualizacji komentarza substancji", None)


@substances_bp.route('/substance/<int:substance_id>/edit', methods=['POST'])
@login_required
@edit_permission_required
def update_substance(substance_id):
    """Obsługuje aktualizację wszystkich pól substancji."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/edit przez {current_user.username}")
    substance = Substance.query.get_or_404(substance_id)

    # Sprawdź czy użytkownik może modyfikować komórkę organizacyjną substancji
    if not current_user.can_modify_organizational_unit(substance.location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował edytować substancję bez uprawnień do komórki ID: {substance.location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz edytować substancje tylko w swojej komórce organizacyjnej.'}), 403

    data = request.get_json()
    if data is None:
        return jsonify({'status': 'error', 'message': 'Nieprawidłowe dane żądania.'}), 400

    try:
        # Aktualizuj wszystkie edytowalne pola
        if 'name' in data:
            substance.name = data['name'].strip()
        if 'cas' in data:
            substance.cas = data['cas'].strip() if data['cas'] else None
        if 'ec_number' in data:
            substance.ec_number = data['ec_number'].strip() if data['ec_number'] else None
        if 'classification' in data:
            substance.classification = data['classification'].strip() if data['classification'] else None
        if 'h_phrases' in data:
            substance.h_phrases = data['h_phrases'].strip() if data['h_phrases'] else None
        if 'scl_mfactor' in data:
            substance.scl_mfactor = data['scl_mfactor'].strip() if data['scl_mfactor'] else None
        if 'comment' in data:
            substance.comment = data['comment'].strip() if data['comment'] else None
        if 'physical_location' in data:
            substance.physical_location = data['physical_location'].strip() if data['physical_location'] else None

        # Aktualizuj flagi CMR/SVHC
        if 'is_cmr' in data:
            substance.is_cmr = bool(data['is_cmr'])
        if 'is_svhc' in data:
            substance.is_svhc = bool(data['is_svhc'])
        if 'contains_cmr' in data:
            substance.contains_cmr = bool(data['contains_cmr'])
        if 'contains_svhc' in data:
            substance.contains_svhc = bool(data['contains_svhc'])

        # Zaktualizuj datę ostatniej modyfikacji lokalizacji
        location = db.session.get(Location, substance.location_id)
        if location:
            location.last_modified = utcnow()

        db.session.commit()
        current_app.logger.info(f"Pomyślnie zaktualizowano substancję ID: {substance_id}")

        # Logowanie akcji
        log_action(
            action='UPDATE_SUBSTANCE',
            target_type='Substance',
            target_id=substance_id,
            details=f"Zaktualizowano '{substance.name}'"
        )

        return jsonify({'status': 'success', 'message': 'Substancja zaktualizowana.'})

    except Exception as e:
        return handle_exception(e, "aktualizacji substancji", None)


@substances_bp.route('/substances/move', methods=['POST'])
@login_required
@move_permission_required
def move_substances():
    """Obsługuje przenoszenie wybranych substancji do innej lokalizacji."""
    current_app.logger.debug("Otrzymano POST na /substances/move")
    data = request.get_json()
    
    moved_count, skipped_count, skipped_names = 0, 0, []
    
    if not data or 'substance_ids' not in data or 'target_location_id' not in data:
        return jsonify({'status': 'error', 'message': 'Niekompletne dane.'}), 400
        
    substance_ids = data.get('substance_ids', [])
    target_location_id_str = data.get('target_location_id') # Zmieniono nazwę dla jasności
    
    if not substance_ids:
        return jsonify({'status': 'error', 'message': 'Nie wybrano substancji.'}), 400
        
    try:
        target_location_id = int(target_location_id_str)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Nieprawidłowe ID celu.'}), 400
    
    target_location = db.session.get(Location, target_location_id)

    if not target_location:
        return jsonify({'status': 'error', 'message': 'Lokalizacja docelowa nie istnieje.'}), 404

    # Sprawdź czy użytkownik może modyfikować komórkę docelową
    if not current_user.can_modify_organizational_unit(target_location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował przenieść substancje do komórki bez uprawnień ID: {target_location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz przenosić substancje tylko do swojej komórki organizacyjnej.'}), 403

    try:
        substances_to_move = Substance.query.filter(Substance.id.in_(substance_ids)).all()

        # DODANE: Słownik do śledzenia zmodyfikowanych lokalizacji źródłowych
        source_locations_modified = {}

        for sub in substances_to_move:
            # DODANE: Pobierz i zaktualizuj lokalizację źródłową
            if sub.location_id != target_location_id: # Tylko jeśli faktycznie zmieniamy lokalizację
                original_location = db.session.get(Location, sub.location_id)
                if original_location:
                    source_locations_modified[original_location.id] = original_location

                # Sprawdź, czy substancja o tej samej nazwie i CAS już istnieje w lokalizacji docelowej
                existing_in_target = Substance.query.filter_by(
                    location_id=target_location_id, 
                    name=sub.name, 
                    cas=sub.cas
                ).first()

                if existing_in_target:
                    skipped_count += 1
                    skipped_names.append(sub.name)
                    current_app.logger.info(f"Pominięto move (duplikat w lokacji docelowej): {sub.name}")
                else:
                    sub.location_id = target_location_id
                    db.session.add(sub) # Dodajemy substancję do sesji po modyfikacji
                    moved_count += 1
                    current_app.logger.info(f"Przeniesiono: {sub.name} do Lok ID: {target_location_id}")
            else:
                # Próba przeniesienia do tej samej lokalizacji - pomiń
                skipped_count +=1
                skipped_names.append(f"{sub.name} (już w tej lokalizacji)")


        # DODANE: Aktualizacja czasu modyfikacji dla wszystkich zmienionych lokalizacji źródłowych
        for loc_id, loc_obj in source_locations_modified.items():
            loc_obj.last_modified = utcnow()
            db.session.add(loc_obj)

        # DODANE: Aktualizacja czasu modyfikacji dla lokalizacji docelowej, jeśli coś przeniesiono
        if moved_count > 0:
            target_location.last_modified = utcnow()
            db.session.add(target_location)
            
        db.session.commit()
        
        log_action(
            'MOVE_SUBSTANCES', 
            target_type='Location', 
            target_id=target_location_id, 
            details=f"Do '{target_location.name}'. Przeniesiono: {moved_count}, Pominięto: {skipped_count} (Duplikaty/Ta sama lok.). ID: {substance_ids}"
        )
        
        message = f"Przeniesiono {moved_count} substancji do '{target_location.name}'."
        if skipped_count > 0:
            message += f" Pominięto {skipped_count} (duplikaty lub substancje były już w tej lokalizacji: {', '.join(skipped_names)})."
            
        return jsonify({'status': 'success', 'message': message})
        
    except Exception as e:
        db.session.rollback() # DODANE: Rollback w razie błędu
        return handle_exception(e, "przenoszenia substancji", None)


@substances_bp.route('/substances/copy', methods=['POST'])
@login_required
@copy_permission_required
def copy_substances():
    """Obsługuje kopiowanie wybranych substancji do innej lokalizacji."""
    current_app.logger.debug("Otrzymano POST na /substances/copy")
    data = request.get_json()
    
    copied_count, skipped_count, skipped_names = 0, 0, []
    
    if not data or 'substance_ids' not in data or 'target_location_id' not in data:
        return jsonify({'status': 'error', 'message': 'Niekompletne dane.'}), 400
        
    substance_ids = data.get('substance_ids', [])
    target_location_id_str = data.get('target_location_id') # Zmieniono nazwę
    
    if not substance_ids:
        return jsonify({'status': 'error', 'message': 'Nie wybrano substancji.'}), 400
        
    try:
        target_location_id = int(target_location_id_str)
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Nieprawidłowe ID celu.'}), 400
    
    target_location = db.session.get(Location, target_location_id) # Pobierz obiekt lokalizacji docelowej

    if not target_location:
        return jsonify({'status': 'error', 'message': 'Lokalizacja docelowa nie istnieje.'}), 404

    # Sprawdź czy użytkownik może modyfikować komórkę docelową
    if not current_user.can_modify_organizational_unit(target_location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował skopiować substancje do komórki bez uprawnień ID: {target_location_id}")
        return jsonify({'status': 'error', 'message': 'Możesz kopiować substancje tylko do swojej komórki organizacyjnej.'}), 403

    try:
        substances_to_copy_from = Substance.query.filter(Substance.id.in_(substance_ids)).all()
        
        something_was_copied = False # DODANE: Flaga do śledzenia, czy coś faktycznie skopiowano

        for sub_original in substances_to_copy_from:
            existing_in_target = Substance.query.filter_by(
                location_id=target_location_id, 
                name=sub_original.name, 
                cas=sub_original.cas
            ).first()
            
            if existing_in_target:
                skipped_count += 1
                skipped_names.append(sub_original.name)
                current_app.logger.info(f"Pominięto copy (duplikat w lokacji docelowej): {sub_original.name}")
            else:
                new_substance = Substance(
                    location_id=target_location_id,
                    name=sub_original.name,
                    cas=sub_original.cas,
                    ec_number=sub_original.ec_number, # DODANE: Kopiowanie ec_number
                    classification=sub_original.classification,
                    h_phrases=sub_original.h_phrases,
                    comment=sub_original.comment,
                    sds_filename=sub_original.sds_filename, # Rozważ, czy chcesz kopiować plik SDS, czy tylko referencję
                    sds_upload_timestamp=sub_original.sds_upload_timestamp, # To samo co wyżej
                    scl_mfactor=sub_original.scl_mfactor,
                    physical_location=sub_original.physical_location, # Kopiowanie lokalizacji fizycznej
                    is_cmr=sub_original.is_cmr,  # DODANE: Kopiowanie flagi CMR
                    is_svhc=sub_original.is_svhc  # DODANE: Kopiowanie flagi SVHC
                )
                db.session.add(new_substance)
                copied_count += 1
                something_was_copied = True # DODANE
                
        # DODANE: Aktualizacja czasu modyfikacji dla lokalizacji docelowej, jeśli coś skopiowano
        if something_was_copied:
            target_location.last_modified = utcnow()
            db.session.add(target_location)

        db.session.commit()
        
        log_action(
            'COPY_SUBSTANCES', 
            target_type='Location', 
            target_id=target_location_id,
            details=f"Do '{target_location.name}'. Skopiowano: {copied_count}, Pominięto (duplikaty): {skipped_count}. Oryginalne ID: {substance_ids}"
        )
        
        message = f"Skopiowano {copied_count} substancji do '{target_location.name}'."
        if skipped_count > 0:
            message += f" Pominięto {skipped_count} (duplikaty: {', '.join(skipped_names)})."
            
        return jsonify({'status': 'success', 'message': message})
        
    except Exception as e:
        db.session.rollback() # DODANE: Rollback w razie błędu
        return handle_exception(e, "kopiowania substancji", None)