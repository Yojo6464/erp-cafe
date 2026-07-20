import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime

# ==========================
# BASE DE DATOS
# ==========================

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER
)
""")

conexion.commit()
cursor.execute("""
CREATE TABLE IF NOT EXISTS produccion_costos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    lote TEXT,
    proveedor TEXT,
    producto TEXT,
    tipo_compra TEXT,
    kg_comprados REAL,
    precio_kg REAL,
    maquila_kg REAL,
    merma REAL,
    presentacion TEXT,
    bolsas INTEGER,
    precio_venta REAL,
    kg_utiles REAL,
    costo_total REAL,
    costo_bolsa REAL,
    utilidad_bolsa REAL,
    utilidad_total REAL,
    margen REAL
)
""")

conexion.commit()

# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Producción Costos")

ventana.geometry("1000x750")

# ==========================
# TITULO
# ==========================

tk.Label(
    ventana,
    text="PRODUCCIÓN Y COSTOS",
    font=("Arial",16,"bold")
).pack(pady=10)

# ==========================
# LOTE
# ==========================

tk.Label(ventana,text="Lote").pack()

entry_lote = tk.Entry(
    ventana,
    width=30
)

entry_lote.pack()

# ==========================
# PROVEEDOR
# ==========================

tk.Label(
    ventana,
    text="Proveedor"
).pack()

entry_proveedor = tk.Entry(
    ventana,
    width=40
)

entry_proveedor.pack()

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
        "Tradicional",
        "Premium"
    ],
    state="readonly"
)

combo_producto.pack()

# ==========================
# TIPO COMPRA
# ==========================

tk.Label(
    ventana,
    text="Tipo Compra"
).pack()

combo_compra = ttk.Combobox(
    ventana,
    values=[
        "Pasilla",
        "Pergamino"
    ],
    state="readonly"
)

combo_compra.pack()

# ==========================
# KG COMPRADOS
# ==========================

tk.Label(
    ventana,
    text="Kg Comprados"
).pack()

entry_kg = tk.Entry(
    ventana
)

entry_kg.pack()

# ==========================
# PRECIO KG
# ==========================

tk.Label(
    ventana,
    text="Precio Kg"
).pack()

entry_precio_kg = tk.Entry(
    ventana
)

entry_precio_kg.pack()

# ==========================
# MAQUILA KG
# ==========================

tk.Label(
    ventana,
    text="Maquila Kg"
).pack()

entry_maquila = tk.Entry(
    ventana
)

entry_maquila.insert(
    0,
    "781.25"
)

entry_maquila.pack()

# ==========================
# MERMA
# ==========================

tk.Label(
    ventana,
    text="Merma (%)"
).pack()

entry_merma = tk.Entry(
    ventana
)

entry_merma.insert(
    0,
    "50"
)

entry_merma.pack()

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
# CANTIDAD BOLSAS
# ==========================

tk.Label(
    ventana,
    text="Cantidad Bolsas"
).pack()

entry_bolsas = tk.Entry(
    ventana
)

entry_bolsas.pack()

# ==========================
# PRECIO VENTA
# ==========================

tk.Label(
    ventana,
    text="Precio Venta Bolsa"
).pack()

entry_precio_venta = tk.Entry(
    ventana
)

entry_precio_venta.pack()

def calcular():

    try:

        kg_comprados = float(entry_kg.get())
        precio_kg = float(entry_precio_kg.get())
        maquila_kg = float(entry_maquila.get())
        merma = float(entry_merma.get())
        bolsas = int(entry_bolsas.get())
        precio_venta = float(entry_precio_venta.get())

        kg_utiles = kg_comprados * ((100 - merma) / 100)

        costo_materia_prima = kg_comprados * precio_kg

        costo_maquila = kg_comprados * maquila_kg

        costo_total = costo_materia_prima + costo_maquila

        costo_bolsa = costo_total / bolsas

        utilidad_bolsa = precio_venta - costo_bolsa

        utilidad_total = utilidad_bolsa * bolsas

        margen = (utilidad_bolsa / precio_venta) * 100

        lbl_resultado.config(
            text=
            f"Kg útiles: {kg_utiles:.2f}\n"
            f"Costo Total: ${costo_total:,.0f}\n"
            f"Costo por Bolsa: ${costo_bolsa:,.0f}\n"
            f"Utilidad por Bolsa: ${utilidad_bolsa:,.0f}\n"
            f"Utilidad Total: ${utilidad_total:,.0f}\n"
            f"Margen: {margen:.2f}%"
        )

    except Exception as e:

        lbl_resultado.config(
        text=f"ERROR: {e}"
        )




def guardar_produccion():

    try:

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lote = entry_lote.get()
        proveedor = entry_proveedor.get()
        producto = combo_producto.get()
        tipo_compra = combo_compra.get()

        kg_comprados = float(entry_kg.get())
        precio_kg = float(entry_precio_kg.get())
        maquila_kg = float(entry_maquila.get())
        merma = float(entry_merma.get())

        presentacion = combo_presentacion.get()
        bolsas = int(entry_bolsas.get())
        precio_venta = float(entry_precio_venta.get())

        kg_utiles = kg_comprados * ((100 - merma) / 100)

        costo_total = (
            (kg_comprados * precio_kg)
            +
            (kg_comprados * maquila_kg)
        )

        costo_bolsa = costo_total / bolsas

        utilidad_bolsa = precio_venta - costo_bolsa
        utilidad_total = utilidad_bolsa * bolsas
        margen = (utilidad_bolsa / precio_venta) * 100

        cursor.execute("""
        INSERT INTO produccion_costos(
            fecha,
            lote,
            proveedor,
            producto,
            tipo_compra,
            kg_comprados,
            precio_kg,
            maquila_kg,
            merma,
            presentacion,
            bolsas,
            precio_venta,
            kg_utiles,
            costo_total,
            costo_bolsa,
            utilidad_bolsa,
            utilidad_total,
            margen
        )
        VALUES(
            ?,?,?,?,?,?,?,?,?,?,
            ?,?,?,?,?,?,?,?
        )
        """,
        (
            fecha,
            lote,
            proveedor,
            producto,
            tipo_compra,
            kg_comprados,
            precio_kg,
            maquila_kg,
            merma,
            presentacion,
            bolsas,
            precio_venta,
            kg_utiles,
            costo_total,
            costo_bolsa,
            utilidad_bolsa,
            utilidad_total,
            margen
        ))

        cursor.execute("""
        SELECT id, cantidad
        FROM inventario
        WHERE producto=? AND presentacion=?
        """,
        (
            producto,
            presentacion
        ))

        inventario = cursor.fetchone()

        if inventario:

            nuevo_stock = inventario[1] + bolsas

            cursor.execute("""
            UPDATE inventario
            SET cantidad=?
            WHERE id=?
            """,
            (
                nuevo_stock,
                inventario[0]
            ))

        else:

            cursor.execute("""
            INSERT INTO inventario(
                producto,
                presentacion,
                cantidad
            )
            VALUES(?,?,?)
            """,
            (
                producto,
                presentacion,
                bolsas
            ))

        conexion.commit()

        lbl_resultado.config(
            text=
            lbl_resultado.cget("text")
            +
            "\n\nLOTE GUARDADO EN BASE DE DATOS"
        )

    except Exception as e:

        lbl_resultado.config(
            text=f"ERROR: {e}"
        )   
# ==========================
# BOTONES
# ==========================

tk.Button(
    ventana,
    text="Calcular",
    width=25,
    command=calcular
).pack(pady=5)

tk.Button(
    ventana,
    text="Guardar Producción",
    width=25,
    command=guardar_produccion
).pack(pady=5)

# ==========================
# RESULTADOS
# ==========================

frame_resultados = tk.LabelFrame(
    ventana,
    text="Resultados"
)

frame_resultados.pack(
    fill="x",
    padx=10,
    pady=10
)

lbl_resultado = tk.Label(
    frame_resultados,
    text="Esperando cálculo..."
)

lbl_resultado.pack(
    pady=10
)

ventana.mainloop()

conexion.close()
