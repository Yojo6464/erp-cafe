import sqlite3

con = sqlite3.connect("erp_cafe.db")
cur = con.cursor()

print("=" * 60)
print("TABLAS")
print("=" * 60)

for t in cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
"""):
    print(t[0])

print("\n" + "=" * 60)
print("REGISTROS EN INVENTARIO")
print("=" * 60)

try:
    print(cur.execute("SELECT COUNT(*) FROM inventario").fetchone())
except Exception as e:
    print(e)

print("\n" + "=" * 60)
print("PRIMEROS REGISTROS")
print("=" * 60)

try:
    for r in cur.execute("SELECT * FROM inventario LIMIT 5"):
        print(r)
except Exception as e:
    print(e)

con.close()