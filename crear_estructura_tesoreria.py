import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

print("\nPROVEEDORES")
cursor.execute("PRAGMA table_info(proveedores)")
for campo in cursor.fetchall():
    print(campo)

print("\nBANCOS")
cursor.execute("PRAGMA table_info(bancos)")
for campo in cursor.fetchall():
    print(campo)

conexion.close()