import sqlite3
import os

print("CARPETA ACTUAL:")
print(os.getcwd())

bases = [
    "cafe_alto_cruz.db",
    "cafe_alto_de_la_cruz.db"
]

for bd in bases:

    print("\n====================")
    print("BASE:", bd)
    print("====================")

    try:

        con = sqlite3.connect(bd)
        cur = con.cursor()

        cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        """)

        tablas = cur.fetchall()

        print("TABLAS:", tablas)

        for tabla in ["ventas", "clientes", "inventario"]:

            try:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                print(tabla, "=", cur.fetchone()[0])

            except Exception as e:
                print(tabla, "ERROR")

        con.close()

    except Exception as e:
        print("ERROR:", e)