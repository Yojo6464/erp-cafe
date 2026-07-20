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
cliente_id_seleccionado = None

# =====================================
# TABLA
# =====================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_registro TEXT,
    nit TEXT,
    nombre TEXT,
    telefono TEXT,
    ciudad TEXT,
    correo TEXT
)
""")

conexion.commit()

# =====================================
# FUNCIONES
# =====================================

def guardar_cliente():

    try:

        nit = entry_nit.get().strip()
        nombre = entry_nombre.get().strip()
        telefono = entry_telefono.get().strip()
        ciudad = entry_ciudad.get().strip()
        correo = entry_correo.get().strip()

        if nombre == "":
            messagebox.showerror(
                "Error",
                "Debe ingresar el nombre."
            )
            return

        fecha = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
        INSERT INTO clientes
(
    fecha_registro,
    nit,
    nombre,
    telefono,
    ciudad,
    correo
)
VALUES (?,?,?,?,?,?)
        """,
        (
            fecha,
            nit,
            nombre,
            telefono,
            ciudad,
            correo
        ))

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Cliente registrado."
        )
        entry_nit.delete(0, tk.END)
        entry_nombre.delete(0, tk.END)
        entry_telefono.delete(0, tk.END)
        entry_ciudad.delete(0, tk.END)
        entry_correo.delete(0, tk.END)

        mostrar_clientes()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

# =====================================

def mostrar_clientes():

    tabla.delete(*tabla.get_children())

    cursor.execute("""
SELECT
    id,
    IFNULL(nit,''),
    nombre,
    telefono,
    ciudad,
    correo
FROM clientes
ORDER BY nombre
""")

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )
    # =====================================

def buscar_clientes():

    texto = entry_busqueda.get().strip()

    tabla.delete(*tabla.get_children())

    cursor.execute(
        """
        SELECT
            id,
            IFNULL(nit,''),
            nombre,
            telefono,
            ciudad,
            correo
        FROM clientes
        WHERE
            nit LIKE ?
            OR nombre LIKE ?
        ORDER BY nombre
        """,
        (
            "%" + texto + "%",
            "%" + texto + "%"
        )
    )

    registros = cursor.fetchall()

    for fila in registros:

        tabla.insert(
            "",
            tk.END,
            values=fila
        )    
    # =====================================

def seleccionar_cliente(event):

    global cliente_id_seleccionado

    item = tabla.focus()

    if item == "":
        return

    datos = tabla.item(item, "values")

    cliente_id_seleccionado = datos[0]

    entry_nit.delete(0, tk.END)
    entry_nombre.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_ciudad.delete(0, tk.END)
    entry_correo.delete(0, tk.END)

    entry_nit.insert(0, datos[1])
    entry_nombre.insert(0, datos[2])
    entry_telefono.insert(0, datos[3])
    entry_ciudad.insert(0, datos[4])
    entry_correo.insert(0, datos[5])  
      # =====================================

def actualizar_cliente():

    global cliente_id_seleccionado

    try:

        if cliente_id_seleccionado is None:

            messagebox.showerror(
                "Error",
                "Debe seleccionar un cliente."
            )
            return

        nit = entry_nit.get().strip()
        nombre = entry_nombre.get().strip()
        telefono = entry_telefono.get().strip()
        ciudad = entry_ciudad.get().strip()
        correo = entry_correo.get().strip()
        print("ID:", cliente_id_seleccionado)

        cursor.execute(
            """
            UPDATE clientes
            SET
                nit=?,
                nombre=?,
                telefono=?,
                ciudad=?,
                correo=?
            WHERE id=?
            """,
            (
                nit,
                nombre,
                telefono,
                ciudad,
                correo,
                cliente_id_seleccionado
            )
        )

        conexion.commit()

        messagebox.showinfo(
            "Éxito",
            "Cliente actualizado."
        )

        mostrar_clientes()

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )
        # =====================================

def eliminar_cliente():

    global cliente_id_seleccionado

    try:

        if cliente_id_seleccionado is None:

            messagebox.showerror(
                "Error",
                "Debe seleccionar un cliente."
            )
            return

        respuesta = messagebox.askyesno(
            "Confirmar",
            "¿Desea eliminar este cliente?"
        )

        if not respuesta:
            return

        cursor.execute(
            """
            DELETE FROM clientes
            WHERE id = ?
            """,
            (cliente_id_seleccionado,)
        )

        conexion.commit()

        entry_nit.delete(0, tk.END)
        entry_nombre.delete(0, tk.END)
        entry_telefono.delete(0, tk.END)
        entry_ciudad.delete(0, tk.END)
        entry_correo.delete(0, tk.END)

        cliente_id_seleccionado = None

        mostrar_clientes()

        messagebox.showinfo(
            "Éxito",
            "Cliente eliminado correctamente."
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
    "ERP Café Alto de la Cruz - Clientes"
)

ventana.geometry("1100x650")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="GESTION DE CLIENTES",
    font=("Arial",18,"bold")
)

titulo.pack(pady=10)

# =====================================
# FORMULARIO
# =====================================

frame = tk.Frame(ventana)

frame.pack(pady=10)

tk.Label(
    frame,
    text="NIT"
).grid(row=0,column=0,padx=10,pady=5)

entry_nit = tk.Entry(
    frame,
    width=20
)

entry_nit.grid(row=1,column=0)

tk.Label(
    frame,
    text="Nombre"
).grid(row=0,column=1,padx=10,pady=5)

entry_nombre = tk.Entry(
    frame,
    width=30
)

entry_nombre.grid(row=1,column=1)

tk.Label(
    frame,
    text="Telefono"
).grid(row=0,column=2,padx=10,pady=5)

entry_telefono = tk.Entry(
    frame,
    width=20
)

entry_telefono.grid(row=1,column=2)

tk.Label(
    frame,
    text="Ciudad"
).grid(row=0,column=3,padx=10,pady=5)

entry_ciudad = tk.Entry(
    frame,
    width=20
)

entry_ciudad.grid(row=1,column=3)

tk.Label(
    frame,
    text="Correo"
).grid(row=0,column=4,padx=10,pady=5)

entry_correo = tk.Entry(
    frame,
    width=30
)

entry_correo.grid(row=1,column=4)
# =====================================
# BUSQUEDA
# =====================================

frame_busqueda = tk.Frame(ventana)

frame_busqueda.pack(pady=5)

tk.Label(
    frame_busqueda,
    text="Buscar Cliente"
).pack(side="left", padx=5)

entry_busqueda = tk.Entry(
    frame_busqueda,
    width=40
)

entry_busqueda.pack(side="left", padx=5)
tk.Button(
    frame_busqueda,
    text="Buscar",
    command=buscar_clientes
).pack(side="left", padx=5)


tk.Button(
    ventana,
    text="Guardar Cliente",
    width=25,
    command=guardar_cliente
).pack(pady=10)
tk.Button(
    ventana,
    text="Actualizar Cliente",
    width=25
).pack(pady=5)
tk.Button(
    ventana,
    text="Eliminar Cliente",
    width=25,
    command=eliminar_cliente
).pack(pady=5)

# =====================================
# TABLA
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "NIT",
        "Nombre",
        "Telefono",
        "Ciudad",
        "Correo"
    ),
    show="headings"
)

tabla.heading("ID", text="ID")
tabla.heading("NIT", text="NIT")
tabla.heading("Nombre", text="Nombre")
tabla.heading("Telefono", text="Teléfono")
tabla.heading("Ciudad", text="Ciudad")
tabla.heading("Correo", text="Correo")

tabla.column("ID", width=70)
tabla.column("NIT", width=120)
tabla.column("Nombre", width=220)
tabla.column("Telefono", width=130)
tabla.column("Ciudad", width=150)
tabla.column("Correo", width=250)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)
tabla.bind(
    "<<TreeviewSelect>>",
    seleccionar_cliente
)

# =====================================
# CARGA INICIAL
# =====================================

mostrar_clientes()

ventana.mainloop()

conexion.close()