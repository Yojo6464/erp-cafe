import tkinter as tk
from tkinter import ttk
import sqlite3

# ==================================
# CONEXION
# ==================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# ==================================
# FUNCIONES
# ==================================

def cargar_resumen():

    try:

        cursor.execute("""
        SELECT
            IFNULL(SUM(total),0),
            IFNULL(SUM(costo_unitario * cantidad),0),
            IFNULL(SUM(utilidad_total),0)
        FROM ventas
        """)

        datos = cursor.fetchone()

        ventas = round(datos[0], 2)
        costos = round(datos[1], 2)
        utilidad = round(datos[2], 2)

        margen = 0

        if ventas > 0:

            margen = round(
                (utilidad / ventas) * 100,
                2
            )

        lbl_ventas.config(
            text=f"${ventas:,.0f}"
        )

        lbl_costos.config(
            text=f"${costos:,.0f}"
        )

        lbl_utilidad.config(
            text=f"${utilidad:,.0f}"
        )

        lbl_margen.config(
            text=f"{margen}%"
        )

    except Exception as e:

        print(e)

# ==================================

def cargar_detalle():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        SUM(cantidad),
        SUM(total),
        SUM(utilidad_total)
    FROM ventas
    GROUP BY producto,presentacion
    ORDER BY SUM(utilidad_total) DESC
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=(
                fila[0],
                fila[1],
                fila[2],
                f"${fila[3]:,.0f}",
                f"${fila[4]:,.0f}"
            )
        )

# ==================================
# VENTANA
# ==================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Rentabilidad"
)

ventana.geometry("1200x700")

# ==================================
# TITULO
# ==================================

titulo = tk.Label(
    ventana,
    text="ANALISIS DE RENTABILIDAD",
    font=("Arial",16,"bold")
)

titulo.pack(pady=10)

# ==================================
# RESUMEN
# ==================================

frame = tk.Frame(
    ventana
)

frame.pack(
    pady=10
)

# VENTAS

tk.Label(
    frame,
    text="Ventas Totales"
).grid(
    row=0,
    column=0,
    padx=20
)

lbl_ventas = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_ventas.grid(
    row=1,
    column=0
)

# COSTOS

tk.Label(
    frame,
    text="Costos Totales"
).grid(
    row=0,
    column=1,
    padx=20
)

lbl_costos = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_costos.grid(
    row=1,
    column=1
)

# UTILIDAD

tk.Label(
    frame,
    text="Utilidad Total"
).grid(
    row=0,
    column=2,
    padx=20
)

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_utilidad.grid(
    row=1,
    column=2
)

# MARGEN

tk.Label(
    frame,
    text="Margen %"
).grid(
    row=0,
    column=3,
    padx=20
)

lbl_margen = tk.Label(
    frame,
    text="0%"
)

lbl_margen.grid(
    row=1,
    column=3
)

# ==================================
# TABLA
# ==================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "Producto",
        "Presentacion",
        "Cantidad",
        "Ventas",
        "Utilidad"
    ),
    show="headings"
)

tabla.heading(
    "Producto",
    text="Producto"
)

tabla.heading(
    "Presentacion",
    text="Presentación"
)

tabla.heading(
    "Cantidad",
    text="Cantidad Vendida"
)

tabla.heading(
    "Ventas",
    text="Ventas"
)

tabla.heading(
    "Utilidad",
    text="Utilidad"
)

tabla.column(
    "Producto",
    width=250
)

tabla.column(
    "Presentacion",
    width=150
)

tabla.column(
    "Cantidad",
    width=150
)

tabla.column(
    "Ventas",
    width=180
)

tabla.column(
    "Utilidad",
    width=180
)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# ==================================
# CARGA INICIAL
# ==================================

cargar_resumen()
cargar_detalle()

ventana.mainloop()

conexion.close()