import pandas as pd

df = pd.read_excel('substancje_baza.xlsx', header=0)
print("Kolumny w pliku Excel:")
print(df.columns.tolist())
print(f"\nLiczba wierszy: {len(df)}")

print("\n=== Pierwsze 5 wierszy kolumny 'International Chemical Identification': ===")
for idx in range(5):
    val = df.iloc[idx]['International Chemical Identification']
    print(f"Wiersz {idx}: {repr(val)}")

print("\n=== Pierwsze 5 wierszy kolumny 'CAS No': ===")
for idx in range(5):
    val = df.iloc[idx]['CAS No']
    print(f"Wiersz {idx}: {repr(val)}")