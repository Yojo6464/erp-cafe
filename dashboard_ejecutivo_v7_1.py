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

    cartera = valor(
    "SELECT IFNULL(SUM(valor),0) FROM cuentas_cobrar_v1 WHERE estado='Pendiente'"
)

    bancos = valor(
    "SELECT IFNULL(SUM(saldo),0) FROM bancos"
)

    clientes = valor(
    "SELECT COUNT(*) FROM clientes"
)

    produccion = valor(
    "SELECT IFNULL(SUM(cafe_tostado),0) FROM produccion_cafe"
)

    inventario = valor(
    "SELECT IFNULL(SUM(saldo_kg),0) FROM almacen_pergamino"
)

    cxp = valor(
    "SELECT IFNULL(SUM(saldo),0) FROM cuentas_pagar WHERE estado='Pendiente'"
)

    utilidad = ventas * 0.40

    lbl_ventas.config(text=f"${ventas:,.0f}")
    lbl_cartera.config(text=f"${cartera:,.0f}")
    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_clientes.config(text=str(clientes))

    lbl_produccion.config(text=f"{produccion:,.0f} Kg")
    lbl_inventario.config(text=f"{inventario:,.0f} Kg")
    lbl_cxp.config(text=f"${cxp:,.0f}")
    lbl_utilidad.config(text=f"${utilidad:,.0f}")


ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Dashboard Ejecutivo V7.1")
ventana.geometry("1200x650")

titulo = tk.Label(
ventana,
text="DASHBOARD EJECUTIVO V7.1",
font=("Arial",24,"bold")
)
titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=20)

tk.Label(frame,text="VENTAS TOTALES",font=("Arial",14,"bold")).grid(row=0,column=0,padx=30,pady=15)
lbl_ventas = tk.Label(frame,text="$0",font=("Arial",16))
lbl_ventas.grid(row=1,column=0)

tk.Label(frame,text="CARTERA",font=("Arial",14,"bold")).grid(row=0,column=1,padx=30,pady=15)
lbl_cartera = tk.Label(frame,text="$0",font=("Arial",16))
lbl_cartera.grid(row=1,column=1)

tk.Label(frame,text="BANCOS",font=("Arial",14,"bold")).grid(row=0,column=2,padx=30,pady=15)
lbl_bancos = tk.Label(frame,text="$0",font=("Arial",16))
lbl_bancos.grid(row=1,column=2)

tk.Label(frame,text="CLIENTES",font=("Arial",14,"bold")).grid(row=0,column=3,padx=30,pady=15)
lbl_clientes = tk.Label(frame,text="0",font=("Arial",16))
lbl_clientes.grid(row=1,column=3)

tk.Label(frame,text="PRODUCCION",font=("Arial",14,"bold")).grid(row=2,column=0,padx=30,pady=25)
lbl_produccion = tk.Label(frame,text="0 Kg",font=("Arial",16))
lbl_produccion.grid(row=3,column=0)

tk.Label(frame,text="INVENTARIO",font=("Arial",14,"bold")).grid(row=2,column=1,padx=30,pady=25)
lbl_inventario = tk.Label(frame,text="0 Kg",font=("Arial",16))
lbl_inventario.grid(row=3,column=1)

tk.Label(frame,text="CUENTAS POR PAGAR",font=("Arial",14,"bold")).grid(row=2,column=2,padx=30,pady=25)
lbl_cxp = tk.Label(frame,text="$0",font=("Arial",16))
lbl_cxp.grid(row=3,column=2)

tk.Label(frame,text="UTILIDAD ESTIMADA",font=("Arial",14,"bold")).grid(row=2,column=3,padx=30,pady=25)
lbl_utilidad = tk.Label(frame,text="$0",font=("Arial",16))
lbl_utilidad.grid(row=3,column=3)

btn_actualizar = tk.Button(
ventana,
text="Actualizar Dashboard",
width=25,
height=2,
command=actualizar
)

btn_actualizar.pack(pady=30)

actualizar()

ventana.mainloop()
