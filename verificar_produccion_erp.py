import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
AND name='produccion'
""")

resultado = cursor.fetchone()

if resultado:

    print("TABLA PRODUCCION EXISTE")

else:

    print("TABLA PRODUCCION NO EXISTE")

conexion.close()