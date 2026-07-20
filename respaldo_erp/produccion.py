import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

conexion = sqlite3.connect("cafe_alto_cruz.db")
cursor = conexion.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS produccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    lote TEXT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto TEXT,
    presentacion TEXT,
    cantidad INTEGER
)
''')

conexion.commit()

def registrar_produccion():
    try:
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lote = entry_lote.get()
        producto = combo_producto.get()
        presentacion = combo_presentacion.get()
        cantidad = int(entry_cantidad.get())

        cursor.execute(
            'INSERT INTO produccion (fecha,lote,producto,presentacion,cantidad) VALUES (?,?,?,?,?)',
            (fecha, lote, producto, presentacion, cantidad)
        )

        cursor.execute(
            'SELECT id,cantidad FROM inventario WHERE producto=? AND presentacion=?',
            (producto, presentacion)
        )

        resultado = cursor.fetchone()

        if resultado:
            cursor.execute(
                'UPDATE inventario SET cantidad=? WHERE id=?',
                (resultado[1] + cantidad, resultado[0])
            )
        else:
            cursor.execute(
                'INSERT INTO inventario(producto,presentacion,cantidad) VALUES (?,?,?)',
                (producto, presentacion, cantidad)
            )

        conexion.commit()
        messagebox.showinfo('Éxito', 'Producción registrada correctamente')
        mostrar_produccion()

    except Exception as e:
        messagebox.showerror('Error', str(e))

def mostrar_produccion():
    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute('SELECT fecha,lote,producto,presentacion,cantidad FROM produccion ORDER BY id DESC')

    for fila in cursor.fetchall():
        tabla.insert('', tk.END, values=fila)

ventana = tk.Tk()
ventana.title('ERP Café Alto de la Cruz - Producción')
ventana.geometry('900x600')

tk.Label(ventana, text='Lote').pack()
entry_lote = tk.Entry(ventana, width=30)
entry_lote.pack()

tk.Label(ventana, text='Producto').pack()
combo_producto = ttk.Combobox(
    ventana,
    values=['Tradicional','Premium','Edición Especial'],
    state='readonly'
)
combo_producto.pack()

tk.Label(ventana, text='Presentación').pack()
combo_presentacion = ttk.Combobox(
    ventana,
    values=['125 g','250 g','500 g','1000 g'],
    state='readonly'
)
combo_presentacion.pack()

tk.Label(ventana, text='Cantidad').pack()
entry_cantidad = tk.Entry(ventana)
entry_cantidad.pack()

tk.Button(
    ventana,
    text='Registrar Producción',
    command=registrar_produccion
).pack(pady=10)

tabla = ttk.Treeview(
    ventana,
    columns=('Fecha','Lote','Producto','Presentación','Cantidad'),
    show='headings'
)

for col in ('Fecha','Lote','Producto','Presentación','Cantidad'):
    tabla.heading(col, text=col)

tabla.pack(fill='both', expand=True)

mostrar_produccion()

ventana.mainloop()

conexion.close()

