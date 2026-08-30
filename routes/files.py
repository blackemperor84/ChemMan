import os
from flask import Blueprint, request, flash, redirect, url_for, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from decorators import upload_sds_permission_required, view_permission_required

from models import db, Substance, Location, SDSFile
from utils import allowed_file, log_action, handle_exception, utcnow
from utils.file_manager import FileManager
from werkzeug.utils import secure_filename

# Utworzenie blueprintu dla operacji na plikach
files_bp = Blueprint('files', __name__)

# MIME types dozwolone dla plików
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/x-pdf',
}

# Funkcja do walidacji MIME type
def validate_mime_type(file_stream):
    """
    Waliduje MIME type pliku.
    
    Args:
        file_stream: plik z request.files
    
    Returns:
        bool: True jeśli MIME type jest dozwolony, False w przeciwnym razie
    """
    try:
        # Czytaj pierwsze 2048 bajtów pliku
        file_header = file_stream.read(2048)
        file_stream.seek(0)  # Reset stream do początku
        
        # Sprawdzenie magic number dla PDF (pierwsze 4 bajty)
        if file_header.startswith(b'%PDF'):
            return True
        
        # Jeśli magic number nie pasuje - odrzuć plik
        return False
        
    except Exception as e:
        current_app.logger.error(f"Błąd walidacji MIME type: {e}")
        return False


@files_bp.route('/substance/<int:substance_id>/upload_sds', methods=['POST'])
@login_required
@upload_sds_permission_required
def upload_sds(substance_id):
    """Obsługuje upload pliku SDS dla substancji (obsługuje wiele plików)."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/upload_sds")
    substance = Substance.query.get_or_404(substance_id)

    # Sprawdź czy użytkownik może modyfikować komórkę organizacyjną substancji
    if not current_user.can_modify_organizational_unit(substance.location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował dodać SDS do substancji bez uprawnień do komórki ID: {substance.location_id}")
        flash('Możesz dodawać karty SDS tylko do substancji w swojej komórce organizacyjnej.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # Sprawdź, czy plik został wysłany
    if 'sds_file' not in request.files:
        flash('Nie wybrano pliku do wysłania.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    file = request.files['sds_file']
    manufacturer = request.form.get('manufacturer', '').strip()  # Pobierz nazwę producenta

    # Sprawdź, czy wybrano plik (przeglądarka może wysłać pustą część)
    if file.filename == '':
        flash('Nie wybrano pliku.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # WALIDACJA 1: Sprawdź rozszerzenie pliku
    if not allowed_file(file.filename):
        flash(f'Niedozwolony typ pliku. Dozwolone są tylko: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # WALIDACJA 2: Sprawdź rozmiar pliku
    file.seek(0, os.SEEK_END)  # Idź na koniec pliku
    file_size = file.tell()
    file.seek(0)  # Reset do początku

    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    if file_size > max_size:
        flash(f'Plik jest za duży. Maksymalny rozmiar: {max_size / (1024*1024):.1f} MB', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # WALIDACJA 3: Sprawdź MIME type (magic number)
    if not validate_mime_type(file):
        current_app.logger.warning(f"Odrzucono plik o nieprawidłowym MIME type: {file.filename}")
        flash('Plik nie jest prawidłowym plikiem PDF. Upewnij się że wysyłasz plik PDF.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # Jeśli wszystkie walidacje przeszły - zapisz plik
    if file:
        # Plik trafia na dysk przed commitem, wiec przy bledzie zapisu do bazy
        # trzeba go skasowac — inaczej zostaje osierocony plik bez wpisu w DB.
        unique_filename = None
        try:
            # Użyj menedżera plików do zapisania pliku (nie usuwamy starych - obsługujemy wiele)
            unique_filename = FileManager.save_sds_file(file, None)
            original_filename = secure_filename(file.filename)

            # Zaktualizuj datę ostatniej modyfikacji lokalizacji
            location = db.session.get(Location, substance.location_id)
            if location:
                location.last_modified = utcnow()
            else:
                current_app.logger.warning(f"Nie znaleziono lokalizacji ID: {substance.location_id} podczas uploadu SDS dla substancji ID: {substance.id}")

            # Utwórz nowy wpis w tabeli sds_files
            new_sds_file = SDSFile(
                substance_id=substance.id,
                filename=unique_filename,
                original_filename=original_filename,
                manufacturer=manufacturer if manufacturer else None,
                upload_timestamp=utcnow()
            )
            db.session.add(new_sds_file)

            # Zachowaj kompatybilność wsteczną - zaktualizuj też stare pola
            if not substance.sds_filename:
                substance.sds_filename = unique_filename
                substance.sds_upload_timestamp = utcnow()

            db.session.commit()

            flash_msg = f'Plik SDS "{original_filename}" został pomyślnie przesłany dla {substance.name}.'
            if manufacturer:
                flash_msg += f' (Producent: {manufacturer})'
            flash(flash_msg, 'success')

            log_action(
                'UPLOAD_SDS',
                target_type='Substance',
                target_id=substance.id,
                details=f"Plik: {original_filename}, Producent: {manufacturer or 'Nie podano'}, Rozmiar: {file_size} bajtów"
            )

        except Exception as e:
            # Wycofaj transakcje, a nastepnie posprzataj plik zapisany na dysku.
            db.session.rollback()
            if unique_filename:
                try:
                    FileManager.delete_sds_file(unique_filename)
                    current_app.logger.info(
                        f"Wycofano zapis SDS — usunieto osierocony plik: {unique_filename}"
                    )
                except Exception as cleanup_error:
                    current_app.logger.exception(
                        f"Nie udalo sie usunac osieroconego pliku {unique_filename}: {cleanup_error}"
                    )
            return handle_exception(e, "zapisywania pliku SDS",
                                   url_for('locations.view_location', location_id=substance.location_id))

    return redirect(url_for('locations.view_location', location_id=substance.location_id))


@files_bp.route('/uploads/sds/<path:filename>')
@login_required
@view_permission_required
def download_sds(filename):
    """Serwuje (do pobrania) zapisany plik SDS."""
    current_app.logger.debug(f"Żądanie pobrania pliku SDS: {filename}")
    try:
        # WALIDACJA: Sprawdź czy filename nie zawiera path traversal (../)
        if '..' in filename or filename.startswith('/'):
            current_app.logger.error(f"SECURITY: Próba path traversal: {filename}")
            flash('Niedozwolony dostęp do pliku.', 'error')
            abort(403)
        
        # Użyj send_from_directory dla bezpieczeństwa - serwuje pliki tylko z podanego folderu
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True  # Wymusz pobieranie zamiast wyświetlania w przeglądarce
        )
    except FileNotFoundError:
        current_app.logger.error(f"BŁĄD: Nie znaleziono pliku SDS: {filename} w folderze {current_app.config['UPLOAD_FOLDER']}")
        flash('Nie znaleziono żądanego pliku SDS.', 'error')
        abort(404)
    except Exception as e:
        current_app.logger.exception(f"BŁĄD podczas serwowania pliku SDS {filename}: {e}")
        flash(f'Wystąpił błąd podczas pobierania pliku: {e}', 'error')
        abort(500)


@files_bp.route('/substance/<int:substance_id>/delete_sds/<int:sds_file_id>', methods=['POST'])
@login_required
@upload_sds_permission_required
def delete_sds(substance_id, sds_file_id):
    """Usuwa konkretny plik SDS."""
    current_app.logger.debug(f"Otrzymano POST na /substance/{substance_id}/delete_sds/{sds_file_id}")
    substance = Substance.query.get_or_404(substance_id)
    sds_file = SDSFile.query.get_or_404(sds_file_id)

    # Sprawdź czy użytkownik może modyfikować komórkę organizacyjną substancji
    if not current_user.can_modify_organizational_unit(substance.location_id):
        current_app.logger.warning(f"Użytkownik {current_user.username} próbował usunąć SDS z substancji bez uprawnień do komórki ID: {substance.location_id}")
        flash('Możesz usuwać karty SDS tylko z substancji w swojej komórce organizacyjnej.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    # Sprawdź, czy plik SDS należy do tej substancji
    if sds_file.substance_id != substance_id:
        flash('Nieprawidłowe żądanie.', 'error')
        return redirect(url_for('locations.view_location', location_id=substance.location_id))

    filename_to_delete = sds_file.filename
    original_filename = sds_file.original_filename

    try:
        # Kolejnosc ma znaczenie: najpierw baza, potem dysk. Gdyby plik znikal
        # pierwszy, a commit sie nie powiodl, w bazie zostalby wpis wskazujacy
        # na nieistniejacy plik. Osierocony plik po nieudanym kasowaniu z dysku
        # jest znacznie mniej szkodliwy niz martwy odnosnik w interfejsie.

        # Krok 1: Zaktualizuj datę ostatniej modyfikacji lokalizacji
        location = db.session.get(Location, substance.location_id)
        if location:
            location.last_modified = utcnow()
        else:
            current_app.logger.warning(f"Nie znaleziono lokalizacji ID: {substance.location_id} podczas usuwania SDS dla substancji ID: {substance.id}")

        # Krok 2: Usuń wpis z bazy danych
        db.session.delete(sds_file)
        db.session.flush()

        # Krok 3: Jeśli to był jedyny plik, wyczyść stare pola w substance
        remaining_files = SDSFile.query.filter_by(substance_id=substance_id).count()
        if remaining_files == 0:
            substance.sds_filename = None
            substance.sds_upload_timestamp = None

        db.session.commit()

        # Krok 4: Dopiero teraz usun plik z dysku
        try:
            FileManager.delete_sds_file(filename_to_delete)
        except Exception as file_error:
            current_app.logger.exception(
                f"Wpis SDS usuniety z bazy, ale nie udalo sie skasowac pliku "
                f"{filename_to_delete}: {file_error}"
            )

        # Krok 5: Zapisz log akcji
        try:
            log_action(
                'DELETE_SDS',
                target_type='Substance',
                target_id=substance.id,
                details=f"Usunięto plik: {original_filename or filename_to_delete}"
            )
        except Exception as log_e:
            current_app.logger.warning(f"OSTRZEŻENIE: Nie udało się zapisać logu dla DELETE_SDS: {log_e}")

        flash(f'Plik SDS "{original_filename or filename_to_delete}" został usunięty dla {substance.name}.', 'success')

    except Exception as e:
        return handle_exception(e, "usuwania pliku SDS",
                               url_for('locations.view_location', location_id=substance.location_id))

    return redirect(url_for('locations.view_location', location_id=substance.location_id))