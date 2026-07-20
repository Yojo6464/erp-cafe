import tkinter as tk
from tkinter import ttk
import sqlite3

# =====================================
# BASE DE DATOS
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS prestaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado TEXT,
    salario REAL,
    cesantias REAL,
    intereses_cesantias REAL,
    prima REAL,
    vacaciones REAL,
    total_prestaciones REAL,
    fecha TEXT
)
""")

conexion.commit()

# =====================================
# FUNCIONES
# =====================================

def calcular():

    nombre = cmb_empleado.get()

    cursor.execute("""
    SELECT salario
    FROM empleados
    WHERE nombre=?
    """,(nombre,))

    dato = cursor.fetchone()

    if dato is None:
        return

    salario = float(dato[0])

    cesantias = salario / 12
    intereses = cesantias * 0.12
    prima = salario / 12
    vacaciones = salario / 24

    total = (
        cesantias +
        intereses +
        prima +
        vacaciones
    )

    lbl_resultado.config(
        text=
        f"Total Prestaciones: ${total:,.0f}"
    )

def guardar():

    nombre = cmb_empleado.get()

    cursor.execute("""
    SELECT salario
    FROM empleados
    WHERE nombre=?
    """,(nombre,))

    dato = cursor.fetchone()

    if dato is None:
        return

    salario = float(dato[0])

    cesantias = salario / 12
    intereses = cesantias * 0.12
    prima = salario / 12
    vacaciones = salario / 24

    total = (
        cesantias +
        intereses +
        prima +
        vacaciones
    )

    cursor.execute("""
    INSERT INTO prestaciones
    (
        empleado,
        salario,
        cesantias,
        intereses_cesantias,
        prima,
        vacaciones,
        total_prestaciones,
        fecha
    )
    VALUES
    (?,?,?,?,?,?,?,date('now'))
    """,
    (
        nombre,
        salario,
        cesantias,
        intereses,
        prima,
        vacaciones,
        total
    ))

    conexion.commit()

    lbl_resultado.config(
        text=
        f"Prestaciones Guardadas: ${total:,.0f}"
    )

def consultar():

    for fila in tabla.get_children():
        tabla.delete(fila)

    cursor.execute("""
    SELECT
        empleado,
        fecha,
        salario,
        total_prestaciones
    FROM prestaciones
    ORDER BY id DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Prestaciones V2"
)

ventana.geometry("1000x650")

titulo = tk.Label(
    ventana,
    text="PRESTACIONES SOCIALES V2",
    font=("Arial",20,"bold")
)

titulo.pack(pady=20)

# =====================================
# EMPLEADOS
# =====================================

tk.Label(
    ventana,
    text="Empleado"
).pack()

cmb_empleado = ttk.Combobox(
    ventana,
    width=50,
    state="readonly"
)

cmb_empleado.pack(pady=5)

cursor.execute("""
SELECT nombre
FROM empleados
WHERE estado='Activo'
ORDER BY nombre
""")

empleados = []

for fila in cursor.fetchall():
    empleados.append(fila[0])

cmb_empleado["values"] = empleados

if len(empleados) > 0:
    cmb_empleado.current(0)

# =====================================
# BOTONES
# =====================================

btn_calcular = tk.Button(
    ventana,
    text="Calcular Prestaciones",
    width=25,
    command=calcular
)

btn_calcular.pack(pady=5)

btn_guardar = tk.Button(
    ventana,
    text="Guardar Prestaciones",
    width=25,
    command=guardar
)

btn_guardar.pack(pady=5)

btn_consultar = tk.Button(
    ventana,
    text="Consultar Prestaciones",
    width=25,
    command=consultar
)

btn_consultar.pack(pady=5)

lbl_resultado = tk.Label(
    ventana,
    text="Prestaciones: $0",
    font=("Arial",12,"bold")
)

lbl_resultado.pack(pady=10)

# =====================================
# TABLA
# =====================================

columnas = (
    "Empleado",
    "Fecha",
    "Salario",
    "Total"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=12
)

for col in columnas:
    tabla.heading(col,text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

ventana.mainloop()

conexion.close()