import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# =====================================
# RUTA ERP
# =====================================

RUTA_BASE = r"C:\Users\jrive\visual"

# =====================================
# ABRIR MODULO
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

    subprocess.Popen(
        ["python", ruta]
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Centro de Reportes V2"
)

ventana.geometry("900x700")

titulo = tk.Label(
    ventana,
    text="CENTRO DE REPORTES EJECUTIVO",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

# =====================================
# COMERCIAL
# =====================================

frame_comercial = tk.LabelFrame(
    ventana,
    text="COMERCIAL",
    padx=10,
    pady=10
)

frame_comercial.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Button(
    frame_comercial,
    text="Clientes",
    width=25,
    command=lambda:
    abrir_modulo("clientes.py")
).pack(side="left", padx=5)

tk.Button(
    frame_comercial,
    text="Ventas",
    width=25,
    command=lambda:
    abrir_modulo("ventas.py")
).pack(side="left", padx=5)

tk.Button(
    frame_comercial,
    text="Cuentas por Cobrar",
    width=25,
    command=lambda:
    abrir_modulo("cuentas_cobrar.py")
).pack(side="left", padx=5)

# =====================================
# OPERACIONES
# =====================================

frame_operaciones = tk.LabelFrame(
    ventana,
    text="OPERACIONES",
    padx=10,
    pady=10
)

frame_operaciones.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Button(
    frame_operaciones,
    text="Compras",
    width=25,
    command=lambda:
    abrir_modulo("compras.py")
).pack(side="left", padx=5)

tk.Button(
    frame_operaciones,
    text="Proveedores",
    width=25,
    command=lambda:
    abrir_modulo("proveedores.py")
).pack(side="left", padx=5)

tk.Button(
    frame_operaciones,
    text="Inventario",
    width=25,
    command=lambda:
    abrir_modulo("inventario.py")
).pack(side="left", padx=5)

# =====================================
# TESORERIA
# =====================================

frame_tesoreria = tk.LabelFrame(
    ventana,
    text="TESORERIA",
    padx=10,
    pady=10
)

frame_tesoreria.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Button(
    frame_tesoreria,
    text="Bancos",
    width=25,
    command=lambda:
    abrir_modulo("bancos.py")
).pack(side="left", padx=5)

tk.Button(
    frame_tesoreria,
    text="Flujo de Caja",
    width=25,
    command=lambda:
    abrir_modulo("flujo_caja.py")
).pack(side="left", padx=5)

# =====================================
# RRHH
# =====================================

frame_rrhh = tk.LabelFrame(
    ventana,
    text="RECURSOS HUMANOS",
    padx=10,
    pady=10
)

frame_rrhh.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Button(
    frame_rrhh,
    text="Nomina",
    width=25,
    command=lambda:
    abrir_modulo("nomina_v3.py")
).pack(side="left", padx=5)

tk.Button(
    frame_rrhh,
    text="Prestaciones",
    width=25,
    command=lambda:
    abrir_modulo("prestaciones_v2.py")
).pack(side="left", padx=5)

tk.Button(
    frame_rrhh,
    text="Dashboard RRHH",
    width=25,
    command=lambda:
    abrir_modulo("dashboard_rrhh_v1.py")
).pack(side="left", padx=5)

# =====================================
# DIRECCION EJECUTIVA
# =====================================

frame_ejecutivo = tk.LabelFrame(
    ventana,
    text="DIRECCION EJECUTIVA",
    padx=10,
    pady=10
)

frame_ejecutivo.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Button(
    frame_ejecutivo,
    text="Dashboard Ejecutivo V9",
    width=25,
    command=lambda:
    abrir_modulo("dashboard_ejecutivo_v9.py")
).pack(side="left", padx=5)

tk.Button(
    frame_ejecutivo,
    text="Dashboard Tesoreria",
    width=25,
    command=lambda:
    abrir_modulo("dashboard_tesoreria_v1.py")
).pack(side="left", padx=5)

tk.Button(
    frame_ejecutivo,
    text="Estado Resultados",
    width=25,
    command=lambda:
    abrir_modulo("estado_resultados.py")
).pack(side="left", padx=5)

ventana.mainloop()