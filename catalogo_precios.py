import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ==========================
# BASE DE DATOS
# ==========================

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS precios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    precio REAL
)
""")

conexion.commit()

# ==========================
# FUNCIONES
# ==========================

def guardar_precio():

    try:

        producto = combo_producto.get()
        presentacion = combo_presentacion.get()
        precio = float(entry_precio.get())

        if producto == "" or presentacion == "":
            messagebox.showwarning(
                "Aviso",
                "Seleccione producto y presentación."
            )
            return

        cursor.execute("""
        INSERT INTO precios(
            producto,
            presentacion,
            precio
        )
        VALUES(?,?,?)
        """,
        (
            producto,
            presentacion,
            precio
        ))

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Precio guardado correctamente."
        )

        limpiar_campos()
        mostrar_precios()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


def mostrar_precios():

    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
    SELECT *
    FROM precios
    ORDER BY producto,presentacion
    """)

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )


def limpiar_campos():

    combo_producto.set("")
    combo_presentacion.set("")

    entry_precio.delete(
        0,
        tk.END
    )

    entry_precio.focus()


def eliminar_precio():

    seleccionado = tabla.focus()

    if seleccionado == "":

        messagebox.showwarning(
            "Aviso",
            "Seleccione un precio."
        )
        return

    datos = tabla.item(seleccionado)

    id_precio = datos["values"][0]

    respuesta = messagebox.askyesno(
        "Confirmar",
        "¿Eliminar precio?"
    )

    if respuesta:

        cursor.execute("""
        DELETE FROM precios
        WHERE id=?
        """,
        (id_precio,)
        )

        conexion.commit()

        mostrar_precios()


# ==========================
# VENTANA
# ==========================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Catálogo de Precios"
)

ventana.geometry("900x600")

# ==========================
# FORMULARIO
# ==========================

tk.Label(
    ventana,
    text="Producto"
).pack()

combo_producto = ttk.Combobox(
    ventana,
    values=[
        "Tradicional",
        "Premium"
    ],
    state="readonly"
)

combo_producto.pack()

tk.Label(
    ventana,
    text="Presentación"
).pack()

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

tk.Label(
    ventana,
    text="Precio"
).pack()

entry_precio = tk.Entry(
    ventana
)

entry_precio.pack()

# ==========================
# BOTONES
# ==========================

tk.Button(
    ventana,
    text="Guardar Precio",
    width=25,
    command=guardar_precio
).pack(pady=5)

tk.Button(
    ventana,
    text="Eliminar Precio",
    width=25,
    command=eliminar_precio
).pack(pady=5)

tk.Button(
    ventana,
    text="Limpiar Formulario",
    width=25,
    command=limpiar_campos
).pack(pady=5)

# ==========================
# TABLA
# ==========================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Producto",
        "Presentación",
        "Precio"
    ),
    show="headings"
)

tabla.heading("ID", text="ID")
tabla.heading("Producto", text="Producto")
tabla.heading("Presentación", text="Presentación")
tabla.heading("Precio", text="Precio")

tabla.column("ID", width=60)
tabla.column("Producto", width=200)
tabla.column("Presentación", width=150)
tabla.column("Precio", width=120)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

mostrar_precios()

ventana.mainloop()

conexion.close()
