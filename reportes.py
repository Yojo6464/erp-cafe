import tkinter as tk
from tkinter import ttk
import sqlite3

# =====================================
# CONEXION
# =====================================

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Reportes"
)

ventana.geometry("1200x700")

titulo = tk.Label(
    ventana,
    text="REPORTE INVENTARIO VALORIZADO",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# TABLA
# =====================================

columnas = (
    "Producto",
    "Presentacion",
    "Cantidad",
    "Costo Unitario",
    "Valor Total"
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
        width=200
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# CARGAR DATOS
# =====================================

cursor.execute("""
SELECT
    producto,
    presentacion,
    cantidad,
    costo_unitario
FROM inventario
ORDER BY producto
""")

total_inventario = 0

for fila in cursor.fetchall():

   producto = fila[0]
presentacion = fila[1]
cantidad = float(fila[2] or 0)
costo_unitario = float(fila[3] or 0)
valor_total = (

        cantidad *
        costo_unitario
    )

total_inventario += valor_total

tabla.insert(
        "",
        tk.END,
        values=(
            producto,
            presentacion,
            cantidad,
            f"${costo_unitario:,.0f}",
            f"${valor_total:,.0f}"
        )
    )

# =====================================
# TOTAL
# =====================================

lbl_total = tk.Label(
    ventana,
    text=f"Valor Total Inventario: ${total_inventario:,.0f}",
    font=("Arial",14,"bold")
)

lbl_total.pack(pady=10)

# =====================================
# INICIO
# =====================================

ventana.mainloop()

conexion.close()