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

def cargar_cuentas():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        cliente,
        valor,
        saldo,
        vencimiento,
        estado
    FROM cuentas_cobrar
    ORDER BY id DESC
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def registrar_pago():

    seleccion = tabla.selection()

    if not seleccion:

        messagebox.showerror(
            "Error",
            "Seleccione una cuenta."
        )
        return

    try:

        valor_pago = float(
            entry_pago.get()
        )

    except:

        messagebox.showerror(
            "Error",
            "Valor inválido."
        )
        return

    datos = tabla.item(
        seleccion[0]
    )["values"]

    cuenta_id = datos[0]
    saldo_actual = float(datos[3])

    if valor_pago <= 0:

        messagebox.showerror(
            "Error",
            "El pago debe ser mayor que cero."
        )
        return

    if valor_pago > saldo_actual:

        messagebox.showerror(
            "Error",
            "El pago supera el saldo."
        )
        return

    nuevo_saldo = saldo_actual - valor_pago

    estado = "PAGADA"

    if nuevo_saldo > 0:
        estado = "PENDIENTE"

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
    INSERT INTO pagos_cxc
    (
        cuenta_id,
        fecha,
        valor_pagado
    )
    VALUES (?,?,?)
    """,
    (
        cuenta_id,
        fecha,
        valor_pago
    ))

    cursor.execute("""
    UPDATE cuentas_cobrar
    SET
        saldo=?,
        estado=?
    WHERE id=?
    """,
    (
        nuevo_saldo,
        estado,
        cuenta_id
    ))

    conexion.commit()

    messagebox.showinfo(
        "Pago Registrado",
        f"Nuevo saldo: ${nuevo_saldo:,.0f}"
    )
    entry_pago.delete(0, tk.END)



def cargar_historial():

    historial.delete(*historial.get_children())

    seleccion = tabla.selection()

    if not seleccion:
        return

    datos = tabla.item(
        seleccion[0]
    )["values"]

    cuenta_id = datos[0]

    cursor.execute("""
    SELECT
        id,
        fecha,
        valor_pagado
    FROM pagos_cxc
    WHERE cuenta_id=?
    ORDER BY id DESC
    """,
    (
        cuenta_id,
    ))

    for fila in cursor.fetchall():

        historial.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Pagos CxC"
)

ventana.geometry("1200x700")

titulo = tk.Label(
    ventana,
    text="PAGOS DE CUENTAS POR COBRAR",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# TABLA CUENTAS
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Cliente",
        "Valor",
        "Saldo",
        "Vencimiento",
        "Estado"
    ),
    show="headings"
)

for col in (
    "ID",
    "Cliente",
    "Valor",
    "Saldo",
    "Vencimiento",
    "Estado"
):
    tabla.heading(col, text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

tabla.bind(
    "<<TreeviewSelect>>",
    lambda e: cargar_historial()
)

# =====================================
# PAGO
# =====================================

frame_pago = tk.Frame(
    ventana
)

frame_pago.pack(pady=10)

tk.Label(
    frame_pago,
    text="Valor Pago"
).grid(
    row=0,
    column=0,
    padx=10
)

entry_pago = tk.Entry(
    frame_pago
)

entry_pago.grid(
    row=0,
    column=1
)

tk.Button(
    frame_pago,
    text="Registrar Pago",
    command=registrar_pago
).grid(
    row=0,
    column=2,
    padx=10
)

# =====================================
# HISTORIAL
# =====================================

tk.Label(
    ventana,
    text="Historial de Pagos",
    font=("Arial",12,"bold")
).pack()

historial = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Valor"
    ),
    show="headings"
)

historial.heading(
    "ID",
    text="ID"
)

historial.heading(
    "Fecha",
    text="Fecha"
)

historial.heading(
    "Valor",
    text="Valor Pagado"
)
historial.column("ID", width=80)
historial.column("Fecha", width=250)
historial.column("Valor", width=150)

historial.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# CARGA INICIAL
# =====================================

cargar_cuentas()

cursor.execute("""
SELECT
    id,
    fecha,
    valor_pagado
FROM pagos_cxc
ORDER BY id DESC
""")

for fila in cursor.fetchall():

    historial.insert(
        "",
        tk.END,
        values=fila
    )

ventana.mainloop()


conexion.close()