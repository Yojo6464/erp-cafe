import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

# Bancos

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM bancos
""")

print(
    "BANCOS:",
    cursor.fetchone()[0]
)

# CxC

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM cuentas_cobrar
""")

print(
    "CUENTAS COBRAR:",
    cursor.fetchone()[0]
)

# CxP

cursor.execute("""
SELECT IFNULL(SUM(saldo),0)
FROM cuentas_pagar
""")

print(
    "CUENTAS PAGAR:",
    cursor.fetchone()[0]
)

# Solicitudes pendientes

cursor.execute("""
SELECT COUNT(*)
FROM solicitudes_pago
WHERE estado='PENDIENTE'
""")

print(
    "SOLICITUDES:",
    cursor.fetchone()[0]
)

conexion.close()
