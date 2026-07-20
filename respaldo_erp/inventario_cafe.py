import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# CREAR TABLA
# =====================================

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario_cafe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    producto TEXT,
    tipo_movimiento TEXT,
    cantidad REAL,
    costo_unitario REAL,
    observaciones TEXT
)
""")

conexion.commit()
conexion.close()

# =====================================
# GUARDAR MOVIMIENTO
# =====================================

def guardar_movimiento():

    try:

        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO inventario_cafe
        (
            fecha,
            producto,
            tipo_movimiento,
            cantidad,
            costo_unitario,
            observaciones
        )
        VALUES
        (?,?,?,?,?,?)
        """,
        (
            entry_fecha.get(),
            combo_producto.get(),
            combo_tipo.get(),
            float(entry_cantidad.get()),
            float(entry_costo.get()),
            entry_observaciones.get()
        ))

        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Inventario",
            "Movimiento guardado correctamente"
        )

        limpiar()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# LIMPIAR
# =====================================

def limpiar():

    entry_fecha.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_costo.delete(0, tk.END)
    entry_observaciones.delete(0, tk.END)

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Inventario"
)

ventana.geometry("750x650")

titulo = tk.Label(
    ventana,
    text="INVENTARIO DE CAFÉ",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=10)

# FECHA

tk.Label(
    frame,
    text="Fecha"
).grid(row=0,column=0,padx=10,pady=10,sticky="w")

entry_fecha = tk.Entry(frame,width=35)
entry_fecha.grid(row=0,column=1)

# PRODUCTO

tk.Label(
    frame,
    text="Producto"
).grid(row=1,column=0,padx=10,pady=10,sticky="w")

combo_producto = ttk.Combobox(
    frame,
    width=32,
    state="readonly"
)

combo_producto["values"] = (
    "Cafe Pergamino",
    "Cafe Verde",
    "Cafe Tostado",
    "Cafe Molido",
    "Empaques"
)

combo_producto.grid(row=1,column=1)

# TIPO

tk.Label(
    frame,
    text="Tipo Movimiento"
).grid(row=2,column=0,padx=10,pady=10,sticky="w")

combo_tipo = ttk.Combobox(
    frame,
    width=32,
    state="readonly"
)

combo_tipo["values"] = (
    "Entrada",
    "Salida"
)

combo_tipo.grid(row=2,column=1)

# CANTIDAD

tk.Label(
    frame,
    text="Cantidad"
).grid(row=3,column=0,padx=10,pady=10,sticky="w")

entry_cantidad = tk.Entry(frame,width=35)
entry_cantidad.grid(row=3,column=1)

# COSTO

tk.Label(
    frame,
    text="Costo Unitario"
).grid(row=4,column=0,padx=10,pady=10,sticky="w")

entry_costo = tk.Entry(frame,width=35)
entry_costo.grid(row=4,column=1)

# OBSERVACIONES

tk.Label(
    frame,
    text="Observaciones"
).grid(row=5,column=0,padx=10,pady=10,sticky="w")

entry_observaciones = tk.Entry(frame,width=35)
entry_observaciones.grid(row=5,column=1)

# BOTON

btn_guardar = tk.Button(
    ventana,
    text="Guardar Movimiento",
    width=25,
    height=2,
    command=guardar_movimiento
)

btn_guardar.pack(pady=30)

ventana.mainloop()