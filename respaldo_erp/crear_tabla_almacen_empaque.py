import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS almacen_empaques (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    tipo_empaque TEXT,

    proveedor TEXT,

    cantidad INTEGER,

    saldo INTEGER,

    costo_unitario REAL,

    costo_total REAL,

    observaciones TEXT

)
""")

conexion.commit()

print(
    "TABLA ALMACEN_EMPAQUES CREADA"
)

conexion.close()