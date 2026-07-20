import tkinter as tk
from tkinter import messagebox
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# CREAR TABLA SI NO EXISTE
# =====================================

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produccion_cafe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    lote TEXT,
    pergamino REAL,
    cafe_verde REAL,
    cafe_tostado REAL,
    merma REAL,
    observaciones TEXT
)
""")

conexion.commit()
conexion.close()


# =====================================
# GUARDAR PRODUCCION
# =====================================

def guardar_produccion():

    try:

        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO produccion_cafe
        (
            fecha,
            lote,
            pergamino,
            cafe_verde,
            cafe_tostado,
            merma,
            observaciones
        )
        VALUES
        (?,?,?,?,?,?,?)
        """,
        (
            entry_fecha.get(),
            entry_lote.get(),
            float(entry_pergamino.get()),
            float(entry_verde.get()),
            float(entry_tostado.get()),
            float(entry_merma.get()),
            entry_observaciones.get()
        ))

        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Producción",
            "Registro guardado correctamente"
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
    entry_lote.delete(0, tk.END)
    entry_pergamino.delete(0, tk.END)
    entry_verde.delete(0, tk.END)
    entry_tostado.delete(0, tk.END)
    entry_merma.delete(0, tk.END)
    entry_observaciones.delete(0, tk.END)


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Producción"
)

ventana.geometry("700x600")


titulo = tk.Label(
    ventana,
    text="PRODUCCIÓN DE CAFÉ",
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

entry_fecha = tk.Entry(frame,width=30)
entry_fecha.grid(row=0,column=1)


# LOTE

tk.Label(
    frame,
    text="Lote"
).grid(row=1,column=0,padx=10,pady=10,sticky="w")

entry_lote = tk.Entry(frame,width=30)
entry_lote.grid(row=1,column=1)


# PERGAMINO

tk.Label(
    frame,
    text="Pergamino Ingresado (kg)"
).grid(row=2,column=0,padx=10,pady=10,sticky="w")

entry_pergamino = tk.Entry(frame,width=30)
entry_pergamino.grid(row=2,column=1)


# VERDE

tk.Label(
    frame,
    text="Café Verde Obtenido (kg)"
).grid(row=3,column=0,padx=10,pady=10,sticky="w")

entry_verde = tk.Entry(frame,width=30)
entry_verde.grid(row=3,column=1)


# TOSTADO

tk.Label(
    frame,
    text="Café Tostado Obtenido (kg)"
).grid(row=4,column=0,padx=10,pady=10,sticky="w")

entry_tostado = tk.Entry(frame,width=30)
entry_tostado.grid(row=4,column=1)


# MERMA

tk.Label(
    frame,
    text="Merma (kg)"
).grid(row=5,column=0,padx=10,pady=10,sticky="w")

entry_merma = tk.Entry(frame,width=30)
entry_merma.grid(row=5,column=1)


# OBSERVACIONES

tk.Label(
    frame,
    text="Observaciones"
).grid(row=6,column=0,padx=10,pady=10,sticky="w")

entry_observaciones = tk.Entry(frame,width=30)
entry_observaciones.grid(row=6,column=1)


# BOTON

btn_guardar = tk.Button(
    ventana,
    text="Guardar Producción",
    width=25,
    height=2,
    command=guardar_produccion
)

btn_guardar.pack(pady=30)

ventana.mainloop()