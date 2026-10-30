import sqlite3

conn = sqlite3.connect("voxera.db")
rows = conn.execute("SELECT id, name, tagline FROM domain_profiles").fetchall()
print("All rows in domain_profiles:")
for r in rows:
    print(r)
conn.close()
