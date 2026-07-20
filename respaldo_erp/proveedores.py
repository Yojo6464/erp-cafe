import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# TABLA
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS proveedores(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    telefono TEXT,
    ciudad TEXT,
    correo TEXT
)
""")

conexion.commit()

# =====================================
# FUNCIONES
# =====================================

def mostrar_proveedores():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        nombre,
        telefono,
        ciudad,
        correo
    FROM proveedores
    ORDER BY nombre
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def guardar_proveedor():

    nombre = entry_nombre.get().strip()
    telefono = entry_telefono.get().strip()
    ciudad = entry_ciudad.get().strip()
    correo = entry_correo.get().strip()

    if nombre == "":

        messagebox.showerror(
            "Error",
            "Ingrese nombre."
        )
        return

    cursor.execute("""
    INSERT INTO proveedores(
        nombre,
        telefono,
        ciudad,
        correo
    )
    VALUES(?,?,?,?)
    """,
    (
        nombre,
        telefono,
        ciudad,
        correo
    ))

    conexion.commit()

    messagebox.showinfo(
        "OK",
        "Proveedor registrado."
    )

    entry_nombre.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_ciudad.delete(0, tk.END)
    entry_correo.delete(0, tk.END)

    mostrar_proveedores()

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Proveedores"
)

ventana.geometry("1100x700")

titulo = tk.Label(
    ventana,
    text="GESTIÓN DE PROVEEDORES",
    font=("Arial",18,"bold")
)

titulo.pack(pady=15)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)
frame.pack(pady=10)

tk.Label(
    frame,
    text="Nombre"
).grid(row=0,column=0,padx=5)

entry_nombre = tk.Entry(
    frame,
    width=25
)

entry_nombre.grid(row=1,column=0)

tk.Label(
    frame,
    text="Teléfono"
).grid(row=0,column=1,padx=5)

entry_telefono = tk.Entry(
    frame,
    width=20
)

entry_telefono.grid(row=1,column=1)

tk.Label(
    frame,
    text="Ciudad"
).grid(row=0,column=2,padx=5)

entry_ciudad = tk.Entry(
    frame,
    width=20
)

entry_ciudad.grid(row=1,column=2)

tk.Label(
    frame,
    text="Correo"
).grid(row=0,column=3,padx=5)

entry_correo = tk.Entry(
    frame,
    width=30
)

entry_correo.grid(row=1,column=3)

tk.Button(
    ventana,
    text="Guardar Proveedor",
    width=25,
    command=guardar_proveedor
).pack(pady=10)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Nombre",
        "Telefono",
        "Ciudad",
        "Correo"
    ),
    show="headings"
)

for col in (
    "ID",
    "Nombre",
    "Telefono",
    "Ciudad",
    "Correo"
):
    tabla.heading(
        col,
        text=col
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

mostrar_proveedores()

ventana.mainloop()

conexion.close()