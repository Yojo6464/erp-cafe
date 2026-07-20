import sqlite3

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tablas = cursor.fetchall()

print("\nTABLAS EN ERP_CAFE.DB\n")

for tabla in tablas:
    print(tabla[0])

conexion.close()
exit()
quit()
