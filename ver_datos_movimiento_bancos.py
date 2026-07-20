import sqlite3

conexion = sqlite3.connect(
r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT *
FROM movimientos_bancos
ORDER BY id DESC
LIMIT 20
""")

print("\nULTIMOS MOVIMIENTOS BANCARIOS\n")

for fila in cursor.fetchall():
    print(fila)

conexion.close()