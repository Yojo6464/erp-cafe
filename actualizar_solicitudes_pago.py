import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:

    cursor.execute("""
    ALTER TABLE solicitudes_pago
    ADD COLUMN tipo_gasto TEXT
    """)

    conexion.commit()

    print("CAMPO TIPO_GASTO AGREGADO")

except Exception as e:

    print("YA EXISTE O ERROR:")
    print(e)

conexion.close()