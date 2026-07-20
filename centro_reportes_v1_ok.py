import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# =====================================
# RUTA BASE
# =====================================

RUTA_BASE = r"C:\Users\jrive\visual"

# =====================================
# ABRIR REPORTES
# =====================================

def abrir_reporte(nombre_archivo):

    ruta = os.path.join(
        RUTA_BASE,
        nombre_archivo
    )

    if not os.path.exists(ruta):

        messagebox.showerror(
            "Error",
            f"No existe:\n{ruta}"
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
    "ERP Café Alto de la Cruz - Centro de Reportes V1"
)

ventana.geometry("700x600")

titulo = tk.Label(
    ventana,
    text="CENTRO DE REPORTES",
    font=("Arial",20,"bold")
)

titulo.pack(pady=20)

# =====================================
# REPORTES
# =====================================

tk.Button(
    ventana,
    text="Estado de Resultados",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("estado_resultados.py")
).pack(pady=5)

tk.Button(
    ventana,
    text="Dashboard Ejecutivo V9",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("dashboard_ejecutivo_v9.py")
).pack(pady=5)

tk.Button(
    ventana,
    text="Dashboard Tesoreria",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("dashboard_tesoreria_v1.py")
).pack(pady=5)

tk.Button(
    ventana,
    text="Dashboard RRHH",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("dashboard_rrhh_v1.py")
).pack(pady=5)

tk.Button(
    ventana,
    text="Nomina",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("nomina_v3.py")
).pack(pady=5)

tk.Button(
    ventana,
    text="Prestaciones",
    width=40,
    height=2,
    command=lambda:
    abrir_reporte("prestaciones_v2.py")
).pack(pady=5)

ventana.mainloop()