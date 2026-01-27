import pandas as pd

df = pd.read_excel('svhc.xlsx', header=0)
print("Kolumny w pliku SVHC:")
print(df.columns.tolist())
print(f"\nLiczba wierszy: {len(df)}")
print("\nPierwsze 3 wiersze:")
print(df.head(3))