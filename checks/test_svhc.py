from app import create_app, db, SVHCSubstance
from utils import is_svhc_substance

app = create_app()

with app.app_context():
    # Sprawdź czy SVHC są w bazie
    total = SVHCSubstance.query.count()
    print(f"Substancji SVHC w bazie: {total}")
    
    # Sprawdź pierwszą substancję
    first = SVHCSubstance.query.first()
    print(f"\nPrzykład SVHC:")
    print(f"Nazwa: {first.name}")
    print(f"CAS: {first.cas}")
    
    # Testuj funkcję sprawdzania
    result = is_svhc_substance(cas=first.cas, ec_number=first.ec_number, name=first.name)
    print(f"\nCzy jest SVHC? {result is not None}")
    if result:
        print(f"Powód: {result}")