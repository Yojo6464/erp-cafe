import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# FUNCIONES
# =====================================

def mostrar_bancos():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        banco,
        numero_cuenta,
        tipo_cuenta,
        titular,
        saldo,
        estado
    FROM bancos
    ORDER BY banco
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================

def guardar_banco():

    banco = entry_banco.get().strip()
    cuenta = entry_cuenta.get().strip()
    tipo = combo_tipo.get().strip()
    titular = entry_titular.get().strip()

    try:
        saldo = float(entry_saldo.get())
    except:
        messagebox.showerror(
            "Error",
            "Saldo inválido."
        )
        return

    if banco == "":
        return

    cursor.execute("""
    INSERT INTO bancos(
        banco,
        numero_cuenta,
        tipo_cuenta,
        titular,
        saldo,
        estado
    )
    VALUES(?,?,?,?,?,?)
    """, (
        banco,
        cuenta,
        tipo,
        titular,
        saldo,
        "ACTIVA"
    ))

    conexion.commit()

    messagebox.showinfo(
        "Éxito",
        "Cuenta bancaria registrada."
    )

    entry_banco.delete(0, tk.END)
    entry_cuenta.delete(0, tk.END)
    entry_titular.delete(0, tk.END)
    entry_saldo.delete(0, tk.END)

    mostrar_bancos()

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Bancos"
)

ventana.geometry("1200x650")

titulo = tk.Label(
    ventana,
    text="GESTIÓN DE BANCOS",
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
    text="Banco"
).grid(row=0,column=0,padx=5)

entry_banco = tk.Entry(
    frame,
    width=20
)

entry_banco.grid(row=1,column=0)

tk.Label(
    frame,
    text="Número Cuenta"
).grid(row=0,column=1,padx=5)

entry_cuenta = tk.Entry(
    frame,
    width=20
)

entry_cuenta.grid(row=1,column=1)

tk.Label(
    frame,
    text="Tipo"
).grid(row=0,column=2,padx=5)

combo_tipo = ttk.Combobox(
    frame,
    values=[
        "Ahorros",
        "Corriente"
    ],
    width=15
)

combo_tipo.grid(row=1,column=2)

tk.Label(
    frame,
    text="Titular"
).grid(row=0,column=3,padx=5)

entry_titular = tk.Entry(
    frame,
    width=25
)

entry_titular.grid(row=1,column=3)

tk.Label(
    frame,
    text="Saldo Inicial"
).grid(row=0,column=4,padx=5)

entry_saldo = tk.Entry(
    frame,
    width=15
)

entry_saldo.grid(row=1,column=4)

tk.Button(
    ventana,
    text="Guardar Banco",
    width=25,
    command=guardar_banco
).pack(pady=10)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Banco",
        "Cuenta",
        "Tipo",
        "Titular",
        "Saldo",
        "Estado"
    ),
    show="headings"
)

for col in (
    "ID",
    "Banco",
    "Cuenta",
    "Tipo",
    "Titular",
    "Saldo",
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

mostrar_bancos()

ventana.mainloop()

conexion.close()