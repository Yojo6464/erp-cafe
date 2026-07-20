import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

print("\n===== TABLAS =====\n")

for tabla in cursor.fetchall():
    print(tabla[0])

conexion.close()