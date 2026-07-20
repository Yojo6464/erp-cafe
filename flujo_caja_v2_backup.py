import tkinter as tk
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

def actualizar():

    # SALDO BANCOS

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM bancos
    """)

    saldo_bancos = cursor.fetchone()[0]

    # COBROS RECIBIDOS

    cursor.execute("""
    SELECT IFNULL(SUM(valor_pagado),0)
    FROM pagos_cxc
    """)

    cobros = cursor.fetchone()[0]

    # PAGOS REALIZADOS

    cursor.execute("""
    SELECT IFNULL(SUM(valor),0)
    FROM pagos_cxp
    """)

    pagos = cursor.fetchone()[0]

    # CUENTAS POR COBRAR

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_cobrar
    WHERE estado='PENDIENTE'
    """)

    cxc = cursor.fetchone()[0]

    # CUENTAS POR PAGAR

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_pagar
    WHERE estado='PENDIENTE'
    """)

    cxp = cursor.fetchone()[0]

    # UTILIDAD ACUMULADA

    cursor.execute("""
    SELECT IFNULL(SUM(utilidad_total),0)
    FROM ventas
    """)

    utilidad = cursor.fetchone()[0]

    # FLUJO DE CAJA REAL

    flujo = cobros - pagos

    # LIQUIDEZ DISPONIBLE

    liquidez = saldo_bancos + cxc - cxp

    # ACTUALIZAR PANTALLA

    lbl_bancos.config(text=f"${saldo_bancos:,.0f}")
    lbl_liquidez.config(text=f"${liquidez:,.0f}")
    lbl_cobros.config(text=f"${cobros:,.0f}")
    lbl_pagos.config(text=f"${pagos:,.0f}")
    lbl_cxc.config(text=f"${cxc:,.0f}")
    lbl_cxp.config(text=f"${cxp:,.0f}")
    lbl_utilidad.config(text=f"${utilidad:,.0f}")
    lbl_flujo.config(text=f"${flujo:,.0f}")

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Flujo de Caja V2")

ventana.geometry("900x650")

titulo = tk.Label(
    ventana,
    text="FLUJO DE CAJA V2",
    font=("Arial",18,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=20)

# FILA 1

tk.Label(
    frame,
    text="Saldo Bancos"
).grid(row=0,column=0,padx=40)

lbl_bancos = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_bancos.grid(row=1,column=0)

tk.Label(
    frame,
    text="Liquidez Disponible"
).grid(row=0,column=1,padx=40)

lbl_liquidez = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_liquidez.grid(row=1,column=1)

# FILA 2

tk.Label(
    frame,
    text="Cobros CxC"
).grid(row=2,column=0,pady=20)

lbl_cobros = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_cobros.grid(row=3,column=0)

tk.Label(
    frame,
    text="Pagos CxP"
).grid(row=2,column=1,pady=20)

lbl_pagos = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_pagos.grid(row=3,column=1)

# FILA 3

tk.Label(
    frame,
    text="Cuentas por Cobrar"
).grid(row=4,column=0,pady=20)

lbl_cxc = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_cxc.grid(row=5,column=0)

tk.Label(
    frame,
    text="Cuentas por Pagar"
).grid(row=4,column=1,pady=20)

lbl_cxp = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_cxp.grid(row=5,column=1)

# FILA 4

tk.Label(
    frame,
    text="Utilidad Acumulada"
).grid(row=6,column=0,pady=20)

lbl_utilidad = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_utilidad.grid(row=7,column=0)

tk.Label(
    frame,
    text="Flujo Neto"
).grid(row=6,column=1,pady=20)

lbl_flujo = tk.Label(
    frame,
    text="$0",
    font=("Arial",12,"bold")
)

lbl_flujo.grid(row=7,column=1)

# BOTON

tk.Button(
    ventana,
    text="Actualizar Flujo",
    width=25,
    command=actualizar
).pack(pady=20)

actualizar()

ventana.mainloop()

conexion.close()