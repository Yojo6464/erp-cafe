import os
import subprocess
import tkinter as tk
from tkinter import messagebox

RUTA_PROYECTO = r"C:\Users\jrive\visual"
RUTA_DASHBOARD = r"C:\Users\jrive\visual\main_erp.py"
RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"
PYTHONW = r"C:\Users\jrive\AppData\Local\Programs\Python\Python314\pythonw.exe"


def iniciar_erp():
    if not os.path.exists(PYTHONW):
        messagebox.showerror("Error", f"No se encontró Python:\n{PYTHONW}")
        return

    if not os.path.exists(RUTA_DASHBOARD):
        messagebox.showerror("Error", f"No se encontró el Dashboard:\n{RUTA_DASHBOARD}")
        return

    if not os.path.exists(RUTA_DB):
        messagebox.showerror("Error", f"No se encontró la base de datos:\n{RUTA_DB}")
        return

    subprocess.Popen(
        [PYTHONW, RUTA_DASHBOARD],
        cwd=RUTA_PROYECTO
    )

    ventana.destroy()


ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Inicio")
ventana.geometry("500x300")
ventana.resizable(False, False)
ventana.configure(bg="#E9EEF4")

tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial", 20, "bold"),
    bg="#E9EEF4",
    fg="#0F4C81"
).pack(pady=35)

tk.Label(
    ventana,
    text="Sistema Integrado de Gestión",
    font=("Arial", 13),
    bg="#E9EEF4"
).pack(pady=5)

tk.Button(
    ventana,
    text="INICIAR ERP",
    width=25,
    height=2,
    font=("Arial", 12, "bold"),
    command=iniciar_erp
).pack(pady=30)

tk.Label(
    ventana,
    text="Versión 0.90 - Sprint Integración",
    font=("Arial", 9),
    bg="#E9EEF4",
    fg="#555555"
).pack(side="bottom", pady=15)

ventana.mainloop()