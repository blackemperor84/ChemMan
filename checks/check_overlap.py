from app import create_app, db
from models import ExcelSourceSubstance, SVHCSubstance

app = create_app()

with app.app_context():
    # Pobierz kilka SVHC
    svhc_substances = SVHCSubstance.query.limit(10).all()
    
    print("Szukam substancji SVHC w bazie CLP...\n")
    
    found_count = 0
    for svhc in svhc_substances:
        # Szukaj po CAS
        if svhc.cas:
            match = ExcelSourceSubstance.query.filter_by(cas=svhc.cas).first()
            if match:
                print(f"✓ ZNALEZIONO: {svhc.name}")
                print(f"  CAS: {svhc.cas}")
                print(f"  W bazie jako: {match.name}\n")
                found_count += 1
    
    print(f"\nZnaleziono {found_count} z 10 sprawdzonych substancji SVHC w bazie CLP")