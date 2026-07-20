import sqlite3

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA table_info(ventas)")

for fila in cursor.fetchall():
    print(fila)

conexion.close()
