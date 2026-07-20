import sqlite3

con = sqlite3.connect(
r"C:\Users\jrive\visual\erp_cafe.db"
)

cur = con.cursor()

tablas = [
    "bancos",
    "movimientos_bancos",
    "ventas",
    "cuentas_cobrar",
    "pagos_cxc",
    "compras",
    "cuentas_pagar",
    "pagos_cxp"
]

for tabla in tablas:

    print("\n")
    print("=" * 50)
    print("TABLA:", tabla)
    print("=" * 50)

    cur.execute(
        f"PRAGMA table_info({tabla})"
    )

    for campo in cur.fetchall():

        print(campo)

con.close()