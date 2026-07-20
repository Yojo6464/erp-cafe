import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

print("\nCUENTAS_COBRAR\n")

cursor.execute(
    "PRAGMA table_info(cuentas_cobrar)"
)

for fila in cursor.fetchall():
    print(fila)

print("\nPAGOS_CXC\n")

cursor.execute(
    "PRAGMA table_info(pagos_cxc)"
)

for fila in cursor.fetchall():
    print(fila)

print("\nCLIENTES\n")

cursor.execute(
    "PRAGMA table_info(clientes)"
)

for fila in cursor.fetchall():
    print(fila)

conexion.close()