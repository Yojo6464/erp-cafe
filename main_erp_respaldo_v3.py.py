import tkinter as tk
from tkinter import messagebox
import sqlite3
import subprocess
import os
print("=" * 60)
print("ESTE ES EL MAIN_ERP QUE SE ESTÁ EJECUTANDO")
print(__file__)
print("=" * 60)

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"
RUTA_MODULOS = r"C:\Users\jrive\visual"


def valor(sql):
    con = None

    try:
        con = sqlite3.connect(RUTA_DB)
        cur = con.cursor()
        cur.execute(sql)

        dato = cur.fetchone()

        if dato is None or dato[0] is None:
            return 0

        return dato[0]

    except sqlite3.Error as e:
        print("=" * 60)
        print("ERROR DASHBOARD")
        print(sql)
        print(e)
        print("=" * 60)
        return 0

    finally:
        if con:
            con.close()


def abrir_modulo(nombre_archivo):

    print("=" * 60)
    print("SE EJECUTÓ abrir_modulo()")
    print("Archivo solicitado:", nombre_archivo)

    ruta = os.path.join(RUTA_MODULOS, nombre_archivo)

    print("Ruta:", ruta)
    print("Existe:", os.path.exists(ruta))
    print("=" * 60)

    if not os.path.exists(ruta):
        messagebox.showerror(
            "Error",
            f"No se encontró el módulo:\n{ruta}"
        )
        return

    subprocess.Popen(["python", ruta])


def actualizar():

    ventas = valor("""
        SELECT IFNULL(SUM(total),0)
        FROM ventas_cafe
    """)

    cartera = valor("""
        SELECT IFNULL(SUM(valor),0)
        FROM cuentas_cobrar_v1
        WHERE UPPER(estado)='PENDIENTE'
    """)

    bancos = valor("""
        SELECT IFNULL(SUM(saldo),0)
        FROM bancos
        WHERE UPPER(estado)='ACTIVA'
    """)

    clientes = valor("""
        SELECT COUNT(*)
        FROM clientes
    """)

    produccion = valor("""
        SELECT IFNULL(SUM(cafe_tostado),0)
        FROM produccion_cafe
    """)

    inventario = valor("""
        SELECT IFNULL(
            SUM(cantidad*COALESCE(costo_unitario,costo,0)),
            0
        )
        FROM inventario
    """)

    cxp = valor("""
        SELECT IFNULL(SUM(saldo),0)
        FROM cuentas_pagar
        WHERE saldo>0
    """)

    nomina = valor("""
        SELECT IFNULL(SUM(neto_pagar),0)
        FROM nomina
    """)

    prestaciones = valor("""
        SELECT IFNULL(SUM(total_prestaciones),0)
        FROM prestaciones
    """)

    utilidad = ventas * 0.40
    costo_personal = nomina + prestaciones

    lbl_ventas.config(text=f"${ventas:,.0f}")
    lbl_cartera.config(text=f"${cartera:,.0f}")
    lbl_bancos.config(text=f"${bancos:,.0f}")
    lbl_clientes.config(text=f"{clientes:,}")
    lbl_produccion.config(text=f"{produccion:,.0f} Kg")
    lbl_inventario.config(text=f"${inventario:,.0f}")
    lbl_cxp.config(text=f"${cxp:,.0f}")
    lbl_utilidad.config(text=f"${utilidad:,.0f}")
    lbl_nomina.config(text=f"${nomina:,.0f}")
    lbl_prestaciones.config(text=f"${prestaciones:,.0f}")
    lbl_costo_personal.config(text=f"${costo_personal:,.0f}")

    def refrescar_dashboard():

     actualizar()

    ventana.after(
        5000,
        refrescar_dashboard
    )

    ventana = tk.Tk()
    ventana.title("ERP Café Alto de la Cruz - Menú Principal")
    ventana.geometry("1350x780")
    ventana.configure(bg="#E9EEF4")

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial", 26, "bold"),
    bg="#E9EEF4",
    fg="#0F4C81"
)

titulo.pack(pady=(20, 5))

subtitulo = tk.Label(
    ventana,
    text="Dashboard Ejecutivo y Menú Principal",
    font=("Arial", 14),
    bg="#E9EEF4",
    fg="#333333"
)

subtitulo.pack(pady=(0, 15))


frame_modulos = tk.LabelFrame(
    ventana,
    text="MÓDULOS DEL ERP",
    font=("Arial", 13, "bold"),
    bg="white",
    padx=20,
    pady=15
)

frame_modulos.pack(fill="x", padx=30, pady=10)


tk.Button(
    frame_modulos,
    text="📦 Inventario",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("inventario_interfaz_v1_0.py")
).grid(row=0, column=0, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="🛒 Compras",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: messagebox.showinfo("Compras", "Módulo en desarrollo")
).grid(row=0, column=1, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="🏭 Producción",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: messagebox.showinfo("Producción", "Módulo en desarrollo")
).grid(row=0, column=2, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="💰 Ventas",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: messagebox.showinfo("Ventas", "Módulo en desarrollo")
).grid(row=0, column=3, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="👥 Clientes",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: messagebox.showinfo("Clientes", "Módulo en desarrollo")
).grid(row=1, column=0, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="🏢 Proveedores",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("proveedores.py")
).grid(row=1, column=1, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="🏦 Bancos",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("bancos.py")
).grid(row=1, column=2, padx=10, pady=8)


tk.Button(
    frame_modulos,
    text="📊 Reportes",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: messagebox.showinfo("Reportes", "Módulo en desarrollo")
).grid(row=1, column=3, padx=10, pady=8)

tk.Button(
    frame_modulos,
    text="📑 Cuentas por Pagar",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("cuentas_pagar.py")
).grid(row=2, column=0, padx=10, pady=8)

tk.Button(
    frame_modulos,
    text="📝 Solicitudes Pago",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("solicitudes_pagos.py")
).grid(row=2, column=1, padx=10, pady=8)

tk.Button(
    frame_modulos,
    text="✅ Aprobación Pagos",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("aprobacion_pagos.py")
).grid(row=2, column=2, padx=10, pady=8)

tk.Button(
    frame_modulos,
    text="💵 Pagos CxP",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("pagos_cxp.py")
).grid(row=2, column=3, padx=10, pady=8)

tk.Button(
    frame_modulos,
    text="💳 Transferencias",
    width=20,
    height=2,
    font=("Arial", 11, "bold"),
    command=lambda: abrir_modulo("transferencias_bancarias.py")
).grid(row=2, column=4, padx=10, pady=8)


frame = tk.LabelFrame(
    ventana,
    text="DASHBOARD EJECUTIVO",
    font=("Arial", 13, "bold"),
    bg="white",
    padx=20,
    pady=20
)

frame.pack(fill="both", expand=True, padx=30, pady=10)


tk.Label(frame, text="VENTAS", font=("Arial", 14, "bold"), bg="white").grid(row=0, column=0, padx=30, pady=15)
lbl_ventas = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_ventas.grid(row=1, column=0)


tk.Label(frame, text="CARTERA", font=("Arial", 14, "bold"), bg="white").grid(row=0, column=1, padx=30, pady=15)
lbl_cartera = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_cartera.grid(row=1, column=1)


tk.Label(frame, text="BANCOS", font=("Arial", 14, "bold"), bg="white").grid(row=0, column=2, padx=30, pady=15)
lbl_bancos = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_bancos.grid(row=1, column=2)


tk.Label(frame, text="CLIENTES", font=("Arial", 14, "bold"), bg="white").grid(row=0, column=3, padx=30, pady=15)
lbl_clientes = tk.Label(frame, text="0", font=("Arial", 16), bg="white")
lbl_clientes.grid(row=1, column=3)


tk.Label(frame, text="PRODUCCIÓN", font=("Arial", 14, "bold"), bg="white").grid(row=2, column=0, padx=30, pady=15)
lbl_produccion = tk.Label(frame, text="0 Kg", font=("Arial", 16), bg="white")
lbl_produccion.grid(row=3, column=0)


tk.Label(frame, text="VALOR INVENTARIO", font=("Arial", 14, "bold"), bg="white").grid(row=2, column=1, padx=30, pady=15)
lbl_inventario = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_inventario.grid(row=3, column=1)


tk.Label(frame, text="CUENTAS POR PAGAR", font=("Arial", 14, "bold"), bg="white").grid(row=2, column=2, padx=30, pady=15)
lbl_cxp = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_cxp.grid(row=3, column=2)


tk.Label(frame, text="UTILIDAD ESTIMADA", font=("Arial", 14, "bold"), bg="white").grid(row=2, column=3, padx=30, pady=15)
lbl_utilidad = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_utilidad.grid(row=3, column=3)


tk.Label(frame, text="NÓMINA", font=("Arial", 14, "bold"), bg="white").grid(row=4, column=0, padx=30, pady=15)
lbl_nomina = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_nomina.grid(row=5, column=0)


tk.Label(frame, text="PRESTACIONES", font=("Arial", 14, "bold"), bg="white").grid(row=4, column=1, padx=30, pady=15)
lbl_prestaciones = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_prestaciones.grid(row=5, column=1)


tk.Label(frame, text="COSTO PERSONAL", font=("Arial", 14, "bold"), bg="white").grid(row=4, column=2, padx=30, pady=15)
lbl_costo_personal = tk.Label(frame, text="$0", font=("Arial", 16), bg="white")
lbl_costo_personal.grid(row=5, column=2)


btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    height=2,
    command=actualizar
)

btn_actualizar.pack(pady=12)

refrescar_dashboard()

ventana.mainloop()

