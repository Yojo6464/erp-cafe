import sqlite3

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

cursor.execute("""
SELECT
    IFNULL(SUM(total),0),
    IFNULL(SUM(utilidad_total),0)
FROM ventas
""")

print(cursor.fetchone())

conexion.close()