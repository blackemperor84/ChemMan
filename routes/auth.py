from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from limiter import limiter
from models import db, User
from utils import log_action, handle_exception

# Utworzenie blueprintu dla uwierzytelniania
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Max 10 prób logowania na minutę
def login():
    """Obsługa logowania użytkownika."""
    # Jeśli użytkownik jest już zalogowany, przekieruj na stronę główną
    if current_user.is_authenticated:
        return redirect(url_for('locations.index'))

    # Jeśli formularz został wysłany (metoda POST)
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # WALIDACJA: Sprawdź czy username i password nie są puste
        if not username or not password:
            flash('Nazwa użytkownika i hasło są wymagane.', 'error')
            return redirect(url_for('auth.login'))
        
        # WALIDACJA: Sprawdź długość username (min 3, max 50)
        if len(username) < 3 or len(username) > 50:
            flash('Nieprawidłowa nazwa użytkownika (3-50 znaków).', 'error')
            return redirect(url_for('auth.login'))
        
        # WALIDACJA: Sprawdź długość hasła (min 4)
        if len(password) < 4:
            flash('Hasło jest za krótkie.', 'error')
            return redirect(url_for('auth.login'))

        current_app.logger.debug(f"Próba logowania użytkownika")

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Logowanie udane
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Witaj {user.username}! Zalogowano pomyślnie.', 'success')
            current_app.logger.info(f"Logowanie udane dla użytkownika")
            return redirect(next_page or url_for('locations.index'))
        else:
            # Logowanie nieudane - nie ujawniaj czy user istnieje
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
            current_app.logger.warning(f"Nieudane logowanie - błędy kredencjałów")
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
    current_app.logger.info(f"Wylogowano użytkownika")
    return redirect(url_for('auth.login'))  # Przekieruj na stronę logowania


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Obsługuje formularz zmiany hasła przez zalogowanego użytkownika."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # WALIDACJA: Sprawdź czy pola nie są puste
        if not current_password or not new_password or not confirm_password:
            flash('Wszystkie pola są wymagane.', 'error')
            return redirect(url_for('auth.change_password'))

        # Sprawdź, czy obecne hasło jest poprawne
        if not current_user.check_password(current_password):
            flash('Obecne hasło jest nieprawidłowe.', 'error')
        # Sprawdź, czy nowe hasło ma odpowiednią długość (minimum 4 znaki)
        elif len(new_password) < 4:
            flash('Nowe hasło musi mieć co najmniej 4 znaki.', 'error')
        # Sprawdź maksymalną długość hasła (bezpieczeństwo)
        elif len(new_password) > 128:
            flash('Hasło jest za długie (max 128 znaków).', 'error')
        # Sprawdź, czy nowe hasła się zgadzają
        elif new_password != confirm_password:
            flash('Nowe hasła nie pasują do siebie.', 'error')
        # Sprawdź czy nowe hasło różni się od starego
        elif new_password == current_password:
            flash('Nowe hasło musi być inne od poprzedniego.', 'error')
        else:
            # Jeśli wszystko OK, zaktualizuj hasło
            try:
                current_user.set_password(new_password)  # Ustaw i zahashuj nowe hasło
                db.session.commit()  # Zapisz zmianę w bazie
                
                log_action(
                    'CHANGE_PASSWORD', 
                    target_type='User', 
                    target_id=current_user.id, 
                    details=f"Użytkownik zmienił swoje hasło"
                )
                
                flash('Twoje hasło zostało pomyślnie zmienione.', 'success')
                current_app.logger.info(f"Użytkownik zmienił swoje hasło.")
                return redirect(url_for('locations.index'))
            except Exception as e:
                return handle_exception(e, "zmiany hasła", url_for('auth.change_password'))

        # Jeśli wystąpił błąd walidacji, wróć do formularza zmiany hasła
        return redirect(url_for('auth.change_password'))

    # Dla metody GET - wyświetl formularz zmiany hasła
    return render_template('change_password.html')