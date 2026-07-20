import sqlite3

con = sqlite3.connect("erp_cafe.db")
cur = con.cursor()

tablas = [
    "bancos",
    "inventario",
    "ventas",
    "cuentas_cobrar",
    "cuentas_pagar"
]

for tabla in tablas:

    print("\n" + "=" * 50)
    print(tabla.upper())
    print("=" * 50)

    try:
        for fila in cur.execute(
            f"PRAGMA table_info({tabla})"
        ):
            print(fila)

    except Exception as e:
        print(e)

con.close()