import tkinter as tk

ventana = tk.Tk()

ventana.title("Café Alto de la Cruz")
ventana.geometry("400x300")

titulo = tk.Label(
    ventana,
    text="CAFÉ ALTO DE LA CRUZ",
    font=("Arial",16,"bold")
)

titulo.pack(pady=20)

ventana.mainloop()
