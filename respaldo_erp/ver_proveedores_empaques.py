import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT nombre
FROM proveedores
ORDER BY nombre
""")

for fila in cursor.fetchall():

    print(fila[0])

conexion.close()