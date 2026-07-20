import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute(
    "PRAGMA table_info(clientes)"
)

for campo in cursor.fetchall():
    print(campo)

conexion.close()