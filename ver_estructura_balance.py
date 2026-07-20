import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

tablas = [
    "inventario",
    "cuentas_cobrar",
    "cuentas_pagar",
    "bancos"
]

for tabla in tablas:

    print("\n" + "=" * 50)
    print(tabla.upper())
    print("=" * 50)

    cursor.execute(
        f"PRAGMA table_info({tabla})"
    )

    for campo in cursor.fetchall():
        print(campo)

conexion.close()