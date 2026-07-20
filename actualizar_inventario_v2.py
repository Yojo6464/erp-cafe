import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

campos = [
    ("lote", "TEXT"),
    ("costo_unitario", "REAL"),
    ("fecha_ingreso", "TEXT")
]

for nombre, tipo in campos:

    try:

        cursor.execute(
            f"ALTER TABLE inventario ADD COLUMN {nombre} {tipo}"
        )

        print(
            f"CAMPO {nombre.upper()} AGREGADO"
        )

    except Exception:

        print(
            f"CAMPO {nombre.upper()} YA EXISTE"
        )

conexion.commit()

conexion.close()

print(
    "\nINVENTARIO V2 ACTUALIZADO"
)