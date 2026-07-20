import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:

    cursor.execute("""
    ALTER TABLE ventas
    ADD COLUMN costo_unitario REAL
    """)

except:
    pass

try:

    cursor.execute("""
    ALTER TABLE ventas
    ADD COLUMN utilidad_total REAL
    """)

except:
    pass

try:

    cursor.execute("""
    ALTER TABLE ventas
    ADD COLUMN margen REAL
    """)

except:
    pass

conexion.commit()

cursor.execute(
    "PRAGMA table_info(ventas)"
)

for campo in cursor.fetchall():
    print(campo)

conexion.close()

print("TABLA ACTUALIZADA")