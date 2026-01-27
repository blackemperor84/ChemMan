from app import create_app, db, SVHCSubstance
import pandas as pd

app = create_app()

with app.app_context():
    print("Rozpoczynam import SVHC...")
    
    # Wczytaj Excel
    df = pd.read_excel('svhc.xlsx', header=0)
    print(f"Wczytano {len(df)} wierszy z SVHC Excel")
    print(f"Kolumny: {list(df.columns)}")
    
    # Mapowanie kolumn
    column_map = {
        'Nazwa substancji ': 'name',
        'Nr WE': 'ec_number',
        'Nr CAS': 'cas',
        'Powód włączenia ': 'reason',
        'Data włączenia ': 'date_inclusion'
    }
    
    # Usuń stare dane
    deleted = SVHCSubstance.query.delete()
    print(f"Usunięto {deleted} starych rekordów SVHC")
    
    # Zmapuj nazwy kolumn
    df.rename(columns=column_map, inplace=True)
    
    # Upewnij się że wszystkie kolumny istnieją
    for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
        if col not in df.columns:
            df[col] = None
    
    # Zachowaj tylko zmapowane kolumny
    df = df[['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]
    
    # Import - convert all values to strings, handle NaN
    count = 0
    for idx, row in df.iterrows():
        # Convert to string and handle NaN/None
        def safe_str(val):
            if pd.isna(val):
                return None
            return str(val)

        substance = SVHCSubstance(
            name=safe_str(row['name']),
            cas=safe_str(row['cas']),
            ec_number=safe_str(row['ec_number']),
            reason=safe_str(row['reason']),
            date_inclusion=safe_str(row['date_inclusion'])
        )
        db.session.add(substance)
        count += 1
        if count % 50 == 0:
            print(f"Zaimportowano {count}...")
            db.session.commit()  # Commit in batches

    # Final commit for remaining records
    if count % 50 != 0:
        db.session.commit()

    print(f"Gotowe! Zaimportowano {count} substancji SVHC!")
