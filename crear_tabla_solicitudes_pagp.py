import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS solicitudes_pago(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    proveedor TEXT,

    concepto TEXT,

    valor REAL,

    banco TEXT,

    estado TEXT,

    fecha_aprobacion TEXT
)
""")

conexion.commit()

conexion.close()

print("TABLA SOLICITUDES_PAGO CREADA")