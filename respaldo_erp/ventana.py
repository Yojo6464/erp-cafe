import tkinter as tk
import sqlite3


# ==========================
# CREAR BASE DE DATOS
# ==========================

def crear_base_datos():

    conexion = sqlite3.connect("cafe_alto_cruz.db")

    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT
    )
    """)

    conexion.commit()
    conexion.close()


crear_base_datos()


# ==========================
# MODULO VENTAS
# ==========================

def ventas():

    ventana_ventas = tk.Toplevel()

    ventana_ventas.title("Registro de Ventas")
    ventana_ventas.geometry("400x300")

    tk.Label(
        ventana_ventas,
        text="REGISTRO DE VENTAS",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    tk.Label(
        ventana_ventas,
        text="Cliente"
    ).pack()

    cliente = tk.Entry(ventana_ventas)
    cliente.pack()

    tk.Label(
        ventana_ventas,
        text="Cantidad"
    ).pack()

    cantidad = tk.Entry(ventana_ventas)
    cantidad.pack()

    tk.Button(
        ventana_ventas,
        text="Guardar Venta"
    ).pack(pady=20)


# ==========================
# MODULO CLIENTES
# ==========================

def clientes():

    ventana_clientes = tk.Toplevel()

    ventana_clientes.title("Clientes")
    ventana_clientes.geometry("400x350")

    tk.Label(
        ventana_clientes,
        text="REGISTRO DE CLIENTES",
        font=("Arial", 14, "bold")
    ).pack(pady=10)

    tk.Label(
        ventana_clientes,
        text="Nombre"
    ).pack()

    nombre = tk.Entry(ventana_clientes)
    nombre.pack()

    tk.Label(
        ventana_clientes,
        text="Teléfono"
    ).pack()

    telefono = tk.Entry(ventana_clientes)
    telefono.pack()

    def guardar_cliente():

        conexion = sqlite3.connect(
            "cafe_alto_cruz.db"
        )

        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO clientes
            (nombre, telefono)
            VALUES (?, ?)
            """,
            (
                nombre.get(),
                telefono.get()
            )
        )

        conexion.commit()
        conexion.close()

        mensaje.config(
            text="Cliente guardado correctamente"
        )

        nombre.delete(0, tk.END)
        telefono.delete(0, tk.END)

    tk.Button(
        ventana_clientes,
        text="Guardar Cliente",
        command=guardar_cliente
    ).pack(pady=10)

    mensaje = tk.Label(
        ventana_clientes,
        text=""
    )

    mensaje.pack()


# ==========================
# VENTANA PRINCIPAL
# ==========================

ventana = tk.Tk()

ventana.title("CAFÉ ALTO DE LA CRUZ")

ventana.geometry("500x400")

titulo = tk.Label(
    ventana,
    text="CAFÉ ALTO DE LA CRUZ",
    font=("Arial", 20, "bold")
)

titulo.pack(pady=20)

boton_ventas = tk.Button(
    ventana,
    text="Ventas",
    width=20,
    command=ventas
)

boton_ventas.pack(pady=10)

boton_clientes = tk.Button(
    ventana,
    text="Clientes",
    width=20,
    command=clientes
)

boton_clientes.pack(pady=10)

ventana.mainloop()
