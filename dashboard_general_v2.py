import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def actualizar_dashboard():

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    # ==========================
    # FINANZAS
    # ==========================

    cursor.execute("SELECT IFNULL(SUM(saldo),0) FROM bancos")
    bancos = float(cursor.fetchone()[0])

    cursor.execute("SELECT IFNULL(SUM(saldo),0) FROM cuentas_cobrar")
    cuentas_cobrar = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(
        SUM(cantidad * costo_unitario),
        0
    )
    FROM inventario
    """)
    inventario = float(cursor.fetchone()[0])

    cursor.execute("SELECT IFNULL(SUM(saldo),0) FROM cuentas_pagar")
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

    # ==========================
    # OPERACIONES
    # ==========================

    cursor.execute("SELECT COUNT(*) FROM inventario")
    registros_inventario = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(cantidad),0)
    FROM inventario
    """)
    cantidad_inventario = float(cursor.fetchone()[0])

    # ==========================
    # PRODUCCION
    # ==========================

    cursor.execute("""
    SELECT COUNT(*)
    FROM produccion_cafe
    """)
    lotes = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(pergamino),0)
    FROM produccion_cafe
    """)
    pergamino = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(cafe_verde),0)
    FROM produccion_cafe
    """)
    verde = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(cafe_tostado),0)
    FROM produccion_cafe
    """)
    tostado = float(cursor.fetchone()[0])

    cursor.execute("""
    SELECT IFNULL(SUM(merma),0)
    FROM produccion_cafe
    """)
    merma = float(cursor.fetchone()[0])

    conexion.close()

    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_cxc.config(text=f"${cuentas_cobrar:,.0f}")
    lbl_inventario.config(text=f"${inventario:,.0f}")
    lbl_cxp.config(text=f"${cuentas_pagar:,.0f}")
    lbl_patrimonio.config(text=f"${patrimonio:,.0f}")

    lbl_registros.config(text=f"{registros_inventario:,}")
    lbl_cantidad.config(text=f"{cantidad_inventario:,.0f}")

    lbl_lotes.config(text=f"{lotes:,}")
    lbl_pergamino.config(text=f"{pergamino:,.0f} kg")
    lbl_verde.config(text=f"{verde:,.0f} kg")
    lbl_tostado.config(text=f"{tostado:,.0f} kg")
    lbl_merma.config(text=f"{merma:,.0f} kg")


ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard General V2"
)

ventana.geometry("1400x900")

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial",26,"bold")
)

titulo.pack(pady=15)

# ==================================
# FINANZAS
# ==================================

frame_finanzas = tk.LabelFrame(
    ventana,
    text="RESUMEN FINANCIERO",
    padx=20,
    pady=20
)

frame_finanzas.pack(fill="x", padx=20, pady=10)

lbl_bancos = tk.Label(frame_finanzas,text="$0",font=("Arial",14,"bold"))
lbl_cxc = tk.Label(frame_finanzas,text="$0",font=("Arial",14,"bold"))
lbl_inventario = tk.Label(frame_finanzas,text="$0",font=("Arial",14,"bold"))
lbl_cxp = tk.Label(frame_finanzas,text="$0",font=("Arial",14,"bold"))
lbl_patrimonio = tk.Label(frame_finanzas,text="$0",font=("Arial",14,"bold"))

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

frame_operaciones.pack(fill="x", padx=20, pady=10)

lbl_registros = tk.Label(frame_operaciones,text="0",font=("Arial",14,"bold"))
lbl_cantidad = tk.Label(frame_operaciones,text="0",font=("Arial",14,"bold"))

tk.Label(frame_operaciones,text="Registros Inventario").grid(row=0,column=0,padx=30)
tk.Label(frame_operaciones,text="Cantidad Inventario").grid(row=0,column=1,padx=30)

lbl_registros.grid(row=1,column=0)
lbl_cantidad.grid(row=1,column=1)

# ==================================
# PRODUCCION
# ==================================

frame_produccion = tk.LabelFrame(
    ventana,
    text="PRODUCCIÓN",
    padx=20,
    pady=20
)

frame_produccion.pack(fill="x", padx=20, pady=10)

lbl_lotes = tk.Label(frame_produccion,text="0",font=("Arial",14,"bold"))
lbl_pergamino = tk.Label(frame_produccion,text="0",font=("Arial",14,"bold"))
lbl_verde = tk.Label(frame_produccion,text="0",font=("Arial",14,"bold"))
lbl_tostado = tk.Label(frame_produccion,text="0",font=("Arial",14,"bold"))
lbl_merma = tk.Label(frame_produccion,text="0",font=("Arial",14,"bold"))

tk.Label(frame_produccion,text="Lotes").grid(row=0,column=0,padx=20)
tk.Label(frame_produccion,text="Pergamino").grid(row=0,column=1,padx=20)
tk.Label(frame_produccion,text="Café Verde").grid(row=0,column=2,padx=20)
tk.Label(frame_produccion,text="Café Tostado").grid(row=0,column=3,padx=20)
tk.Label(frame_produccion,text="Merma").grid(row=0,column=4,padx=20)

lbl_lotes.grid(row=1,column=0)
lbl_pergamino.grid(row=1,column=1)
lbl_verde.grid(row=1,column=2)
lbl_tostado.grid(row=1,column=3)
lbl_merma.grid(row=1,column=4)

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    command=actualizar_dashboard
)

btn_actualizar.pack(pady=20)

actualizar_dashboard()

ventana.mainloop()