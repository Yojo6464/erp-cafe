import tkinter as tk
from tkinter import ttk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def cargar_existencias():

    for fila in tabla.get_children():
        tabla.delete(fila)

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT DISTINCT producto
    FROM inventario_cafe
    ORDER BY producto
    """)

    productos = cursor.fetchall()

    for producto in productos:

        nombre = producto[0]

        cursor.execute("""
        SELECT IFNULL(SUM(cantidad),0)
        FROM inventario_cafe
        WHERE producto = ?
        AND tipo_movimiento = 'Entrada'
        """, (nombre,))

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""
        SELECT IFNULL(SUM(cantidad),0)
        FROM inventario_cafe
        WHERE producto = ?
        AND tipo_movimiento = 'Salida'
        """, (nombre,))

        salidas = float(cursor.fetchone()[0])

        existencia = entradas - salidas

        tabla.insert(
            "",
            "end",
            values=(
                nombre,
                f"{entradas:,.2f}",
                f"{salidas:,.2f}",
                f"{existencia:,.2f}"
            )
        )

    conexion.close()


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Existencias"
)

ventana.geometry("900x600")

titulo = tk.Label(
    ventana,
    text="EXISTENCIAS DE INVENTARIO",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

tabla = ttk.Treeview(
    ventana,
    columns=(
        "producto",
        "entradas",
        "salidas",
        "existencia"
    ),
    show="headings"
)

tabla.heading("producto", text="Producto")
tabla.heading("entradas", text="Entradas")
tabla.heading("salidas", text="Salidas")
tabla.heading("existencia", text="Existencia")

tabla.column("producto", width=250)
tabla.column("entradas", width=150)
tabla.column("salidas", width=150)
tabla.column("existencia", width=150)

tabla.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar",
    width=20,
    command=cargar_existencias
)

btn_actualizar.pack(pady=10)

cargar_existencias()

ventana.mainloop()