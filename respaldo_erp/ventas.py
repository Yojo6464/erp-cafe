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
# CALCULAR TOTAL
# =====================================

def calcular_total():

    try:

        cantidad = float(entry_cantidad.get())
        precio = float(entry_precio.get())

        total = cantidad * precio

        entry_total.config(state="normal")
        entry_total.delete(0, tk.END)
        entry_total.insert(0, f"{total:.2f}")
        entry_total.config(state="readonly")

    except:

        messagebox.showerror(
            "Error",
            "Ingrese cantidad y precio válidos."
        )


# =====================================
# GUARDAR VENTA
# =====================================

def guardar_venta():

    try:

        fecha = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cliente = entry_cliente.get().strip()

        producto = combo_producto.get()

        presentacion = combo_presentacion.get()

        cantidad = float(
            entry_cantidad.get()
        )

        precio = float(
            entry_precio.get()
        )

        if not cliente:

            messagebox.showerror(
                "Error",
                "Debe ingresar un cliente."
            )

            return

        # ==========================
        # INVENTARIO
        # ==========================

        cursor.execute("""
        SELECT
            cantidad,
            costo_unitario
        FROM inventario
        WHERE producto=?
        AND presentacion=?
        """,
        (
            producto,
            presentacion
        ))

        inventario = cursor.fetchone()

        if inventario is None:

            messagebox.showerror(
                "Error",
                "No existe inventario para este producto."
            )

            return

        stock_actual = float(
            inventario[0]
        )

        costo_unitario = float(
            inventario[1] or 0
        )

        if cantidad > stock_actual:

            messagebox.showerror(
                "Error",
                f"Stock insuficiente. Disponible: {stock_actual}"
            )

            return

        # ==========================
        # CALCULOS
        # ==========================

        total = cantidad * precio

        costo_total_venta = (
            costo_unitario * cantidad
        )

        utilidad_total = (
            total - costo_total_venta
        )

        margen = 0

        if total > 0:

            margen = round(
                (
                    utilidad_total
                    / total
                ) * 100,
                2
            )

        # ==========================
        # GUARDAR VENTA
        # ==========================

        cursor.execute("""
        INSERT INTO ventas
        (
            fecha,
            cliente,
            producto,
            presentacion,
            cantidad,
            precio_unitario,
            total,
            costo_unitario,
            utilidad_total,
            margen
        )
        VALUES
        (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            fecha,
            cliente,
            producto,
            presentacion,
            cantidad,
            precio,
            total,
            costo_unitario,
            utilidad_total,
            margen
        ))

        # ==========================
        # DESCONTAR INVENTARIO
        # ==========================

        nuevo_stock = (
            stock_actual
            - cantidad
        )

        cursor.execute("""
        UPDATE inventario
        SET cantidad=?
        WHERE producto=?
        AND presentacion=?
        """,
        (
            nuevo_stock,
            producto,
            presentacion
        ))

        # ==========================
        # KARDEX
        # ==========================

        cursor.execute("""
        INSERT INTO kardex
        (
            fecha,
            producto,
            presentacion,
            movimiento,
            entrada,
            salida,
            saldo,
            costo_unitario,
            lote,
            origen,
            observaciones
        )
        VALUES
        (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            fecha,
            producto,
            presentacion,
            "SALIDA",
            0,
            cantidad,
            nuevo_stock,
            costo_unitario,
            "",
            "VENTA",
            cliente
        ))

        conexion.commit() 

        messagebox.showinfo(
            "Venta Registrada",
            f"Total Venta: ${total:,.0f}\n\n"
            f"Costo: ${costo_total_venta:,.0f}\n"
            f"Utilidad: ${utilidad_total:,.0f}\n"
            f"Margen: {margen}%\n\n"
            f"Stock Restante: {nuevo_stock}"
        )

        # LIMPIAR

        entry_cliente.delete(
            0,
            tk.END
        )

        entry_cantidad.delete(
            0,
            tk.END
        )

        entry_precio.delete(
            0,
            tk.END
        )

        combo_producto.set("")
        combo_presentacion.set("")

        entry_total.config(
            state="normal"
        )

        entry_total.delete(
            0,
            tk.END
        )

        entry_total.config(
            state="readonly"
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Ventas"
)

ventana.geometry("500x550")

# CLIENTE

tk.Label(
    ventana,
    text="Cliente"
).pack(pady=5)

entry_cliente = tk.Entry(
    ventana,
    width=40
)

entry_cliente.pack()

# PRODUCTO

tk.Label(
    ventana,
    text="Producto"
).pack(pady=5)

combo_producto = ttk.Combobox(
    ventana,
    values=[
        "Café Especial",
        "Premium",
        "Tradicional"
    ],
    state="readonly"
)

combo_producto.pack()

# PRESENTACION

tk.Label(
    ventana,
    text="Presentación"
).pack(pady=5)

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

# CANTIDAD

tk.Label(
    ventana,
    text="Cantidad"
).pack(pady=5)

entry_cantidad = tk.Entry(
    ventana
)

entry_cantidad.pack()

# PRECIO

tk.Label(
    ventana,
    text="Precio Unitario"
).pack(pady=5)

entry_precio = tk.Entry(
    ventana
)

entry_precio.pack()

# TOTAL

tk.Label(
    ventana,
    text="Total"
).pack(pady=5)

entry_total = tk.Entry(
    ventana,
    state="readonly"
)

entry_total.pack()

# BOTONES

tk.Button(
    ventana,
    text="Calcular Total",
    command=calcular_total
).pack(pady=10)

tk.Button(
    ventana,
    text="Guardar Venta",
    bg="green",
    fg="white",
    command=guardar_venta
).pack(pady=10)

ventana.mainloop()

conexion.close()