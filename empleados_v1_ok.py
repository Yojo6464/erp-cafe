import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3

# =====================================
# BASE DE DATOS
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS empleados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    documento TEXT,
    cargo TEXT,
    salario REAL,
    fecha_ingreso TEXT,
    estado TEXT
)
""")

conexion.commit()

# =====================================
# FUNCIONES
# =====================================

def limpiar():

    txt_nombre.delete(0, tk.END)
    txt_documento.delete(0, tk.END)
    txt_cargo.delete(0, tk.END)
    txt_salario.delete(0, tk.END)
    txt_fecha.delete(0, tk.END)

    cmb_estado.set("Activo")


def guardar():

    nombre = txt_nombre.get()
    documento = txt_documento.get()
    cargo = txt_cargo.get()
    salario = txt_salario.get()
    fecha = txt_fecha.get()
    estado = cmb_estado.get()

    if nombre == "":
        messagebox.showwarning(
            "Validación",
            "Digite el nombre"
        )
        return

    cursor.execute("""
    INSERT INTO empleados
    (
        nombre,
        documento,
        cargo,
        salario,
        fecha_ingreso,
        estado
    )
    VALUES (?,?,?,?,?,?)
    """,
    (
        nombre,
        documento,
        cargo,
        salario,
        fecha,
        estado
    ))

    conexion.commit()

    messagebox.showinfo(
        "ERP",
        "Empleado guardado correctamente"
    )

    limpiar()
    consultar()


def consultar():

    for fila in tabla.get_children():
        tabla.delete(fila)

    cursor.execute("""
    SELECT
    id,
    nombre,
    documento,
    cargo,
    salario,
    fecha_ingreso,
    estado
    FROM empleados
    ORDER BY id
    """)

    datos = cursor.fetchall()

    for fila in datos:
        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def eliminar():

    seleccionado = tabla.selection()

    if not seleccionado:
        messagebox.showwarning(
            "ERP",
            "Seleccione un empleado"
        )
        return

    datos = tabla.item(seleccionado)

    id_empleado = datos["values"][0]

    cursor.execute(
        "DELETE FROM empleados WHERE id=?",
        (id_empleado,)
    )

    conexion.commit()

    consultar()

    messagebox.showinfo(
        "ERP",
        "Empleado eliminado"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Empleados V1"
)

ventana.geometry("1200x700")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="GESTIÓN DE EMPLEADOS",
    font=("Arial",20,"bold")
)

titulo.pack(pady=15)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(frame,text="Nombre").grid(row=0,column=0,padx=10,pady=5)
txt_nombre = tk.Entry(frame,width=40)
txt_nombre.grid(row=0,column=1)

tk.Label(frame,text="Documento").grid(row=1,column=0,padx=10,pady=5)
txt_documento = tk.Entry(frame,width=40)
txt_documento.grid(row=1,column=1)

tk.Label(frame,text="Cargo").grid(row=2,column=0,padx=10,pady=5)
txt_cargo = tk.Entry(frame,width=40)
txt_cargo.grid(row=2,column=1)

tk.Label(frame,text="Salario").grid(row=3,column=0,padx=10,pady=5)
txt_salario = tk.Entry(frame,width=40)
txt_salario.grid(row=3,column=1)

tk.Label(frame,text="Fecha Ingreso").grid(row=4,column=0,padx=10,pady=5)
txt_fecha = tk.Entry(frame,width=40)
txt_fecha.grid(row=4,column=1)

tk.Label(frame,text="Estado").grid(row=5,column=0,padx=10,pady=5)

cmb_estado = ttk.Combobox(
    frame,
    width=37,
    state="readonly"
)

cmb_estado["values"] = (
    "Activo",
    "Inactivo"
)

cmb_estado.current(0)
cmb_estado.grid(row=5,column=1)

# =====================================
# BOTONES
# =====================================

frame_botones = tk.Frame(ventana)

frame_botones.pack(pady=15)

tk.Button(
    frame_botones,
    text="Nuevo",
    width=15,
    command=limpiar
).grid(row=0,column=0,padx=5)

tk.Button(
    frame_botones,
    text="Guardar",
    width=15,
    command=guardar
).grid(row=0,column=1,padx=5)

tk.Button(
    frame_botones,
    text="Consultar",
    width=15,
    command=consultar
).grid(row=0,column=2,padx=5)

tk.Button(
    frame_botones,
    text="Eliminar",
    width=15,
    command=eliminar
).grid(row=0,column=3,padx=5)

# =====================================
# TABLA
# =====================================

columnas = (
    "ID",
    "Nombre",
    "Documento",
    "Cargo",
    "Salario",
    "Fecha",
    "Estado"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=15
)

for col in columnas:
    tabla.heading(col, text=col)

tabla.column("ID", width=60)
tabla.column("Nombre", width=250)
tabla.column("Documento", width=150)
tabla.column("Cargo", width=180)
tabla.column("Salario", width=120)
tabla.column("Fecha", width=120)
tabla.column("Estado", width=120)

tabla.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

consultar()

ventana.mainloop()

conexion.close()