import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB = "erp_cafe.db"


# ==================================================
# CONEXION
# ==================================================

def conectar():
    return sqlite3.connect(DB)


# ==================================================
# CARGAR LOTES
# ==================================================

def cargar_lotes():

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT lote
        FROM almacen_pergamino
        WHERE saldo_kg > 0
        ORDER BY lote
    """)

    datos = [fila[0] for fila in cur.fetchall()]

    con.close()

    return datos


# ==================================================
# HISTORIAL
# ==================================================

def cargar_historial():

    for item in tabla.get_children():
        tabla.delete(item)

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT
            fecha,
            lote,
            producto,
            presentacion,
            cantidad_bolsas,
            costo_unitario
        FROM produccion
        ORDER BY id DESC
    """)

    for fila in cur.fetchall():
        tabla.insert("", tk.END, values=fila)

    con.close()


# ==================================================
# REGISTRAR PRODUCCION
# ==================================================

def registrar_produccion():

    try:

        lote = combo_lote.get()

        if lote == "":
            messagebox.showerror(
                "Error",
                "Seleccione un lote"
            )
            return

        kg_verde = float(entry_kg_verde.get())
        merma = float(entry_merma.get())

        producto = combo_producto.get()
        presentacion = combo_presentacion.get()

        cantidad_bolsas = int(entry_bolsas.get())

        costo_maquila = float(
            entry_maquila.get() or 0
        )

        costo_empaque = float(
            entry_empaque.get() or 0
        )

        costo_transporte = float(
            entry_transporte.get() or 0
        )

        observaciones = txt_obs.get(
            "1.0",
            tk.END
        ).strip()

        con = conectar()
        cur = con.cursor()

        # =====================================
        # VALIDAR PERGAMINO
        # =====================================

        cur.execute("""
            SELECT saldo_kg,
                   costo_kg
            FROM almacen_pergamino
            WHERE lote = ?
            ORDER BY id DESC
            LIMIT 1
        """, (lote,))

        fila = cur.fetchone()

        if fila is None:

            messagebox.showerror(
                "Error",
                "Lote no encontrado"
            )

            con.close()
            return

        saldo_actual = fila[0]
        costo_kg = fila[1]

        if kg_verde > saldo_actual:

            messagebox.showerror(
                "Error",
                f"Saldo disponible: {saldo_actual} kg"
            )

            con.close()
            return

        # =====================================
        # CALCULOS
        # =====================================

        cafe_tostado = kg_verde * (
            1 - (merma / 100)
        )

        costo_materia_prima = (
            kg_verde * costo_kg
        )

        costo_total = (
            costo_materia_prima
            + costo_maquila
            + costo_empaque
            + costo_transporte
        )

        costo_unitario = (
            costo_total / cantidad_bolsas
        )

        saldo_nuevo = (
            saldo_actual - kg_verde
        )

        # =====================================
        # DESCONTAR PERGAMINO
        # =====================================

        cur.execute("""
            UPDATE almacen_pergamino
            SET saldo_kg = ?
            WHERE lote = ?
        """, (
            saldo_nuevo,
            lote
        ))

        # =====================================
        # GUARDAR PRODUCCION
        # =====================================

        cur.execute("""
        INSERT INTO produccion
        (
            fecha,
            lote,
            cafe_verde_kg,
            merma_pct,
            cafe_tostado_kg,
            producto,
            presentacion,
            cantidad_bolsas,
            costo_materia_prima,
            costo_maquila,
            costo_empaque,
            costo_transporte,
            costo_total,
            costo_unitario,
            observaciones
        )
        VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            lote,
            kg_verde,
            merma,
            cafe_tostado,
            producto,
            presentacion,
            cantidad_bolsas,
            costo_materia_prima,
            costo_maquila,
            costo_empaque,
            costo_transporte,
            costo_total,
            costo_unitario,
            observaciones

        ))

        # =====================================
        # ACTUALIZAR INVENTARIO
        # =====================================

        cur.execute("""
            SELECT id,
                   cantidad
            FROM inventario
            WHERE producto = ?
            AND presentacion = ?
        """, (
            producto,
            presentacion
        ))

        inv = cur.fetchone()

        if inv:

            nuevo_stock = (
                inv[1]
                + cantidad_bolsas
            )

            cur.execute("""
                UPDATE inventario
                SET cantidad = ?,
                    lote = ?,
                    costo_unitario = ?,
                    fecha_ingreso = ?
                WHERE id = ?
            """, (
                nuevo_stock,
                lote,
                costo_unitario,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                inv[0]
            ))

        else:

            cur.execute("""
            INSERT INTO inventario
            (
                producto,
                presentacion,
                cantidad,
                lote,
                costo_unitario,
                fecha_ingreso,
                numero_despacho
            )
            VALUES
            (?,?,?,?,?,?,?)
            """, (

                producto,
                presentacion,
                cantidad_bolsas,
                lote,
                costo_unitario,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                None

            ))

        # =====================================
        # DESCONTAR EMPAQUES
        # =====================================

        tipo_empaque = (
            "bolsa "
            + presentacion.replace(" g", " gr")
        )

        cur.execute("""
            SELECT id,
                   saldo
            FROM almacen_empaques
            WHERE LOWER(tipo_empaque)=LOWER(?)
            ORDER BY id DESC
            LIMIT 1
        """, (tipo_empaque,))

        empaque = cur.fetchone()

        if empaque:

            saldo_empaque = empaque[1]

            if saldo_empaque < cantidad_bolsas:

                messagebox.showerror(
                    "Error",
                    f"No hay suficientes empaques. Saldo disponible: {saldo_empaque}"
                )

                con.rollback()
                con.close()
                return

            nuevo_saldo_empaque = (
                saldo_empaque
                - cantidad_bolsas
            )

            cur.execute("""
                UPDATE almacen_empaques
                SET saldo = ?
                WHERE id = ?
            """, (
                nuevo_saldo_empaque,
                empaque[0]
            ))

        else:

            messagebox.showerror(
                "Error",
                f"No existe el empaque {tipo_empaque}"
            )

            con.rollback()
            con.close()
            return
     
    # =====================================
    # REGISTRAR EN KARDEX
    # =====================================

        cur.execute("""
    SELECT cantidad
    FROM inventario
    WHERE producto=?
    AND presentacion=?
    """,
    (
        producto,
        presentacion
    ))

        fila_kardex = cur.fetchone()

        if fila_kardex:
         saldo_kardex = float(fila_kardex[0])
        else:
         saldo_kardex = float(cantidad_bolsas)

        cur.execute("""
    INSERT INTO kardex(
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
    "",
    (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        producto,
        presentacion,
        "ENTRADA",
        float(cantidad_bolsas),
        0,
        saldo_kardex,
        float(costo_unitario),
        lote,
        "PRODUCCION",
        observaciones
    ))

    con.commit()

   
        con.commit()
        con.close()

        messagebox.showinfo(
            "Correcto",
            "Producción registrada correctamente"
        )

        cargar_historial()

        cargar_historial()

    except Exception as e:

        import traceback

        print(traceback.format_exc())

        messagebox.showerror(
            "Error",
            str(e)
        )
        messagebox.showerror(
            "Error",
            str(e)
        )


# ==================================================
# VENTANA
# ==================================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Producción"
)

ventana.geometry("1200x750")

frame = tk.Frame(ventana)
frame.pack(pady=10)

tk.Label(frame, text="Lote").grid(row=0, column=0)
combo_lote = ttk.Combobox(
    frame,
    values=cargar_lotes(),
    width=30,
    state="readonly"
)
combo_lote.grid(row=0, column=1)

tk.Label(frame, text="Kg Café Verde").grid(row=1, column=0)
entry_kg_verde = tk.Entry(frame)
entry_kg_verde.grid(row=1, column=1)

tk.Label(frame, text="Merma (%)").grid(row=2, column=0)
entry_merma = tk.Entry(frame)
entry_merma.insert(0, "18")
entry_merma.grid(row=2, column=1)

tk.Label(frame, text="Producto").grid(row=3, column=0)
combo_producto = ttk.Combobox(
    frame,
    values=[
        "Tradicional",
        "Premium",
        "Café Especial"
    ],
    state="readonly"
)
combo_producto.grid(row=3, column=1)

tk.Label(frame, text="Presentación").grid(row=4, column=0)
combo_presentacion = ttk.Combobox(
    frame,
    values=[
        "125 g",
        "250 g",
        "500 g",
        "1000 g"
    ],
    state="readonly"
)
combo_presentacion.grid(row=4, column=1)

tk.Label(frame, text="Cantidad Bolsas").grid(row=5, column=0)
entry_bolsas = tk.Entry(frame)
entry_bolsas.grid(row=5, column=1)

tk.Label(frame, text="Costo Maquila").grid(row=6, column=0)
entry_maquila = tk.Entry(frame)
entry_maquila.grid(row=6, column=1)

tk.Label(frame, text="Costo Empaque").grid(row=7, column=0)
entry_empaque = tk.Entry(frame)
entry_empaque.grid(row=7, column=1)

tk.Label(frame, text="Costo Transporte").grid(row=8, column=0)
entry_transporte = tk.Entry(frame)
entry_transporte.grid(row=8, column=1)

tk.Label(frame, text="Observaciones").grid(row=9, column=0)

txt_obs = tk.Text(
    frame,
    width=40,
    height=4
)
txt_obs.grid(row=9, column=1)

tk.Button(
    frame,
    text="Registrar Producción",
    bg="green",
    fg="white",
    command=registrar_produccion
).grid(row=10, column=1, pady=10)

columnas = (
    "Fecha",
    "Lote",
    "Producto",
    "Presentación",
    "Bolsas",
    "Costo Unitario"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings",
    height=15
)

for col in columnas:
    tabla.heading(col, text=col)

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

cargar_historial()

ventana.mainloop()
