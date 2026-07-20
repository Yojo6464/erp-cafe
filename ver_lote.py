import sqlite3

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute("""
SELECT
id,
fecha,
producto,
presentacion,
bolsas,
precio_venta,
costo_bolsa
FROM produccion_costos
ORDER BY id DESC
""")

registros = cursor.fetchall()

if len(registros) == 0:
    print("NO HAY LOTES GUARDADOS")
else:
    for fila in registros:
        print(fila)

conexion.close()
