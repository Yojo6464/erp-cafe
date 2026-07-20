import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagos_cxp(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id INTEGER,
    fecha TEXT,
    valor REAL
)
""")

conexion.commit()

conexion.close()

print("TABLA PAGOS_CXP CREADA")