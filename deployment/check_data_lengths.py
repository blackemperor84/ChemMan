import sqlite3

conn = sqlite3.connect('instance/chem_man.db')
cursor = conn.cursor()

print("Checking data lengths in SQLite database...")
print("=" * 60)

# Check EC number lengths
cursor.execute('SELECT MAX(LENGTH(ec_number)) FROM excel_source_substances WHERE ec_number IS NOT NULL')
max_ec = cursor.fetchone()[0]
print(f"Max EC number length: {max_ec}")

if max_ec and max_ec > 50:
    cursor.execute('SELECT ec_number FROM excel_source_substances WHERE LENGTH(ec_number) > 50 LIMIT 5')
    print("EC numbers longer than 50 chars:")
    for row in cursor.fetchall():
        print(f"  {len(row[0])} chars: {row[0]}")

# Check CAS number lengths
cursor.execute('SELECT MAX(LENGTH(cas)) FROM excel_source_substances WHERE cas IS NOT NULL')
max_cas = cursor.fetchone()[0]
print(f"\nMax CAS number length: {max_cas}")

if max_cas and max_cas > 50:
    cursor.execute('SELECT cas FROM excel_source_substances WHERE LENGTH(cas) > 50 LIMIT 5')
    print("CAS numbers longer than 50 chars:")
    for row in cursor.fetchall():
        print(f"  {len(row[0])} chars: {row[0]}")

# Check name lengths
cursor.execute('SELECT MAX(LENGTH(name)) FROM excel_source_substances WHERE name IS NOT NULL')
max_name = cursor.fetchone()[0]
print(f"\nMax name length: {max_name}")

if max_name and max_name > 500:
    cursor.execute('SELECT name FROM excel_source_substances WHERE LENGTH(name) > 500 LIMIT 5')
    print("Names longer than 500 chars:")
    for row in cursor.fetchall():
        print(f"  {len(row[0])} chars: {row[0][:100]}...")

conn.close()
