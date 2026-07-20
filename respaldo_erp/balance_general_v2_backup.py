import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def actualizar_balance():

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

    # INVENTARIO VALORIZADO
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

    total_pasivos = cuentas_pagar

    patrimonio = (
        total_activos -
        total_pasivos
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

    lbl_total_activos.config(
        text=f"${total_activos:,.0f}"
    )

    lbl_cxp.config(
        text=f"${cuentas_pagar:,.0f}"
    )

    lbl_total_pasivos.config(
        text=f"${total_pasivos:,.0f}"
    )

    lbl_patrimonio.config(
        text=f"${patrimonio:,.0f}"
    )


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Balance General"
)

ventana.geometry("850x650")

titulo = tk.Label(
    ventana,
    text="BALANCE GENERAL",
    font=("Arial", 22, "bold")
)

titulo.pack(pady=20)

# =====================================
# ACTIVOS
# =====================================

frame_activos = tk.LabelFrame(
    ventana,
    text="ACTIVOS",
    padx=20,
    pady=20
)

frame_activos.pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Label(
    frame_activos,
    text="Bancos"
).grid(
    row=0,
    column=0,
    sticky="w"
)

lbl_bancos = tk.Label(
    frame_activos,
    text="$0"
)

lbl_bancos.grid(
    row=0,
    column=1,
    sticky="e"
)

tk.Label(
    frame_activos,
    text="Cuentas por Cobrar"
).grid(
    row=1,
    column=0,
    sticky="w"
)

lbl_cxc = tk.Label(
    frame_activos,
    text="$0"
)

lbl_cxc.grid(
    row=1,
    column=1,
    sticky="e"
)

tk.Label(
    frame_activos,
    text="Inventario"
).grid(
    row=2,
    column=0,
    sticky="w"
)

lbl_inventario = tk.Label(
    frame_activos,
    text="$0"
)

lbl_inventario.grid(
    row=2,
    column=1,
    sticky="e"
)

tk.Label(
    frame_activos,
    text="TOTAL ACTIVOS",
    font=("Arial", 10, "bold")
).grid(
    row=3,
    column=0,
    pady=10
)

lbl_total_activos = tk.Label(
    frame_activos,
    text="$0",
    font=("Arial", 10, "bold")
)

lbl_total_activos.grid(
    row=3,
    column=1
)

# =====================================
# PASIVOS
# =====================================

frame_pasivos = tk.LabelFrame(
    ventana,
    text="PASIVOS",
    padx=20,
    pady=20
)

frame_pasivos.pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Label(
    frame_pasivos,
    text="Cuentas por Pagar"
).grid(
    row=0,
    column=0,
    sticky="w"
)

lbl_cxp = tk.Label(
    frame_pasivos,
    text="$0"
)

lbl_cxp.grid(
    row=0,
    column=1,
    sticky="e"
)

tk.Label(
    frame_pasivos,
    text="TOTAL PASIVOS",
    font=("Arial", 10, "bold")
).grid(
    row=1,
    column=0,
    pady=10
)

lbl_total_pasivos = tk.Label(
    frame_pasivos,
    text="$0",
    font=("Arial", 10, "bold")
)

lbl_total_pasivos.grid(
    row=1,
    column=1
)

# =====================================
# PATRIMONIO
# =====================================

frame_patrimonio = tk.LabelFrame(
    ventana,
    text="PATRIMONIO",
    padx=20,
    pady=20
)

frame_patrimonio.pack(
    fill="x",
    padx=20,
    pady=10
)

lbl_patrimonio = tk.Label(
    frame_patrimonio,
    text="$0",
    font=("Arial", 14, "bold")
)

lbl_patrimonio.pack()

# =====================================
# BOTON
# =====================================

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar",
    width=20,
    command=actualizar_balance
)

btn_actualizar.pack(
    pady=20
)

actualizar_balance()

ventana.mainloop()