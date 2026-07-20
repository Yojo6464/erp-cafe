import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT *
FROM ventas
""")

for fila in cursor.fetchall():
    print(fila)

conexion.close()