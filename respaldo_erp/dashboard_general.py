import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def actualizar_dashboard():

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

    # REGISTROS INVENTARIO
    cursor.execute("""
    SELECT COUNT(*)
    FROM inventario
    """)
    registros_inventario = int(cursor.fetchone()[0])

    # CANTIDAD INVENTARIO
    cursor.execute("""
    SELECT IFNULL(SUM(cantidad),0)
    FROM inventario
    """)
    cantidad_inventario = float(cursor.fetchone()[0])

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

    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_cxc.config(text=f"${cuentas_cobrar:,.0f}")
    lbl_inventario.config(text=f"${inventario:,.0f}")
    lbl_cxp.config(text=f"${cuentas_pagar:,.0f}")
    lbl_patrimonio.config(text=f"${patrimonio:,.0f}")

    lbl_registros.config(text=f"{registros_inventario:,}")
    lbl_cantidad.config(text=f"{cantidad_inventario:,.0f}")


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard General"
)

ventana.geometry("1400x850")

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial", 26, "bold")
)

titulo.pack(pady=15)

# ==================================
# FINANCIERO
# ==================================

frame_finanzas = tk.LabelFrame(
    ventana,
    text="RESUMEN FINANCIERO",
    padx=20,
    pady=20
)

frame_finanzas.pack(
    fill="x",
    padx=20,
    pady=10
)

lbl_bancos = tk.Label(frame_finanzas, text="$0", font=("Arial",14,"bold"))
lbl_cxc = tk.Label(frame_finanzas, text="$0", font=("Arial",14,"bold"))
lbl_inventario = tk.Label(frame_finanzas, text="$0", font=("Arial",14,"bold"))
lbl_cxp = tk.Label(frame_finanzas, text="$0", font=("Arial",14,"bold"))
lbl_patrimonio = tk.Label(frame_finanzas, text="$0", font=("Arial",14,"bold"))

tk.Label(frame_finanzas,text="Bancos").grid(row=0,column=0,padx=20)
tk.Label(frame_finanzas,text="Cuentas por Cobrar").grid(row=0,column=1,padx=20)
tk.Label(frame_finanzas,text="Inventario").grid(row=0,column=2,padx=20)
tk.Label(frame_finanzas,text="Cuentas por Pagar").grid(row=0,column=3,padx=20)
tk.Label(frame_finanzas,text="Patrimonio").grid(row=0,column=4,padx=20)

lbl_bancos.grid(row=1,column=0)
lbl_cxc.grid(row=1,column=1)
lbl_inventario.grid(row=1,column=2)
lbl_cxp.grid(row=1,column=3)
lbl_patrimonio.grid(row=1,column=4)

# ==================================
# OPERACIONES
# ==================================

frame_operaciones = tk.LabelFrame(
    ventana,
    text="OPERACIONES",
    padx=20,
    pady=20
)

frame_operaciones.pack(
    fill="x",
    padx=20,
    pady=10
)

lbl_registros = tk.Label(frame_operaciones, text="0", font=("Arial",14,"bold"))
lbl_cantidad = tk.Label(frame_operaciones, text="0", font=("Arial",14,"bold"))

tk.Label(frame_operaciones,text="Registros Inventario").grid(row=0,column=0,padx=30)
tk.Label(frame_operaciones,text="Cantidad Inventario").grid(row=0,column=1,padx=30)

lbl_registros.grid(row=1,column=0)
lbl_cantidad.grid(row=1,column=1)

# ==================================
# ACCESOS RAPIDOS
# ==================================

frame_menu = tk.LabelFrame(
    ventana,
    text="ACCESOS RAPIDOS",
    padx=20,
    pady=20
)

frame_menu.pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Button(frame_menu,text="Ventas",width=18).grid(row=0,column=0,padx=10,pady=10)
tk.Button(frame_menu,text="Inventarios",width=18).grid(row=0,column=1,padx=10,pady=10)
tk.Button(frame_menu,text="Produccion",width=18).grid(row=0,column=2,padx=10,pady=10)
tk.Button(frame_menu,text="Compras",width=18).grid(row=0,column=3,padx=10,pady=10)

tk.Button(frame_menu,text="Cuentas por Cobrar",width=18).grid(row=1,column=0,padx=10,pady=10)
tk.Button(frame_menu,text="Cuentas por Pagar",width=18).grid(row=1,column=1,padx=10,pady=10)
tk.Button(frame_menu,text="Balance General",width=18).grid(row=1,column=2,padx=10,pady=10)
tk.Button(frame_menu,text="Dashboard",width=18).grid(row=1,column=3,padx=10,pady=10)

# ==================================
# ALERTAS
# ==================================

frame_alertas = tk.LabelFrame(
    ventana,
    text="ALERTAS",
    padx=20,
    pady=20
)

frame_alertas.pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Label(
    frame_alertas,
    text="Sistema operativo correctamente"
).pack()

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    command=actualizar_dashboard
)

btn_actualizar.pack(pady=20)

actualizar_dashboard()

ventana.mainloop()