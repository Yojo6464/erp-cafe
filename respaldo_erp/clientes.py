import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

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
CREATE TABLE IF NOT EXISTS clientes
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_registro TEXT,
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

def guardar_cliente():

    try:

        nombre = entry_nombre.get().strip()
        telefono = entry_telefono.get().strip()
        ciudad = entry_ciudad.get().strip()
        correo = entry_correo.get().strip()

        if nombre == "":
            messagebox.showerror(
                "Error",
                "Debe ingresar el nombre."
            )
            return

        fecha = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
        INSERT INTO clientes
        (
            fecha_registro,
            nombre,
            telefono,
            ciudad,
            correo
        )
        VALUES (?,?,?,?,?)
        """,
        (
            fecha,
            nombre,
            telefono,
            ciudad,
            correo
        ))

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Cliente registrado."
        )

        entry_nombre.delete(0, tk.END)
        entry_telefono.delete(0, tk.END)
        entry_ciudad.delete(0, tk.END)
        entry_correo.delete(0, tk.END)

        mostrar_clientes()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================

def mostrar_clientes():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        nombre,
        telefono,
        ciudad,
        correo
    FROM clientes
    ORDER BY nombre
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Clientes"
)

ventana.geometry("1100x650")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="GESTION DE CLIENTES",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(
    frame,
    text="Nombre"
).grid(row=0,column=0,padx=10,pady=5)

entry_nombre = tk.Entry(
    frame,
    width=30
)

entry_nombre.grid(row=1,column=0)

tk.Label(
    frame,
    text="Teléfono"
).grid(row=0,column=1,padx=10,pady=5)

entry_telefono = tk.Entry(
    frame,
    width=20
)

entry_telefono.grid(row=1,column=1)

tk.Label(
    frame,
    text="Ciudad"
).grid(row=0,column=2,padx=10,pady=5)

entry_ciudad = tk.Entry(
    frame,
    width=20
)

entry_ciudad.grid(row=1,column=2)

tk.Label(
    frame,
    text="Correo"
).grid(row=0,column=3,padx=10,pady=5)

entry_correo = tk.Entry(
    frame,
    width=30
)

entry_correo.grid(row=1,column=3)

tk.Button(
    ventana,
    text="Guardar Cliente",
    width=25,
    command=guardar_cliente
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

tabla.heading("ID", text="ID")
tabla.heading("Nombre", text="Nombre")
tabla.heading("Telefono", text="Teléfono")
tabla.heading("Ciudad", text="Ciudad")
tabla.heading("Correo", text="Correo")

tabla.column("ID", width=70)
tabla.column("Nombre", width=250)
tabla.column("Telefono", width=150)
tabla.column("Ciudad", width=150)
tabla.column("Correo", width=250)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# CARGA INICIAL
# =====================================

mostrar_clientes()

ventana.mainloop()

conexion.close()