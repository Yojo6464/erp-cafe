import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

for tabla in [
    "compras",
    "cuentas_cobrar",
    "cuentas_pagar",
    "pagos_cxc",
    "pagos_cxp"
]:

    print("\n" + "="*50)
    print(tabla)
    print("="*50)

    cursor.execute(
        f"PRAGMA table_info({tabla})"
    )

    for fila in cursor.fetchall():
        print(fila)

conexion.close()