import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

tablas = [
    "produccion",
    "inventario",
    "ventas",
    "recepcion_produccion"
]

for tabla in tablas:

    print("\n")
    print("=" * 50)
    print(tabla.upper())
    print("=" * 50)

    cursor.execute(f"PRAGMA table_info({tabla})")

    for campo in cursor.fetchall():
        print(campo)

conexion.close()