import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:

    cursor.execute("""
    ALTER TABLE despachos_maquila
    ADD COLUMN cantidad_cajas INTEGER
    """)

    print(
        "CAMPO CANTIDAD_CAJAS AGREGADO"
    )

except:

    print(
        "CAMPO CANTIDAD_CAJAS YA EXISTE"
    )

try:

    cursor.execute("""
    ALTER TABLE despachos_maquila
    ADD COLUMN otros_insumos TEXT
    """)

    print(
        "CAMPO OTROS_INSUMOS AGREGADO"
    )

except:

    print(
        "CAMPO OTROS_INSUMOS YA EXISTE"
    )

conexion.commit()

print(
    "\nDESPACHOS_MAQUILA ACTUALIZADA"
)

conexion.close()