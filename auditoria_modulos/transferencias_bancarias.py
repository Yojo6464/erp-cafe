import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# =====================================
# CONEXION
# =====================================

conexion = sqlite3.connect(
    r"C:\Users\jrive\visual\erp_cafe.db"
)

cursor = conexion.cursor()

# =====================================
# CARGAR BANCOS
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

        lista.append(
            f"{fila[0]} - {fila[1]} - ${fila[2]:,.0f}"
        )

    combo_origen["values"] = lista
    combo_destino["values"] = lista

    if len(lista) > 0:

        combo_origen.current(0)

        if len(lista) > 1:
            combo_destino.current(1)
        else:
            combo_destino.current(0)

# =====================================
# MOSTRAR HISTORIAL
# =====================================

def mostrar_transferencias():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        fecha,
        banco_origen,
        banco_destino,
        valor,
        autorizado_por
    FROM transferencias_bancarias
    ORDER BY id DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================
# TRANSFERIR
# =====================================

def realizar_transferencia():

    if combo_origen.get() == "":

        messagebox.showerror(
            "Error",
            "Seleccione banco origen"
        )

        return

    if combo_destino.get() == "":

        messagebox.showerror(
            "Error",
            "Seleccione banco destino"
        )

        return

    try:

        valor = float(
            entry_valor.get()
        )

    except:

        messagebox.showerror(
            "Error",
            "Valor inválido"
        )

        return

    if valor <= 0:

        messagebox.showerror(
            "Error",
            "El valor debe ser mayor que cero"
        )

        return

    texto_origen = combo_origen.get()
    texto_destino = combo_destino.get()

    origen_id = int(
        texto_origen.split(" - ")[0]
    )

    destino_id = int(
        texto_destino.split(" - ")[0]
    )

    if origen_id == destino_id:

        messagebox.showerror(
            "Error",
            "Seleccione bancos diferentes"
        )

        return

    cursor.execute("""
    SELECT banco,saldo
    FROM bancos
    WHERE id=?
    """,
    (
        origen_id,
    ))

    origen = cursor.fetchone()

    nombre_origen = origen[0]
    saldo_origen = float(origen[1])

    if saldo_origen < valor:

        messagebox.showerror(
            "Error",
            "Saldo insuficiente"
        )

        return

    cursor.execute("""
    SELECT banco,saldo
    FROM bancos
    WHERE id=?
    """,
    (
        destino_id,
    ))

    destino = cursor.fetchone()

    nombre_destino = destino[0]
    saldo_destino = float(destino[1])

    nuevo_origen = saldo_origen - valor
    nuevo_destino = saldo_destino + valor

    cursor.execute("""
    UPDATE bancos
    SET saldo=?
    WHERE id=?
    """,
    (
        nuevo_origen,
        origen_id
    ))

    cursor.execute("""
    UPDATE bancos
    SET saldo=?
    WHERE id=?
    """,
    (
        nuevo_destino,
        destino_id
    ))

    fecha = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
    INSERT INTO transferencias_bancarias(
        fecha,
        banco_origen,
        banco_destino,
        valor,
        autorizado_por
    )
    VALUES(?,?,?,?,?)
    """,
    (
        fecha,
        nombre_origen,
        nombre_destino,
        valor,
        "GERENCIA"
    ))

    cursor.execute("""
    INSERT INTO movimientos_bancos(
        fecha,
        banco_id,
        tipo,
        concepto,
        valor,
        saldo_anterior,
        saldo_nuevo,
        autorizado_por
    )
    VALUES(?,?,?,?,?,?,?,?)
    """,
    (
        fecha,
        origen_id,
        "TRANSFERENCIA SALIENTE",
        f"A {nombre_destino}",
        valor,
        saldo_origen,
        nuevo_origen,
        "GERENCIA"
    ))

    cursor.execute("""
    INSERT INTO movimientos_bancos(
        fecha,
        banco_id,
        tipo,
        concepto,
        valor,
        saldo_anterior,
        saldo_nuevo,
        autorizado_por
    )
    VALUES(?,?,?,?,?,?,?,?)
    """,
    (
        fecha,
        destino_id,
        "TRANSFERENCIA ENTRANTE",
        f"Desde {nombre_origen}",
        valor,
        saldo_destino,
        nuevo_destino,
        "GERENCIA"
    ))

    conexion.commit()

    messagebox.showinfo(
        "Correcto",
        "Transferencia registrada"
    )

    entry_valor.delete(
        0,
        tk.END
    )

    cargar_bancos()
    mostrar_transferencias()

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Transferencias Bancarias"
)

ventana.geometry("1200x700")

titulo = tk.Label(
    ventana,
    text="TRANSFERENCIAS BANCARIAS",
    font=("Arial",20,"bold")
)

titulo.pack(pady=15)

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(
    frame,
    text="Banco Origen"
).grid(row=0,column=0)

combo_origen = ttk.Combobox(
    frame,
    width=40,
    state="readonly"
)

combo_origen.grid(
    row=1,
    column=0,
    padx=5
)

tk.Label(
    frame,
    text="Banco Destino"
).grid(row=0,column=1)

combo_destino = ttk.Combobox(
    frame,
    width=40,
    state="readonly"
)

combo_destino.grid(
    row=1,
    column=1,
    padx=5
)

tk.Label(
    frame,
    text="Valor"
).grid(row=0,column=2)

entry_valor = tk.Entry(
    frame,
    width=20
)

entry_valor.grid(
    row=1,
    column=2,
    padx=5
)

tk.Button(
    ventana,
    text="Realizar Transferencia",
    width=30,
    command=realizar_transferencia
).pack(pady=15)

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Origen",
        "Destino",
        "Valor",
        "Autoriza"
    ),
    show="headings"
)

for col in (
    "ID",
    "Fecha",
    "Origen",
    "Destino",
    "Valor",
    "Autoriza"
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

cargar_bancos()
mostrar_transferencias()

ventana.mainloop()

conexion.close()
