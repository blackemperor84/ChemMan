from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User
from utils import log_action, handle_exception

# Utworzenie blueprintu dla uwierzytelniania
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Obsługa logowania użytkownika."""
    # Jeśli użytkownik jest już zalogowany, przekieruj na stronę główną
    if current_user.is_authenticated:
        return redirect(url_for('locations.index'))

    # Jeśli formularz został wysłany (metoda POST)
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        current_app.logger.debug(f"Próba logowania użytkownika: '{username}'")

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Logowanie udane
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Witaj {user.username}! Zalogowano pomyślnie.', 'success')
            current_app.logger.info(f"Logowanie udane: {username}")
            return redirect(next_page or url_for('locations.index'))
        else:
            # Logowanie nieudane
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
            current_app.logger.warning(f"Nieudane logowanie dla: {username}")
            return redirect(url_for('auth.login'))

    # Jeśli metoda GET - wyświetl formularz
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Obsługa wylogowania użytkownika."""
    user_name = current_user.username  # Zapamiętaj nazwę dla komunikatu
    logout_user()  # Funkcja z Flask-Login
    flash('Zostałeś pomyślnie wylogowany.', 'success')
    current_app.logger.info(f"Wylogowano użytkownika: {user_name}")
    return redirect(url_for('auth.login'))  # Przekieruj na stronę logowania


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Obsługuje formularz zmiany hasła przez zalogowanego użytkownika."""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Sprawdź, czy obecne hasło jest poprawne
        if not current_user.check_password(current_password):
            flash('Obecne hasło jest nieprawidłowe.', 'error')
        # Sprawdź, czy nowe hasło ma odpowiednią długość
        elif len(new_password) < 4:
            flash('Nowe hasło musi mieć co najmniej 4 znaki.', 'error')
        # Sprawdź, czy nowe hasła się zgadzają
        elif new_password != confirm_password:
            flash('Nowe hasła nie pasują do siebie.', 'error')
        else:
            # Jeśli wszystko OK, zaktualizuj hasło
            try:
                current_user.set_password(new_password)  # Ustaw i zahashuj nowe hasło
                db.session.commit()  # Zapisz zmianę w bazie
                
                log_action(
                    'CHANGE_PASSWORD', 
                    target_type='User', 
                    target_id=current_user.id, 
                    details=f"Użytkownik '{current_user.username}' zmienił swoje hasło"
                )
                
                flash('Twoje hasło zostało pomyślnie zmienione.', 'success')
                current_app.logger.info(f"Użytkownik '{current_user.username}' zmienił swoje hasło.")
                return redirect(url_for('locations.index'))
            except Exception as e:
                return handle_exception(e, "zmiany hasła", url_for('auth.change_password'))

        # Jeśli wystąpił błąd walidacji, wróć do formularza zmiany hasła
        return redirect(url_for('auth.change_password'))

    # Dla metody GET - wyświetl formularz zmiany hasła
    return render_template('change_password.html')