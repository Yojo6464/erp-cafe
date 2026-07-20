import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def cargar_indicadores():

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    # BANCOS
    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM bancos
    """)
    bancos = float(cursor.fetchone()[0])

    # CUENTAS POR COBRAR
    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_cobrar
    """)
    cuentas_cobrar = float(cursor.fetchone()[0])

    # INVENTARIO
    cursor.execute("""
    SELECT IFNULL(
        SUM(cantidad * costo_unitario),
        0
    )
    FROM inventario
    """)
    inventario = float(cursor.fetchone()[0])

    # CUENTAS POR PAGAR
    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_pagar
    """)
    cuentas_pagar = float(cursor.fetchone()[0])

    conexion.close()

    total_activos = (
        bancos +
        cuentas_cobrar +
        inventario
    )

    patrimonio = (
        total_activos -
        cuentas_pagar
    )

    lbl_bancos.config(
        text=f"${bancos:,.0f}"
    )

    lbl_cxc.config(
        text=f"${cuentas_cobrar:,.0f}"
    )

    lbl_inventario.config(
        text=f"${inventario:,.0f}"
    )

    lbl_cxp.config(
        text=f"${cuentas_pagar:,.0f}"
    )

    lbl_patrimonio.config(
        text=f"${patrimonio:,.0f}"
    )


# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard Gerencial"
)

ventana.geometry("1200x700")

titulo = tk.Label(
    ventana,
    text="DASHBOARD GERENCIAL",
    font=("Arial", 24, "bold")
)

titulo.pack(pady=20)

# ==========================
# TARJETAS
# ==========================

frame = tk.Frame(ventana)
frame.pack(pady=20)

# BANCOS

card1 = tk.LabelFrame(
    frame,
    text="BANCOS",
    padx=30,
    pady=20
)
card1.grid(row=0, column=0, padx=15, pady=15)

lbl_bancos = tk.Label(
    card1,
    text="$0",
    font=("Arial", 16, "bold")
)
lbl_bancos.pack()

# CUENTAS POR COBRAR

card2 = tk.LabelFrame(
    frame,
    text="CUENTAS POR COBRAR",
    padx=30,
    pady=20
)
card2.grid(row=0, column=1, padx=15, pady=15)

lbl_cxc = tk.Label(
    card2,
    text="$0",
    font=("Arial", 16, "bold")
)
lbl_cxc.pack()

# INVENTARIO

card3 = tk.LabelFrame(
    frame,
    text="INVENTARIO",
    padx=30,
    pady=20
)
card3.grid(row=0, column=2, padx=15, pady=15)

lbl_inventario = tk.Label(
    card3,
    text="$0",
    font=("Arial", 16, "bold")
)
lbl_inventario.pack()

# CUENTAS POR PAGAR

card4 = tk.LabelFrame(
    frame,
    text="CUENTAS POR PAGAR",
    padx=30,
    pady=20
)
card4.grid(row=1, column=0, padx=15, pady=15)

lbl_cxp = tk.Label(
    card4,
    text="$0",
    font=("Arial", 16, "bold")
)
lbl_cxp.pack()

# PATRIMONIO

card5 = tk.LabelFrame(
    frame,
    text="PATRIMONIO",
    padx=30,
    pady=20
)
card5.grid(row=1, column=1, padx=15, pady=15)

lbl_patrimonio = tk.Label(
    card5,
    text="$0",
    font=("Arial", 16, "bold")
)
lbl_patrimonio.pack()

# BOTON

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    command=cargar_indicadores
)

btn_actualizar.pack(pady=30)

cargar_indicadores()

ventana.mainloop()