import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# =====================================
# CONFIGURACIÓN
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, "erp_cafe.db")

# =====================================
# BASE DE DATOS
# =====================================

def obtener_conexion():
    return sqlite3.connect(RUTA_DB)


def crear_tabla():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
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

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("""
        SELECT id, nombre, telefono, ciudad, correo
        FROM proveedores
        ORDER BY nombre
        """)
        filas = cursor.fetchall()

    for fila in filas:
        tabla.insert("", tk.END, values=fila)


def limpiar_campos():
    entry_nombre.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_ciudad.delete(0, tk.END)
    entry_correo.delete(0, tk.END)
    entry_nombre.focus()


def guardar_proveedor():
    nombre = entry_nombre.get().strip()
    telefono = entry_telefono.get().strip()
    ciudad = entry_ciudad.get().strip()
    correo = entry_correo.get().strip()

    if not nombre:
        messagebox.showerror("Error", "Ingrese el nombre del proveedor.")
        entry_nombre.focus()
        return

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute("""
            INSERT INTO proveedores(nombre, telefono, ciudad, correo)
            VALUES(?,?,?,?)
            """, (nombre, telefono, ciudad, correo))
            conexion.commit()

        messagebox.showinfo("OK", "Proveedor registrado correctamente.")
        limpiar_campos()
        mostrar_proveedores()

    except sqlite3.Error as e:
        messagebox.showerror("Error de base de datos", f"No se pudo guardar el proveedor:\n{e}")


def eliminar_proveedor():
    seleccionado = tabla.selection()

    if not seleccionado:
        messagebox.showwarning("Atención", "Seleccione un proveedor para eliminar.")
        return

    valores = tabla.item(seleccionado[0], "values")
    proveedor_id = valores[0]
    nombre = valores[1]

    confirmar = messagebox.askyesno(
        "Confirmar eliminación",
        f"¿Desea eliminar el proveedor '{nombre}'?"
    )

    if not confirmar:
        return

    try:
        with obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
            conexion.commit()

        mostrar_proveedores()
        messagebox.showinfo("OK", "Proveedor eliminado correctamente.")

    except sqlite3.Error as e:
        messagebox.showerror("Error de base de datos", f"No se pudo eliminar el proveedor:\n{e}")

# =====================================
# VENTANA
# =====================================

crear_tabla()

ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Proveedores")
ventana.geometry("1100x700")
ventana.configure(bg="#E9EEF4")

titulo = tk.Label(
    ventana,
    text="GESTIÓN DE PROVEEDORES",
    font=("Arial", 18, "bold"),
    bg="#E9EEF4",
    fg="#0F4C81"
)
titulo.pack(pady=15)

# =====================================
# FORMULARIO
# =====================================

frame = tk.LabelFrame(
    ventana,
    text="Datos del proveedor",
    font=("Arial", 11, "bold"),
    bg="white",
    padx=15,
    pady=12
)
frame.pack(fill="x", padx=20, pady=10)

labels = ["Nombre", "Teléfono", "Ciudad", "Correo"]
for i, texto in enumerate(labels):
    tk.Label(frame, text=texto, bg="white").grid(row=0, column=i, padx=5, pady=3, sticky="w")

entry_nombre = tk.Entry(frame, width=30)
entry_telefono = tk.Entry(frame, width=20)
entry_ciudad = tk.Entry(frame, width=20)
entry_correo = tk.Entry(frame, width=35)

entry_nombre.grid(row=1, column=0, padx=5, pady=3)
entry_telefono.grid(row=1, column=1, padx=5, pady=3)
entry_ciudad.grid(row=1, column=2, padx=5, pady=3)
entry_correo.grid(row=1, column=3, padx=5, pady=3)

frame_botones = tk.Frame(ventana, bg="#E9EEF4")
frame_botones.pack(pady=10)

tk.Button(frame_botones, text="Guardar Proveedor", width=22, command=guardar_proveedor).grid(row=0, column=0, padx=6)
tk.Button(frame_botones, text="Eliminar Seleccionado", width=22, command=eliminar_proveedor).grid(row=0, column=1, padx=6)
tk.Button(frame_botones, text="Limpiar", width=15, command=limpiar_campos).grid(row=0, column=2, padx=6)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=("ID", "Nombre", "Telefono", "Ciudad", "Correo"),
    show="headings"
)

anchos = {
    "ID": 60,
    "Nombre": 280,
    "Telefono": 150,
    "Ciudad": 180,
    "Correo": 280
}

for col in ("ID", "Nombre", "Telefono", "Ciudad", "Correo"):
    tabla.heading(col, text=col)
    tabla.column(col, width=anchos[col], anchor="center")

tabla.pack(fill="both", expand=True, padx=20, pady=10)

mostrar_proveedores()
entry_nombre.focus()
ventana.mainloop()
