import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pagos_cxc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id INTEGER,
    fecha TEXT,
    valor_pagado REAL
)
""")

conexion.commit()

print("TABLA PAGOS_CXC CREADA")

conexion.close()