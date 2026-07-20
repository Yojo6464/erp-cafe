import sqlite3

conexion = sqlite3.connect(
r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

tablas = [
    "bancos",
    "movimientos_bancos",
    "cuentas_cobrar",
    "pagos_cxc",
    "cuentas_pagar",
    "pagos_cxp"
]

print("\nREGISTROS EN TABLAS FINANCIERAS\n")

for tabla in tablas:

    try:

        cursor.execute(
            f"SELECT COUNT(*) FROM {tabla}"
        )

        cantidad = cursor.fetchone()[0]

        print(f"{tabla}: {cantidad}")

    except Exception as e:

        print(f"{tabla}: ERROR -> {e}")

conexion.close()