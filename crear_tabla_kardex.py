import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS kardex (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    producto TEXT,

    presentacion TEXT,

    movimiento TEXT,

    entrada REAL,

    salida REAL,

    saldo REAL,

    costo_unitario REAL,

    lote TEXT,

    origen TEXT,

    observaciones TEXT

)
""")

conexion.commit()

print("TABLA KARDEX CREADA")

conexion.close()