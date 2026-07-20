import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT
id,
fecha,
cliente,
producto,
presentacion,
cantidad,
precio_unitario,
total
FROM ventas
ORDER BY id DESC
LIMIT 5
""")

for fila in cursor.fetchall():
    print(fila)

conexion.close()