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

def cargar_bancos():

    cursor.execute("""
    SELECT
        id,
        banco,
        saldo
    FROM bancos
    WHERE estado='ACTIVA'
    ORDER BY banco
    """)

    registros = cursor.fetchall()

    lista = []

    for fila in registros:

        texto = (
            f"{fila[0]} - "
            f"{fila[1]} - "
            f"Saldo ${fila[2]:,.0f}"
        )

        lista.append(texto)

    combo_banco["values"] = lista

    if lista:
        combo_banco.current(0)


# =====================================

def mostrar_movimientos():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        fecha,
        banco_id,
        tipo,
        concepto,
        valor,
        saldo_anterior,
        saldo_nuevo
    FROM movimientos_bancos
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

def registrar_movimiento():

    if combo_banco.get() == "":

        messagebox.showerror(
            "Error",
            "Seleccione un banco."
        )

        return

    try:

        valor = float(
            entry_valor.get()
        )

    except:

        messagebox.showerror(
            "Error",
            "Valor inválido."
        )

        return

    tipo = combo_tipo.get()

    concepto = entry_concepto.get().strip()

    if concepto == "":

        messagebox.showerror(
            "Error",
            "Ingrese un concepto."
        )

        return

    banco_id = int(
        combo_banco.get().split("-")[0].strip()
    )

    cursor.execute("""
    SELECT saldo
    FROM bancos
    WHERE id=?
    """,
    (banco_id,)
    )

    resultado = cursor.fetchone()

    if resultado is None:

        messagebox.showerror(
            "Error",
            "Banco no encontrado."
        )

        return

    saldo_actual = float(
        resultado[0]
    )

    saldo_anterior = saldo_actual

    if tipo == "CONSIGNACION":

        saldo_nuevo = (
            saldo_actual + valor
        )

    else:

        if valor > saldo_actual:

            messagebox.showerror(
                "Error",
                "Fondos insuficientes."
            )

            return

        saldo_nuevo = (
            saldo_actual - valor
        )

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
    INSERT INTO movimientos_bancos(

        fecha,
        banco_id,
        tipo,
        concepto,
        valor,
        saldo_anterior,
        saldo_nuevo

    )
    VALUES(?,?,?,?,?,?,?)
    """,
    (
        fecha,
        banco_id,
        tipo,
        concepto,
        valor,
        saldo_anterior,
        saldo_nuevo
    ))

    cursor.execute("""
    UPDATE bancos
    SET saldo=?
    WHERE id=?
    """,
    (
        saldo_nuevo,
        banco_id
    ))

    conexion.commit()

    messagebox.showinfo(
        "Éxito",
        f"Movimiento registrado.\n"
        f"Nuevo saldo: ${saldo_nuevo:,.0f}"
    )

    entry_concepto.delete(
        0,
        tk.END
    )

    entry_valor.delete(
        0,
        tk.END
    )

    cargar_bancos()
    mostrar_movimientos()


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Movimientos Bancarios"
)

ventana.geometry("1300x750")

titulo = tk.Label(
    ventana,
    text="MOVIMIENTOS BANCARIOS",
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
    text="Banco"
).grid(
    row=0,
    column=0,
    padx=5
)

combo_banco = ttk.Combobox(
    frame,
    width=40,
    state="readonly"
)

combo_banco.grid(
    row=1,
    column=0,
    padx=5
)

tk.Label(
    frame,
    text="Tipo"
).grid(
    row=0,
    column=1,
    padx=5
)

combo_tipo = ttk.Combobox(
    frame,
    width=20,
    state="readonly",
    values=[
        "CONSIGNACION",
        "RETIRO"
    ]
)

combo_tipo.grid(
    row=1,
    column=1,
    padx=5
)

tk.Label(
    frame,
    text="Concepto"
).grid(
    row=0,
    column=2,
    padx=5
)

entry_concepto = tk.Entry(
    frame,
    width=40
)

entry_concepto.grid(
    row=1,
    column=2,
    padx=5
)

tk.Label(
    frame,
    text="Valor"
).grid(
    row=0,
    column=3,
    padx=5
)

entry_valor = tk.Entry(
    frame,
    width=20
)

entry_valor.grid(
    row=1,
    column=3,
    padx=5
)

tk.Button(
    ventana,
    text="Registrar Movimiento",
    width=30,
    command=registrar_movimiento
).pack(pady=10)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Banco",
        "Tipo",
        "Concepto",
        "Valor",
        "Saldo Anterior",
        "Saldo Nuevo"
    ),
    show="headings"
)

for col in (
    "ID",
    "Fecha",
    "Banco",
    "Tipo",
    "Concepto",
    "Valor",
    "Saldo Anterior",
    "Saldo Nuevo"
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

cargar_bancos()
mostrar_movimientos()

ventana.mainloop()

conexion.close()