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
total,
costo_unitario,
utilidad_total,
margen
FROM ventas
""")

for fila in cursor.fetchall():
    print(fila)

conexion.close()