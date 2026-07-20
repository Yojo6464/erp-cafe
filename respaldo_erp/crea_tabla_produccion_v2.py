import sqlite3

# =====================================
# CONEXION
# =====================================

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

# =====================================
# TABLA PRODUCCION V2
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS produccion (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    lote TEXT,

    cafe_verde_kg REAL,

    merma_pct REAL,

    cafe_tostado_kg REAL,

    producto TEXT,

    presentacion TEXT,

    cantidad_bolsas INTEGER,

    costo_materia_prima REAL,

    costo_maquila REAL,

    costo_empaque REAL,

    costo_transporte REAL,

    costo_total REAL,

    costo_unitario REAL,

    observaciones TEXT

)
""")

conexion.commit()

print(
    "TABLA PRODUCCION V2 CREADA"
)

conexion.close()