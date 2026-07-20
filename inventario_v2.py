import tkinter as tk
from tkinter import ttk
import sqlite3

DB = "erp_cafe.db"


def conectar():
    return sqlite3.connect(DB)


def cargar_inventario():

    for item in tabla.get_children():
        tabla.delete(item)

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT
            producto,
            presentacion,
            cantidad,
            lote,
            costo_unitario,
            fecha_ingreso
        FROM inventario
        ORDER BY producto, presentacion
    """)

    total_bolsas = 0
    total_valor = 0

    for fila in cur.fetchall():

        producto = fila[0]
        presentacion = fila[1]
        cantidad = fila[2]
        lote = fila[3]
        costo = fila[4] or 0
        fecha = fila[5]

        valor = cantidad * costo

        total_bolsas += cantidad
        total_valor += valor

        tabla.insert(
            "",
            tk.END,
            values=(
                producto,
                presentacion,
                cantidad,
                lote,
                round(costo, 2),
                round(valor, 2),
                fecha
            )
        )

    lbl_total_bolsas.config(
        text=f"Total Bolsas: {total_bolsas:,.0f}"
    )

    lbl_total_valor.config(
        text=f"Valor Inventario: ${total_valor:,.0f}"
    )

    con.close()


ventana = tk.Tk()
ventana.title(
    "ERP Café Alto de la Cruz - Inventario"
)

ventana.geometry("1200x700")

frame_top = tk.Frame(ventana)
frame_top.pack(fill="x", pady=10)

tk.Button(
    frame_top,
    text="Actualizar",
    bg="green",
    fg="white",
    command=cargar_inventario
).pack(side="left", padx=10)

lbl_total_bolsas = tk.Label(
    frame_top,
    text="Total Bolsas: 0",
    font=("Arial", 11, "bold")
)

lbl_total_bolsas.pack(
    side="left",
    padx=20
)

lbl_total_valor = tk.Label(
    frame_top,
    text="Valor Inventario: $0",
    font=("Arial", 11, "bold")
)

lbl_total_valor.pack(
    side="left",
    padx=20
)

columnas = (
    "Producto",
    "Presentación",
    "Cantidad",
    "Lote",
    "Costo Unitario",
    "Valor Inventario",
    "Fecha Ingreso"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=25
)

for col in columnas:

    tabla.heading(col, text=col)

    tabla.column(
        col,
        width=150,
        anchor="center"
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

cargar_inventario()

ventana.mainloop()