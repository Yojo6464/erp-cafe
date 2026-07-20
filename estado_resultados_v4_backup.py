import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

def valor(sql):

    try:
        con = sqlite3.connect(RUTA_DB)
        cur = con.cursor()

        cur.execute(sql)

        dato = cur.fetchone()

        con.close()

        if dato is None:
            return 0

        if dato[0] is None:
            return 0

        return dato[0]

    except:
        return 0


def actualizar():

    ventas = valor(
        "SELECT IFNULL(SUM(total),0) FROM ventas_cafe"
    )

    compras = valor(
        "SELECT IFNULL(SUM(total),0) FROM compras"
    )

    nomina = valor(
        "SELECT IFNULL(SUM(neto_pagar),0) FROM nomina"
    )

    gastos = valor(
        "SELECT IFNULL(SUM(valor),0) FROM gastos_operativos"
    )

    utilidad = (
        ventas
        - compras
        - nomina
        - gastos
    )

    margen = 0

    if ventas > 0:
        margen = (utilidad / ventas) * 100

    lbl_ventas.config(text=f"${ventas:,.0f}")
    lbl_compras.config(text=f"${compras:,.0f}")
    lbl_nomina.config(text=f"${nomina:,.0f}")
    lbl_gastos.config(text=f"${gastos:,.0f}")
    lbl_utilidad.config(text=f"${utilidad:,.0f}")
    lbl_margen.config(text=f"{margen:,.2f}%")

    if utilidad >= 0:
        lbl_utilidad.config(fg="green")
    else:
        lbl_utilidad.config(fg="red")


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Estado de Resultados V3"
)

ventana.geometry("900x650")

titulo = tk.Label(
    ventana,
    text="ESTADO DE RESULTADOS",
    font=("Arial",22,"bold")
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

tk.Label(frame,text="Ingresos por Ventas",
         font=("Arial",12)).grid(row=0,column=0,sticky="w",pady=8)

lbl_ventas = tk.Label(frame,text="$0",
                      font=("Arial",12,"bold"))
lbl_ventas.grid(row=0,column=1)

tk.Label(frame,text="Compras",
         font=("Arial",12)).grid(row=1,column=0,sticky="w",pady=8)

lbl_compras = tk.Label(frame,text="$0",
                       font=("Arial",12,"bold"))
lbl_compras.grid(row=1,column=1)

tk.Label(frame,text="Nómina",
         font=("Arial",12)).grid(row=2,column=0,sticky="w",pady=8)

lbl_nomina = tk.Label(frame,text="$0",
                      font=("Arial",12,"bold"))
lbl_nomina.grid(row=2,column=1)

tk.Label(frame,text="Gastos Operativos",
         font=("Arial",12)).grid(row=3,column=0,sticky="w",pady=8)

lbl_gastos = tk.Label(frame,text="$0",
                      font=("Arial",12,"bold"))
lbl_gastos.grid(row=3,column=1)

tk.Label(frame,
         text="Utilidad Operacional",
         font=("Arial",14,"bold")).grid(
            row=4,column=0,sticky="w",pady=15)

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial",14,"bold")
)

lbl_utilidad.grid(row=4,column=1)

tk.Label(frame,
         text="Margen (%)",
         font=("Arial",12,"bold")).grid(
            row=5,column=0,sticky="w",pady=8)

lbl_margen = tk.Label(
    frame,
    text="0%",
    font=("Arial",12,"bold")
)

lbl_margen.grid(row=5,column=1)

btn = tk.Button(
    ventana,
    text="Actualizar Estado de Resultados",
    width=30,
    command=actualizar
)

btn.pack(pady=20)

actualizar()

ventana.mainloop()