import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

print("\nSOLICITUDES_PAGO")
cursor.execute("""
PRAGMA table_info(solicitudes_pago)
""")

for campo in cursor.fetchall():
    print(campo)

print("\nMOVIMIENTOS_BANCOS")
cursor.execute("""
PRAGMA table_info(movimientos_bancos)
""")

for campo in cursor.fetchall():
    print(campo)

conexion.close()