import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:

    cursor.execute("""
    ALTER TABLE inventario
    ADD COLUMN numero_despacho TEXT
    """)

    print(
        "CAMPO NUMERO_DESPACHO AGREGADO"
    )

except:

    print(
        "CAMPO NUMERO_DESPACHO YA EXISTE"
    )

conexion.commit()

print(
    "\nINVENTARIO V3 ACTUALIZADO"
)

conexion.close()