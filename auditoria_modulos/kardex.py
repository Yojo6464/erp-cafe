import tkinter as tk
from tkinter import ttk
import sqlite3

# =====================================
# CONEXION
# =====================================

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

# =====================================
# CONSULTAR
# =====================================

def consultar():

    for item in tabla.get_children():
        tabla.delete(item)

    producto = combo_producto.get()
    presentacion = combo_presentacion.get()

    sql = """
    SELECT
        fecha,
        producto,
        presentacion,
        movimiento,
        entrada,
        salida,
        saldo
    FROM kardex
    WHERE 1=1
    """

    parametros = []

    if producto:

        sql += " AND producto=?"
        parametros.append(producto)

    if presentacion:

        sql += " AND presentacion=?"
        parametros.append(presentacion)

    sql += " ORDER BY id"

    cursor.execute(sql, parametros)

    entradas = 0
    salidas = 0
    saldo_actual = 0

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

        entradas += float(fila[4])
        salidas += float(fila[5])
        saldo_actual = float(fila[6])

    lbl_entradas.config(
        text=f"{entradas:,.0f}"
    )

    lbl_salidas.config(
        text=f"{salidas:,.0f}"
    )

    lbl_saldo.config(
        text=f"{saldo_actual:,.0f}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Kardex"
)

ventana.geometry("1200x700")

# =====================================
# FILTROS
# =====================================

frame = tk.Frame(ventana)

frame.pack(
    pady=15
)

tk.Label(
    frame,
    text="Producto"
).grid(
    row=0,
    column=0,
    padx=5
)

combo_producto = ttk.Combobox(
    frame,
    values=[
        "",
        "Premium",
        "Tradicional",
        "Café Especial"
    ],
    width=20
)

combo_producto.grid(
    row=0,
    column=1
)

tk.Label(
    frame,
    text="Presentación"
).grid(
    row=0,
    column=2,
    padx=5
)

combo_presentacion = ttk.Combobox(
    frame,
    values=[
        "",
        "125 g",
        "250 g",
        "500 g",
        "1000 g"
    ],
    width=20
)

combo_presentacion.grid(
    row=0,
    column=3
)

tk.Button(
    frame,
    text="Consultar",
    command=consultar
).grid(
    row=0,
    column=4,
    padx=10
)

# =====================================
# TABLA
# =====================================

columnas = (
    "Fecha",
    "Producto",
    "Presentación",
    "Movimiento",
    "Entrada",
    "Salida",
    "Saldo"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings"
)

for col in columnas:

    tabla.heading(
        col,
        text=col
    )

    tabla.column(
        col,
        width=150
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# RESUMEN
# =====================================

frame_resumen = tk.Frame(
    ventana
)

frame_resumen.pack(
    pady=10
)

tk.Label(
    frame_resumen,
    text="Entradas:"
).grid(
    row=0,
    column=0,
    padx=10
)

lbl_entradas = tk.Label(
    frame_resumen,
    text="0",
    font=("Arial", 12, "bold")
)

lbl_entradas.grid(
    row=0,
    column=1
)

tk.Label(
    frame_resumen,
    text="Salidas:"
).grid(
    row=0,
    column=2,
    padx=10
)

lbl_salidas = tk.Label(
    frame_resumen,
    text="0",
    font=("Arial", 12, "bold")
)

lbl_salidas.grid(
    row=0,
    column=3
)

tk.Label(
    frame_resumen,
    text="Saldo:"
).grid(
    row=0,
    column=4,
    padx=10
)

lbl_saldo = tk.Label(
    frame_resumen,
    text="0",
    font=("Arial", 12, "bold")
)

lbl_saldo.grid(
    row=0,
    column=5
)

# =====================================
# CARGA INICIAL
# =====================================

consultar()

ventana.mainloop()

conexion.close()