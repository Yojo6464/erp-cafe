import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# =====================================
# RUTA DEL PROYECTO
# =====================================

RUTA_BASE = r"C:\Users\jrive\visual"

# =====================================
# ABRIR MODULOS
# =====================================

def abrir_modulo(nombre_archivo):

    ruta = os.path.join(
        RUTA_BASE,
        nombre_archivo
    )

    if not os.path.exists(ruta):

        messagebox.showerror(
            "Error",
            f"No existe el archivo:\n{ruta}"
        )

        return

    try:

        subprocess.Popen(
            ["python", ruta]
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz"
)

ventana.state("zoomed")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial", 24, "bold")
)

titulo.pack(
    pady=20
)

subtitulo = tk.Label(
    ventana,
    text="Sistema Integral de Gestión Empresarial",
    font=("Arial", 12)
)

subtitulo.pack(
    pady=5
)

# =====================================
# FRAME PRINCIPAL
# =====================================

frame_principal = tk.Frame(
    ventana
)

frame_principal.pack(
    pady=20
)

# =====================================
# COMERCIAL
# =====================================

frame_comercial = tk.LabelFrame(
    frame_principal,
    text="COMERCIAL",
    padx=15,
    pady=15
)

frame_comercial.grid(
    row=0,
    column=0,
    padx=20,
    pady=10,
    sticky="n"
)

tk.Button(
    frame_comercial,
    text="Clientes",
    width=30,
    command=lambda:
    abrir_modulo("clientes.py")
).pack(pady=4)

tk.Button(
    frame_comercial,
    text="Ventas",
    width=30,
    command=lambda:
    abrir_modulo("ventas.py")
).pack(pady=4)

tk.Button(
    frame_comercial,
    text="Cuentas por Cobrar",
    width=30,
    command=lambda:
    abrir_modulo("cuentas_cobrar.py")
).pack(pady=4)

tk.Button(
    frame_comercial,
    text="Pagos CxC",
    width=30,
    command=lambda:
    abrir_modulo("pagos_cxc.py")
).pack(pady=4)

tk.Button(
    frame_comercial,
    text="Facturación PDF",
    width=30,
    command=lambda:
    abrir_modulo("facturacion_pdf.py")
).pack(pady=4)

# =====================================
# OPERACIONES
# =====================================

frame_operaciones = tk.LabelFrame(
    frame_principal,
    text="OPERACIONES",
    padx=15,
    pady=15
)

frame_operaciones.grid(
    row=0,
    column=1,
    padx=20,
    pady=10,
    sticky="n"
)

tk.Button(
    frame_operaciones,
    text="Inventario",
    width=30,
    command=lambda:
    abrir_modulo("inventario.py")
).pack(pady=4)
tk.Button(
    frame_operaciones,
    text="Producción V2",
    width=30,
    command=lambda:
    abrir_modulo("produccion_v2.py")
).pack(pady=4)

tk.Button(
    frame_operaciones,
    text="Costos",
    width=30,
    command=lambda:
    abrir_modulo("costos.py")
).pack(pady=4)

tk.Button(
    frame_operaciones,
    text="Compras",
    width=30,
    command=lambda:
    abrir_modulo("compras.py")
).pack(pady=4)

tk.Button(
    frame_operaciones,
    text="Proveedores",
    width=30,
    command=lambda:
    abrir_modulo("proveedores.py")
).pack(pady=4)

tk.Button(
    frame_operaciones,
    text="Cuentas por Pagar",
    width=30,
    command=lambda:
    abrir_modulo("cuentas_pagar.py")
).pack(pady=4)

tk.Button(
    frame_operaciones,
    text="Pagos CxP",
    width=30,
    command=lambda:
    abrir_modulo("pagos_cxp.py")
).pack(pady=4)

# =====================================
# TESORERIA
# =====================================

frame_tesoreria = tk.LabelFrame(
    frame_principal,
    text="TESORERÍA",
    padx=15,
    pady=15
)

frame_tesoreria.grid(
    row=0,
    column=2,
    padx=20,
    pady=10,
    sticky="n"
)

tk.Button(
    frame_tesoreria,
    text="Bancos",
    width=30,
    command=lambda:
    abrir_modulo("bancos.py")
).pack(pady=4)

tk.Button(
    frame_tesoreria,
    text="Movimientos Bancarios",
    width=30,
    command=lambda:
    abrir_modulo("movimientos_bancarios.py")
).pack(pady=4)

tk.Button(
    frame_tesoreria,
    text="Solicitudes de Pago",
    width=30,
    command=lambda:
    abrir_modulo("solicitudes_pagos.py")
).pack(pady=4)

tk.Button(
    frame_tesoreria,
    text="Aprobación Gerencial",
    width=30,
    command=lambda:
    abrir_modulo("aprobacion_pagos.py")
).pack(pady=4)

tk.Button(
    frame_tesoreria,
    text="Flujo de Caja",
    width=30,
    command=lambda:
    abrir_modulo("flujo_caja.py")
).pack(pady=4)
# =====================================
# RECURSOS HUMANOS
# =====================================

frame_rrhh = tk.LabelFrame(
    frame_principal,
    text="RECURSOS HUMANOS",
    padx=15,
    pady=15
)

frame_rrhh.grid(
    row=1,
    column=0,
    padx=20,
    pady=10,
    sticky="n"
)

tk.Button(
    frame_rrhh,
    text="Empleados",
    width=30,
    command=lambda:
    abrir_modulo("empleados_v1.py")
).pack(pady=4)

tk.Button(
    frame_rrhh,
    text="Nomina V3",
    width=30,
    command=lambda:
    abrir_modulo("nomina_v3.py")
).pack(pady=4)

tk.Button(
    frame_rrhh,
    text="Prestaciones V2",
    width=30,
    command=lambda:
    abrir_modulo("prestaciones_v2.py")
).pack(pady=4)

tk.Button(
    frame_rrhh,
    text="Dashboard RRHH",
    width=30,
    command=lambda:
    abrir_modulo("dashboard_rrhh_v1.py")
).pack(pady=4)
# =====================================
# DIRECCION EJECUTIVA
# =====================================

frame_direccion = tk.LabelFrame(
    frame_principal,
    text="DIRECCION EJECUTIVA",
    padx=15,
    pady=15
)

frame_direccion.grid(
    row=1,
    column=1,
    padx=20,
    pady=10,
    sticky="n"
)

tk.Button(
    frame_direccion,
    text="Dashboard Ejecutivo V9",
    width=30,
    command=lambda:
    abrir_modulo("dashboard_ejecutivo_v9.py")
).pack(pady=4)

tk.Button(
    frame_direccion,
    text="Dashboard Tesoreria V1",
    width=30,
    command=lambda:
    abrir_modulo("dashboard_tesoreria_v1.py")
).pack(pady=4)

tk.Button(
    frame_direccion,
    text="Estado de Resultados",
    width=30,
    command=lambda:
    abrir_modulo("estado_resultados.py")
).pack(pady=4)

# =====================================
# GERENCIA
# =====================================

frame_gerencia = tk.LabelFrame(
    frame_principal,
    text="GERENCIA",
    padx=15,
    pady=15
)

frame_gerencia.grid(
    row=1,
    column=2,
    columnspan=2,
    pady=20
)

tk.Button(
    frame_gerencia,
    text="Dashboard Gerencial",
    width=30,
    command=lambda:
    abrir_modulo("dashboard.py")
).pack(pady=4)

tk.Button(
    frame_gerencia,
    text="Rentabilidad",
    width=30,
    command=lambda:
    abrir_modulo("rentabilidad.py")
).pack(pady=4)

tk.Button(
    frame_gerencia,
    text="Reportes Excel",
    width=30,
    command=lambda:
    abrir_modulo("reporte_excel.py")
).pack(pady=4)
tk.Button(
    frame_gerencia,
    text="Estado de Resultados",
    width=30,
    command=lambda:
    abrir_modulo("estado_resultados.py")
).pack(pady=4)

# =====================================
# PIE
# =====================================

pie = tk.Label(
    ventana,
    text="Café Alto de la Cruz © 2026",
    font=("Arial", 10)
)

pie.pack(
    side="bottom",
    pady=20
)

ventana.mainloop()