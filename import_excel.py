"""
Import bazy CLP z pliku Excel do tabeli `excel_source_substances`.

Skrypt jest cienką nakładką na `utils.database_import.import_clp_data` —
tę samą funkcję, z której korzystają panel admina i komenda
`flask import-excel`. Wszystkie trzy drogi dają identyczny wynik.

Wcześniej skrypt miał własną pętlę importu, która kasowała tabelę
referencyjną i zatwierdzała dane paczkami po 50/100 rekordów. Błąd w połowie
zostawiał bazę CLP częściowo wypełnioną, bez możliwości cofnięcia — DELETE
był już zatwierdzony. Pomijał też walidację pliku i zachowywanie
uzupełnionych ręcznie kolumn (SCL / M-factor), które nowsze eksporty ECHA
potrafią wyczyścić.

Użycie:
    python import_excel.py [ścieżka/do/pliku.xlsx]

Bez argumentu importowany jest plik wskazany przez EXCEL_FILE_PATH
w konfiguracji (domyślnie substancje_baza.xlsx w katalogu projektu).
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from utils.database_import import import_clp_data


def main(argv):
    app = create_app()

    with app.app_context():
        excel_path = argv[1] if len(argv) > 1 else app.config.get('EXCEL_FILE_PATH')

        if not excel_path or not os.path.exists(excel_path):
            sys.exit(f"BŁĄD: Plik Excel nie istnieje pod ścieżką: {excel_path}")

        print(f"Rozpoczynam import CLP z: {excel_path}...")
        with open(excel_path, 'rb') as stream:
            success, message, count = import_clp_data(stream)

        print(message)
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
