import tkinter as tk
import subprocess
import os

# =====================================
# FUNCION PARA ABRIR MODULOS
# =====================================

def abrir_modulo(archivo):

    try:

        if os.path.exists(archivo):

            subprocess.Popen(
                ["python", archivo]
            )

        else:

            print(
                f"No existe: {archivo}"
            )

    except Exception as e:

        print(e)

# =====================================
# VENTANA PRINCIPAL
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz"
)

ventana.geometry("600x700")

titulo = tk.Label(
    ventana,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Arial",24,"bold")
)

titulo.pack(pady=20)

subtitulo = tk.Label(
    ventana,
    text="MENÚ EJECUTIVO",
    font=("Arial",16)
)

subtitulo.pack(pady=10)

# =====================================
# BOTONES
# =====================================

tk.Button(
    ventana,
    text="Dashboard General",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "dashboard_general_v2.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Producción",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "produccion_cafe.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Inventario",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "inventario_cafe.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Existencias",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "existencias_inventario.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Ventas",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "ventas_cafe.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Cuentas por Cobrar",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "cuentas_cobrar_v1.py"
    )
).pack(pady=5)

tk.Button(
    ventana,
    text="Balance General",
    width=30,
    height=2,
    command=lambda:
    abrir_modulo(
        "balance_general_v2.py"
    )
).pack(pady=5)

# =====================================
# SALIR
# =====================================

tk.Button(
    ventana,
    text="Salir",
    width=30,
    height=2,
    bg="red",
    fg="white",
    command=ventana.destroy
).pack(pady=25)

# =====================================
# PIE
# =====================================

pie = tk.Label(
    ventana,
    text="ERP Café Alto de la Cruz v1.0",
    font=("Arial",10)
)

pie.pack(side="bottom", pady=10)

ventana.mainloop()