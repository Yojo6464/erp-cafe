import tkinter as tk
import sqlite3

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# CONSULTAS
# =====================================

def obtener_valor(sql):

    try:

        cursor.execute(sql)

        dato = cursor.fetchone()[0]

        if dato is None:
            return 0

        return float(dato)

    except:

        return 0


# =====================================
# INDICADORES
# =====================================

saldo_bancos = obtener_valor("""
SELECT SUM(saldo)
FROM bancos
""")

cuentas_cobrar = obtener_valor("""
SELECT SUM(saldo)
FROM cuentas_cobrar
WHERE estado='PENDIENTE'
""")

cuentas_pagar = obtener_valor("""
SELECT SUM(saldo)
FROM cuentas_pagar
WHERE estado='PENDIENTE'
""")

ventas_totales = obtener_valor("""
SELECT SUM(total)
FROM ventas
""")

utilidad_total = obtener_valor("""
SELECT SUM(utilidad_total)
FROM ventas
""")

cursor.execute("""
SELECT
    SUM(
        cantidad * costo_unitario
    )
FROM inventario
""")

dato = cursor.fetchone()[0]

if dato is None:
    inventario_valor = 0
else:
    inventario_valor = float(dato)

patrimonio_operativo = (
    saldo_bancos
    + cuentas_cobrar
    + inventario_valor
    - cuentas_pagar
)

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard Financiero"
)

ventana.geometry("900x650")

titulo = tk.Label(
    ventana,
    text="DASHBOARD FINANCIERO",
    font=("Arial",20,"bold")
)

titulo.pack(pady=20)

# =====================================
# TARJETAS
# =====================================

frame = tk.Frame(ventana)
frame.pack(pady=10)

datos = [

    (
        "Saldo Bancos",
        saldo_bancos
    ),

    (
        "Cuentas por Cobrar",
        cuentas_cobrar
    ),

    (
        "Cuentas por Pagar",
        cuentas_pagar
    ),

    (
        "Valor Inventario",
        inventario_valor
    ),

    (
        "Ventas Acumuladas",
        ventas_totales
    ),

    (
        "Utilidad Acumulada",
        utilidad_total
    ),

    (
        "Patrimonio Operativo",
        patrimonio_operativo
    )

]

fila = 0
columna = 0

for nombre, valor in datos:

    tarjeta = tk.LabelFrame(
        frame,
        text=nombre,
        padx=20,
        pady=20
    )

    tarjeta.grid(
        row=fila,
        column=columna,
        padx=10,
        pady=10
    )

    tk.Label(
        tarjeta,
        text=f"${valor:,.0f}",
        font=("Arial",16,"bold")
    ).pack()

    columna += 1

    if columna > 2:
        columna = 0
        fila += 1

# =====================================
# CIERRE
# =====================================

ventana.mainloop()

conexion.close()