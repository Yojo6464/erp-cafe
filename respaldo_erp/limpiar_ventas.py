import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
DELETE FROM ventas
WHERE costo_unitario IS NULL
""")

conexion.commit()

print("VENTAS ANTIGUAS ELIMINADAS")

conexion.close()