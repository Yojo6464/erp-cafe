import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT COUNT(*)
FROM ventas
""")

print("VENTAS:", cursor.fetchone()[0])

cursor.execute("""
SELECT COUNT(*)
FROM compras
""")

print("COMPRAS:", cursor.fetchone()[0])

cursor.execute("""
SELECT COUNT(*)
FROM solicitudes_pago
""")

print("SOLICITUDES:", cursor.fetchone()[0])

conexion.close()