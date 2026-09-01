from app import create_app
from models import db, ExcelSourceSubstance
import pandas as pd

app = create_app()

with app.app_context():
    print("Rozpoczynam import...")
    
    # Wczytaj Excel - POMIŃ pierwszy pusty wiersz!
    df = pd.read_excel('substancje_baza.xlsx', header=0, skiprows=[1])
    print(f"Wczytano {len(df)} wierszy z Excel")
    print(f"Kolumny: {list(df.columns)}")
    
    # Mapowanie kolumn
    column_map = {
        'International Chemical Identification': 'name',
        'CAS No': 'cas',
        'EC No': 'ec_number',
        'Classification': 'classification',
        'Unnamed: 5': 'h_phrases',
        'Specific Conc. Limits, M-factors': 'scl_mfactor'
    }
    
    # Usuń stare dane
    deleted = ExcelSourceSubstance.query.delete()
    print(f"Usunięto {deleted} starych rekordów")
    
    # Zmapuj nazwy kolumn
    df.rename(columns=column_map, inplace=True)
    
    # Zachowaj tylko zmapowane kolumny
    df = df[list(column_map.values())]
    
    # Import - convert all values to strings, handle NaN
    count = 0
    for idx, row in df.iterrows():
        # Convert to string and handle NaN/None
        def safe_str(val):
            if pd.isna(val):
                return None
            return str(val)

        substance = ExcelSourceSubstance(
            name=safe_str(row['name']),
            cas=safe_str(row['cas']),
            ec_number=safe_str(row['ec_number']),
            classification=safe_str(row['classification']),
            h_phrases=safe_str(row['h_phrases']),
            scl_mfactor=safe_str(row['scl_mfactor'])
        )
        db.session.add(substance)
        count += 1
        if count % 100 == 0:
            print(f"Zaimportowano {count}...")
            db.session.commit()  # Commit in batches

    # Final commit for remaining records
    if count % 100 != 0:
        db.session.commit()

    print(f"Gotowe! Zaimportowano {count} substancji!")