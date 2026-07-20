import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bancos (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    banco TEXT,

    numero_cuenta TEXT,

    tipo_cuenta TEXT,

    titular TEXT,

    saldo REAL,

    estado TEXT
)
""")

conexion.commit()

conexion.close()

print("TABLA BANCOS CREADA")