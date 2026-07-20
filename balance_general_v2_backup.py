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

    bancos = valor(
        "SELECT IFNULL(SUM(saldo),0) FROM bancos"
    )

    cartera = valor(
        """
        SELECT IFNULL(SUM(valor),0)
        FROM cuentas_cobrar_v1
        WHERE estado='Pendiente'
        """
    )

    inv_pergamino = valor(
        """
        SELECT IFNULL(
            SUM(saldo_kg * costo_kg),0
        )
        FROM almacen_pergamino
        """
    )

    inv_empaques = valor(
        """
        SELECT IFNULL(
            SUM(saldo * costo_unitario),0
        )
        FROM almacen_empaques
        """
    )

    activos = (
        bancos
        + cartera
        + inv_pergamino
        + inv_empaques
    )

    pasivos = valor(
        """
        SELECT IFNULL(SUM(saldo),0)
        FROM cuentas_pagar
        WHERE estado='Pendiente'
        """
    )

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

    patrimonio = (
        ventas
        - compras
        - nomina
        - gastos
    )

    pasivo_patrimonio = (
        pasivos
        + patrimonio
    )

    diferencia = (
        activos
        - pasivo_patrimonio
    )

    lbl_bancos.config(
        text=f"${bancos:,.0f}"
    )

    lbl_cartera.config(
        text=f"${cartera:,.0f}"
    )

    lbl_pergamino.config(
        text=f"${inv_pergamino:,.0f}"
    )

    lbl_empaques.config(
        text=f"${inv_empaques:,.0f}"
    )

    lbl_activos.config(
        text=f"${activos:,.0f}"
    )

    lbl_pasivos.config(
        text=f"${pasivos:,.0f}"
    )

    lbl_patrimonio.config(
        text=f"${patrimonio:,.0f}"
    )

    lbl_pasivo_patrimonio.config(
        text=f"${pasivo_patrimonio:,.0f}"
    )

    lbl_diferencia.config(
        text=f"${diferencia:,.0f}"
    )


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Balance General V1"
)

ventana.geometry("900x700")

titulo = tk.Label(
    ventana,
    text="BALANCE GENERAL",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=10)

def fila(texto, fila_num):

    tk.Label(
        frame,
        text=texto,
        font=("Arial",12,"bold")
    ).grid(
        row=fila_num,
        column=0,
        sticky="w",
        padx=20,
        pady=6
    )

fila("Bancos",0)
lbl_bancos = tk.Label(frame,text="$0")
lbl_bancos.grid(row=0,column=1)

fila("Cartera",1)
lbl_cartera = tk.Label(frame,text="$0")
lbl_cartera.grid(row=1,column=1)

fila("Inventario Pergamino",2)
lbl_pergamino = tk.Label(frame,text="$0")
lbl_pergamino.grid(row=2,column=1)

fila("Inventario Empaques",3)
lbl_empaques = tk.Label(frame,text="$0")
lbl_empaques.grid(row=3,column=1)

fila("TOTAL ACTIVOS",4)
lbl_activos = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)
lbl_activos.grid(row=4,column=1)

fila("TOTAL PASIVOS",5)
lbl_pasivos = tk.Label(frame,text="$0")
lbl_pasivos.grid(row=5,column=1)

fila("PATRIMONIO",6)
lbl_patrimonio = tk.Label(frame,text="$0")
lbl_patrimonio.grid(row=6,column=1)

fila("PASIVO + PATRIMONIO",7)
lbl_pasivo_patrimonio = tk.Label(frame,text="$0")
lbl_pasivo_patrimonio.grid(row=7,column=1)

fila("DIFERENCIA",8)
lbl_diferencia = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)
lbl_diferencia.grid(row=8,column=1)

btn = tk.Button(
    ventana,
    text="Actualizar Balance",
    width=25,
    height=2,
    command=actualizar
)

btn.pack(pady=20)

actualizar()

ventana.mainloop()