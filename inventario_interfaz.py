# ==========================================================
# INVENTARIO - INTERFAZ V2
# ENTREGA 2.1
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
style = ttk.Style()

style.theme_use("clam")

style.configure(
    "Treeview.Heading",
    font=("Segoe UI",10,"bold")
)

style.configure(
    "Treeview",
    rowheight=28,
    font=("Segoe UI",10)
)
# ==========================================================
# BASE DE DATOS
# ==========================================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER,
    stock_minimo INTEGER,
    costo REAL,
    lote TEXT,
    fecha TEXT,
    despacho TEXT
)
""")

conexion.commit()
# Agregar columnas si la tabla ya existía en versión anterior
columnas_nuevas = [
    ("stock_minimo", "INTEGER DEFAULT 0"),
    ("costo", "REAL DEFAULT 0"),
    ("lote", "TEXT DEFAULT ''"),
    ("fecha", "TEXT DEFAULT ''"),
    ("despacho", "TEXT DEFAULT ''")
]

for nombre_columna, tipo_columna in columnas_nuevas:
    try:
        cursor.execute(
            f"ALTER TABLE inventario ADD COLUMN {nombre_columna} {tipo_columna}"
        )
    except sqlite3.OperationalError:
        pass

conexion.commit()
# ==========================================================
# FUNCIONES
# ==========================================================

def limpiar_formulario():
    combo_producto.set("")
    combo_presentacion.set("")
    txt_cantidad.delete(0, tk.END)
    txt_stock.delete(0, tk.END)
    txt_costo.delete(0, tk.END)
    txt_lote.delete(0, tk.END)
    txt_fecha.delete(0, tk.END)
    txt_despacho.delete(0, tk.END)
    lbl_valor.config(text="VALOR DEL INVENTARIO : $ 0.00")


def actualizar_indicadores():
    cursor.execute("SELECT COUNT(*) FROM inventario")
    referencias = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(cantidad),0) FROM inventario")
    unidades = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(cantidad * costo),0) FROM inventario")
    valor_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventario WHERE cantidad <= stock_minimo AND cantidad > 0")
    stock_bajo = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventario WHERE cantidad = 0")
    agotados = cursor.fetchone()[0]

    lbl_referencias.config(text=str(referencias))
    lbl_unidades.config(text=str(unidades))
    lbl_valor_total.config(text=f"${valor_total:,.0f}")
    lbl_stock.config(text=str(stock_bajo))
    lbl_agotados.config(text=str(agotados))


def cargar_inventario():
    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
        SELECT 
            id,
            producto,
            presentacion,
            cantidad,
            lote,
            COALESCE(costo_unitario, costo, 0) AS costo,
            cantidad * COALESCE(costo_unitario, costo, 0) AS valor,
            COALESCE(fecha_ingreso, fecha, '') AS fecha
        FROM inventario
        ORDER BY producto, presentacion
    """)

    registros = cursor.fetchall()

    for fila in registros:
        tabla.insert("", tk.END, values=fila)

    actualizar_indicadores()


def agregar_inventario():
    producto = combo_producto.get()
    presentacion = combo_presentacion.get()

    if producto == "":
        messagebox.showerror("Error", "Seleccione un producto.")
        return

    if presentacion == "":
        messagebox.showerror("Error", "Seleccione una presentación.")
        return

    try:
        cantidad = int(txt_cantidad.get())
        stock_minimo = int(txt_stock.get())
        costo = float(txt_costo.get())
    except:
        messagebox.showerror("Error", "Cantidad, stock mínimo y costo deben ser números.")
        return

    lote = txt_lote.get()
    fecha = txt_fecha.get()
    despacho = txt_despacho.get()

    cursor.execute("""
    INSERT INTO inventario (
        producto,
        presentacion,
        cantidad,
        stock_minimo,
        costo,
        lote,
        fecha,
        despacho
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        producto,
        presentacion,
        cantidad,
        stock_minimo,
        costo,
        lote,
        fecha,
        despacho
    ))

    conexion.commit()

    messagebox.showinfo("Éxito", "Inventario agregado correctamente.")

    limpiar_formulario()
    cargar_inventario()

# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Inventario")
ventana.state("zoomed")
ventana.configure(bg="#E9EEF4")

# ==========================================================
# GRID PRINCIPAL
# ==========================================================

ventana.grid_columnconfigure(0, weight=1)

ventana.grid_rowconfigure(0, weight=0)
ventana.grid_rowconfigure(1, weight=0)
ventana.grid_rowconfigure(2, weight=0)
ventana.grid_rowconfigure(3, weight=1)
ventana.grid_rowconfigure(4, weight=0)

# ==========================================================
# HEADER
# ==========================================================

frame_header = tk.Frame(
    ventana,
    bg="#0F4C81",
    height=90
)

frame_header.grid(
    row=0,
    column=0,
    sticky="nsew"
)

frame_header.grid_propagate(False)

lbl_empresa = tk.Label(
    frame_header,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Segoe UI",22,"bold"),
    bg="#0F4C81",
    fg="white"
)

lbl_empresa.pack(pady=(12,0))

lbl_modulo = tk.Label(
    frame_header,
    text="MÓDULO DE INVENTARIO",
    font=("Segoe UI",12),
    bg="#0F4C81",
    fg="white"
)

lbl_modulo.pack()

# ==========================================================
# PANEL REGISTRO
# ==========================================================

frame_registro = tk.LabelFrame(
    ventana,
    text="REGISTRO DE INVENTARIO",
    font=("Segoe UI",11,"bold"),
    bg="white",
    padx=20,
    pady=15
)

frame_registro.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=15,
    pady=(10,5)
)

frame_registro.grid_columnconfigure(1,weight=1)
frame_registro.grid_columnconfigure(3,weight=1)

# ==========================================================
# FILA 1
# ==========================================================

tk.Label(
    frame_registro,
    text="Producto",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=0,
    column=0,
    sticky="w",
    pady=6
)

combo_producto = ttk.Combobox(
    frame_registro,
    width=40,
    state="readonly"
)

combo_producto["values"] = (
    "Café Especial",
    "Café Premium",
    "Café Tradicional"
)

combo_producto.grid(
    row=0,
    column=1,
    padx=(10,25),
    sticky="ew"
)

tk.Label(
    frame_registro,
    text="Presentación",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=0,
    column=2,
    sticky="w"
)

combo_presentacion = ttk.Combobox(
    frame_registro,
    width=20,
    state="readonly"
)

combo_presentacion["values"] = (
    "125 g",
    "250 g",
    "500 g",
    "1000 g"
)

combo_presentacion.grid(
    row=0,
    column=3,
    sticky="w"
)

# ==========================================================
# FILA 2
# ==========================================================

tk.Label(
    frame_registro,
    text="Cantidad",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=1,
    column=0,
    sticky="w",
    pady=6
)

txt_cantidad = tk.Entry(
    frame_registro,
    width=30
)

txt_cantidad.grid(
    row=1,
    column=1,
    sticky="w",
    padx=(10,25)
)

tk.Label(
    frame_registro,
    text="Stock mínimo",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=1,
    column=2,
    sticky="w"
)

txt_stock = tk.Entry(
    frame_registro,
    width=22
)

txt_stock.grid(
    row=1,
    column=3,
    sticky="w"
)

# ==========================================================
# FILA 3
# ==========================================================

tk.Label(
    frame_registro,
    text="Costo Unitario",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=2,
    column=0,
    sticky="w",
    pady=6
)

txt_costo = tk.Entry(
    frame_registro,
    width=30
)

txt_costo.grid(
    row=2,
    column=1,
    sticky="w",
    padx=(10,25)
)

tk.Label(
    frame_registro,
    text="Lote",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=2,
    column=2,
    sticky="w"
)

txt_lote = tk.Entry(
    frame_registro,
    width=22
)

txt_lote.grid(
    row=2,
    column=3,
    sticky="w"
)

# ==========================================================
# FILA 4
# ==========================================================

tk.Label(
    frame_registro,
    text="Fecha Ingreso",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=3,
    column=0,
    sticky="w",
    pady=6
)

txt_fecha = tk.Entry(
    frame_registro,
    width=30
)

txt_fecha.grid(
    row=3,
    column=1,
    sticky="w",
    padx=(10,25)
)

tk.Label(
    frame_registro,
    text="No. Despacho",
    bg="white",
    font=("Segoe UI",10,"bold")
).grid(
    row=3,
    column=2,
    sticky="w"
)

txt_despacho = tk.Entry(
    frame_registro,
    width=22
)

txt_despacho.grid(
    row=3,
    column=3,
    sticky="w"
)

# ==========================================================
# VALOR
# ==========================================================

lbl_valor = tk.Label(
    frame_registro,
    text="VALOR DEL INVENTARIO : $ 0.00",
    bg="white",
    fg="#0F4C81",
    font=("Segoe UI",12,"bold")
)

lbl_valor.grid(
    row=4,
    column=0,
    columnspan=4,
    pady=(15,10)
)

# ==========================================================
# BOTONES
# ==========================================================

frame_botones = tk.Frame(
    frame_registro,
    bg="white"
)

frame_botones.grid(
    row=5,
    column=0,
    columnspan=4,
    pady=10
)

btn_agregar = tk.Button(
    frame_botones,
    text="AGREGAR INVENTARIO",
    width=22,
    height=2,
    bg="#0F4C81",
    fg="white",
    font=("Segoe UI",10,"bold"),
    command=agregar_inventario
)

btn_agregar.pack(
    side="left",
    padx=10
)

btn_limpiar = tk.Button(
    frame_botones,
    text="LIMPIAR",
    width=14,
    height=2
)

btn_limpiar.pack(
    side="left",
    padx=10
)

btn_cancelar = tk.Button(
    frame_botones,
    text="CANCELAR",
    width=14,
    height=2
)

btn_cancelar.pack(
    side="left",
    padx=10
)

# ==========================================================
# CONTINÚA EN LA ENTREGA 2.2
# ==========================================================
# ==========================================================
# PANEL ACCIONES
# ==========================================================

frame_acciones = tk.LabelFrame(
    ventana,
    text="ACCIONES",
    font=("Segoe UI",11,"bold"),
    bg="white",
    padx=15,
    pady=10
)

frame_acciones.grid(
    row=2,
    column=0,
    sticky="ew",
    padx=15,
    pady=(0,5)
)

#---------------------------------------------------------

btn_actualizar = tk.Button(
    frame_acciones,
    text="Actualizar",
    width=14,
    bg="#0F4C81",
    fg="white",
    font=("Segoe UI",9,"bold"),
    command=cargar_inventario
)

btn_actualizar.pack(side="left", padx=6)

#---------------------------------------------------------

btn_buscar = tk.Button(
    frame_acciones,
    text="Buscar",
    width=14,
    font=("Segoe UI",9)
)

btn_buscar.pack(side="left", padx=6)

#---------------------------------------------------------

btn_editar = tk.Button(
    frame_acciones,
    text="Editar",
    width=14,
    font=("Segoe UI",9)
)

btn_editar.pack(side="left", padx=6)

#---------------------------------------------------------

btn_eliminar = tk.Button(
    frame_acciones,
    text="Eliminar",
    width=14,
    font=("Segoe UI",9)
)

btn_eliminar.pack(side="left", padx=6)

#---------------------------------------------------------

btn_excel = tk.Button(
    frame_acciones,
    text="Exportar Excel",
    width=16,
    font=("Segoe UI",9)
)

btn_excel.pack(side="left", padx=6)

#---------------------------------------------------------

btn_imprimir = tk.Button(
    frame_acciones,
    text="Imprimir",
    width=14,
    font=("Segoe UI",9)
)

btn_imprimir.pack(side="left", padx=6)
# ==========================================================
# PANEL TABLA
# ==========================================================

frame_tabla = tk.LabelFrame(
    ventana,
    text="INVENTARIO ACTUAL",
    font=("Segoe UI",11,"bold"),
    bg="white"
)

frame_tabla.grid(
    row=3,
    column=0,
    sticky="nsew",
    padx=15,
    pady=5
)

frame_tabla.grid_rowconfigure(0, weight=1)
frame_tabla.grid_columnconfigure(0, weight=1)
columnas = (

    "ID",
    "Producto",
    "Presentación",
    "Cantidad",
    "Lote",
    "Costo",
    "Valor",
    "Fecha"

)

tabla = ttk.Treeview(

    frame_tabla,

    columns=columnas,

    show="headings"

)

for col in columnas:

    tabla.heading(
        col,
        text=col
    )

tabla.column(
    "ID",
    width=60,
    anchor="center"
)

tabla.column(
    "Producto",
    width=250
)

tabla.column(
    "Presentación",
    width=120,
    anchor="center"
)

tabla.column(
    "Cantidad",
    width=100,
    anchor="center"
)

tabla.column(
    "Lote",
    width=120,
    anchor="center"
)

tabla.column(
    "Costo",
    width=120,
    anchor="e"
)

tabla.column(
    "Valor",
    width=140,
    anchor="e"
)

tabla.column(
    "Fecha",
    width=130,
    anchor="center"
)
scroll_y = ttk.Scrollbar(
    frame_tabla,
    orient="vertical",
    command=tabla.yview
)

tabla.configure(
    yscrollcommand=scroll_y.set
)

tabla.grid(
    row=0,
    column=0,
    sticky="nsew"
)

scroll_y.grid(
    row=0,
    column=1,
    sticky="ns"
)
# ==========================================================
# PANEL INDICADORES
# ==========================================================

frame_indicadores = tk.Frame(
    ventana,
    bg="#E9EEF4",
    height=90
)

frame_indicadores.grid(
    row=4,
    column=0,
    sticky="ew",
    padx=15,
    pady=(5,10)
)

frame_indicadores.grid_propagate(False)

for i in range(5):
 frame_indicadores.grid_columnconfigure(i, weight=1)
card1 = tk.Frame(
    frame_indicadores,
    bg="white",
    bd=1,
    relief="solid"
)

card1.grid(
    row=0,
    column=0,
    padx=8,
    pady=8,
    sticky="nsew"
)

tk.Label(
    card1,
    text="REFERENCIAS",
    font=("Segoe UI",10,"bold"),
    bg="white",
    fg="#555"
).pack(pady=(10,2))

lbl_referencias = tk.Label(
    card1,
    text="0",
    font=("Segoe UI",22,"bold"),
    bg="white",
    fg="#0F4C81"
)

lbl_referencias.pack()
card2 = tk.Frame(
    frame_indicadores,
    bg="white",
    bd=1,
    relief="solid"
)

card2.grid(
    row=0,
    column=1,
    padx=8,
    pady=8,
    sticky="nsew"
)

tk.Label(
    card2,
    text="UNIDADES",
    font=("Segoe UI",10,"bold"),
    bg="white",
    fg="#555"
).pack(pady=(10,2))

lbl_unidades = tk.Label(
    card2,
    text="0",
    font=("Segoe UI",22,"bold"),
    bg="white",
    fg="#0F4C81"
)

lbl_unidades.pack()
card3 = tk.Frame(
    frame_indicadores,
    bg="white",
    bd=1,
    relief="solid"
)

card3.grid(
    row=0,
    column=2,
    padx=8,
    pady=8,
    sticky="nsew"
)

tk.Label(
    card3,
    text="VALOR INVENTARIO",
    font=("Segoe UI",10,"bold"),
    bg="white",
    fg="#555"
).pack(pady=(10,2))

lbl_valor_total = tk.Label(
    card3,
    text="$0",
    font=("Segoe UI",18,"bold"),
    bg="white",
    fg="#0F4C81"
)

lbl_valor_total.pack()
card4 = tk.Frame(
    frame_indicadores,
    bg="white",
    bd=1,
    relief="solid"
)

card4.grid(
    row=0,
    column=3,
    padx=8,
    pady=8,
    sticky="nsew"
)

tk.Label(
    card4,
    text="STOCK BAJO",
    font=("Segoe UI",10,"bold"),
    bg="white",
    fg="#555"
).pack(pady=(10,2))

lbl_stock = tk.Label(
    card4,
    text="0",
    font=("Segoe UI",22,"bold"),
    bg="white",
    fg="#C47A00"
)

lbl_stock.pack()
card5 = tk.Frame(
    frame_indicadores,
    bg="white",
    bd=1,
    relief="solid"
)

card5.grid(
    row=0,
    column=4,
    padx=8,
    pady=8,
    sticky="nsew"
)

tk.Label(
    card5,
    text="AGOTADOS",
    font=("Segoe UI",10,"bold"),
    bg="white",
    fg="#555"
).pack(pady=(10,2))

lbl_agotados = tk.Label(
    card5,
    text="0",
    font=("Segoe UI",22,"bold"),
    bg="white",
    fg="red"
)

lbl_agotados.pack()
cargar_inventario()
ventana.mainloop()