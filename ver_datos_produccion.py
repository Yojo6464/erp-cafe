import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

cursor.execute("""
SELECT *
FROM produccion
""")

for fila in cursor.fetchall():
    print(fila)

conexion.close()