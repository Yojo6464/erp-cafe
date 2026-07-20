import sqlite3

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute("""
SELECT
producto,
presentacion,
costo_bolsa,
utilidad_bolsa,
precio_venta
FROM produccion_costos
ORDER BY id DESC
""")

for fila in cursor.fetchall():
    print(fila)

conexion.close()
