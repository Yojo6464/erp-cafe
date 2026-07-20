import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cuentas_pagar(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor TEXT,
    valor REAL,
    saldo REAL,
    fecha TEXT,
    vencimiento TEXT,
    estado TEXT
)
""")

conexion.commit()

conexion.close()

print("TABLA CUENTAS_PAGAR CREADA")