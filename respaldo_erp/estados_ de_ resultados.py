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

# CALCULAR DATOS

# =====================================

def cargar_estado_resultados():


# -------------------------
# VENTAS
# -------------------------

cursor.execute("""
SELECT IFNULL(SUM(total),0)
FROM ventas
""")

ventas = float(
    cursor.fetchone()[0]
)

# -------------------------
# COMPRAS
# -------------------------

cursor.execute("""
SELECT IFNULL(SUM(valor),0)
FROM compras
""")

compras = float(
    cursor.fetchone()[0]
)

# -------------------------
# GASTOS APROBADOS
# -------------------------

cursor.execute("""
SELECT IFNULL(SUM(valor),0)
FROM solicitudes_pago
WHERE estado='APROBADA'
""")

gastos = float(
    cursor.fetchone()[0]
)

utilidad = ventas - compras - gastos

if ventas > 0:

    margen = (
        utilidad / ventas
    ) * 100

else:

    margen = 0

lbl_ventas.config(
    text=f"${ventas:,.0f}"
)

lbl_compras.config(
    text=f"${compras:,.0f}"
)

lbl_gastos.config(
    text=f"${gastos:,.0f}"
)

lbl_utilidad.config(
    text=f"${utilidad:,.0f}"
)

lbl_margen.config(
    text=f"{margen:.2f}%"
)
```

# =====================================

# CARGAR DETALLE GASTOS

# =====================================

def cargar_gastos():


tabla.delete(
    *tabla.get_children()
)

cursor.execute("""
SELECT
    fecha,
    proveedor,
    tipo_gasto,
    concepto,
    valor
FROM solicitudes_pago
WHERE estado='APROBADA'
ORDER BY id DESC
""")

registros = cursor.fetchall()

for fila in registros:

    tabla.insert(
        "",
        tk.END,
        values=fila
    )


# =====================================

# VENTANA

# =====================================

ventana = tk.Tk()

ventana.title(
"ERP Café Alto de la Cruz - Estado de Resultados"
)

ventana.geometry(
"1200x700"
)

# =====================================

# TITULO

# =====================================

titulo = tk.Label(
ventana,
text="ESTADO DE RESULTADOS",
font=("Arial",22,"bold")
)

titulo.pack(
pady=15
)

# =====================================

# RESUMEN

# =====================================

frame = tk.Frame(
ventana
)

frame.pack(
pady=10
)

tk.Label(
frame,
text="Ventas Totales",
font=("Arial",12,"bold")
).grid(
row=0,
column=0,
padx=20
)

lbl_ventas = tk.Label(
frame,
text="$0",
font=("Arial",12)
)

lbl_ventas.grid(
row=1,
column=0
)

# -------------------------

tk.Label(
frame,
text="Compras",
font=("Arial",12,"bold")
).grid(
row=0,
column=1,
padx=20
)

lbl_compras = tk.Label(
frame,
text="$0",
font=("Arial",12)
)

lbl_compras.grid(
row=1,
column=1
)

# -------------------------

tk.Label(
frame,
text="Gastos Aprobados",
font=("Arial",12,"bold")
).grid(
row=0,
column=2,
padx=20
)

lbl_gastos = tk.Label(
frame,
text="$0",
font=("Arial",12)
)

lbl_gastos.grid(
row=1,
column=2
)

# -------------------------

tk.Label(
frame,
text="Utilidad",
font=("Arial",12,"bold")
).grid(
row=0,
column=3,
padx=20
)

lbl_utilidad = tk.Label(
frame,
text="$0",
font=("Arial",12)
)

lbl_utilidad.grid(
row=1,
column=3
)

# -------------------------

tk.Label(
frame,
text="Margen %",
font=("Arial",12,"bold")
).grid(
row=0,
column=4,
padx=20
)

lbl_margen = tk.Label(
frame,
text="0%",
font=("Arial",12)
)

lbl_margen.grid(
row=1,
column=4
)

# =====================================

# TABLA GASTOS

# =====================================

tabla = ttk.Treeview(
ventana,
columns=(
"Fecha",
"Proveedor",
"Tipo",
"Concepto",
"Valor"
),
show="headings"
)

tabla.heading(
"Fecha",
text="Fecha"
)

tabla.heading(
"Proveedor",
text="Proveedor"
)

tabla.heading(
"Tipo",
text="Tipo Gasto"
)

tabla.heading(
"Concepto",
text="Concepto"
)

tabla.heading(
"Valor",
text="Valor"
)

tabla.pack(
fill="both",
expand=True,
padx=10,
pady=20
)

# =====================================

# INICIO

# =====================================

cargar_estado_resultados()
cargar_gastos()

ventana.mainloop()

conexion.close()
