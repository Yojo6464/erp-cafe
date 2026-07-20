# ==========================================================
# INVENTARIO - INTERFAZ V2 CORREGIDA
# ERP CAFÉ ALTO DE LA CRUZ
# Sprint 4.1
# ==========================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()


def inicializar_bd():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            presentacion TEXT,
            cantidad REAL DEFAULT 0,
            lote TEXT DEFAULT '',
            costo_unitario REAL DEFAULT 0,
            fecha_ingreso TEXT DEFAULT '',
            numero_despacho TEXT DEFAULT '',
            stock_minimo INTEGER DEFAULT 0,
            costo REAL DEFAULT 0,
            fecha TEXT DEFAULT '',
            despacho TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kardex (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            producto TEXT,
            presentacion TEXT,
            lote TEXT,
            tipo_movimiento TEXT,
            cantidad REAL,
            costo_unitario REAL,
            valor REAL,
            documento TEXT,
            observacion TEXT
        )
    """)

    conexion.commit()


def limpiar_formulario():
    combo_producto.set("")
    combo_presentacion.set("")
    txt_cantidad.delete(0, tk.END)
    txt_stock.delete(0, tk.END)
    txt_costo.delete(0, tk.END)
    txt_lote.delete(0, tk.END)
    txt_fecha.delete(0, tk.END)
    txt_despacho.delete(0, tk.END)
    lbl_valor.config(text="VALOR DEL INVENTARIO : $ 0.00")


def calcular_valor_formulario(event=None):
    try:
        cantidad = float(txt_cantidad.get() or 0)
        costo = float(txt_costo.get() or 0)
        valor = cantidad * costo
        lbl_valor.config(text=f"VALOR DEL INVENTARIO : $ {valor:,.0f}")
    except:
        lbl_valor.config(text="VALOR DEL INVENTARIO : $ 0.00")


def actualizar_indicadores():
    cursor.execute("SELECT COUNT(*) FROM inventario")
    referencias = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(cantidad),0) FROM inventario")
    unidades = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(cantidad * COALESCE(costo_unitario, costo, 0)),0)
        FROM inventario
    """)
    valor_total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM inventario
        WHERE cantidad <= stock_minimo
          AND cantidad > 0
          AND stock_minimo > 0
    """)
    stock_bajo = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventario WHERE cantidad = 0")
    agotados = cursor.fetchone()[0]

    lbl_referencias.config(text=str(referencias))
    lbl_unidades.config(text=f"{unidades:,.0f}")
    lbl_valor_total.config(text=f"${valor_total:,.0f}")
    lbl_stock.config(text=str(stock_bajo))
    lbl_agotados.config(text=str(agotados))


def cargar_inventario():
    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
        SELECT
            id,
            producto,
            presentacion,
            cantidad,
            COALESCE(lote, ''),
            COALESCE(costo_unitario, costo, 0),
            cantidad * COALESCE(costo_unitario, costo, 0),
            COALESCE(fecha_ingreso, fecha, '')
        FROM inventario
        ORDER BY producto, presentacion
    """)

    for fila in cursor.fetchall():
        tabla.insert("", tk.END, values=fila)

    actualizar_indicadores()

def buscar_inventario():
    criterio = simpledialog.askstring(
        "Buscar inventario",
        "Ingrese producto, presentación o lote:"
    )

    if criterio is None:
        return

    criterio = criterio.strip()

    if criterio == "":
        cargar_inventario()
        return

    for item in tabla.get_children():
        tabla.delete(item)

    cursor.execute("""
        SELECT
            id,
            producto,
            presentacion,
            cantidad,
            COALESCE(lote, ''),
            COALESCE(costo_unitario, costo, 0),
            cantidad * COALESCE(costo_unitario, costo, 0),
            COALESCE(fecha_ingreso, fecha, '')
        FROM inventario
        WHERE producto LIKE ?
           OR presentacion LIKE ?
           OR lote LIKE ?
        ORDER BY producto, presentacion
    """, (
        f"%{criterio}%",
        f"%{criterio}%",
        f"%{criterio}%"
    ))

    registros = cursor.fetchall()

    for fila in registros:
        tabla.insert("", tk.END, values=fila)

    if len(registros) == 0:
        messagebox.showinfo("Buscar", "No se encontraron resultados.")  

def obtener_id_seleccionado():
    seleccionado = tabla.selection()

    if not seleccionado:
        messagebox.showwarning("Atención", "Seleccione un registro.")
        return None

    valores = tabla.item(seleccionado[0], "values")
    return valores[0]


def editar_inventario():
    id_registro = obtener_id_seleccionado()

    if id_registro is None:
        return

    cursor.execute("""
        SELECT
            producto,
            presentacion,
            cantidad,
            stock_minimo,
            COALESCE(costo_unitario, costo, 0),
            COALESCE(lote, ''),
            COALESCE(fecha_ingreso, fecha, ''),
            COALESCE(numero_despacho, despacho, '')
        FROM inventario
        WHERE id = ?
    """, (id_registro,))

    fila = cursor.fetchone()

    if not fila:
        messagebox.showerror("Error", "No se encontró el registro.")
        return

    nuevo_cantidad = simpledialog.askfloat(
        "Editar cantidad",
        "Nueva cantidad:",
        initialvalue=fila[2]
    )

    if nuevo_cantidad is None:
        return

    nuevo_costo = simpledialog.askfloat(
        "Editar costo",
        "Nuevo costo unitario:",
        initialvalue=fila[4]
    )

    if nuevo_costo is None:
        return

    try:
        cursor.execute("""
            UPDATE inventario
            SET cantidad = ?,
                costo = ?,
                costo_unitario = ?
            WHERE id = ?
        """, (
            nuevo_cantidad,
            nuevo_costo,
            nuevo_costo,
            id_registro
        ))

        conexion.commit()
        cargar_inventario()

        messagebox.showinfo("Éxito", "Registro editado correctamente.")

    except Exception as e:
        conexion.rollback()
        messagebox.showerror("Error", f"No se pudo editar:\n{e}")  
        
def eliminar_inventario():
    id_registro = obtener_id_seleccionado()

    if id_registro is None:
        return

    confirmar = messagebox.askyesno(
        "Confirmar eliminación",
        "¿Está seguro de eliminar este registro del inventario?"
    )

    if not confirmar:
        return

    try:
        cursor.execute("""
            SELECT producto, presentacion, cantidad, COALESCE(lote, ''), COALESCE(costo_unitario, costo, 0)
            FROM inventario
            WHERE id = ?
        """, (id_registro,))

        fila = cursor.fetchone()

        if fila:
            producto, presentacion, cantidad, lote, costo = fila
            registrar_kardex(
                producto,
                presentacion,
                lote,
                cantidad,
                costo,
                "ELIMINACIÓN",
                "REGISTRO ELIMINADO DEL INVENTARIO"
            )

        cursor.execute("DELETE FROM inventario WHERE id = ?", (id_registro,))
        conexion.commit()

        cargar_inventario()
        messagebox.showinfo("Éxito", "Registro eliminado correctamente.")

    except Exception as e:
        conexion.rollback()
        messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")   


def registrar_kardex(producto, presentacion, lote, cantidad, costo, documento, observacion):
    fecha_movimiento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT IFNULL(SUM(entrada - salida), 0)
        FROM kardex
        WHERE producto = ?
          AND presentacion = ?
          AND COALESCE(lote, '') = ?
    """, (producto, presentacion, lote))

    saldo_anterior = cursor.fetchone()[0]
    saldo_nuevo = saldo_anterior + cantidad

    cursor.execute("""
        INSERT INTO kardex (
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fecha_movimiento,
        producto,
        presentacion,
        "ENTRADA INVENTARIO",
        cantidad,
        0,
        saldo_nuevo,
        costo,
        lote,
        documento,
        observacion
    ))


def agregar_inventario():
    producto = combo_producto.get().strip()
    presentacion = combo_presentacion.get().strip()

    if producto == "":
        messagebox.showerror("Error", "Seleccione un producto.")
        return

    if presentacion == "":
        messagebox.showerror("Error", "Seleccione una presentación.")
        return

    try:
        cantidad = float(txt_cantidad.get())
        stock_minimo = int(txt_stock.get() or 0)
        costo = float(txt_costo.get() or 0)
    except:
        messagebox.showerror("Error", "Cantidad, stock mínimo y costo deben ser números.")
        return

    if cantidad <= 0:
        messagebox.showerror("Error", "La cantidad debe ser mayor que cero.")
        return

    lote = txt_lote.get().strip()
    fecha = txt_fecha.get().strip()
    despacho = txt_despacho.get().strip()

    if fecha == "":
        fecha = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute("""
            SELECT id
            FROM inventario
            WHERE producto = ?
              AND presentacion = ?
              AND COALESCE(lote, '') = ?
        """, (producto, presentacion, lote))

        existe = cursor.fetchone()

        if existe:
            id_inventario = existe[0]

            cursor.execute("""
                UPDATE inventario
                SET cantidad = cantidad + ?,
                    stock_minimo = ?,
                    costo = ?,
                    costo_unitario = ?,
                    fecha = ?,
                    fecha_ingreso = ?,
                    despacho = ?,
                    numero_despacho = ?
                WHERE id = ?
            """, (
                cantidad, stock_minimo, costo, costo,
                fecha, fecha, despacho, despacho, id_inventario
            ))

            operacion = "ACTUALIZACIÓN"
        else:
            cursor.execute("""
                INSERT INTO inventario (
                    producto, presentacion, cantidad, stock_minimo,
                    costo, costo_unitario, lote, fecha, fecha_ingreso,
                    despacho, numero_despacho
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                producto, presentacion, cantidad, stock_minimo,
                costo, costo, lote, fecha, fecha,
                despacho, despacho
            ))

            operacion = "NUEVO REGISTRO"

        registrar_kardex(producto, presentacion, lote, cantidad, costo, despacho, operacion)

        conexion.commit()
        limpiar_formulario()
        cargar_inventario()

        messagebox.showinfo(
            "Éxito",
            f"Inventario actualizado correctamente.\nOperación: {operacion}"
        )

    except Exception as e:
        conexion.rollback()
        messagebox.showerror("Error", f"No se pudo agregar inventario:\n{e}")


def accion_no_disponible(nombre):
    messagebox.showinfo("En desarrollo", f"La función {nombre} se implementará en el siguiente sprint.")


# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

inicializar_bd()

ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Inventario")
ventana.state("zoomed")
ventana.configure(bg="#E9EEF4")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))

ventana.grid_columnconfigure(0, weight=1)
ventana.grid_rowconfigure(0, weight=0)
ventana.grid_rowconfigure(1, weight=0)
ventana.grid_rowconfigure(2, weight=0)
ventana.grid_rowconfigure(3, weight=1)
ventana.grid_rowconfigure(4, weight=0)

frame_header = tk.Frame(ventana, bg="#0F4C81", height=90)
frame_header.grid(row=0, column=0, sticky="nsew")
frame_header.grid_propagate(False)

tk.Label(
    frame_header,
    text="ERP CAFÉ ALTO DE LA CRUZ",
    font=("Segoe UI", 22, "bold"),
    bg="#0F4C81",
    fg="white"
).pack(pady=(12, 0))

tk.Label(
    frame_header,
    text="MÓDULO DE INVENTARIO",
    font=("Segoe UI", 12),
    bg="#0F4C81",
    fg="white"
).pack()

frame_registro = tk.LabelFrame(
    ventana,
    text="REGISTRO DE INVENTARIO",
    font=("Segoe UI", 11, "bold"),
    bg="white",
    padx=20,
    pady=15
)

frame_registro.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 5))
frame_registro.grid_columnconfigure(1, weight=1)
frame_registro.grid_columnconfigure(3, weight=1)

tk.Label(frame_registro, text="Producto", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)

combo_producto = ttk.Combobox(frame_registro, width=40, state="readonly")
combo_producto["values"] = (
    "Café Especial",
    "Café Premium",
    "Café Tradicional",
    "Premium",
    "Tradicional"
)
combo_producto.grid(row=0, column=1, padx=(10, 25), sticky="ew")

tk.Label(frame_registro, text="Presentación", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w")

combo_presentacion = ttk.Combobox(frame_registro, width=20, state="readonly")
combo_presentacion["values"] = ("125 g", "250 g", "500 g", "1000 g")
combo_presentacion.grid(row=0, column=3, sticky="w")

tk.Label(frame_registro, text="Cantidad", bg="white", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
txt_cantidad = tk.Entry(frame_registro, width=30)
txt_cantidad.grid(row=1, column=1, sticky="w", padx=(10, 25))
txt_cantidad.bind("<KeyRelease>", calcular_valor_formulario)

tk.Label(frame_registro, text="Stock mínimo", bg="white", font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w")
txt_stock = tk.Entry(frame_registro, width=22)
txt_stock.grid(row=1, column=3, sticky="w")

tk.Label(frame_registro, text="Costo Unitario", bg="white", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
txt_costo = tk.Entry(frame_registro, width=30)
txt_costo.grid(row=2, column=1, sticky="w", padx=(10, 25))
txt_costo.bind("<KeyRelease>", calcular_valor_formulario)

tk.Label(frame_registro, text="Lote", bg="white", font=("Segoe UI", 10, "bold")).grid(row=2, column=2, sticky="w")
txt_lote = tk.Entry(frame_registro, width=22)
txt_lote.grid(row=2, column=3, sticky="w")

tk.Label(frame_registro, text="Fecha Ingreso", bg="white", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
txt_fecha = tk.Entry(frame_registro, width=30)
txt_fecha.grid(row=3, column=1, sticky="w", padx=(10, 25))

tk.Label(frame_registro, text="No. Despacho", bg="white", font=("Segoe UI", 10, "bold")).grid(row=3, column=2, sticky="w")
txt_despacho = tk.Entry(frame_registro, width=22)
txt_despacho.grid(row=3, column=3, sticky="w")

lbl_valor = tk.Label(
    frame_registro,
    text="VALOR DEL INVENTARIO : $ 0.00",
    bg="white",
    fg="#0F4C81",
    font=("Segoe UI", 12, "bold")
)
lbl_valor.grid(row=4, column=0, columnspan=4, pady=(15, 10))

frame_botones = tk.Frame(frame_registro, bg="white")
frame_botones.grid(row=5, column=0, columnspan=4, pady=10)

tk.Button(
    frame_botones,
    text="AGREGAR INVENTARIO",
    width=22,
    height=2,
    bg="#0F4C81",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    command=agregar_inventario
).pack(side="left", padx=10)

tk.Button(frame_botones, text="LIMPIAR", width=14, height=2, command=limpiar_formulario).pack(side="left", padx=10)
tk.Button(frame_botones, text="CANCELAR", width=14, height=2, command=limpiar_formulario).pack(side="left", padx=10)

frame_acciones = tk.LabelFrame(
    ventana,
    text="ACCIONES",
    font=("Segoe UI", 11, "bold"),
    bg="white",
    padx=15,
    pady=10
)

frame_acciones.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 5))

tk.Button(frame_acciones, text="Actualizar", width=14, bg="#0F4C81", fg="white", font=("Segoe UI", 9, "bold"), command=cargar_inventario).pack(side="left", padx=6)
tk.Button(frame_acciones, text="Buscar", width=14, font=("Segoe UI", 9), command=buscar_inventario).pack(side="left", padx=6)
tk.Button(frame_acciones, text="Editar", width=14, font=("Segoe UI", 9), command=editar_inventario).pack(side="left", padx=6)
tk.Button(frame_acciones, text="Eliminar", width=14, font=("Segoe UI", 9), command=eliminar_inventario).pack(side="left", padx=6)
tk.Button(frame_acciones, text="Exportar Excel", width=16, font=("Segoe UI", 9), command=lambda: accion_no_disponible("Exportar Excel")).pack(side="left", padx=6)
tk.Button(frame_acciones, text="Imprimir", width=14, font=("Segoe UI", 9), command=lambda: accion_no_disponible("Imprimir")).pack(side="left", padx=6)

frame_tabla = tk.LabelFrame(
    ventana,
    text="INVENTARIO ACTUAL",
    font=("Segoe UI", 11, "bold"),
    bg="white"
)

frame_tabla.grid(row=3, column=0, sticky="nsew", padx=15, pady=5)
frame_tabla.grid_rowconfigure(0, weight=1)
frame_tabla.grid_columnconfigure(0, weight=1)

columnas = ("ID", "Producto", "Presentación", "Cantidad", "Lote", "Costo", "Valor", "Fecha")

tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

for col in columnas:
    tabla.heading(col, text=col)

tabla.column("ID", width=60, anchor="center")
tabla.column("Producto", width=250)
tabla.column("Presentación", width=120, anchor="center")
tabla.column("Cantidad", width=100, anchor="center")
tabla.column("Lote", width=120, anchor="center")
tabla.column("Costo", width=120, anchor="e")
tabla.column("Valor", width=140, anchor="e")
tabla.column("Fecha", width=130, anchor="center")

scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscrollcommand=scroll_y.set)

tabla.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")

frame_indicadores = tk.Frame(ventana, bg="#E9EEF4", height=90)
frame_indicadores.grid(row=4, column=0, sticky="ew", padx=15, pady=(5, 10))
frame_indicadores.grid_propagate(False)

for i in range(5):
    frame_indicadores.grid_columnconfigure(i, weight=1)


def crear_card(columna, titulo, color, tamano=22):
    card = tk.Frame(frame_indicadores, bg="white", bd=1, relief="solid")
    card.grid(row=0, column=columna, padx=8, pady=8, sticky="nsew")

    tk.Label(
        card,
        text=titulo,
        font=("Segoe UI", 10, "bold"),
        bg="white",
        fg="#555"
    ).pack(pady=(10, 2))

    label = tk.Label(
        card,
        text="0",
        font=("Segoe UI", tamano, "bold"),
        bg="white",
        fg=color
    )
    label.pack()

    return label


lbl_referencias = crear_card(0, "REFERENCIAS", "#0F4C81")
lbl_unidades = crear_card(1, "UNIDADES", "#0F4C81")
lbl_valor_total = crear_card(2, "VALOR INVENTARIO", "#0F4C81", 18)
lbl_stock = crear_card(3, "STOCK BAJO", "#C47A00")
lbl_agotados = crear_card(4, "AGOTADOS", "red")

cargar_inventario()
ventana.mainloop()