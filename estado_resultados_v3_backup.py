import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# FUNCIONES
# =====================================

def valor(sql):

    try:

        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()

        cursor.execute(sql)

        dato = cursor.fetchone()[0]

        conexion.close()

        if dato is None:
            return 0

        return dato

    except:

        return 0

# =====================================
# ACTUALIZAR
# =====================================

def actualizar():

    ventas = valor(
        "SELECT IFNULL(SUM(total),0) FROM ventas_cafe"
    )

    cantidad_ventas = valor(
        "SELECT COUNT(*) FROM ventas_cafe"
    )

    promedio = 0

    if cantidad_ventas > 0:

        promedio = ventas / cantidad_ventas

    costo_estimado = ventas * 0.60

    utilidad_bruta = ventas - costo_estimado

    lbl_ventas.config(
        text=f"${ventas:,.0f}"
    )

    lbl_cantidad.config(
        text=f"{cantidad_ventas}"
    )

    lbl_promedio.config(
        text=f"${promedio:,.0f}"
    )

    lbl_costos.config(
        text=f"${costo_estimado:,.0f}"
    )

    lbl_utilidad.config(
        text=f"${utilidad_bruta:,.0f}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Estado de Resultados V2"
)

ventana.geometry("900x600")

titulo = tk.Label(
    ventana,
    text="ESTADO DE RESULTADOS",
    font=("Arial",24,"bold")
)

titulo.pack(pady=20)

frame = tk.LabelFrame(
    ventana,
    text="RESULTADOS FINANCIEROS",
    padx=20,
    pady=20
)

frame.pack(
    fill="x",
    padx=20,
    pady=20
)

# VENTAS

tk.Label(
    frame,
    text="Ingresos por Ventas",
    font=("Arial",12)
).grid(row=0,column=0,padx=20,pady=10,sticky="w")

lbl_ventas = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_ventas.grid(row=0,column=1)

# CANTIDAD

tk.Label(
    frame,
    text="Número de Ventas",
    font=("Arial",12)
).grid(row=1,column=0,padx=20,pady=10,sticky="w")

lbl_cantidad = tk.Label(
    frame,
    text="0",
    font=("Arial",12,"bold")
)

lbl_cantidad.grid(row=1,column=1)

# PROMEDIO

tk.Label(
    frame,
    text="Venta Promedio",
    font=("Arial",12)
).grid(row=2,column=0,padx=20,pady=10,sticky="w")

lbl_promedio = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_promedio.grid(row=2,column=1)

# COSTOS

tk.Label(
    frame,
    text="Costo Estimado (60%)",
    font=("Arial",12)
).grid(row=3,column=0,padx=20,pady=10,sticky="w")

lbl_costos = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_costos.grid(row=3,column=1)

# UTILIDAD

tk.Label(
    frame,
    text="Utilidad Bruta",
    font=("Arial",14,"bold")
).grid(row=4,column=0,padx=20,pady=20,sticky="w")

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial",14,"bold")
)

lbl_utilidad.grid(row=4,column=1)

# BOTON

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Estado de Resultados",
    width=30,
    command=actualizar
)

btn_actualizar.pack(pady=20)

actualizar()

ventana.mainloop()