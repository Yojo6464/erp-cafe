import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB = "erp_cafe.db"


# =========================
# CONEXION
# =========================

def conectar():
    return sqlite3.connect(DB)


# =========================
# GUARDAR
# =========================

def guardar():

    tipo = entry_tipo.get()
    proveedor = entry_proveedor.get()
    descripcion = entry_descripcion.get()
    unidad = entry_unidad.get()

    try:
        cantidad = int(entry_cantidad.get())
        costo_unitario = float(entry_costo.get())
    except:
        messagebox.showerror(
            "Error",
            "Cantidad y costo deben ser numéricos"
        )
        return

    observaciones = txt_obs.get("1.0", tk.END).strip()

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT saldo
        FROM almacen_empaques
        WHERE tipo_empaque=?
        ORDER BY id DESC
        LIMIT 1
    """, (tipo,))

    fila = cursor.fetchone()

    saldo_anterior = fila[0] if fila else 0
    saldo_nuevo = saldo_anterior + cantidad

    costo_total = cantidad * costo_unitario

    cursor.execute("""
        INSERT INTO almacen_empaques
        (
            fecha,
            tipo_empaque,
            proveedor,
            cantidad,
            saldo,
            costo_unitario,
            costo_total,
            observaciones,
            descripcion,
            unidad_medida
        )
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tipo,
        proveedor,
        cantidad,
        saldo_nuevo,
        costo_unitario,
        costo_total,
        observaciones,
        descripcion,
        unidad
    ))

    conexion.commit()
    conexion.close()

    cargar_tabla()
    limpiar()

    messagebox.showinfo(
        "Correcto",
        "Empaque registrado"
    )


# =========================
# LIMPIAR
# =========================

def limpiar():

    entry_tipo.delete(0, tk.END)
    entry_proveedor.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_costo.delete(0, tk.END)
    entry_descripcion.delete(0, tk.END)
    entry_unidad.delete(0, tk.END)

    txt_obs.delete("1.0", tk.END)


# =========================
# TABLA
# =========================

def cargar_tabla():

    for item in tabla.get_children():
        tabla.delete(item)

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
        id,
        fecha,
        tipo_empaque,
        cantidad,
        saldo,
        costo_total
        FROM almacen_empaques
        ORDER BY id DESC
    """)

    datos = cursor.fetchall()

    conexion.close()

    for fila in datos:
        tabla.insert("", tk.END, values=fila)


# =========================
# VENTANA
# =========================

ventana = tk.Tk()
ventana.title("ALMACEN DE EMPAQUES")
ventana.geometry("1200x700")

frame = tk.Frame(ventana)
frame.pack(pady=10)

tk.Label(frame, text="Tipo Empaque").grid(row=0, column=0)
entry_tipo = tk.Entry(frame, width=30)
entry_tipo.grid(row=0, column=1)

tk.Label(frame, text="Proveedor").grid(row=1, column=0)
entry_proveedor = tk.Entry(frame, width=30)
entry_proveedor.grid(row=1, column=1)

tk.Label(frame, text="Cantidad").grid(row=2, column=0)
entry_cantidad = tk.Entry(frame)
entry_cantidad.grid(row=2, column=1)

tk.Label(frame, text="Costo Unitario").grid(row=3, column=0)
entry_costo = tk.Entry(frame)
entry_costo.grid(row=3, column=1)

tk.Label(frame, text="Descripcion").grid(row=4, column=0)
entry_descripcion = tk.Entry(frame, width=40)
entry_descripcion.grid(row=4, column=1)

tk.Label(frame, text="Unidad Medida").grid(row=5, column=0)
entry_unidad = tk.Entry(frame)
entry_unidad.grid(row=5, column=1)

tk.Label(frame, text="Observaciones").grid(row=6, column=0)

txt_obs = tk.Text(frame, width=40, height=4)
txt_obs.grid(row=6, column=1)

tk.Button(
    frame,
    text="Guardar",
    bg="green",
    fg="white",
    command=guardar
).grid(row=7, column=1, pady=10)

# =========================
# TABLA
# =========================

columnas = (
    "ID",
    "FECHA",
    "TIPO",
    "CANTIDAD",
    "SALDO",
    "COSTO"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=20
)

for col in columnas:
    tabla.heading(col, text=col)

tabla.pack(fill="both", expand=True, padx=10, pady=10)

cargar_tabla()

ventana.mainloop()