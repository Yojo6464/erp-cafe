import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3

# =====================================
# BASE DE DATOS
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# CREAR TABLA
# =====================================

def crear_tabla():

    con = sqlite3.connect(RUTA_DB)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gastos_operativos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        categoria TEXT,
        concepto TEXT,
        proveedor TEXT,
        valor REAL,
        centro_costo TEXT,
        observaciones TEXT
    )
    """)

    con.commit()
    con.close()

# =====================================
# GUARDAR
# =====================================

def guardar():

    try:

        con = sqlite3.connect(RUTA_DB)
        cur = con.cursor()

        cur.execute("""
        INSERT INTO gastos_operativos
        (
            fecha,
            categoria,
            concepto,
            proveedor,
            valor,
            centro_costo,
            observaciones
        )
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            txt_fecha.get(),
            cmb_categoria.get(),
            txt_concepto.get(),
            txt_proveedor.get(),
            float(txt_valor.get()),
            txt_centro.get(),
            txt_obs.get()
        ))

        con.commit()
        con.close()

        messagebox.showinfo(
            "ERP",
            "Gasto guardado correctamente"
        )

        limpiar()
        cargar_datos()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# LIMPIAR
# =====================================

def limpiar():

    txt_fecha.delete(0, tk.END)
    txt_concepto.delete(0, tk.END)
    txt_proveedor.delete(0, tk.END)
    txt_valor.delete(0, tk.END)
    txt_centro.delete(0, tk.END)
    txt_obs.delete(0, tk.END)

# =====================================
# CARGAR DATOS
# =====================================

def cargar_datos():

    tabla.delete(*tabla.get_children())

    con = sqlite3.connect(RUTA_DB)
    cur = con.cursor()

    cur.execute("""
    SELECT
        id,
        fecha,
        categoria,
        concepto,
        valor
    FROM gastos_operativos
    ORDER BY id DESC
    """)

    registros = cur.fetchall()

    con.close()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================
# VENTANA
# =====================================

crear_tabla()

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Gastos Operativos V1"
)

ventana.geometry("1000x700")

titulo = tk.Label(
    ventana,
    text="GASTOS OPERATIVOS",
    font=("Arial",20,"bold")
)

titulo.pack(pady=15)

frame = tk.Frame(ventana)
frame.pack()

# FECHA

tk.Label(frame,text="Fecha").grid(row=0,column=0,padx=10,pady=5)

txt_fecha = tk.Entry(frame,width=25)
txt_fecha.grid(row=0,column=1)

# CATEGORIA

tk.Label(frame,text="Categoría").grid(row=1,column=0,padx=10,pady=5)

cmb_categoria = ttk.Combobox(
    frame,
    width=22,
    values=[
        "Administración",
        "Ventas",
        "Producción",
        "Logística",
        "Mantenimiento",
        "Servicios Públicos",
        "Financieros",
        "Otros"
    ]
)

cmb_categoria.grid(row=1,column=1)

# CONCEPTO

tk.Label(frame,text="Concepto").grid(row=2,column=0,padx=10,pady=5)

txt_concepto = tk.Entry(frame,width=40)
txt_concepto.grid(row=2,column=1)

# PROVEEDOR

tk.Label(frame,text="Proveedor").grid(row=3,column=0,padx=10,pady=5)

txt_proveedor = tk.Entry(frame,width=40)
txt_proveedor.grid(row=3,column=1)

# VALOR

tk.Label(frame,text="Valor").grid(row=4,column=0,padx=10,pady=5)

txt_valor = tk.Entry(frame,width=20)
txt_valor.grid(row=4,column=1)

# CENTRO COSTO

tk.Label(frame,text="Centro Costo").grid(row=5,column=0,padx=10,pady=5)

txt_centro = tk.Entry(frame,width=40)
txt_centro.grid(row=5,column=1)

# OBS

tk.Label(frame,text="Observaciones").grid(row=6,column=0,padx=10,pady=5)

txt_obs = tk.Entry(frame,width=50)
txt_obs.grid(row=6,column=1)

# BOTON

btn_guardar = tk.Button(
    ventana,
    text="Guardar Gasto",
    width=25,
    height=2,
    command=guardar
)

btn_guardar.pack(pady=15)

# TABLA

columnas = (
    "ID",
    "Fecha",
    "Categoría",
    "Concepto",
    "Valor"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=15
)

for col in columnas:

    tabla.heading(col,text=col)

tabla.pack(fill="both",expand=True,padx=20,pady=20)

cargar_datos()

ventana.mainloop()