import sqlite3
import os

RUTA_DB = r"c:\Users\jrive\visual\erp_cafe.db"

# Elimina la base anterior si existe
if os.path.exists(RUTA_DB):
    os.remove(RUTA_DB)

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# CLIENTES
cursor.execute("""
CREATE TABLE clientes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
)
""")

# INVENTARIO
cursor.execute("""
CREATE TABLE inventario(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad REAL
)
""")

# VENTAS
cursor.execute("""
CREATE TABLE ventas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    producto TEXT,
    presentacion TEXT,
    cantidad REAL,
    precio_unitario REAL,
    total REAL
)
""")

conexion.commit()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

print("TABLAS:")
print(cursor.fetchall())

conexion.close()

print("BASE:", RUTA_DB)
print("TAMAÑO:", os.path.getsize(RUTA_DB))