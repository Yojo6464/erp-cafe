import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# FUNCIONES
# =====================================

def cargar_proveedores():

    cursor.execute("""
    SELECT nombre
    FROM proveedores
    ORDER BY nombre
    """)

    proveedores = []

    for fila in cursor.fetchall():
        proveedores.append(fila[0])

    combo_proveedor["values"] = proveedores


def mostrar_cuentas():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        proveedor,
        valor,
        saldo,
        vencimiento,
        estado
    FROM cuentas_pagar
    ORDER BY id DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def crear_cuenta():

    try:

        proveedor = combo_proveedor.get()

        valor = float(
            entry_valor.get()
        )

        dias = int(
            entry_dias.get()
        )

        fecha = datetime.now()

        vencimiento = (
            fecha +
            timedelta(days=dias)
        ).strftime("%Y-%m-%d")

        cursor.execute("""
        INSERT INTO cuentas_pagar(
            proveedor,
            valor,
            saldo,
            fecha,
            vencimiento,
            estado
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            proveedor,
            valor,
            valor,
            fecha.strftime("%Y-%m-%d"),
            vencimiento,
            "PENDIENTE"
        ))

        conexion.commit()

        messagebox.showinfo(
            "OK",
            "Cuenta por pagar creada."
        )

        mostrar_cuentas()

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
    "ERP Café Alto de la Cruz - Cuentas por Pagar"
)

ventana.geometry("1100x700")

titulo = tk.Label(
    ventana,
    text="CUENTAS POR PAGAR",
    font=("Arial",18,"bold")
)

titulo.pack(pady=15)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)
frame.pack(pady=10)

tk.Label(
    frame,
    text="Proveedor"
).grid(row=0,column=0,padx=5)

combo_proveedor = ttk.Combobox(
    frame,
    width=30,
    state="readonly"
)

combo_proveedor.grid(
    row=1,
    column=0
)

tk.Label(
    frame,
    text="Valor"
).grid(row=0,column=1,padx=5)

entry_valor = tk.Entry(
    frame,
    width=15
)

entry_valor.grid(
    row=1,
    column=1
)

tk.Label(
    frame,
    text="Días Crédito"
).grid(row=0,column=2,padx=5)

entry_dias = tk.Entry(
    frame,
    width=10
)

entry_dias.grid(
    row=1,
    column=2
)

tk.Button(
    ventana,
    text="Crear Cuenta",
    width=25,
    command=crear_cuenta
).pack(pady=10)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Proveedor",
        "Valor",
        "Saldo",
        "Vencimiento",
        "Estado"
    ),
    show="headings"
)

for col in (
    "ID",
    "Proveedor",
    "Valor",
    "Saldo",
    "Vencimiento",
    "Estado"
):
    tabla.heading(
        col,
        text=col
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# INICIO
# =====================================

cargar_proveedores()
mostrar_cuentas()

ventana.mainloop()

conexion.close()