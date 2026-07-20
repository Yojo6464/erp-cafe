import sqlite3

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

# =====================================
# CLIENTES
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT
)
""")

# =====================================
# INVENTARIO
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER,
    estado TEXT
)
""")

# =====================================
# COSTOS
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS costos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    materia_prima REAL,
    maquila REAL,
    empaque REAL,
    transporte REAL,
    administracion REAL,
    costo_total REAL
)
""")

# =====================================
# VENTAS
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER,
    precio_unitario REAL,
    total_venta REAL,
    costo_unitario REAL,
    utilidad_unitaria REAL,
    utilidad_total REAL,
    margen REAL
)
""")

# =====================================
# RENTABILIDAD
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS rentabilidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    producto TEXT,
    presentacion TEXT,
    ventas REAL,
    costos REAL,
    utilidad REAL,
    margen REAL
)
""")

# =====================================
# INVENTARIO INICIAL
# =====================================

cursor.execute("SELECT COUNT(*) FROM inventario")

if cursor.fetchone()[0] == 0:

    inventario_inicial = [

        ("Tradicional", "250 g", 100, "OK"),
        ("Tradicional", "500 g", 100, "OK"),
        ("Premium", "250 g", 100, "OK"),
        ("Premium", "500 g", 100, "OK")

    ]

    cursor.executemany("""
    INSERT INTO inventario
    (
        producto,
        presentacion,
        cantidad,
        estado
    )
    VALUES (?,?,?,?)
    """, inventario_inicial)

conexion.commit()
conexion.close()

print("BASE DE DATOS EMPRESARIAL V1 CREADA CORRECTAMENTE")
