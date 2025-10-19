from app import create_app, db
from models import ExcelSourceSubstance

app = create_app()

with app.app_context():
    # Sprawdź czy dane są w bazie
    total = ExcelSourceSubstance.query.count()
    print(f"Łącznie substancji w bazie: {total}")
    
    # Pokaż kilka przykładów
    samples = ExcelSourceSubstance.query.limit(5).all()
    print("\nPrzykładowe rekordy:")
    for s in samples:
        print(f"ID: {s.id}")
        print(f"Name: {repr(s.name)}")  # repr pokaże \n jeśli jest
        print(f"CAS: {s.cas}")
        print("-" * 50)
    
    # Sprawdź czy są polskie znaki
    with_polish = ExcelSourceSubstance.query.filter(
        ExcelSourceSubstance.name.like('%wod%')
    ).limit(3).all()
    
    print(f"\nZnaleziono {len(with_polish)} z 'wod' w nazwie:")
    for s in with_polish:
        print(f"Name: {repr(s.name)}")