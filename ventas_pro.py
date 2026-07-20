import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas_pro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER,
    precio_unitario REAL,
    costo_unitario REAL,
    utilidad REAL,
    margen REAL,
    total_venta REAL
)
""")

conexion.commit()
def calcular_total():

try:

        cantidad = int(entry_cantidad.get())
        precio = float(entry_precio.get())

        total = cantidad * precio

        entry_total.config(state="normal")
        entry_total.delete(0, tk.END)
        entry_total.insert(0, str(round(total, 2)))
        entry_total.config(state="readonly")

   except:

    messagebox.showerror(
        "Error",
        "Verifique cantidad y precio."
    )
def guardar_venta():

    try:

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cliente = entry_cliente.get()

        producto = combo_producto.get()

        presentacion = combo_presentacion.get()

        cantidad = int(entry_cantidad.get())

        precio = float(entry_precio.get())

        total_venta = cantidad * precio       
        # BUSCAR COSTO
cursor.execute(...)
cursor.execute("""
SELECT costo_total
FROM costos
WHERE producto=? AND presentacion=?
ORDER BY id DESC
LIMIT 1
""",
(
    producto,
    presentacion
))

costo = cursor.fetchone()

if costo is None:

    messagebox.showerror(
        "Error",
        "No existe costo para este producto."
    )
    return

costo_unitario = costo[0]

utilidad_unitaria = precio - costo_unitario

utilidad_total = utilidad_unitaria * cantidad

margen = (
    utilidad_unitaria / precio
) * 100
# VERIFICAR INVENTARIO
cursor.execute()cursor.execute("""
SELECT costo_total
FROM costos
WHERE producto=? AND presentacion=?
ORDER BY id DESC
LIMIT 1
""",
(
    producto,
    presentacion
))

costo = cursor.fetchone()

if costo is None:

    messagebox.showerror(
        "Error",
        "No existe costo para este producto."
    )
    return

costo_unitario = costo[0]

utilidad_unitaria = precio - costo_unitario

utilidad_total = utilidad_unitaria * cantidad

margen = (
    utilidad_unitaria / precio
) * 100
cursor.execute("""
SELECT costo_total
FROM costos
WHERE producto=? AND presentacion=?
ORDER BY id DESC
LIMIT 1
""",
(
    producto,
    presentacion
))

costo = cursor.fetchone()

if costo is None:

    messagebox.showerror(
        "Error",
        "No existe costo para este producto."
    )
    return

costo_unitario = costo[0]

utilidad_unitaria = precio - costo_unitario

utilidad_total = utilidad_unitaria * cantidad

margen = (
    utilidad_unitaria / precio
) * 100
# GUARDAR VENTA
cursor.execute(cursor.execute("""
SELECT costo_total
FROM costos
WHERE producto=? AND presentacion=?
ORDER BY id DESC
LIMIT 1
""",
(
    producto,
    presentacion
))

costo = cursor.fetchone()

if costo is None:

    messagebox.showerror(
        "Error",
        "No existe costo para este producto."
    )
    return

costo_unitario = costo[0]

utilidad_unitaria = precio - costo_unitario

utilidad_total = utilidad_unitaria * cantidad

margen = (
    utilidad_unitaria / precio
) * 100)
