import tkinter as tk
from tkinter import ttk
import sqlite3

# ==================================
# CONEXION
# ==================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("SELECT COUNT(*) FROM ventas")
print("VENTAS REGISTRADAS:", cursor.fetchone()[0])

# ==================================
# FUNCIONES
# ==================================

def cargar_ranking():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        SUM(cantidad) as unidades,
        ROUND(SUM(total),2) as ventas
    FROM ventas
    GROUP BY producto,presentacion
    ORDER BY unidades DESC
    """)

    registros = cursor.fetchall()

    posicion = 1

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=(
                posicion,
                fila[0],
                fila[1],
                fila[2],
                fila[3]
            )
        )

        posicion += 1

    actualizar_resumen()

# ==================================
# RESUMEN
# ==================================

def actualizar_resumen():

    # PRODUCTO MAS VENDIDO

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        SUM(cantidad)
    FROM ventas
    GROUP BY producto,presentacion
    ORDER BY SUM(cantidad) DESC
    LIMIT 1
    """)

    top = cursor.fetchone()

    if top:

        lbl_top.config(
            text=f"{top[0]} {top[1]} ({top[2]} und)"
        )

    else:

        lbl_top.config(text="Sin ventas")

    # MAYOR FACTURACION

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        SUM(total)
    FROM ventas
    GROUP BY producto,presentacion
    ORDER BY SUM(total) DESC
    LIMIT 1
    """)

    mejor_venta = cursor.fetchone()

    if mejor_venta:

        lbl_facturacion.config(
            text=f"{mejor_venta[0]} {mejor_venta[1]}"
        )

    else:

        lbl_facturacion.config(text="Sin ventas")

# ==================================
# VENTANA
# ==================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Ranking Productos"
)

ventana.geometry("1100x650")

# ==================================
# TITULO
# ==================================

titulo = tk.Label(
    ventana,
    text="RANKING DE PRODUCTOS",
    font=("Arial",16,"bold")
)

titulo.pack(pady=10)

# ==================================
# PANEL SUPERIOR
# ==================================

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(
    frame,
    text="Producto Más Vendido"
).grid(row=0,column=0,padx=30)

lbl_top = tk.Label(
    frame,
    text="-",
    font=("Arial",11,"bold")
)

lbl_top.grid(row=1,column=0)

tk.Label(
    frame,
    text="Mayor Facturación"
).grid(row=0,column=1,padx=30)

lbl_facturacion = tk.Label(
    frame,
    text="-",
    font=("Arial",11,"bold")
)

lbl_facturacion.grid(row=1,column=1)

# ==================================
# TABLA
# ==================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "Ranking",
        "Producto",
        "Presentacion",
        "Cantidad",
        "Ventas"
    ),
    show="headings"
)

tabla.heading(
    "Ranking",
    text="#"
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

tabla.column("Ranking", width=70)
tabla.column("Producto", width=250)
tabla.column("Presentacion", width=150)
tabla.column("Cantidad", width=180)
tabla.column("Ventas", width=180)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# ==================================
# BOTON
# ==================================

tk.Button(
    ventana,
    text="Actualizar Ranking",
    width=20,
    command=cargar_ranking
).pack(pady=10)

# ==================================
# CARGA INICIAL
# ==================================

cargar_ranking()

ventana.mainloop()

conexion.close()