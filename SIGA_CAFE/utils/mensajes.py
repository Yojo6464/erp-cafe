from tkinter import messagebox

def informacion(texto):

    messagebox.showinfo("SIGA Café", texto)

def error(texto):

    messagebox.showerror("SIGA Café", texto)

def advertencia(texto):

    messagebox.showwarning("SIGA Café", texto)

def confirmar(texto):

    return messagebox.askyesno("SIGA Café", texto)