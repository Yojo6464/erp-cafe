import sqlite3

conexion = sqlite3.connect(
r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tablas = cursor.fetchall()

for tabla in tablas:

    nombre = tabla[0]

    print("\n" + "="*60)
    print("TABLA:", nombre)
    print("="*60)

    cursor.execute(f"PRAGMA table_info({nombre})")

    for campo in cursor.fetchall():
        print(campo)

conexion.close()
