import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS recepcion_produccion (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    numero_despacho TEXT,

    lote_pergamino TEXT,

    kg_enviados REAL,

    kg_recibidos REAL,

    merma_kg REAL,

    merma_pct REAL,

    producto TEXT,

    presentacion TEXT,

    bolsas_producidas INTEGER,

    costo_real_kg REAL,

    costo_real_bolsa REAL,

    observaciones TEXT

)
""")

conexion.commit()

print(
    "TABLA RECEPCION_PRODUCCION CREADA"
)

conexion.close()