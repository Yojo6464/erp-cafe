import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# =====================================
# CONEXION
# =====================================

conexion = sqlite3.connect("erp_cafe.db")
cursor = conexion.cursor()

# =====================================
# REGISTRAR CUENTA
# =====================================

def registrar_cuenta():

    try:

        fecha = datetime.now().strftime(
            "%Y-%m-%d"
        )

        cliente = entry_cliente.get().strip()

        concepto = entry_concepto.get().strip()

        valor = float(
            entry_valor.get()
        )

        vencimiento = entry_vencimiento.get().strip()

        if cliente == "":

            messagebox.showerror(
                "Error",
                "Ingrese cliente"
            )

            return

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
        VALUES
        (?,?,?,?,?,?,?)
        """,
        (
            fecha,
            cliente,
            concepto,
            valor,
            valor,
            vencimiento,
            "PENDIENTE"
        ))

        conexion.commit()

        messagebox.showinfo(
            "Correcto",
            "Cuenta por cobrar registrada"
        )

        entry_cliente.delete(0, tk.END)
        entry_concepto.delete(0, tk.END)
        entry_valor.delete(0, tk.END)
        entry_vencimiento.delete(0, tk.END)

        cargar_cartera()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# CARGAR CARTERA
# =====================================

def cargar_cartera():

    for item in tabla.get_children():

        tabla.delete(item)

    cursor.execute("""
    SELECT
        id,
        fecha,
        cliente,
        concepto,
        valor,
        saldo,
        vencimiento,
        estado
    FROM cuentas_cobrar
    ORDER BY id DESC
    """)

    total_cartera = 0

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

        total_cartera += float(
            fila[5]
        )

    lbl_total.config(
        text=f"${total_cartera:,.0f}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Cuentas por Cobrar"
)

ventana.geometry("1200x700")

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(
    ventana
)

frame.pack(
    pady=10
)

tk.Label(
    frame,
    text="Cliente"
).grid(row=0, column=0)

entry_cliente = tk.Entry(
    frame,
    width=30
)

entry_cliente.grid(
    row=0,
    column=1
)

tk.Label(
    frame,
    text="Concepto"
).grid(row=1, column=0)

entry_concepto = tk.Entry(
    frame,
    width=30
)

entry_concepto.grid(
    row=1,
    column=1
)

tk.Label(
    frame,
    text="Valor"
).grid(row=2, column=0)

entry_valor = tk.Entry(
    frame,
    width=30
)

entry_valor.grid(
    row=2,
    column=1
)

tk.Label(
    frame,
    text="Vencimiento"
).grid(row=3, column=0)

entry_vencimiento = tk.Entry(
    frame,
    width=30
)

entry_vencimiento.grid(
    row=3,
    column=1
)

tk.Button(
    frame,
    text="Registrar Cuenta",
    bg="green",
    fg="white",
    command=registrar_cuenta
).grid(
    row=4,
    column=1,
    pady=10
)

# =====================================
# TABLA
# =====================================

columnas = (
    "ID",
    "Fecha",
    "Cliente",
    "Concepto",
    "Valor",
    "Saldo",
    "Vencimiento",
    "Estado"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings"
)

for col in columnas:

    tabla.heading(
        col,
        text=col
    )

    tabla.column(
        col,
        width=130
    )

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# RESUMEN
# =====================================

frame_total = tk.Frame(
    ventana
)

frame_total.pack(
    pady=10
)

tk.Label(
    frame_total,
    text="Total Cartera:"
).pack(
    side=tk.LEFT
)

lbl_total = tk.Label(
    frame_total,
    text="$0",
    font=("Arial", 12, "bold")
)

lbl_total.pack(
    side=tk.LEFT,
    padx=10
)

# =====================================
# CARGA INICIAL
# =====================================

cargar_cartera()

ventana.mainloop()

conexion.close()