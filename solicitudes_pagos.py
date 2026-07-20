import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

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

        proveedores.append(
            fila[0]
        )

    combo_proveedor["values"] = proveedores


# =====================================

def cargar_bancos():

    cursor.execute("""
    SELECT banco
    FROM bancos
    WHERE estado='ACTIVA'
    ORDER BY banco
    """)

    bancos = []

    for fila in cursor.fetchall():

        bancos.append(
            fila[0]
        )

    combo_banco["values"] = bancos


# =====================================

def mostrar_solicitudes():

    tabla.delete(
        *tabla.get_children()
    )

    cursor.execute("""
    SELECT
        id,
        fecha,
        tipo_gasto,
        proveedor,
        concepto,
        valor,
        banco,
        estado
    FROM solicitudes_pago
    ORDER BY id DESC
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )


# =====================================

def guardar_solicitud():

    try:

        fecha = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        tipo_gasto = combo_tipo.get()

        proveedor = combo_proveedor.get()

        concepto = entry_concepto.get().strip()

        valor = float(
            entry_valor.get()
        )

        banco = combo_banco.get()

        if concepto == "":

            messagebox.showerror(
                "Error",
                "Ingrese concepto."
            )

            return

        cursor.execute("""
        INSERT INTO solicitudes_pago(

            fecha,
            proveedor,
            concepto,
            valor,
            banco,
            estado,
            fecha_aprobacion,
            tipo_gasto

        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            fecha,
            proveedor,
            concepto,
            valor,
            banco,
            "PENDIENTE",
            "",
            tipo_gasto
        ))

        conexion.commit()

        messagebox.showinfo(
            "OK",
            "Solicitud creada."
        )

        entry_concepto.delete(
            0,
            tk.END
        )

        entry_valor.delete(
            0,
            tk.END
        )

        mostrar_solicitudes()

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
    "ERP Café Alto de la Cruz - Solicitudes de Pago"
)

ventana.geometry("1400x750")

titulo = tk.Label(
    ventana,
    text="SOLICITUDES DE PAGO",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(
    frame,
    text="Tipo Gasto"
).grid(row=0,column=0,padx=5)

combo_tipo = ttk.Combobox(
    frame,
    width=20,
    state="readonly",
    values=[
        "Compra",
        "Maquila",
        "Transporte",
        "Nomina",
        "Servicios",
        "Impuestos",
        "Administracion",
        "Otros"
    ]
)

combo_tipo.grid(row=1,column=0)

tk.Label(
    frame,
    text="Proveedor"
).grid(row=0,column=1,padx=5)

combo_proveedor = ttk.Combobox(
    frame,
    width=25
)

combo_proveedor.grid(row=1,column=1)

tk.Label(
    frame,
    text="Concepto"
).grid(row=0,column=2,padx=5)

entry_concepto = tk.Entry(
    frame,
    width=40
)

entry_concepto.grid(row=1,column=2)

tk.Label(
    frame,
    text="Valor"
).grid(row=0,column=3,padx=5)

entry_valor = tk.Entry(
    frame,
    width=15
)

entry_valor.grid(row=1,column=3)

tk.Label(
    frame,
    text="Banco"
).grid(row=0,column=4,padx=5)

combo_banco = ttk.Combobox(
    frame,
    width=20,
    state="readonly"
)

combo_banco.grid(row=1,column=4)

tk.Button(
    ventana,
    text="Crear Solicitud",
    width=30,
    command=guardar_solicitud
).pack(pady=10)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Tipo",
        "Proveedor",
        "Concepto",
        "Valor",
        "Banco",
        "Estado"
    ),
    show="headings"
)

for col in (
    "ID",
    "Fecha",
    "Tipo",
    "Proveedor",
    "Concepto",
    "Valor",
    "Banco",
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
cargar_bancos()
mostrar_solicitudes()

ventana.mainloop()

conexion.close()