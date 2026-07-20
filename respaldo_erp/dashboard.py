import tkinter as tk
from tkinter import ttk
import sqlite3

DB = "erp_cafe.db"


# =====================================
# CONEXION
# =====================================

def conectar():
    return sqlite3.connect(DB)


# =====================================
# TABLA RESUMEN
# =====================================

def cargar_tabla():

    for item in tabla.get_children():
        tabla.delete(item)

    con = conectar()
    cur = con.cursor()

    try:

        cur.execute("""
        SELECT
            producto,
            SUM(cantidad),
            SUM(total)
        FROM ventas
        GROUP BY producto
        ORDER BY SUM(total) DESC
        """)

        for fila in cur.fetchall():

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

    con.close()


# =====================================
# INDICADORES
# =====================================

def cargar_indicadores():

    con = conectar()
    cur = con.cursor()

    ventas_totales = 0
    utilidad_total = 0
    stock_total = 0
    valor_inventario = 0
    kg_pergamino = 0
    valor_pergamino = 0
    saldo_empaques = 0
    valor_empaques = 0

    # ==========================
    # VENTAS
    # ==========================

    try:

        cur.execute("""
        SELECT
            IFNULL(SUM(total),0),
            IFNULL(SUM(utilidad_total),0)
        FROM ventas
        """)

        datos = cur.fetchone()

        ventas_totales = float(datos[0])
        utilidad_total = float(datos[1])

    except:
        pass

    # ==========================
    # INVENTARIO
    # ==========================

    try:

        cur.execute("""
        SELECT
            IFNULL(SUM(cantidad),0)
        FROM inventario
        """)

        stock_total = float(
            cur.fetchone()[0]
        )

        cur.execute("""
        SELECT
            IFNULL(
                SUM(
                    cantidad *
                    costo_unitario
                ),
                0
            )
        FROM inventario
        """)

        valor_inventario = float(
            cur.fetchone()[0]
        )

    except:
        pass

    # ==========================
    # PERGAMINO
    # ==========================

    try:

        cur.execute("""
        SELECT
            IFNULL(
                SUM(saldo_kg),
                0
            ),
            IFNULL(
                SUM(
                    saldo_kg *
                    costo_kg
                ),
                0
            )
        FROM almacen_pergamino
        """)

        datos = cur.fetchone()

        kg_pergamino = float(
            datos[0]
        )

        valor_pergamino = float(
            datos[1]
        )

    except:
        pass

    # ==========================
    # EMPAQUES
    # ==========================

    try:

        cur.execute("""
        SELECT
            IFNULL(
                SUM(saldo),
                0
            ),
            IFNULL(
                SUM(
                    saldo *
                    costo_unitario
                ),
                0
            )
        FROM almacen_empaques
        """)

        datos = cur.fetchone()

        saldo_empaques = float(
            datos[0]
        )

        valor_empaques = float(
            datos[1]
        )

    except:
        pass
        # ==========================
    # PRODUCTO MAS VENDIDO
    # ==========================

    producto_top = "Sin ventas"

    try:

        cur.execute("""
        SELECT
            producto,
            SUM(cantidad)
        FROM ventas
        GROUP BY producto
        ORDER BY SUM(cantidad) DESC
        LIMIT 1
        """)

        dato = cur.fetchone()

        if dato:

            producto_top = (
                f"{dato[0]} ({dato[1]})"
            )

    except:
        pass

    capital_operativo = (
        valor_inventario
        + valor_pergamino
        + valor_empaques
    )

    lbl_ventas.config(
        text=f"${ventas_totales:,.0f}"
    )

    lbl_utilidad.config(
        text=f"${utilidad_total:,.0f}"
    )

    lbl_stock.config(
        text=f"{stock_total:,.0f}"
    )

    lbl_inv.config(
        text=f"${valor_inventario:,.0f}"
    )

    lbl_pergamino.config(
        text=f"{kg_pergamino:,.0f} kg"
    )

    lbl_empaques.config(
        text=f"{saldo_empaques:,.0f}"
    )

    lbl_capital.config(
        text=f"${capital_operativo:,.0f}"
    )

    lbl_top.config(
        text=producto_top
    )

    con.close()

    cargar_tabla()


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard"
)

ventana.geometry("1400x800")

titulo = tk.Label(
    ventana,
    text="DASHBOARD GERENCIAL",
    font=("Arial", 20, "bold")
)

titulo.pack(pady=15)

frame = tk.Frame(ventana)
frame.pack(pady=10)

# FILA 1

tk.Label(frame, text="Ventas Totales").grid(row=0, column=0, padx=20)
tk.Label(frame, text="Utilidad Total").grid(row=0, column=1, padx=20)
tk.Label(frame, text="Stock Total").grid(row=0, column=2, padx=20)
tk.Label(frame, text="Valor Inventario").grid(row=0, column=3, padx=20)

lbl_ventas = tk.Label(frame, text="$0", font=("Arial",12,"bold"))
lbl_utilidad = tk.Label(frame, text="$0", font=("Arial",12,"bold"))
lbl_stock = tk.Label(frame, text="0", font=("Arial",12,"bold"))
lbl_inv = tk.Label(frame, text="$0", font=("Arial",12,"bold"))

lbl_ventas.grid(row=1,column=0)
lbl_utilidad.grid(row=1,column=1)
lbl_stock.grid(row=1,column=2)
lbl_inv.grid(row=1,column=3)

# FILA 2

tk.Label(frame, text="Pergamino Disponible").grid(row=2,column=0,padx=20,pady=15)
tk.Label(frame, text="Empaques Disponibles").grid(row=2,column=1,padx=20,pady=15)
tk.Label(frame, text="Capital Operativo").grid(row=2,column=2,padx=20,pady=15)

lbl_pergamino = tk.Label(frame,text="0",font=("Arial",12,"bold"))
lbl_empaques = tk.Label(frame,text="0",font=("Arial",12,"bold"))
lbl_capital = tk.Label(frame,text="$0",font=("Arial",12,"bold"))

lbl_pergamino.grid(row=3,column=0)
lbl_empaques.grid(row=3,column=1)
lbl_capital.grid(row=3,column=2)

# PRODUCTO TOP

tk.Label(
    ventana,
    text="Producto Más Vendido",
    font=("Arial",12)
).pack()

lbl_top = tk.Label(
    ventana,
    text="-",
    font=("Arial",14,"bold")
)

lbl_top.pack(pady=5)

# BOTON

tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=30,
    command=cargar_indicadores
).pack(pady=10)

# TABLA

columnas = (
    "Producto",
    "Cantidad Vendida",
    "Ventas"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=20
)

for col in columnas:

    tabla.heading(
        col,
        text=col
    )

    tabla.column(
        col,
        width=250,
        anchor="center"
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=15
)

# CARGA INICIAL

cargar_indicadores()

ventana.mainloop()