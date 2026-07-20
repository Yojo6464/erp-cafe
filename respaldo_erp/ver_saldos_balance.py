import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM bancos
""")

print(
    "BANCOS:",
    cursor.fetchone()[0]
)

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM cuentas_cobrar
""")

print(
    "CUENTAS COBRAR:",
    cursor.fetchone()[0]
)

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM cuentas_pagar
""")

print(
    "CUENTAS PAGAR:",
    cursor.fetchone()[0]
)

cursor.execute("""
SELECT IFNULL(SUM(cantidad),0)
FROM inventario
""")

print(
    "INVENTARIO:",
    cursor.fetchone()[0]
)

conexion.close()