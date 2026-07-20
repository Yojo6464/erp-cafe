import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# CREAR TABLA
# =====================================

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cuentas_cobrar_v1 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    concepto TEXT,
    valor REAL,
    estado TEXT
)
""")

conexion.commit()
conexion.close()

# =====================================
# GUARDAR
# =====================================

def guardar_cuenta():

    try:

        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO cuentas_cobrar_v1
        (
            fecha,
            cliente,
            concepto,
            valor,
            estado
        )
        VALUES
        (?,?,?,?,?)
        """,
        (
            entry_fecha.get(),
            entry_cliente.get(),
            entry_concepto.get(),
            float(entry_valor.get()),
            combo_estado.get()
        ))

        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Cuentas por Cobrar",
            "Registro guardado correctamente"
        )

        limpiar()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# LIMPIAR
# =====================================

def limpiar():

    entry_fecha.delete(0, tk.END)
    entry_cliente.delete(0, tk.END)
    entry_concepto.delete(0, tk.END)
    entry_valor.delete(0, tk.END)

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Cuentas por Cobrar"
)

ventana.geometry("800x650")

titulo = tk.Label(
    ventana,
    text="CUENTAS POR COBRAR",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=10)

# FECHA

tk.Label(frame,text="Fecha").grid(
    row=0,column=0,padx=10,pady=10,sticky="w"
)

entry_fecha = tk.Entry(frame,width=35)
entry_fecha.grid(row=0,column=1)

# CLIENTE

tk.Label(frame,text="Cliente").grid(
    row=1,column=0,padx=10,pady=10,sticky="w"
)

entry_cliente = tk.Entry(frame,width=35)
entry_cliente.grid(row=1,column=1)

# CONCEPTO

tk.Label(frame,text="Concepto").grid(
    row=2,column=0,padx=10,pady=10,sticky="w"
)

entry_concepto = tk.Entry(frame,width=35)
entry_concepto.grid(row=2,column=1)

# VALOR

tk.Label(frame,text="Valor").grid(
    row=3,column=0,padx=10,pady=10,sticky="w"
)

entry_valor = tk.Entry(frame,width=35)
entry_valor.grid(row=3,column=1)

# ESTADO

tk.Label(frame,text="Estado").grid(
    row=4,column=0,padx=10,pady=10,sticky="w"
)

combo_estado = ttk.Combobox(
    frame,
    width=32,
    state="readonly"
)

combo_estado["values"] = (
    "Pendiente",
    "Pagado"
)

combo_estado.grid(row=4,column=1)

# BOTON

btn_guardar = tk.Button(
    ventana,
    text="Guardar Cuenta",
    width=25,
    height=2,
    command=guardar_cuenta
)

btn_guardar.pack(pady=30)

ventana.mainloop()