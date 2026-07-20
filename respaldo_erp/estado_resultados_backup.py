import tkinter as tk
import sqlite3

conexion = sqlite3.connect(
r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

def valor(sql):

    try:

        cursor.execute(sql)

        dato = cursor.fetchone()[0]

        if dato is None:
            return 0

        return float(dato)

    except:

        return 0
 

ventas = valor("""
SELECT SUM(total)
FROM ventas
""")

utilidad_bruta = valor("""
SELECT SUM(utilidad_total)
FROM ventas
""")

costo_ventas = ventas - utilidad_bruta

gastos_pendientes = valor("""
SELECT SUM(saldo)
FROM cuentas_pagar
WHERE estado='PENDIENTE'
""")

utilidad_operativa = (
utilidad_bruta -
gastos_pendientes
)

ventana = tk.Tk()

ventana.title(
"ERP Café Alto de la Cruz - Estado de Resultados"
)

ventana.geometry("800x600")

titulo = tk.Label(
ventana,
text="ESTADO DE RESULTADOS",
font=("Arial",20,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=20)

datos = [


("Ventas", ventas),
("Costo de Ventas", costo_ventas),
("Utilidad Bruta", utilidad_bruta),
("Cuentas por Pagar", gastos_pendientes),
("Utilidad Operativa", utilidad_operativa)


]

fila = 0

for nombre, valor_dato in datos:

    tk.Label(
        frame,
        text=nombre,
        font=("Arial",12)
    ).grid(
        row=fila,
        column=0,
        sticky="w",
        padx=30,
        pady=10
    )

    tk.Label(
        frame,
        text=f"${valor_dato:,.0f}",
        font=("Arial",12,"bold")
    ).grid(
        row=fila,
        column=1,
        padx=30
    )

    fila += 1


ventana.mainloop()

conexion.close()
