import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS compras(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    proveedor TEXT,
    tipo_compra TEXT,
    descripcion TEXT,
    valor REAL,
    forma_pago TEXT,
    dias_credito INTEGER
)
""")

conexion.commit()

conexion.close()

print("TABLA COMPRAS CREADA")