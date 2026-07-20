import sqlite3

bases = [
    "cafe_alto_cruz.db",
    "cafe_alto_cruz.db",
    "cafe_alto_de_la_cruz_backup.db"
]

for bd in bases:

    print("\n" + "="*50)
    print("BASE:", bd)
    print("="*50)

    try:

        conexion = sqlite3.connect(bd)
        cursor = conexion.cursor()

        cursor.execute("SELECT COUNT(*) FROM ventas")
        print("VENTAS:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM clientes")
        print("CLIENTES:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM inventario")
        print("INVENTARIO:", cursor.fetchone()[0])

        conexion.close()

    except Exception as e:
        print("ERROR:", e)
