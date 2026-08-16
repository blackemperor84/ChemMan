import os
import string
import secrets
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from models import db, User, AuditLog, Location
from utils import log_action, handle_exception
from utils.database_import import (
    validate_excel_mime_type,
    allowed_excel_file,
    import_clp_data,
    import_svhc_data,
    get_database_stats
)

# Utworzenie blueprintu dla administracji
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# Dekorator sprawdzający uprawnienia administratora
def admin_required(f):
    """Sprawdza czy zalogowany użytkownik ma uprawnienia administratora."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Musisz się zalogować, aby uzyskać dostęp do tej strony.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Nie masz uprawnień do tej strony.', 'error')
            return redirect(url_for('locations.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@admin_required
def manage_users():
    """Wyświetla stronę zarządzania użytkownikami."""
    try:
        # Pobierz wszystkich użytkowników posortowanych wg nazwy
        users = User.query.order_by(User.username).all()
        # Pobierz wszystkie komórki organizacyjne do wyboru
        organizational_units = Location.query.order_by(Location.name).all()
        return render_template('admin/manage_users.html', users=users, organizational_units=organizational_units)
    except Exception as e:
        flash(f'Błąd podczas pobierania listy użytkowników: {e}', 'error')
        current_app.logger.error(f"BŁĄD pobierania użytkowników: {e}")
        return render_template('admin/manage_users.html', users=[], organizational_units=[])


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Obsługuje usuwanie użytkownika."""
    # Znajdź użytkownika do usunięcia
    user_to_delete = db.session.get(User, user_id)

    if not user_to_delete:
        flash('Nie znaleziono użytkownika do usunięcia.', 'error')
    elif user_to_delete.username == 'admin':
        flash('Nie można usunąć konta administratora.', 'error')
    else:
        # Usuń użytkownika
        try:
            username_deleted = user_to_delete.username
            db.session.delete(user_to_delete)
            db.session.commit()
            log_action(
                'DELETE_USER', 
                target_type='User', 
                target_id=user_id, 
                details=f"Usunięto użytkownika: {username_deleted}"
            )
            flash(f'Użytkownik "{username_deleted}" został usunięty.', 'success')
            current_app.logger.info(f"Admin '{current_user.username}' usunął użytkownika: {username_deleted}")
        except Exception as e:
            return handle_exception(e, "usuwania użytkownika", url_for('admin.manage_users'))

    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/reset_password', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    """Obsługuje resetowanie hasła użytkownika przez admina."""
    user_to_reset = db.session.get(User, user_id)

    if not user_to_reset:
        flash('Nie znaleziono użytkownika do zresetowania hasła.', 'error')
    else:
        try:
            # Wygeneruj bezpieczne hasło tymczasowe
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*'  # Dodaj znaki specjalne
            temp_password = ''.join(secrets.choice(alphabet) for i in range(12))  # 12 znaków

            user_to_reset.set_password(temp_password)  # Ustaw i zahashuj nowe hasło
            db.session.commit()
            log_action(
                'RESET_PASSWORD', 
                target_type='User', 
                target_id=user_id, 
                details=f"Admin '{current_user.username}' zresetował hasło dla: {user_to_reset.username}"
            )
            # WAŻNE: Pokaż hasło tymczasowe adminowi, aby mógł je przekazać użytkownikowi!
            flash(f'Hasło dla użytkownika "{user_to_reset.username}" zostało zresetowane. '
                  f'Nowe hasło tymczasowe: {temp_password}', 'success')
            current_app.logger.info(f"Admin '{current_user.username}' zresetował hasło dla: {user_to_reset.username}")
        except Exception as e:
            return handle_exception(e, "resetowania hasła", url_for('admin.manage_users'))

    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    """Obsługuje dodawanie nowego użytkownika z uprawnieniami."""
    # Pobierz dane z formularza
    new_username = request.form.get('new_username', '').strip()
    new_password = request.form.get('new_password', '').strip()
    organizational_unit_id = request.form.get('organizational_unit_id', '').strip()

    # Uprawnienia
    can_view = 'can_view' in request.form
    can_add = 'can_add' in request.form
    can_edit = 'can_edit' in request.form
    can_delete = 'can_delete' in request.form
    can_move = 'can_move' in request.form
    can_copy = 'can_copy' in request.form
    can_upload_sds = 'can_upload_sds' in request.form
    can_add_location = 'can_add_location' in request.form
    can_delete_location = 'can_delete_location' in request.form
    can_update_databases = 'can_update_databases' in request.form

    # Walidacja
    if not new_username or not new_password:
        flash('Nazwa użytkownika i hasło są wymagane.', 'error')
    elif len(new_password) < 8:  # Minimalna długość hasła
        flash('Hasło musi mieć co najmniej 8 znaków.', 'error')
    elif User.query.filter_by(username=new_username).first():
        flash(f'Użytkownik "{new_username}" już istnieje.', 'error')
    else:
        # Jeśli walidacja OK, stwórz użytkownika
        try:
            user = User(
                username=new_username,
                can_view=can_view,
                can_add=can_add,
                can_edit=can_edit,
                can_delete=can_delete,
                can_move=can_move,
                can_copy=can_copy,
                can_upload_sds=can_upload_sds,
                can_add_location=can_add_location,
                can_delete_location=can_delete_location,
                can_update_databases=can_update_databases,
                organizational_unit_id=int(organizational_unit_id) if organizational_unit_id else None
            )
            user.set_password(new_password)  # Hashowanie hasła
            db.session.add(user)
            db.session.commit()

            org_unit_name = db.session.get(Location, int(organizational_unit_id)).name if organizational_unit_id else 'Brak'
            log_action(
                'ADD_USER',
                target_type='User',
                target_id=user.id,
                details=f"Utworzono użytkownika: {user.username} z uprawnieniami, Komórka: {org_unit_name}"
            )
            flash(f'Użytkownik "{new_username}" został dodany.', 'success')
            current_app.logger.info(f"Admin '{current_user.username}' dodał użytkownika: {new_username}")
        except Exception as e:
            return handle_exception(e, "dodawania użytkownika", url_for('admin.manage_users'))

    # Zawsze wracaj na stronę zarządzania użytkownikami
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/edit_permissions', methods=['POST'])
@admin_required
def edit_user_permissions(user_id):
    """Obsługuje aktualizację uprawnień użytkownika."""
    user_to_edit = User.query.get_or_404(user_id)

    if user_to_edit.username == 'admin':
        flash('Nie można modyfikować uprawnień konta administratora.', 'error')
        return redirect(url_for('admin.manage_users'))

    try:
        # Aktualizacja uprawnień
        user_to_edit.can_view = 'can_view' in request.form
        user_to_edit.can_add = 'can_add' in request.form
        user_to_edit.can_edit = 'can_edit' in request.form
        user_to_edit.can_delete = 'can_delete' in request.form
        user_to_edit.can_move = 'can_move' in request.form
        user_to_edit.can_copy = 'can_copy' in request.form
        user_to_edit.can_upload_sds = 'can_upload_sds' in request.form
        user_to_edit.can_add_location = 'can_add_location' in request.form
        user_to_edit.can_delete_location = 'can_delete_location' in request.form
        user_to_edit.can_update_databases = 'can_update_databases' in request.form

        # Aktualizacja przypisania do komórki organizacyjnej
        organizational_unit_id = request.form.get('organizational_unit_id', '').strip()
        user_to_edit.organizational_unit_id = int(organizational_unit_id) if organizational_unit_id else None

        db.session.commit()

        org_unit_name = db.session.get(Location, int(organizational_unit_id)).name if organizational_unit_id else 'Brak'
        log_action(
            'UPDATE_USER_PERMISSIONS',
            target_type='User',
            target_id=user_id,
            details=f"Zaktualizowano uprawnienia dla: {user_to_edit.username}, Komórka: {org_unit_name}"
        )

        flash(f'Uprawnienia dla użytkownika "{user_to_edit.username}" zostały zaktualizowane.', 'success')
        current_app.logger.info(f"Admin '{current_user.username}' zaktualizował uprawnienia dla: {user_to_edit.username}")
    except Exception as e:
        return handle_exception(e, "aktualizacji uprawnień", url_for('admin.manage_users'))

    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/changelog')
@admin_required
def view_changelog():
    """Wyświetla stronę z dziennikiem zmian (audit log)."""
    try:
        # Pobierz wszystkie logi, posortowane od najnowszych
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        
        # Przygotuj dane do wyświetlenia z przekonwertowanym czasem
        from utils import convert_utc_to_local
        logs_with_local_time = []
        
        for log in logs:
            local_timestamp = convert_utc_to_local(log.timestamp)
            logs_with_local_time.append({
                'id': log.id,
                'timestamp': log.timestamp,
                'timestamp_local': local_timestamp,
                'username': log.username,
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'details': log.details
            })
        # W przyszłości można dodać paginację, jeśli logów będzie bardzo dużo
        return render_template('admin/changelog.html', logs=logs)

    except Exception as e:
        flash(f'Błąd podczas pobierania dziennika zmian: {e}', 'error')
        current_app.logger.exception(f"BŁĄD pobierania AuditLog: {e}")
        return render_template('admin/changelog.html', logs=[])
    
#===== CZYSZCZENIE LOGÓW =====
@admin_bp.route('/changelog/clear', methods=['POST'])
@admin_required
def clear_changelog():
    """Czyści dziennik zmian (usuwa wszystkie wpisy)."""
    try:
        # Zapisz log o czyszczeniu przed usunięciem
        log_action(
            'CLEAR_AUDIT_LOG', 
            target_type='AuditLog', 
            target_id=None, 
            details=f"Administrator '{current_user.username}' wyczyścił dziennik zmian"
        )
        
        # Pobierz aktualny log czyszczenia (żeby go zachować)
        clear_log = AuditLog.query.filter_by(action='CLEAR_AUDIT_LOG').order_by(AuditLog.timestamp.desc()).first()
        
        # Usuń wszystkie wpisy z wyjątkiem ostatniego wpisu o czyszczeniu
        if clear_log:
            AuditLog.query.filter(AuditLog.id != clear_log.id).delete()
        else:
            AuditLog.query.delete()
        
        db.session.commit()
        
        flash('Dziennik zmian został wyczyszczony.', 'success')
        current_app.logger.info(f"Administrator '{current_user.username}' wyczyścił dziennik zmian")
        
    except Exception as e:
        return handle_exception(e, "czyszczenia dziennika zmian", url_for('admin.view_changelog'))

    return redirect(url_for('admin.view_changelog'))

#===== KONIEC CZYSZCZENIA LOGÓW =====

#===== EXPORT DZIENNIKA DO CSV =====

@admin_bp.route('/changelog/export/csv')
@admin_required
def export_changelog_csv():
    """Eksportuje dziennik zmian do pliku CSV."""
    try:
        # Pobierz wszystkie logi, posortowane od najnowszych
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        
        if not logs:
            flash('Brak wpisów w dzienniku zmian do eksportu.', 'warning')
            return redirect(url_for('admin.view_changelog'))
        
        # Przygotowanie pliku CSV
        import io
        import csv
        from datetime import datetime
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Nagłówek
        header = ['ID', 'Czas UTC', 'Czas lokalny', 'Użytkownik', 'Akcja', 'Typ obiektu', 'ID obiektu', 'Szczegóły']
        writer.writerow(header)
        
        # Konwersja czasu
        from utils import convert_utc_to_local
        
        # Dane
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                convert_utc_to_local(log.timestamp) if log.timestamp else '',
                log.username or 'System',
                log.action,
                log.target_type or '',
                log.target_id or '',
                log.details or ''
            ])
            
        # Finalizacja i przygotowanie odpowiedzi
        csv_data = output.getvalue()
        
        # Nazwa pliku zawiera aktualny czas
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ChemMan_Audit_Log_{current_time}.csv"
        
        # Zapisz informację o eksporcie w dzienniku
        log_action(
            'EXPORT_AUDIT_LOG', 
            target_type='AuditLog', 
            target_id=None, 
            details=f"Administrator '{current_user.username}' wyeksportował dziennik zmian do CSV"
        )
        
        # Zwróć plik CSV do pobrania
        from flask import Response
        response = Response(
            csv_data.encode('utf-8-sig'),  # z BOM dla poprawnego wyświetlania polskich znaków w Excel
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
        
        current_app.logger.info(f"Administrator '{current_user.username}' wyeksportował dziennik zmian do CSV")
        return response
        
    except Exception as e:
        return handle_exception(e, "eksportu dziennika zmian", url_for('admin.view_changelog'))


#===== ZARZĄDZANIE BAZAMI DANYCH SUBSTANCJI =====

@admin_bp.route('/databases')
@admin_required
def manage_databases():
    """Wyświetla stronę zarządzania bazami danych substancji (CLP, SVHC)."""
    try:
        # Pobierz statystyki baz danych
        stats = get_database_stats()

        # Pobierz informacje o ostatnich importach z audit log
        clp_last_import = AuditLog.query.filter_by(action='IMPORT_CLP_DATABASE').order_by(AuditLog.timestamp.desc()).first()
        svhc_last_import = AuditLog.query.filter_by(action='IMPORT_SVHC_DATABASE').order_by(AuditLog.timestamp.desc()).first()

        return render_template(
            'admin/manage_databases.html',
            stats=stats,
            clp_last_import=clp_last_import,
            svhc_last_import=svhc_last_import
        )
    except Exception as e:
        flash(f'Błąd podczas pobierania informacji o bazach danych: {e}', 'error')
        current_app.logger.error(f"BŁĄD pobierania statystyk baz danych: {e}")
        return render_template('admin/manage_databases.html', stats={'clp_count': 0, 'svhc_count': 0})


@admin_bp.route('/databases/upload/clp', methods=['POST'])
@admin_required
def upload_clp_database():
    """Obsługuje upload i import bazy danych CLP."""
    # Sprawdź, czy plik został wysłany
    if 'clp_file' not in request.files:
        flash('Nie wybrano pliku do wysłania.', 'error')
        return redirect(url_for('admin.manage_databases'))

    file = request.files['clp_file']

    # Sprawdź, czy wybrano plik
    if file.filename == '':
        flash('Nie wybrano pliku.', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 1: Sprawdź rozszerzenie pliku
    if not allowed_excel_file(file.filename):
        flash('Niedozwolony typ pliku. Dozwolone są tylko pliki Excel (.xlsx, .xls)', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 2: Sprawdź rozmiar pliku
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    if file_size > max_size:
        flash(f'Plik jest za duży. Maksymalny rozmiar: {max_size / (1024*1024):.1f} MB', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 3: Sprawdź MIME type
    if not validate_excel_mime_type(file):
        current_app.logger.warning(f"Odrzucono plik o nieprawidłowym MIME type: {file.filename}")
        flash('Plik nie jest prawidłowym plikiem Excel.', 'error')
        return redirect(url_for('admin.manage_databases'))

    # Wykonaj import
    try:
        success, message, records_count = import_clp_data(file)

        if success:
            # Zapisz log akcji
            log_action(
                'IMPORT_CLP_DATABASE',
                target_type='ExcelSourceSubstance',
                target_id=None,
                details=f"Plik: {file.filename}, Zaimportowano rekordów: {records_count}"
            )
            flash(message, 'success')
            current_app.logger.info(f"Administrator '{current_user.username}' zaimportował bazę CLP: {file.filename}, {records_count} rekordów")
        else:
            flash(message, 'error')
            current_app.logger.error(f"Błąd importu CLP: {message}")

    except Exception as e:
        return handle_exception(e, "importu bazy CLP", url_for('admin.manage_databases'))

    return redirect(url_for('admin.manage_databases'))


@admin_bp.route('/databases/upload/svhc', methods=['POST'])
@admin_required
def upload_svhc_database():
    """Obsługuje upload i import bazy danych SVHC."""
    # Sprawdź, czy plik został wysłany
    if 'svhc_file' not in request.files:
        flash('Nie wybrano pliku do wysłania.', 'error')
        return redirect(url_for('admin.manage_databases'))

    file = request.files['svhc_file']

    # Sprawdź, czy wybrano plik
    if file.filename == '':
        flash('Nie wybrano pliku.', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 1: Sprawdź rozszerzenie pliku
    if not allowed_excel_file(file.filename):
        flash('Niedozwolony typ pliku. Dozwolone są tylko pliki Excel (.xlsx, .xls)', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 2: Sprawdź rozmiar pliku
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    if file_size > max_size:
        flash(f'Plik jest za duży. Maksymalny rozmiar: {max_size / (1024*1024):.1f} MB', 'error')
        return redirect(url_for('admin.manage_databases'))

    # WALIDACJA 3: Sprawdź MIME type
    if not validate_excel_mime_type(file):
        current_app.logger.warning(f"Odrzucono plik o nieprawidłowym MIME type: {file.filename}")
        flash('Plik nie jest prawidłowym plikiem Excel.', 'error')
        return redirect(url_for('admin.manage_databases'))

    # Wykonaj import
    try:
        success, message, records_count = import_svhc_data(file)

        if success:
            # Zapisz log akcji
            log_action(
                'IMPORT_SVHC_DATABASE',
                target_type='SVHCSubstance',
                target_id=None,
                details=f"Plik: {file.filename}, Zaimportowano rekordów: {records_count}"
            )
            flash(message, 'success')
            current_app.logger.info(f"Administrator '{current_user.username}' zaimportował bazę SVHC: {file.filename}, {records_count} rekordów")
        else:
            flash(message, 'error')
            current_app.logger.error(f"Błąd importu SVHC: {message}")

    except Exception as e:
        return handle_exception(e, "importu bazy SVHC", url_for('admin.manage_databases'))

    return redirect(url_for('admin.manage_databases'))

#===== KONIEC ZARZĄDZANIA BAZAMI DANYCH =====