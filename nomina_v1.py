import tkinter as tk

ventana = tk.Tk()

ventana.title("ERP Café Alto de la Cruz - Nómina V1")
ventana.geometry("1000x600")

titulo = tk.Label(
    ventana,
    text="GESTIÓN DE NÓMINA",
    font=("Arial", 22, "bold")
)

titulo.pack(pady=20)

mensaje = tk.Label(
    ventana,
    text="Módulo de Nómina V1",
    font=("Arial", 12)
)

mensaje.pack(pady=10)

ventana.mainloop()