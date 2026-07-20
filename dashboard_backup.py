import tkinter as tk
from tkinter import ttk
import sqlite3

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# FUNCIONES
# =====================================

def cargar_indicadores():

    try:

        cursor.execute("""
        SELECT
            IFNULL(SUM(total),0),
            IFNULL(SUM(utilidad_total),0)
        FROM ventas
        """)

        datos = cursor.fetchone()

        ventas = round(datos[0], 2)
        utilidad = round(datos[1], 2)

        lbl_ventas.config(
            text=f"${ventas:,.0f}"
        )

        lbl_utilidad.config(
            text=f"${utilidad:,.0f}"
        )

    except:

        lbl_ventas.config(text="$0")
        lbl_utilidad.config(text="$0")

    try:

        cursor.execute("""
        SELECT COUNT(*)
        FROM clientes
        """)

        clientes = cursor.fetchone()[0]

        lbl_clientes.config(
            text=str(clientes)
        )

    except:

        lbl_clientes.config(text="0")

    try:

        cursor.execute("""
        SELECT IFNULL(SUM(saldo),0)
        FROM cuentas_cobrar
        WHERE estado='PENDIENTE'
        """)

        saldo = cursor.fetchone()[0]

        lbl_cxc.config(
            text=f"${saldo:,.0f}"
        )

    except:

        lbl_cxc.config(text="$0")

    try:

        cursor.execute("""
        SELECT IFNULL(SUM(cantidad),0)
        FROM inventario
        """)

        stock = cursor.fetchone()[0]

        lbl_stock.config(
            text=f"{stock:,.0f}"
        )

    except:

        lbl_stock.config(text="0")

    try:

        cursor.execute("""
        SELECT
            producto,
            SUM(cantidad)
        FROM ventas
        GROUP BY producto
        ORDER BY SUM(cantidad) DESC
        LIMIT 1
        """)

        dato = cursor.fetchone()

        if dato:
            lbl_top.config(
                text=f"{dato[0]} ({dato[1]})"
            )
        else:
            lbl_top.config(
                text="Sin ventas"
            )

    except:

        lbl_top.config(
            text="Sin datos"
        )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard"
)

ventana.geometry("1200x700")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="DASHBOARD GERENCIAL",
    font=("Arial", 20, "bold")
)

titulo.pack(pady=20)

# =====================================
# INDICADORES
# =====================================

frame = tk.Frame(
    ventana
)

frame.pack(pady=20)

# Ventas

tk.Label(
    frame,
    text="Ventas Totales",
    font=("Arial", 11)
).grid(row=0, column=0, padx=30)

lbl_ventas = tk.Label(
    frame,
    text="$0",
    font=("Arial", 14, "bold")
)

lbl_ventas.grid(row=1, column=0)

# Utilidad

tk.Label(
    frame,
    text="Utilidad Total",
    font=("Arial", 11)
).grid(row=0, column=1, padx=30)

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial", 14, "bold")
)

lbl_utilidad.grid(row=1, column=1)

# Clientes

tk.Label(
    frame,
    text="Clientes",
    font=("Arial", 11)
).grid(row=0, column=2, padx=30)

lbl_clientes = tk.Label(
    frame,
    text="0",
    font=("Arial", 14, "bold")
)

lbl_clientes.grid(row=1, column=2)

# Cuentas por Cobrar

tk.Label(
    frame,
    text="Cuentas por Cobrar",
    font=("Arial", 11)
).grid(row=0, column=3, padx=30)

lbl_cxc = tk.Label(
    frame,
    text="$0",
    font=("Arial", 14, "bold")
)

lbl_cxc.grid(row=1, column=3)

# Stock

tk.Label(
    frame,
    text="Stock Total",
    font=("Arial", 11)
).grid(row=0, column=4, padx=30)

lbl_stock = tk.Label(
    frame,
    text="0",
    font=("Arial", 14, "bold")
)

lbl_stock.grid(row=1, column=4)

# Producto Top

tk.Label(
    ventana,
    text="Producto Más Vendido",
    font=("Arial", 12)
).pack(pady=10)

lbl_top = tk.Label(
    ventana,
    text="-",
    font=("Arial", 14, "bold")
)

lbl_top.pack()

# =====================================
# BOTON ACTUALIZAR
# =====================================

tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=30,
    command=cargar_indicadores
).pack(pady=25)

# =====================================
# TABLA RESUMEN VENTAS
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "Producto",
        "Cantidad",
        "Ventas"
    ),
    show="headings"
)

tabla.heading(
    "Producto",
    text="Producto"
)

tabla.heading(
    "Cantidad",
    text="Cantidad Vendida"
)

tabla.heading(
    "Ventas",
    text="Ventas"
)

tabla.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

try:

    cursor.execute("""
    SELECT
        producto,
        SUM(cantidad),
        SUM(total)
    FROM ventas
    GROUP BY producto
    ORDER BY SUM(total) DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=(
                fila[0],
                fila[1],
                f"${fila[2]:,.0f}"
            )
        )

except:
    pass

# =====================================
# CARGA INICIAL
# =====================================

cargar_indicadores()

ventana.mainloop()

conexion.close()