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
CREATE TABLE IF NOT EXISTS nomina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empleado TEXT,
    cargo TEXT,
    salario_base REAL,
    dias_trabajados REAL,
    horas_extras REAL,
    bonificaciones REAL,
    salud REAL,
    pension REAL,
    otros_descuentos REAL,
    total_devengado REAL,
    total_deducciones REAL,
    neto_pagar REAL,
    fecha TEXT
)
""")
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
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Nómina V2"
)

ventana.geometry("1000x600")

titulo = tk.Label(
    ventana,
    text="NÓMINA QUINCENAL V2",
    font=("Arial",20,"bold")
)

titulo.pack(pady=20)

mensaje = tk.Label(
    ventana,
    text="Paso 1 - Tabla Nómina creada correctamente",
    font=("Arial",12)
)

mensaje.pack(pady=10)
# =====================================
# EMPLEADOS
# =====================================

tk.Label(
    ventana,
    text="Empleado"
).pack(pady=5)

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
# PRESTACIONES SOCIALES
# =====================================

def calcular_prestaciones():

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
        cesantias
        + intereses
        + prima
        + vacaciones
    )

    lbl_prestaciones.config(
        text=(
            f"Cesantías: ${cesantias:,.0f} | "
            f"Intereses: ${intereses:,.0f} | "
            f"Prima: ${prima:,.0f} | "
            f"Vacaciones: ${vacaciones:,.0f} | "
            f"Total: ${total:,.0f}"
        )
    )

btn_prestaciones = tk.Button(
    ventana,
    text="Calcular Prestaciones",
    width=25,
    command=calcular_prestaciones
)

btn_prestaciones.pack(pady=5)

lbl_prestaciones = tk.Label(
    ventana,
    text="Prestaciones: $0",
    font=("Arial",12,"bold")
)

lbl_prestaciones.pack(pady=5)  
  # =====================================
# DATOS NOMINA
# =====================================

frame = tk.Frame(ventana)
frame.pack(pady=20)

tk.Label(frame,text="Dias Trabajados").grid(row=0,column=0,padx=10,pady=5)
txt_dias = tk.Entry(frame,width=15)
txt_dias.insert(0,"15")
txt_dias.grid(row=0,column=1)

tk.Label(frame,text="Horas Extras").grid(row=1,column=0,padx=10,pady=5)
txt_horas = tk.Entry(frame,width=15)
txt_horas.insert(0,"0")
txt_horas.grid(row=1,column=1)

tk.Label(frame,text="Bonificaciones").grid(row=2,column=0,padx=10,pady=5)
txt_bonos = tk.Entry(frame,width=15)
txt_bonos.insert(0,"0")
txt_bonos.grid(row=2,column=1)

tk.Label(frame,text="Otros Descuentos").grid(row=3,column=0,padx=10,pady=5)
txt_desc = tk.Entry(frame,width=15)
txt_desc.insert(0,"0")
txt_desc.grid(row=3,column=1)  
# =====================================
# CALCULAR
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

    dias = float(txt_dias.get())
    horas = float(txt_horas.get())
    bonos = float(txt_bonos.get())
    descuentos = float(txt_desc.get())

    salario_periodo = (salario / 30) * dias

    total_devengado = (
        salario_periodo
        + horas
        + bonos
    )

    salud = total_devengado * 0.04
    pension = total_devengado * 0.04

    total_deducciones = (
        salud
        + pension
        + descuentos
    )

    neto = (
        total_devengado
        - total_deducciones
    )

    lbl_neto.config(
        text=f"Neto a Pagar: ${neto:,.0f}"
    )

btn_calcular = tk.Button(
    ventana,
    text="Calcular Nomina",
    width=25,
    command=calcular
)

btn_calcular.pack(pady=10)

lbl_neto = tk.Label(
    ventana,
    text="Neto a Pagar: $0",
    font=("Arial",14,"bold")
)

lbl_neto.pack(pady=10)
# =====================================
# GUARDAR NOMINA
# =====================================

def guardar_nomina():

    nombre = cmb_empleado.get()

    cursor.execute("""
    SELECT cargo,salario
    FROM empleados
    WHERE nombre=?
    """,(nombre,))

    dato = cursor.fetchone()

    if dato is None:
        return

    cargo = dato[0]
    salario = float(dato[1])

    dias = float(txt_dias.get())
    horas = float(txt_horas.get())
    bonos = float(txt_bonos.get())
    descuentos = float(txt_desc.get())

    salario_periodo = (salario / 30) * dias

    total_devengado = (
        salario_periodo
        + horas
        + bonos
    )

    salud = total_devengado * 0.04
    pension = total_devengado * 0.04

    total_deducciones = (
        salud
        + pension
        + descuentos
    )

    neto = (
        total_devengado
        - total_deducciones
    )

    cursor.execute("""
    INSERT INTO nomina
    (
        empleado,
        cargo,
        salario_base,
        dias_trabajados,
        horas_extras,
        bonificaciones,
        salud,
        pension,
        otros_descuentos,
        total_devengado,
        total_deducciones,
        neto_pagar,
        fecha
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,date('now'))
    """,
    (
        nombre,
        cargo,
        salario,
        dias,
        horas,
        bonos,
        salud,
        pension,
        descuentos,
        total_devengado,
        total_deducciones,
        neto
    ))

    conexion.commit()

    lbl_neto.config(
        text=f"Nómina Guardada - Neto ${neto:,.0f}"
    )

btn_guardar = tk.Button(
    ventana,
    text="Guardar Nomina",
    width=25,
    command=guardar_nomina
)

btn_guardar.pack(pady=5)

# =====================================
# CONSULTAR NOMINA
# =====================================

from tkinter import ttk

def consultar_nomina():

    for fila in tabla.get_children():
        tabla.delete(fila)

    cursor.execute("""
    SELECT
        empleado,
        cargo,
        fecha,
        total_devengado,
        total_deducciones,
        neto_pagar
    FROM nomina
    ORDER BY id DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

btn_consultar = tk.Button(
    ventana,
    text="Consultar Nomina",
    width=25,
    command=consultar_nomina
)

btn_consultar.pack(pady=5)

# =====================================
# TABLA HISTORICA
# =====================================

columnas = (
    "Empleado",
    "Cargo",
    "Fecha",
    "Devengado",
    "Deducciones",
    "Neto"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=10
)

for col in columnas:
    tabla.heading(col, text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=10
)

ventana.mainloop()

conexion.close()