import sqlite3
from datetime import datetime

con = sqlite3.connect("erp_cafe.db")
cur = con.cursor()

cur.execute("""
INSERT INTO kardex
(
    fecha,
    producto,
    presentacion,
    movimiento,
    entrada,
    salida,
    saldo,
    costo_unitario,
    lote,
    origen,
    observaciones
)
VALUES
(?,?,?,?,?,?,?,?,?,?,?)
""",
(
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "PRUEBA",
    "250 g",
    "ENTRADA",
    1,
    0,
    1,
    1000,
    "TEST",
    "PRUEBA",
    "Registro manual"
))

con.commit()
con.close()

print("KARDEX OK")