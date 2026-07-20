import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# CARPETA FACTURAS
# =====================================

CARPETA_FACTURAS = r"C:\Users\jrive\visual\facturas"

if not os.path.exists(CARPETA_FACTURAS):
    os.makedirs(CARPETA_FACTURAS)

# =====================================
# FUNCIONES
# =====================================

def cargar_ventas():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        fecha,
        cliente,
        producto,
        presentacion,
        cantidad
    FROM ventas
    ORDER BY id DESC
    """)

    registros = cursor.fetchall()

    for fila in registros:
        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def generar_factura():

    seleccion = tabla.selection()

    if not seleccion:
        messagebox.showerror(
            "Error",
            "Seleccione una venta."
        )
        return

    datos = tabla.item(seleccion[0])["values"]

    venta_id = int(datos[0])

    cursor.execute("""
    SELECT
        fecha,
        cliente,
        producto,
        presentacion,
        cantidad,
        precio_unitario,
        total
    FROM ventas
    WHERE id = ?
    """, (venta_id,))

    venta = cursor.fetchone()

    if venta is None:
        messagebox.showerror(
            "Error",
            "Venta no encontrada."
        )
        return

    fecha = str(venta[0])
    cliente = str(venta[1])
    producto = str(venta[2])
    presentacion = str(venta[3])

    cantidad = float(venta[4])
    precio = float(venta[5])
    total = float(venta[6])

    archivo_pdf = os.path.join(
        CARPETA_FACTURAS,
        f"FACTURA_{venta_id}.pdf"
    )

    pdf = canvas.Canvas(
        archivo_pdf,
        pagesize=letter
    )

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(
        50,
        760,
        "CAFÉ ALTO DE LA CRUZ"
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawString(
        50,
        735,
        "Montañas del Tolima"
    )

    pdf.line(50, 725, 550, 725)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(
        50,
        690,
        f"FACTURA No. {venta_id}"
    )

    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        50,
        660,
        f"Fecha: {fecha}"
    )

    pdf.drawString(
        50,
        635,
        f"Cliente: {cliente}"
    )

    pdf.drawString(
        50,
        600,
        f"Producto: {producto}"
    )

    pdf.drawString(
        50,
        575,
        f"Presentación: {presentacion}"
    )

    pdf.drawString(
        50,
        550,
        f"Cantidad: {cantidad}"
    )

    pdf.drawString(
        50,
        525,
        f"Precio Unitario: ${precio:,.0f}"
    )

    pdf.drawString(
        50,
        500,
        f"Total Factura: ${total:,.0f}"
    )

    pdf.line(50, 470, 550, 470)

    pdf.drawString(
        50,
        440,
        "Gracias por comprar Café Alto de la Cruz"
    )

    pdf.save()

    messagebox.showinfo(
        "Factura Generada",
        f"PDF guardado en:\n{archivo_pdf}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Facturación PDF"
)

ventana.geometry("1000x600")

titulo = tk.Label(
    ventana,
    text="FACTURACIÓN PDF",
    font=("Arial", 18, "bold")
)

titulo.pack(pady=10)

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Cliente",
        "Producto",
        "Presentación",
        "Cantidad"
    ),
    show="headings"
)

for col in (
    "ID",
    "Fecha",
    "Cliente",
    "Producto",
    "Presentación",
    "Cantidad"
):
    tabla.heading(col, text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

btn_pdf = tk.Button(
    ventana,
    text="Generar Factura PDF",
    width=25,
    command=generar_factura
)

btn_pdf.pack(pady=10)

cargar_ventas()

ventana.mainloop()

conexion.close()