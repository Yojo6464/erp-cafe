import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# =====================================
# CONEXION
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

# =====================================
# FUNCIONES
# =====================================

def mostrar_solicitudes():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
    SELECT
        id,
        fecha,
        tipo_gasto,
        proveedor,
        concepto,
        valor,
        banco,
        estado
    FROM solicitudes_pago
    WHERE estado='PENDIENTE'
    ORDER BY id DESC
    """)

    for fila in cursor.fetchall():

        tabla.insert(
            "",
            tk.END,
            values=fila
        )

# =====================================

def aprobar_solicitud():

    seleccion = tabla.selection()

    if not seleccion:
        messagebox.showerror(
            "Error",
            "Seleccione una solicitud."
        )
        return

    datos = tabla.item(seleccion[0])["values"]

    solicitud_id = datos[0]
    proveedor = datos[3]
    concepto = datos[4]
    valor = float(datos[5])

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_corta = datetime.now().strftime("%Y-%m-%d")

    # Aprobar solicitud
    cursor.execute("""
    UPDATE solicitudes_pago
    SET
        estado='APROBADA',
        fecha_aprobacion=?,
        autorizado_por='GERENCIA'
    WHERE id=?
    """,
    (
        fecha,
        solicitud_id
    ))

    print("=== CREANDO CUENTA POR PAGAR ===")
    print("Proveedor:", proveedor)
    print("Valor:", valor)
    print("Fecha:", fecha_corta)

    # Crear cuenta por pagar automáticamente
    cursor.execute("""
    INSERT INTO cuentas_pagar(
        proveedor,
        valor,
        saldo,
        fecha,
        vencimiento,
        estado
    )
    VALUES(?,?,?,?,?,?)
    """,
    (
        proveedor,
        valor,
        valor,
        fecha_corta,
        fecha_corta,
        "PENDIENTE"
    ))

    conexion.commit()

    messagebox.showinfo(
        "OK",
        "Solicitud aprobada y cuenta por pagar creada."
    )

    mostrar_solicitudes()

# =====================================

def rechazar_solicitud():

    seleccion = tabla.selection()

    if not seleccion:

        messagebox.showerror(
            "Error",
            "Seleccione una solicitud."
        )

        return

    datos = tabla.item(
        seleccion[0]
    )["values"]

    solicitud_id = datos[0]

    cursor.execute("""
    UPDATE solicitudes_pago
    SET
        estado='RECHAZADA',
        autorizado_por='GERENCIA'
    WHERE id=?
    """,
    (
        solicitud_id,
    ))

    conexion.commit()

    messagebox.showinfo(
        "OK",
        "Solicitud rechazada."
    )

    mostrar_solicitudes()
    # =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Aprobación de Pagos"
)

ventana.geometry("1400x750")

titulo = tk.Label(
    ventana,
    text="APROBACIÓN GERENCIAL DE PAGOS",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# BOTONES
# =====================================

frame_botones = tk.Frame(
    ventana
)

frame_botones.pack(pady=10)

tk.Button(
    frame_botones,
    text="APROBAR",
    width=20,
    command=aprobar_solicitud
).grid(
    row=0,
    column=0,
    padx=10
)

tk.Button(
    frame_botones,
    text="RECHAZAR",
    width=20,
    command=rechazar_solicitud
).grid(
    row=0,
    column=1,
    padx=10
)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Tipo",
        "Proveedor",
        "Concepto",
        "Valor",
        "Banco",
        "Estado"
    ),
    show="headings"
)

tabla.heading("ID", text="ID")
tabla.heading("Fecha", text="Fecha")
tabla.heading("Tipo", text="Tipo Gasto")
tabla.heading("Proveedor", text="Proveedor")
tabla.heading("Concepto", text="Concepto")
tabla.heading("Valor", text="Valor")
tabla.heading("Banco", text="Banco")
tabla.heading("Estado", text="Estado")

tabla.column("ID", width=60)
tabla.column("Fecha", width=150)
tabla.column("Tipo", width=120)
tabla.column("Proveedor", width=180)
tabla.column("Concepto", width=250)
tabla.column("Valor", width=120)
tabla.column("Banco", width=150)
tabla.column("Estado", width=120)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# =====================================
# INICIO
# =====================================

mostrar_solicitudes()

ventana.mainloop()

conexion.close()