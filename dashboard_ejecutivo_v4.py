import tkinter as tk
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"


def valor(cursor, sql):
    try:
        cursor.execute(sql)
        dato = cursor.fetchone()[0]

        if dato is None:
            return 0

        return float(dato)

    except:
        return 0


def actualizar():

    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()

    # =========================
    # FINANZAS
    # =========================

    bancos = valor(
        cursor,
        "SELECT IFNULL(SUM(saldo),0) FROM bancos"
    )

    inventario = valor(
        cursor,
        """
        SELECT IFNULL(
        SUM(cantidad*costo_unitario),
        0
        )
        FROM inventario
        """
    )

    cuentas_pagar = valor(
        cursor,
        "SELECT IFNULL(SUM(saldo),0) FROM cuentas_pagar"
    )

    patrimonio = (
        bancos +
        inventario -
        cuentas_pagar
    )

    # =========================
    # PRODUCCION
    # =========================

    lotes = valor(
        cursor,
        "SELECT COUNT(*) FROM produccion_cafe"
    )

    pergamino = valor(
        cursor,
        "SELECT IFNULL(SUM(pergamino),0) FROM produccion_cafe"
    )

    verde = valor(
        cursor,
        "SELECT IFNULL(SUM(cafe_verde),0) FROM produccion_cafe"
    )

    tostado = valor(
        cursor,
        "SELECT IFNULL(SUM(cafe_tostado),0) FROM produccion_cafe"
    )

    # =========================
    # VENTAS
    # =========================

    ventas = valor(
        cursor,
        "SELECT COUNT(*) FROM ventas_cafe"
    )

    valor_ventas = valor(
        cursor,
        "SELECT IFNULL(SUM(total),0) FROM ventas_cafe"
    )

    # =========================
    # CARTERA
    # =========================

    cartera = valor(
        cursor,
        """
        SELECT IFNULL(SUM(valor),0)
        FROM cuentas_cobrar_v1
        WHERE estado='Pendiente'
        """
    )

    conexion.close()

    # =========================
    # ACTUALIZAR INDICADORES
    # =========================

    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_inventario.config(text=f"${inventario:,.0f}")
    lbl_patrimonio.config(text=f"${patrimonio:,.0f}")

    lbl_lotes.config(text=f"{lotes:,.0f}")
    lbl_pergamino.config(text=f"{pergamino:,.0f} kg")
    lbl_verde.config(text=f"{verde:,.0f} kg")
    lbl_tostado.config(text=f"{tostado:,.0f} kg")

    lbl_ventas.config(text=f"{ventas:,.0f}")
    lbl_valor_ventas.config(text=f"${valor_ventas:,.0f}")

    lbl_cartera.config(text=f"${cartera:,.0f}")

    # =========================
    # ALERTAS
    # =========================

    alertas = []

    if bancos > 0:
        alertas.append("🟢 Bancos con saldo positivo")
    else:
        alertas.append("🔴 Bancos sin saldo")

    if inventario > 0:
        alertas.append("🟢 Inventario disponible")
    else:
        alertas.append("🔴 Inventario agotado")

    if lotes > 0:
        alertas.append("🟢 Producción registrada")
    else:
        alertas.append("🔴 No existe producción")

    if cartera > 50000:
        alertas.append(
            f"🟡 Cartera pendiente: ${cartera:,.0f}"
        )
    else:
        alertas.append("🟢 Cartera controlada")

    texto_alertas = "\n".join(alertas)

    lbl_alertas.config(text=texto_alertas)


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard Ejecutivo V4"
)

ventana.geometry("1200x850")

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial",24,"bold")
)

titulo.pack(pady=15)

# =====================================
# FINANZAS
# =====================================

frame1 = tk.LabelFrame(
    ventana,
    text="FINANZAS",
    padx=20,
    pady=20
)

frame1.pack(fill="x", padx=20, pady=10)

tk.Label(frame1,text="Bancos").grid(row=0,column=0,padx=30)
tk.Label(frame1,text="Inventario").grid(row=0,column=1,padx=30)
tk.Label(frame1,text="Patrimonio").grid(row=0,column=2,padx=30)

lbl_bancos = tk.Label(frame1,font=("Arial",12,"bold"))
lbl_bancos.grid(row=1,column=0)

lbl_inventario = tk.Label(frame1,font=("Arial",12,"bold"))
lbl_inventario.grid(row=1,column=1)

lbl_patrimonio = tk.Label(frame1,font=("Arial",12,"bold"))
lbl_patrimonio.grid(row=1,column=2)

# =====================================
# PRODUCCION
# =====================================

frame2 = tk.LabelFrame(
    ventana,
    text="PRODUCCIÓN",
    padx=20,
    pady=20
)

frame2.pack(fill="x", padx=20, pady=10)

tk.Label(frame2,text="Lotes").grid(row=0,column=0,padx=20)
tk.Label(frame2,text="Pergamino").grid(row=0,column=1,padx=20)
tk.Label(frame2,text="Café Verde").grid(row=0,column=2,padx=20)
tk.Label(frame2,text="Café Tostado").grid(row=0,column=3,padx=20)

lbl_lotes = tk.Label(frame2,font=("Arial",12,"bold"))
lbl_lotes.grid(row=1,column=0)

lbl_pergamino = tk.Label(frame2,font=("Arial",12,"bold"))
lbl_pergamino.grid(row=1,column=1)

lbl_verde = tk.Label(frame2,font=("Arial",12,"bold"))
lbl_verde.grid(row=1,column=2)

lbl_tostado = tk.Label(frame2,font=("Arial",12,"bold"))
lbl_tostado.grid(row=1,column=3)

# =====================================
# VENTAS
# =====================================

frame3 = tk.LabelFrame(
    ventana,
    text="VENTAS",
    padx=20,
    pady=20
)

frame3.pack(fill="x", padx=20, pady=10)

tk.Label(frame3,text="Número Ventas").grid(row=0,column=0,padx=20)
tk.Label(frame3,text="Valor Ventas").grid(row=0,column=1,padx=20)

lbl_ventas = tk.Label(frame3,font=("Arial",12,"bold"))
lbl_ventas.grid(row=1,column=0)

lbl_valor_ventas = tk.Label(frame3,font=("Arial",12,"bold"))
lbl_valor_ventas.grid(row=1,column=1)

# =====================================
# CARTERA
# =====================================

frame4 = tk.LabelFrame(
    ventana,
    text="CUENTAS POR COBRAR",
    padx=20,
    pady=20
)

frame4.pack(fill="x", padx=20, pady=10)

tk.Label(frame4,text="Cartera Pendiente").grid(row=0,column=0)

lbl_cartera = tk.Label(
    frame4,
    font=("Arial",14,"bold")
)

lbl_cartera.grid(row=1,column=0)

# =====================================
# ALERTAS
# =====================================

frame5 = tk.LabelFrame(
    ventana,
    text="ALERTAS GERENCIALES",
    padx=20,
    pady=20
)

frame5.pack(fill="x", padx=20, pady=10)

lbl_alertas = tk.Label(
    frame5,
    justify="left",
    font=("Arial",11)
)

lbl_alertas.pack(anchor="w")

# =====================================
# BOTON
# =====================================

btn = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    command=actualizar
)

btn.pack(pady=20)

actualizar()

ventana.mainloop()