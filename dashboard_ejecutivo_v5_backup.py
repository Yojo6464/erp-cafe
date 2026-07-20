import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# FUNCION CONSULTA
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
# ACTUALIZAR DASHBOARD
# =====================================

def actualizar():

    ventas = valor(
        "SELECT IFNULL(SUM(total),0) FROM ventas_cafe"
    )

    cartera = valor(
        "SELECT IFNULL(SUM(valor),0) FROM cuentas_cobrar_v1 WHERE estado='Pendiente'"
    )

    cantidad_ventas = valor(
        "SELECT COUNT(*) FROM ventas_cafe"
    )

    movimientos_inventario = valor(
        "SELECT COUNT(*) FROM inventario_cafe"
    )

    produccion = valor(
        "SELECT COUNT(*) FROM produccion_cafe"
    )

    utilidad_bruta = ventas * 0.40

    lbl_ventas.config(
        text=f"${ventas:,.0f}"
    )

    lbl_cartera.config(
        text=f"${cartera:,.0f}"
    )

    lbl_utilidad.config(
        text=f"${utilidad_bruta:,.0f}"
    )

    lbl_num_ventas.config(
        text=str(cantidad_ventas)
    )

    lbl_inventario.config(
        text=str(movimientos_inventario)
    )

    lbl_produccion.config(
        text=str(produccion)
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard Ejecutivo V5"
)

ventana.geometry("1000x650")

titulo = tk.Label(
    ventana,
    text="DASHBOARD EJECUTIVO V5",
    font=("Arial",24,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=20)

# =====================================
# FILA 1
# =====================================

tk.Label(
    frame,
    text="VENTAS TOTALES",
    font=("Arial",14,"bold")
).grid(row=0,column=0,padx=40,pady=15)

lbl_ventas = tk.Label(
    frame,
    text="$0",
    font=("Arial",16)
)

lbl_ventas.grid(row=1,column=0)

tk.Label(
    frame,
    text="CUENTAS POR COBRAR",
    font=("Arial",14,"bold")
).grid(row=0,column=1,padx=40,pady=15)

lbl_cartera = tk.Label(
    frame,
    text="$0",
    font=("Arial",16)
)

lbl_cartera.grid(row=1,column=1)

tk.Label(
    frame,
    text="UTILIDAD BRUTA",
    font=("Arial",14,"bold")
).grid(row=0,column=2,padx=40,pady=15)

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial",16)
)

lbl_utilidad.grid(row=1,column=2)

# =====================================
# FILA 2
# =====================================

tk.Label(
    frame,
    text="NUMERO DE VENTAS",
    font=("Arial",14,"bold")
).grid(row=2,column=0,padx=40,pady=25)

lbl_num_ventas = tk.Label(
    frame,
    text="0",
    font=("Arial",16)
)

lbl_num_ventas.grid(row=3,column=0)

tk.Label(
    frame,
    text="MOVIMIENTOS INVENTARIO",
    font=("Arial",14,"bold")
).grid(row=2,column=1,padx=40,pady=25)

lbl_inventario = tk.Label(
    frame,
    text="0",
    font=("Arial",16)
)

lbl_inventario.grid(row=3,column=1)

tk.Label(
    frame,
    text="REGISTROS PRODUCCION",
    font=("Arial",14,"bold")
).grid(row=2,column=2,padx=40,pady=25)

lbl_produccion = tk.Label(
    frame,
    text="0",
    font=("Arial",16)
)

lbl_produccion.grid(row=3,column=2)

# =====================================
# BOTON
# =====================================

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=30,
    height=2,
    command=actualizar
)

btn_actualizar.pack(pady=30)

actualizar()

ventana.mainloop()