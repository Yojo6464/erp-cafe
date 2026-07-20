import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA table_info(kardex)")

for fila in cursor.fetchall():
    print(fila)

conexion.close()