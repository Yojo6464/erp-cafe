import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

try:
    cursor.execute("""
    ALTER TABLE almacen_empaques
    ADD COLUMN descripcion TEXT
    """)
    print("CAMPO DESCRIPCION AGREGADO")
except:
    print("CAMPO DESCRIPCION YA EXISTE")

try:
    cursor.execute("""
    ALTER TABLE almacen_empaques
    ADD COLUMN unidad_medida TEXT
    """)
    print("CAMPO UNIDAD_MEDIDA AGREGADO")
except:
    print("CAMPO UNIDAD_MEDIDA YA EXISTE")

conexion.commit()

print("\nALMACEN_EMPAQUES ACTUALIZADO")

conexion.close()