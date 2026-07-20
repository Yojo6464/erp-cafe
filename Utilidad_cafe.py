import tkinter as tk
from tkinter import messagebox

def ventas():

    ventana_ventas = tk.Toplevel()

    ventana_ventas.title(
        "Registro de Ventas"
    )

    ventana_ventas.geometry(
        "400x300"
    )

    tk.Label(
        ventana_ventas,
        text="REGISTRO DE VENTAS",
        font=("Arial",14,"bold")
    ).pack(pady=10)

    tk.Label(
        ventana_ventas,
        text="Cliente"
    ).pack()

    cliente = tk.Entry(
        ventana_ventas
    )

    cliente.pack()

    tk.Label(
        ventana_ventas,
        text="Cantidad"
    ).pack()

    cantidad = tk.Entry(
        ventana_ventas
    )

    cantidad.pack()

    tk.Button(
        ventana_ventas,
        text="Guardar Venta"
    ).pack(pady=20)

