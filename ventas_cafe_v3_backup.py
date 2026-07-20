import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# CREAR TABLA VENTAS
# =====================================

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas_cafe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    cliente TEXT,
    producto TEXT,
    cantidad REAL,
    precio_unitario REAL,
    total REAL,
    forma_pago TEXT
)
""")

conexion.commit()
conexion.close()

# =====================================
# GUARDAR VENTA
# =====================================

def guardar_venta():

    try:

        fecha = entry_fecha.get()
        cliente = entry_cliente.get()
        producto = combo_producto.get()

        cantidad = float(entry_cantidad.get())
        precio = float(entry_precio.get())

        forma_pago = combo_pago.get()

        total = cantidad * precio

        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()

        # =====================================
        # GUARDAR VENTA
        # =====================================

        cursor.execute("""
        INSERT INTO ventas_cafe
        (
            fecha,
            cliente,
            producto,
            cantidad,
            precio_unitario,
            total,
            forma_pago
        )
        VALUES
        (?,?,?,?,?,?,?)
        """,
        (
            fecha,
            cliente,
            producto,
            cantidad,
            precio,
            total,
            forma_pago
        ))

        # =====================================
        # SALIDA INVENTARIO
        # =====================================

        cursor.execute("""
        INSERT INTO inventario_cafe
        (
            fecha,
            producto,
            tipo_movimiento,
            cantidad,
            costo_unitario,
            observaciones
        )
        VALUES
        (?,?,?,?,?,?)
        """,
        (
            fecha,
            producto,
            "Salida",
            cantidad,
            0,
            f"Venta a {cliente}"
        ))

        # =====================================
        # CUENTA POR COBRAR
        # =====================================

        if forma_pago == "Credito":

            cursor.execute("""
            INSERT INTO cuentas_cobrar_v1
            (
                fecha,
                cliente,
                concepto,
                valor,
                estado
            )
            VALUES
            (?,?,?,?,?)
            """,
            (
                fecha,
                cliente,
                f"Venta {producto}",
                total,
                "Pendiente"
            ))

        conexion.commit()
        conexion.close()

        lbl_total.config(
            text=f"${total:,.0f}"
        )

        if forma_pago == "Credito":

            mensaje = (
                "Venta guardada\n"
                "Inventario descontado\n"
                "Cuenta por cobrar creada"
            )

        else:

            mensaje = (
                "Venta guardada\n"
                "Inventario descontado"
            )

        messagebox.showinfo(
            "Ventas V3",
            mensaje
        )

        limpiar()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================
# LIMPIAR
# =====================================

def limpiar():

    entry_fecha.delete(0, tk.END)
    entry_cliente.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_precio.delete(0, tk.END)
    # =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Cafe Alto de la Cruz - Ventas V3"
)

ventana.geometry("800x700")

titulo = tk.Label(
    ventana,
    text="VENTAS DE CAFE V3",
    font=("Arial",22,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)
frame.pack(pady=10)

# FECHA

tk.Label(
    frame,
    text="Fecha"
).grid(
    row=0,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

entry_fecha = tk.Entry(frame, width=35)
entry_fecha.grid(row=0, column=1)

# CLIENTE

tk.Label(
    frame,
    text="Cliente"
).grid(
    row=1,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

entry_cliente = tk.Entry(frame, width=35)
entry_cliente.grid(row=1, column=1)

# PRODUCTO

tk.Label(
    frame,
    text="Producto"
).grid(
    row=2,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

combo_producto = ttk.Combobox(
    frame,
    width=32,
    state="readonly"
)

combo_producto["values"] = (
    "Cafe Verde",
    "Cafe Tostado",
    "Cafe Molido"
)

combo_producto.grid(row=2, column=1)

# CANTIDAD

tk.Label(
    frame,
    text="Cantidad"
).grid(
    row=3,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

entry_cantidad = tk.Entry(frame, width=35)
entry_cantidad.grid(row=3, column=1)

# PRECIO

tk.Label(
    frame,
    text="Precio Unitario"
).grid(
    row=4,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

entry_precio = tk.Entry(frame, width=35)
entry_precio.grid(row=4, column=1)

# FORMA DE PAGO

tk.Label(
    frame,
    text="Forma de Pago"
).grid(
    row=5,
    column=0,
    padx=10,
    pady=10,
    sticky="w"
)

combo_pago = ttk.Combobox(
    frame,
    width=32,
    state="readonly"
)

combo_pago["values"] = (
    "Contado",
    "Credito"
)

combo_pago.grid(row=5, column=1)

# TOTAL

tk.Label(
    ventana,
    text="TOTAL VENTA",
    font=("Arial",14,"bold")
).pack(pady=10)

lbl_total = tk.Label(
    ventana,
    text="$0",
    font=("Arial",18,"bold")
)

lbl_total.pack()

# BOTON

btn_guardar = tk.Button(
    ventana,
    text="Guardar Venta",
    width=25,
    height=2,
    command=guardar_venta
)

btn_guardar.pack(pady=30)

ventana.mainloop()