import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:

    cursor.execute("""
    ALTER TABLE movimientos_bancos
    ADD COLUMN autorizado_por TEXT
    """)

    conexion.commit()

    print("CAMPO AUTORIZADO_POR AGREGADO")

except Exception as e:

    print(e)

conexion.close()