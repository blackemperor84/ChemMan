"""
Skrypt diagnostyczny: sprawdza, czy wykrywanie SVHC działa na danych z bazy.

NIE jest to test pytest, mimo nazwy pliku (nazwa została zachowana, bo do
skryptu odwołuje się starsza dokumentacja). Zbiór testów automatycznych
znajduje się w katalogu `tests/`, a `pytest.ini` ogranicza zbieranie testów
właśnie do niego, więc pytest tego pliku nie dotyka.

Uruchamianie:
    python checks/test_svhc.py
"""
import sys

from app import create_app
from models import SVHCSubstance
from utils import is_svhc_substance


def main():
    app = create_app()

    with app.app_context():
        total = SVHCSubstance.query.count()
        print(f"Substancji SVHC w bazie: {total}")

        if not total:
            print("Baza SVHC jest pusta - uruchom najpierw: flask import-svhc")
            return 1

        first = SVHCSubstance.query.first()
        print("\nPrzykład SVHC:")
        print(f"Nazwa: {first.name}")
        print(f"CAS: {first.cas}")

        result = is_svhc_substance(cas=first.cas, ec_number=first.ec_number, name=first.name)
        print(f"\nCzy jest SVHC? {result is not None}")
        if result:
            print(f"Powód: {result}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
