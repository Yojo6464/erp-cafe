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
# TABLA
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS cuentas_cobrar
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    concepto TEXT,
    valor REAL,
    saldo REAL,
    vencimiento TEXT,
    estado TEXT
)
""")

conexion.commit()

# =====================================
# FUNCIONES
# =====================================

def crear_cuenta():

    try:

        cliente = combo_cliente.get()

        valor = float(
            entry_valor.get()
        )

        dias = int(
            entry_dias.get()
        )

        fecha = datetime.now()

        vencimiento = fecha + timedelta(days=dias)

        cursor.execute("""
        INSERT INTO cuentas_cobrar
        (
            fecha,
            cliente,
            concepto,
            valor,
            saldo,
            vencimiento,
            estado
        )
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            fecha.strftime("%Y-%m-%d"),
            cliente,
            "Venta a crédito",
            valor,
            valor,
            vencimiento.strftime("%Y-%m-%d"),
            "PENDIENTE"
        ))

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Cuenta por cobrar creada."
        )

        mostrar_cartera()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================

def mostrar_cartera():

    tabla.delete(
        *tabla.get_children()
    )

    cursor.execute("""
    SELECT
        id,
        cliente,
        valor,
        saldo,
        vencimiento,
        estado
    FROM cuentas_cobrar
    ORDER BY vencimiento
    """)

    registros = cursor.fetchall()

    total = 0

    for fila in registros:

        total += fila[3]

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

    lbl_total.config(
        text=f"${total:,.0f}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Cuentas por Cobrar"
)

ventana.geometry("1100x650")

titulo = tk.Label(
    ventana,
    text="CUENTAS POR COBRAR",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(
    ventana
)

frame.pack(pady=10)

tk.Label(
    frame,
    text="Cliente"
).grid(row=0,column=0,padx=10)

combo_cliente = ttk.Combobox(
    frame,
    width=30
)

cursor.execute("""
SELECT nombre
FROM clientes
ORDER BY nombre
""")

combo_cliente["values"] = [
    fila[0]
    for fila in cursor.fetchall()
]

combo_cliente.grid(
    row=1,
    column=0
)

tk.Label(
    frame,
    text="Valor"
).grid(row=0,column=1,padx=10)

entry_valor = tk.Entry(
    frame
)

entry_valor.grid(
    row=1,
    column=1
)

tk.Label(
    frame,
    text="Días Crédito"
).grid(row=0,column=2,padx=10)

entry_dias = tk.Entry(
    frame
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
# TOTAL CARTERA
# =====================================

lbl_total = tk.Label(
    ventana,
    text="$0",
    font=("Arial",14,"bold")
)

lbl_total.pack(pady=5)

# =====================================
# TABLA
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

# =====================================
# CARGA INICIAL
# =====================================

mostrar_cartera()

ventana.mainloop()

conexion.close()