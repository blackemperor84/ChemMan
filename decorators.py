from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def permission_required(permission_type):
    """Sprawdza czy zalogowany użytkownik ma uprawnienie danego typu."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Musisz się zalogować, aby uzyskać dostęp do tej strony.', 'error')
                return redirect(url_for('auth.login'))
            
            # Admin ma wszystkie uprawnienia
            if current_user.is_admin:
                return f(*args, **kwargs)
                
            # Sprawdź konkretne uprawnienie
            if not getattr(current_user, permission_type, False):
                flash('Nie masz uprawnień do wykonania tej operacji.', 'error')
                return redirect(url_for('locations.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def view_permission_required(f):
    """Skrót dla uprawnienia do przeglądania."""
    return permission_required('can_view')(f)

def add_permission_required(f):
    """Skrót dla uprawnienia do dodawania."""
    return permission_required('can_add')(f)

def edit_permission_required(f):
    """Skrót dla uprawnienia do edycji."""
    return permission_required('can_edit')(f)

def delete_permission_required(f):
    """Skrót dla uprawnienia do usuwania."""
    return permission_required('can_delete')(f)

def move_permission_required(f):
    """Skrót dla uprawnienia do przenoszenia."""
    return permission_required('can_move')(f)

def copy_permission_required(f):
    """Skrót dla uprawnienia do kopiowania."""
    return permission_required('can_copy')(f)

def upload_sds_permission_required(f):
    """Skrót dla uprawnienia do zarządzania plikami SDS."""
    return permission_required('can_upload_sds')(f)

def add_location_permission_required(f):
    """Skrót dla uprawnienia do dodawania lokalizacji."""
    return permission_required('can_add_location')(f)

def delete_location_permission_required(f):
    """Skrót dla uprawnienia do usuwania lokalizacji."""
    return permission_required('can_delete_location')(f)