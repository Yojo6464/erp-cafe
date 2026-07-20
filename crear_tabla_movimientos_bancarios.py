import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movimientos_bancos(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    banco_id INTEGER,

    tipo TEXT,

    concepto TEXT,

    valor REAL,

    saldo_anterior REAL,

    saldo_nuevo REAL
)
""")

conexion.commit()

conexion.close()

print("TABLA MOVIMIENTOS_BANCOS CREADA")