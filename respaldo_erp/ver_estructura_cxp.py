import sqlite3

con = sqlite3.connect("erp_cafe.db")
cur = con.cursor()

print("\nCUENTAS_PAGAR\n")

for fila in cur.execute("PRAGMA table_info(cuentas_pagar)"):
    print(fila)

print("\nPAGOS_CXP\n")

for fila in cur.execute("PRAGMA table_info(pagos_cxp)"):
    print(fila)

print("\nPROVEEDORES\n")

for fila in cur.execute("PRAGMA table_info(proveedores)"):
    print(fila)

con.close()