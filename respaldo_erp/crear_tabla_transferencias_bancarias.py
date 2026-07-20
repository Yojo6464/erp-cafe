import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transferencias_bancarias(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    banco_origen TEXT,

    banco_destino TEXT,

    valor REAL,

    autorizado_por TEXT
)
""")

conexion.commit()

conexion.close()

print(
    "TABLA TRANSFERENCIAS_BANCARIAS CREADA"
)