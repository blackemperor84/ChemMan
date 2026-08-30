"""
Wspólna logika pobierania hasła administratora dla skryptów CLI.

Używane przez create_admin.py i update_admin_password.py. Celowo NIE ma tu
żadnego hasła domyślnego - brak jawnie podanego hasła jest błędem, nie
powodem do użycia wartości awaryjnej.
"""
import os
import sys
from getpass import getpass
from typing import Callable, Optional

MIN_PASSWORD_LENGTH = 8
ENV_VAR = 'CHEM_MAN_ADMIN_PASSWORD'


class PasswordError(Exception):
    """Nie udało się uzyskać poprawnego hasła administratora."""


def _stdin_is_interactive() -> bool:
    """
    Sprawdza, czy da się bezpiecznie zapytać o hasło.

    Uwaga: sam `sys.stdin.isatty()` nie wystarcza. Na Windows getpass czyta
    z konsoli przez msvcrt, więc przekierowanie stdin (< /dev/null, potok w CI)
    nie powstrzymuje go przed zablokowaniem się w oczekiwaniu na wejście.
    Dlatego dodatkowo wymagamy, aby stdin w ogóle istniał.

    Returns:
        bool: True jeśli można pytać interaktywnie
    """
    if sys.stdin is None:
        return False
    try:
        return sys.stdin.isatty()
    except (ValueError, AttributeError):
        # stdin zamknięty lub podmieniony na obiekt bez isatty()
        return False


def resolve_admin_password(
    prompt: str = 'Hasło dla użytkownika admin: ',
    getenv: Callable[[str], Optional[str]] = None,
    is_interactive: Callable[[], bool] = None,
    ask: Callable[[str], str] = None,
) -> str:
    """
    Zwraca hasło administratora ze zmiennej środowiskowej lub z pytania interaktywnego.

    Args:
        prompt: Tekst zachęty przy pytaniu interaktywnym
        getenv: Funkcja odczytu zmiennej środowiskowej (wstrzykiwana w testach)
        is_interactive: Funkcja sprawdzająca dostępność terminala (wstrzykiwana w testach)
        ask: Funkcja pytająca o hasło bez echa (wstrzykiwana w testach)

    Returns:
        str: Hasło o długości co najmniej MIN_PASSWORD_LENGTH znaków

    Raises:
        PasswordError: Gdy hasła nie podano, nie da się o nie zapytać,
                       potwierdzenie się nie zgadza albo hasło jest za krótkie
    """
    getenv = getenv or os.environ.get
    is_interactive = is_interactive or _stdin_is_interactive
    ask = ask or getpass

    password = getenv(ENV_VAR)

    if password:
        source = f"zmiennej {ENV_VAR}"
    else:
        if not is_interactive():
            raise PasswordError(
                f"Nie ustawiono {ENV_VAR}, a brak terminala do zapytania o hasło. "
                f"Ustaw {ENV_VAR} przed uruchomieniem skryptu."
            )
        password = ask(prompt)
        if password != ask('Powtórz hasło: '):
            raise PasswordError("Hasła nie są identyczne.")
        source = "wprowadzenia interaktywnego"

    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordError(
            f"Hasło jest za krótkie (minimum {MIN_PASSWORD_LENGTH} znaków). "
            f"Źródło: {source}."
        )

    return password
