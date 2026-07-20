import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS despachos_maquila (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT,

    numero_despacho TEXT,

    maquila TEXT,

    lote_pergamino TEXT,

    kg_pergamino REAL,

    tipo_bolsa TEXT,

    cantidad_bolsas INTEGER,

    cantidad_etiquetas INTEGER,

    cantidad_valvulas INTEGER,

    observaciones TEXT,

    estado TEXT

)
""")

conexion.commit()

print(
    "TABLA DESPACHOS_MAQUILA CREADA"
)

conexion.close()