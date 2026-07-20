import tkinter as tk
from tkinter import ttk
import sqlite3

# ==========================
# BASE DE DATOS
# ==========================

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Histórico Producción")
ventana.geometry("1200x600")

# ==========================
# TITULO
# ==========================

tk.Label(
    ventana,
    text="HISTÓRICO DE PRODUCCIÓN",
    font=("Arial", 16, "bold")
).pack(pady=10)

# ==========================
# TABLA
# ==========================

columnas = (
    "Fecha",
    "Lote",
    "Proveedor",
    "Producto",
    "Compra",
    "Kg",
    "Presentación",
    "Bolsas",
    "Costo",
    "Utilidad",
    "Margen"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings"
)

for col in columnas:
    tabla.heading(col, text=col)

tabla.column("Fecha", width=130)
tabla.column("Lote", width=100)
tabla.column("Proveedor", width=120)
tabla.column("Producto", width=100)
tabla.column("Compra", width=100)
tabla.column("Kg", width=80)
tabla.column("Presentación", width=100)
tabla.column("Bolsas", width=80)
tabla.column("Costo", width=120)
tabla.column("Utilidad", width=120)
tabla.column("Margen", width=80)

tabla.pack(fill="both", expand=True, padx=10, pady=10)

# ==========================
# CARGAR DATOS
# ==========================

def cargar_datos():

    for fila in tabla.get_children():
        tabla.delete(fila)

    cursor.execute("""
    SELECT
        fecha,
        lote,
        proveedor,
        producto,
        tipo_compra,
        kg_comprados,
        presentacion,
        bolsas,
        costo_total,
        utilidad_total,
        margen
    FROM produccion_costos
    ORDER BY id DESC
    """)

    registros = cursor.fetchall()

    for registro in registros:
        tabla.insert("", tk.END, values=registro)

# ==========================
# BOTON RECARGAR
# ==========================

tk.Button(
    ventana,
    text="Actualizar",
    command=cargar_datos
).pack(pady=5)

cargar_datos()

ventana.mainloop()

conexion.close()
