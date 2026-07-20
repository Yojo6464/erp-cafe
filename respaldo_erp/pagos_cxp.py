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


def cargar_historial(cuenta_id):

    tabla_historial.delete(
        *tabla_historial.get_children()
    )

    cursor.execute("""
    SELECT
        id,
        fecha,
        valor
    FROM pagos_cxp
    WHERE cuenta_id=?
    ORDER BY id DESC
    """,
    (cuenta_id,)
    )

    for fila in cursor.fetchall():

        tabla_historial.insert(
            "",
            tk.END,
            values=fila
        )


def seleccionar_cuenta(event):

    seleccion = tabla.selection()

    if not seleccion:
        return

    datos = tabla.item(
        seleccion[0]
    )["values"]

    cuenta_id = datos[0]

    cargar_historial(cuenta_id)


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

    cuenta_id = int(datos[0])

    cursor.execute("""
    SELECT saldo
    FROM cuentas_pagar
    WHERE id=?
    """,
    (cuenta_id,)
    )

    saldo_actual = float(
        cursor.fetchone()[0]
    )

    if valor_pago > saldo_actual:

        messagebox.showerror(
            "Error",
            "El pago supera el saldo."
        )
        return

    nuevo_saldo = saldo_actual - valor_pago

    estado = "PENDIENTE"

    if nuevo_saldo <= 0:
        nuevo_saldo = 0
        estado = "PAGADA"

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
    INSERT INTO pagos_cxp(
        cuenta_id,
        fecha,
        valor
    )
    VALUES(?,?,?)
    """,
    (
        cuenta_id,
        fecha,
        valor_pago
    ))

    cursor.execute("""
    UPDATE cuentas_pagar
    SET saldo=?,
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

    entry_pago.delete(
        0,
        tk.END
    )

    cargar_cuentas()
    cargar_historial(cuenta_id)

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Pagos CxP"
)

ventana.geometry("1200x750")

titulo = tk.Label(
    ventana,
    text="PAGOS DE CUENTAS POR PAGAR",
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

tabla.bind(
    "<<TreeviewSelect>>",
    seleccionar_cuenta
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
).pack(side="left")

entry_pago = tk.Entry(
    frame_pago,
    width=20
)

entry_pago.pack(
    side="left",
    padx=10
)

tk.Button(
    frame_pago,
    text="Registrar Pago",
    command=registrar_pago
).pack(side="left")

# =====================================
# HISTORIAL
# =====================================

subtitulo = tk.Label(
    ventana,
    text="Historial de Pagos",
    font=("Arial",12,"bold")
)

subtitulo.pack()

tabla_historial = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Valor"
    ),
    show="headings"
)

tabla_historial.heading(
    "ID",
    text="ID"
)

tabla_historial.heading(
    "Fecha",
    text="Fecha"
)

tabla_historial.heading(
    "Valor",
    text="Valor Pagado"
)

tabla_historial.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# INICIO
# =====================================

cargar_cuentas()

ventana.mainloop()

conexion.close()