import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT COUNT(*)
FROM solicitudes_pago
""")

print("TOTAL:", cursor.fetchone()[0])

cursor.execute("""
SELECT *
FROM solicitudes_pago
""")

registros = cursor.fetchall()

print("REGISTROS:")
print(registros)

conexion.close()