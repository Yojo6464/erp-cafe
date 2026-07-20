import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

def valor(sql):
try:
conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()


    cursor.execute(sql)

    dato = cursor.fetchone()

    conexion.close()

    if dato is None:
        return 0

    if dato[0] is None:
        return 0

    return dato[0]

except Exception:
    return 0

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

inventario_pergamino = valor(
    "SELECT IFNULL(SUM(saldo_kg),0) FROM almacen_pergamino"
)

produccion_tostado = valor(
    "SELECT IFNULL(SUM(cafe_tostado),0) FROM produccion_cafe"
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
    text=f"{cantidad_ventas:,.0f}"
)

lbl_inventario.config(
    text=f"{inventario_pergamino:,.0f} Kg"
)

lbl_produccion.config(
    text=f"{produccion_tostado:,.0f} Kg"
)


ventana = tk.Tk()

ventana.title(
"ERP Café Alto de la Cruz - Dashboard Ejecutivo V6"
)

ventana.geometry("1000x650")

titulo = tk.Label(
ventana,
text="DASHBOARD EJECUTIVO V6",
font=("Arial", 24, "bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=20)

tk.Label(
frame,
text="VENTAS TOTALES",
font=("Arial", 14, "bold")
).grid(row=0, column=0, padx=40, pady=15)

lbl_ventas = tk.Label(
frame,
text="$0",
font=("Arial", 16)
)

lbl_ventas.grid(row=1, column=0)

tk.Label(
frame,
text="CUENTAS POR COBRAR",
font=("Arial", 14, "bold")
).grid(row=0, column=1, padx=40, pady=15)

lbl_cartera = tk.Label(
frame,
text="$0",
font=("Arial", 16)
)

lbl_cartera.grid(row=1, column=1)

tk.Label(
frame,
text="UTILIDAD BRUTA ESTIMADA",
font=("Arial", 14, "bold")
).grid(row=0, column=2, padx=40, pady=15)

lbl_utilidad = tk.Label(
frame,
text="$0",
font=("Arial", 16)
)

lbl_utilidad.grid(row=1, column=2)

tk.Label(
frame,
text="NUMERO DE VENTAS",
font=("Arial", 14, "bold")
).grid(row=2, column=0, padx=40, pady=25)

lbl_num_ventas = tk.Label(
frame,
text="0",
font=("Arial", 16)
)

lbl_num_ventas.grid(row=3, column=0)

tk.Label(
frame,
text="INVENTARIO PERGAMINO",
font=("Arial", 14, "bold")
).grid(row=2, column=1, padx=40, pady=25)

lbl_inventario = tk.Label(
frame,
text="0 Kg",
font=("Arial", 16)
)

lbl_inventario.grid(row=3, column=1)

tk.Label(
frame,
text="PRODUCCION TOSTADO",
font=("Arial", 14, "bold")
).grid(row=2, column=2, padx=40, pady=25)

lbl_produccion = tk.Label(
frame,
text="0 Kg",
font=("Arial", 16)
)

lbl_produccion.grid(row=3, column=2)

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
