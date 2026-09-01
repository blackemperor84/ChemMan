"""
Import listy SVHC z pliku Excel do tabeli `svhc_substances`.

Skrypt jest cienką nakładką na `utils.database_import.import_svhc_data` —
tę samą funkcję, z której korzystają panel admina i komenda
`flask import-svhc`. Wszystkie trzy drogi dają identyczny wynik.

Wcześniej skrypt miał własną pętlę importu, która kasowała listę SVHC
i zatwierdzała dane paczkami po 50 rekordów. Błąd w połowie zostawiał listę
częściowo wypełnioną, bez możliwości cofnięcia — DELETE był już
zatwierdzony. W rejestrze substancji chemicznych oznacza to ciche
„nie SVHC" przy substancjach, które na liście są.

Użycie:
    python import_svhc.py [ścieżka/do/pliku.xlsx]

Bez argumentu importowany jest plik wskazany przez SVHC_FILE_PATH
w konfiguracji (domyślnie svhc.xlsx w katalogu projektu).
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from utils.database_import import import_svhc_data


def main(argv):
    app = create_app()

    with app.app_context():
        svhc_path = argv[1] if len(argv) > 1 else app.config.get('SVHC_FILE_PATH')

        if not svhc_path or not os.path.exists(svhc_path):
            sys.exit(f"BŁĄD: Plik SVHC nie istnieje pod ścieżką: {svhc_path}")

        print(f"Rozpoczynam import SVHC z: {svhc_path}...")
        with open(svhc_path, 'rb') as stream:
            success, message, count = import_svhc_data(stream)

        print(message)
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
