import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ==========================
# BASE DE DATOS
# ==========================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS costos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    materia_prima REAL,
    maquila REAL,
    empaque REAL,
    transporte REAL,
    administracion REAL,
    costo_total REAL
)
""")

conexion.commit()

# ==========================
# FUNCIONES
# ==========================

def calcular_total():

    try:

        mp = float(entry_mp.get())
        maquila = float(entry_maquila.get())
        empaque = float(entry_empaque.get())
        transporte = float(entry_transporte.get())
        admin = float(entry_admin.get())

        total = mp + maquila + empaque + transporte + admin

        entry_total.config(state="normal")
        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")
        entry_total.config(state="readonly")

    except:

        messagebox.showerror(
            "Error",
            "Verifique los valores."
        )


def guardar_costo():

    try:

        producto = combo_producto.get()
        presentacion = combo_presentacion.get()

        if producto == "" or presentacion == "":

            messagebox.showerror(
                "Error",
                "Seleccione producto y presentación."
            )
            return

        mp = float(entry_mp.get())
        maquila = float(entry_maquila.get())
        empaque = float(entry_empaque.get())
        transporte = float(entry_transporte.get())
        admin = float(entry_admin.get())

        total = mp + maquila + empaque + transporte + admin

        cursor.execute("""
        INSERT INTO costos(
            producto,
            presentacion,
            materia_prima,
            maquila,
            empaque,
            transporte,
            administracion,
            costo_total
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            producto,
            presentacion,
            mp,
            maquila,
            empaque,
            transporte,
            admin,
            total
        ))

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Costo guardado correctamente."
        )

        entry_mp.delete(0, tk.END)
        entry_maquila.delete(0, tk.END)
        entry_empaque.delete(0, tk.END)
        entry_transporte.delete(0, tk.END)
        entry_admin.delete(0, tk.END)

        entry_total.config(state="normal")
        entry_total.delete(0, tk.END)
        entry_total.config(state="readonly")

        combo_producto.set("")
        combo_presentacion.set("")

        mostrar_costos()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


def mostrar_costos():

    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
    SELECT
        producto,
        presentacion,
        materia_prima,
        maquila,
        empaque,
        transporte,
        administracion,
        costo_total
    FROM costos
    ORDER BY producto, presentacion
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Costos")
ventana.geometry("1200x700")

# ==========================
# TITULO
# ==========================

tk.Label(
    ventana,
    text="GESTIÓN DE COSTOS",
    font=("Arial", 16, "bold")
).pack(pady=10)

# ==========================
# PRODUCTO
# ==========================

tk.Label(
    ventana,
    text="Producto"
).pack()

combo_producto = ttk.Combobox(
    ventana,
    values=[
        "Café Especial",
        "Café Premium",
        "Café Tradicional"
    ],
    state="readonly"
)

combo_producto.pack()

# ==========================
# PRESENTACION
# ==========================

tk.Label(
    ventana,
    text="Presentación"
).pack()

combo_presentacion = ttk.Combobox(
    ventana,
    values=[
        "125 g",
        "250 g",
        "500 g",
        "1000 g"
    ],
    state="readonly"
)

combo_presentacion.pack()

# ==========================
# MATERIA PRIMA
# ==========================

tk.Label(
    ventana,
    text="Materia Prima"
).pack()

entry_mp = tk.Entry(ventana)
entry_mp.pack()

# ==========================
# MAQUILA
# ==========================

tk.Label(
    ventana,
    text="Maquila"
).pack()

entry_maquila = tk.Entry(ventana)
entry_maquila.pack()

# ==========================
# EMPAQUE
# ==========================

tk.Label(
    ventana,
    text="Empaque"
).pack()

entry_empaque = tk.Entry(ventana)
entry_empaque.pack()

# ==========================
# TRANSPORTE
# ==========================

tk.Label(
    ventana,
    text="Transporte"
).pack()

entry_transporte = tk.Entry(ventana)
entry_transporte.pack()

# ==========================
# ADMINISTRACION
# ==========================

tk.Label(
    ventana,
    text="Administración"
).pack()

entry_admin = tk.Entry(ventana)
entry_admin.pack()

# ==========================
# TOTAL
# ==========================

tk.Label(
    ventana,
    text="Costo Total"
).pack()

entry_total = tk.Entry(
    ventana,
    state="readonly"
)

entry_total.pack()

# ==========================
# BOTONES
# ==========================

tk.Button(
    ventana,
    text="Calcular Total",
    width=25,
    command=calcular_total
).pack(pady=5)

tk.Button(
    ventana,
    text="Guardar Costo",
    width=25,
    command=guardar_costo
).pack(pady=5)

# ==========================
# TABLA
# ==========================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "Producto",
        "Presentación",
        "MP",
        "Maquila",
        "Empaque",
        "Transporte",
        "Administración",
        "Total"
    ),
    show="headings"
)

for col in (
    "Producto",
    "Presentación",
    "MP",
    "Maquila",
    "Empaque",
    "Transporte",
    "Administración",
    "Total"
):
    tabla.heading(col, text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# ==========================
# CARGA INICIAL
# ==========================

mostrar_costos()

ventana.mainloop()

conexion.close()