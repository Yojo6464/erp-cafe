import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def cargar_indicadores():

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    # FINANCIEROS

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM bancos
    """)
    bancos = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_cobrar
    """)
    cuentas_cobrar = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(
        SUM(cantidad * costo_unitario),
        0
    )
    FROM inventario
    """)
    inventario = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(saldo),0)
    FROM cuentas_pagar
    """)
    cuentas_pagar = float(cursor.fetchone()[0])

    total_activos = (
        bancos +
        cuentas_cobrar +
        inventario
    )

    patrimonio = (
        total_activos -
        cuentas_pagar
    )

    # OPERATIVOS

    cursor.execute("""
    SELECT COUNT(*)
    FROM inventario
    """)
    registros_inventario = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(cantidad),0)
    FROM inventario
    """)
    cantidad_inventario = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT COUNT(*)
    FROM cuentas_cobrar
    """)
    clientes_pendientes = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT COUNT(*)
    FROM cuentas_pagar
    """)
    obligaciones = int(cursor.fetchone()[0])

    conexion.close()

    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_cxc.config(text=f"${cuentas_cobrar:,.0f}")
    lbl_inventario.config(text=f"${inventario:,.0f}")
    lbl_cxp.config(text=f"${cuentas_pagar:,.0f}")
    lbl_patrimonio.config(text=f"${patrimonio:,.0f}")

    lbl_registros.config(text=f"{registros_inventario:,}")
    lbl_cantidad.config(text=f"{cantidad_inventario:,.0f}")
    lbl_clientes.config(text=f"{clientes_pendientes:,}")
    lbl_obligaciones.config(text=f"{obligaciones:,}")


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard Gerencial V3"
)

ventana.geometry("1300x800")

titulo = tk.Label(
    ventana,
    text="DASHBOARD GERENCIAL",
    font=("Arial",24,"bold")
)

titulo.pack(pady=20)

# =========================
# FINANCIEROS
# =========================

frame1 = tk.LabelFrame(
    ventana,
    text="INDICADORES FINANCIEROS",
    padx=20,
    pady=20
)

frame1.pack(
    fill="x",
    padx=20,
    pady=10
)

lbl_bancos = tk.Label(frame1, text="$0", font=("Arial",14,"bold"))
lbl_cxc = tk.Label(frame1, text="$0", font=("Arial",14,"bold"))
lbl_inventario = tk.Label(frame1, text="$0", font=("Arial",14,"bold"))
lbl_cxp = tk.Label(frame1, text="$0", font=("Arial",14,"bold"))
lbl_patrimonio = tk.Label(frame1, text="$0", font=("Arial",14,"bold"))

tk.Label(frame1, text="Bancos").grid(row=0,column=0,padx=20,pady=10)
lbl_bancos.grid(row=1,column=0)

tk.Label(frame1, text="Cuentas por Cobrar").grid(row=0,column=1,padx=20,pady=10)
lbl_cxc.grid(row=1,column=1)

tk.Label(frame1, text="Inventario").grid(row=0,column=2,padx=20,pady=10)
lbl_inventario.grid(row=1,column=2)

tk.Label(frame1, text="Cuentas por Pagar").grid(row=0,column=3,padx=20,pady=10)
lbl_cxp.grid(row=1,column=3)

tk.Label(frame1, text="Patrimonio").grid(row=0,column=4,padx=20,pady=10)
lbl_patrimonio.grid(row=1,column=4)

# =========================
# OPERATIVOS
# =========================

frame2 = tk.LabelFrame(
    ventana,
    text="INDICADORES OPERATIVOS",
    padx=20,
    pady=20
)

frame2.pack(
    fill="x",
    padx=20,
    pady=10
)

lbl_registros = tk.Label(frame2, text="0", font=("Arial",14,"bold"))
lbl_cantidad = tk.Label(frame2, text="0", font=("Arial",14,"bold"))
lbl_clientes = tk.Label(frame2, text="0", font=("Arial",14,"bold"))
lbl_obligaciones = tk.Label(frame2, text="0", font=("Arial",14,"bold"))

tk.Label(frame2, text="Registros Inventario").grid(row=0,column=0,padx=20,pady=10)
lbl_registros.grid(row=1,column=0)

tk.Label(frame2, text="Cantidad Inventario").grid(row=0,column=1,padx=20,pady=10)
lbl_cantidad.grid(row=1,column=1)

tk.Label(frame2, text="Clientes Pendientes").grid(row=0,column=2,padx=20,pady=10)
lbl_clientes.grid(row=1,column=2)

tk.Label(frame2, text="Obligaciones").grid(row=0,column=3,padx=20,pady=10)
lbl_obligaciones.grid(row=1,column=3)

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    command=cargar_indicadores
)

btn_actualizar.pack(pady=25)

cargar_indicadores()

ventana.mainloop()