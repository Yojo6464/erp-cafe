import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ==========================
# BASE DE DATOS
# ==========================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER
)
""")

conexion.commit()

# ==========================
# FUNCIONES
# ==========================

def agregar_inventario():

    producto = combo_producto.get()
    presentacion = combo_presentacion.get()

    if not producto:
        messagebox.showerror(
            "Error",
            "Seleccione un producto."
        )
        return

    if not presentacion:
        messagebox.showerror(
            "Error",
            "Seleccione una presentación."
        )
        return

    try:
        cantidad = int(entry_cantidad.get())
    except:
        messagebox.showerror(
            "Error",
            "Ingrese una cantidad válida."
        )
        return

    cursor.execute("""
    SELECT id, cantidad
    FROM inventario
    WHERE producto=? AND presentacion=?
    """, (producto, presentacion))

    resultado = cursor.fetchone()

    if resultado:

        nuevo_stock = resultado[1] + cantidad

        cursor.execute("""
        UPDATE inventario
        SET cantidad=?
        WHERE id=?
        """, (
            nuevo_stock,
            resultado[0]
        ))

    else:

        cursor.execute("""
        INSERT INTO inventario
        (
            producto,
            presentacion,
            cantidad
        )
        VALUES (?,?,?)
        """, (
            producto,
            presentacion,
            cantidad
        ))

    conexion.commit()

    messagebox.showinfo(
        "Éxito",
        "Inventario actualizado correctamente."
    )

    entry_cantidad.delete(0, tk.END)

    mostrar_inventario()


def mostrar_inventario():

    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        cantidad
    FROM inventario
    ORDER BY producto, presentacion
    """)

    registros = cursor.fetchall()

    for fila in registros:

        estado = "OK"

        if fila[2] <= 10:
            estado = "BAJO"

        tabla.insert(
            "",
            tk.END,
            values=(
                fila[0],
                fila[1],
                fila[2],
                estado
            )
        )

# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Inventario")
ventana.geometry("850x550")

# ==========================
# PRODUCTO
# ==========================

tk.Label(
    ventana,
    text="Producto"
).pack(pady=5)

combo_producto = ttk.Combobox(
    ventana,
    values=[
        "Café Especial",
        "Café Premium",
        "Café Tradicional"
    ],
    state="readonly"
)

combo_producto.pack()

# ==========================
# PRESENTACIÓN
# ==========================

tk.Label(
    ventana,
    text="Presentación"
).pack(pady=5)

combo_presentacion = ttk.Combobox(
    ventana,
    values=[
        "125 g",
        "250 g",
        "500 g",
        "1000 g"
    ],
    state="readonly"
)

combo_presentacion.pack()

# ==========================
# CANTIDAD
# ==========================

tk.Label(
    ventana,
    text="Cantidad a ingresar"
).pack(pady=5)

entry_cantidad = tk.Entry(
    ventana
)

entry_cantidad.pack()

# ==========================
# BOTÓN
# ==========================

tk.Button(
    ventana,
    text="Agregar Inventario",
    width=25,
    command=agregar_inventario
).pack(pady=15)

# ==========================
# TABLA
# ==========================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "Producto",
        "Presentación",
        "Cantidad",
        "Estado"
    ),
    show="headings"
)

tabla.heading(
    "Producto",
    text="Producto"
)

tabla.heading(
    "Presentación",
    text="Presentación"
)

tabla.heading(
    "Cantidad",
    text="Cantidad"
)

tabla.heading(
    "Estado",
    text="Estado"
)

tabla.column(
    "Producto",
    width=200
)

tabla.column(
    "Presentación",
    width=120
)

tabla.column(
    "Cantidad",
    width=120
)

tabla.column(
    "Estado",
    width=100
)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

mostrar_inventario()

ventana.mainloop()

conexion.close()