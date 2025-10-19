import os
import uuid
from datetime import datetime
from flask import Blueprint, request, flash, redirect, url_for, send_from_directory, current_app, abort
from flask_login import login_required, current_user
# Zakładając, że decorators.py jest w głównym folderze. Jeśli przeniosłeś go do utils, zmień import.
from decorators import upload_sds_permission_required, view_permission_required

from models import db, Substance, Location
# Zakładając poprawną strukturę pakietu utils
from utils import allowed_file, log_action, handle_exception
from utils.file_manager import FileManager
from werkzeug.utils import secure_filename

# Utworzenie blueprintu dla operacji na plikach
files_bp = Blueprint('files', __name__)

# --- PRZYWRÓCONA FUNKCJA UPLOAD ---
@files_bp.route('/substance/<int:substance_id>/upload_sds', methods=['POST'])
@login_required
@upload_sds_permission_required
def upload_sds(substance_id):
    """Obsługuje upload pliku SDS dla substancji."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/upload_sds")
    substance = Substance.query.get_or_404(substance_id)

    # Sprawdź, czy plik został wysłany
    if 'sds_file' not in request.files:
        flash('Nie wybrano pliku do wysłania.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    file = request.files['sds_file']

    # Sprawdź, czy wybrano plik (przeglądarka może wysłać pustą część)
    if file.filename == '':
        flash('Nie wybrano pliku.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # Sprawdź rozszerzenie i zapisz plik
    if file and allowed_file(file.filename):
        try:
            # Użyj menedżera plików do zapisania pliku i usunięcia starego
            # FileManager jest już zaimportowany na górze
            old_filename = substance.sds_filename
            unique_filename = FileManager.save_sds_file(file, old_filename)

            # Zaktualizuj datę ostatniej modyfikacji lokalizacji
            location = Location.query.get(substance.location_id)
            if location: # Sprawdź czy lokalizacja istnieje
                location.last_modified = datetime.utcnow()
            else:
                current_app.logger.warning(f"Nie znaleziono lokalizacji ID: {substance.location_id} podczas uploadu SDS dla substancji ID: {substance.id}")

            # Zaktualizuj nazwę pliku w bazie danych
            substance.sds_filename = unique_filename
            substance.sds_upload_timestamp = datetime.utcnow()
            db.session.commit()

            flash(f'Plik SDS "{secure_filename(file.filename)}" został pomyślnie przesłany dla {substance.name}.', 'success') # Użyj secure_filename dla bezpieczeństwa
            log_action(
                'UPLOAD_SDS',
                target_type='Substance',
                target_id=substance.id,
                details=f"Nazwa pliku: {unique_filename}"
            )

        except Exception as e:
            # Użyj centralnego handlera wyjątków
            return handle_exception(e, "zapisywania pliku SDS",
                                   url_for('locations.view_location', location_id=substance.location_id))

    else:
        flash('Niedozwolony typ pliku. Dozwolone są tylko: ' +
              ', '.join(current_app.config['ALLOWED_EXTENSIONS']), 'error')

    return redirect(url_for('locations.view_location', location_id=substance.location_id))
# --- KONIEC PRZYWRÓCONEJ FUNKCJI ---


@files_bp.route('/uploads/sds/<path:filename>')
@login_required
@view_permission_required
def download_sds(filename):
    """Serwuje (do pobrania) zapisany plik SDS."""
    current_app.logger.debug(f"Żądanie pobrania pliku SDS: {filename}")
    try:
        # Użyj send_from_directory dla bezpieczeństwa - serwuje pliki tylko z podanego folderu
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True  # Wymuś pobieranie zamiast wyświetlania w przeglądarce
        )
    except FileNotFoundError:
        current_app.logger.error(f"BŁĄD: Nie znaleziono pliku SDS: {filename} w folderze {current_app.config['UPLOAD_FOLDER']}")
        flash('Nie znaleziono żądanego pliku SDS.', 'error')
        abort(404)
    except Exception as e:
        current_app.logger.error(f"BŁĄD podczas serwowania pliku SDS {filename}: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Wystąpił błąd podczas pobierania pliku: {e}', 'error')
        abort(500)  # Zwróć błąd serwera


@files_bp.route('/substance/<int:substance_id>/delete_sds', methods=['POST'])
@login_required
@upload_sds_permission_required
def delete_sds(substance_id):
    """Usuwa załączony plik SDS i czyści wpis w bazie danych."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/delete_sds")
    substance = Substance.query.get_or_404(substance_id)
    filename_to_delete = substance.sds_filename

    if not filename_to_delete:
        flash('Brak pliku SDS do usunięcia dla tej substancji.', 'warning')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    try:
        # Krok 1: Użyj FileManager do usunięcia pliku
        file_deleted = FileManager.delete_sds_file(filename_to_delete)

        # Krok 2: Zaktualizuj datę ostatniej modyfikacji lokalizacji
        location = Location.query.get(substance.location_id)
        if location: # Sprawdź, czy lokalizacja istnieje
             location.last_modified = datetime.utcnow()
        else:
             current_app.logger.warning(f"Nie znaleziono lokalizacji ID: {substance.location_id} podczas usuwania SDS dla substancji ID: {substance.id}")

        # Krok 3: Wyczyść nazwę pliku i timestamp w bazie danych
        substance.sds_upload_timestamp = None
        substance.sds_filename = None
        db.session.commit() # Zapisz zmiany w bazie

        # Krok 4: Zapisz log akcji
        try:
            log_action(
                'DELETE_SDS',
                target_type='Substance',
                target_id=substance.id,
                details=f"Usunięto plik: {filename_to_delete}"
            )
        except Exception as log_e:
            current_app.logger.warning(f"OSTRZEŻENIE: Nie udało się zapisać logu dla DELETE_SDS: {log_e}")

        flash(f'Plik SDS "{filename_to_delete}" został usunięty dla {substance.name}.', 'success')

    except Exception as e:
        # Użyj istniejącej funkcji handle_exception
        return handle_exception(e, "usuwania pliku SDS",
                               url_for('locations.view_location', location_id=substance.location_id))

    return redirect(url_for('locations.view_location', location_id=substance.location_id))

# --- UPEWNIJ SIĘ, ŻE NIE MA TU JUŻ TEGO BŁĘDNEGO FRAGMENTU KODU ---