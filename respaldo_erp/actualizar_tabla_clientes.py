import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:
    cursor.execute("""
    ALTER TABLE clientes
    ADD COLUMN fecha_registro TEXT
    """)
except:
    pass

try:
    cursor.execute("""
    ALTER TABLE clientes
    ADD COLUMN telefono TEXT
    """)
except:
    pass

try:
    cursor.execute("""
    ALTER TABLE clientes
    ADD COLUMN ciudad TEXT
    """)
except:
    pass

try:
    cursor.execute("""
    ALTER TABLE clientes
    ADD COLUMN correo TEXT
    """)
except:
    pass

conexion.commit()

cursor.execute(
    "PRAGMA table_info(clientes)"
)

for campo in cursor.fetchall():
    print(campo)

conexion.close()

print("TABLA CLIENTES ACTUALIZADA")