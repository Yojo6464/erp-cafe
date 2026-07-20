
"""
SIGA ERP - Ejecución Real de Producción v3
Archivo: ejecucion_produccion_v3.py
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from motor_ejecucion_produccion_v3 import (
    conectar,
    ejecutar_produccion,
)

C_FONDO = "#EEF3F8"
C_BLANCO = "#FFFFFF"
C_OSCURO = "#153B5B"
C_AZUL = "#0F5C8E"
C_VERDE = "#15803D"
C_NARANJA = "#C56A00"
C_ROJO = "#B42318"
C_GRIS = "#64748B"
C_TEXTO = "#1F2937"
C_BORDE = "#D7E0E8"

ordenes_cache = {}


def hoy():
    return datetime.now().strftime("%Y-%m-%d")


def numero(valor):
    return f"{float(valor or 0):,.4f}"


def moneda(valor):
    return f"${float(valor or 0):,.2f}"


def valor_no_negativo(texto, nombre):
    try:
        valor = float(
            str(texto).replace(",", "").strip() or 0
        )
    except ValueError as error:
        raise ValueError(
            f"{nombre} debe ser numérico."
        ) from error

    if valor < 0:
        raise ValueError(
            f"{nombre} no puede ser negativo."
        )

    return valor


def cargar_ordenes():
    ordenes_cache.clear()

    with conectar() as con:
        filas = con.execute("""
            SELECT
                o.id,
                o.numero,
                o.fecha_programada,
                p.nombre AS producto,
                p.presentacion,
                o.cantidad_programada,
                o.cantidad_producida,
                o.unidad,
                o.lote_planeado,
                o.centro_trabajo,
                o.responsable,
                o.estado,
                COALESCE(o.costo_total_real, 0) AS costo_total_real,
                COALESCE(o.estado_contable, 'NO APLICA') AS estado_contable
            FROM ordenes_produccion_v2 o
            INNER JOIN productos_produccion p
                ON p.id=o.producto_id
            WHERE o.estado IN ('LIBERADA', 'EN PROCESO')
            ORDER BY o.id DESC
        """).fetchall()

    opciones = []

    for fila in filas:
        pendiente = (
            float(fila["cantidad_programada"] or 0)
            - float(fila["cantidad_producida"] or 0)
        )

        texto = (
            f"{fila['id']} | {fila['numero']} | "
            f"{fila['producto']} | {fila['presentacion']} | "
            f"Pendiente {pendiente:,.4f} {fila['unidad']}"
        )

        opciones.append(texto)
        ordenes_cache[int(fila["id"])] = dict(fila)

    combo_orden["values"] = opciones

    if opciones:
        combo_orden.current(0)
        cargar_orden_seleccionada()
    else:
        combo_orden.set("")
        limpiar_resumen_orden()


def orden_id():
    valor = combo_orden.get().strip()

    if not valor:
        return None

    try:
        return int(valor.split("|")[0].strip())
    except Exception:
        return None


def limpiar_resumen_orden():
    lbl_numero.config(text="—")
    lbl_producto.config(text="—")
    lbl_programada.config(text="0")
    lbl_producida.config(text="0")
    lbl_pendiente.config(text="0")
    lbl_lote.config(text="—")
    lbl_centro.config(text="—")
    lbl_responsable.config(text="—")
    entry_cantidad.delete(0, "end")


def cargar_orden_seleccionada(evento=None):
    oid = orden_id()

    if not oid or oid not in ordenes_cache:
        limpiar_resumen_orden()
        return

    fila = ordenes_cache[oid]
    programada = float(fila["cantidad_programada"] or 0)
    producida = float(fila["cantidad_producida"] or 0)
    pendiente = programada - producida

    lbl_numero.config(text=fila["numero"])
    lbl_producto.config(
        text=f"{fila['producto']} / {fila['presentacion']}"
    )
    lbl_programada.config(
        text=f"{numero(programada)} {fila['unidad']}"
    )
    lbl_producida.config(
        text=f"{numero(producida)} {fila['unidad']}"
    )
    lbl_pendiente.config(
        text=f"{numero(pendiente)} {fila['unidad']}"
    )
    lbl_lote.config(text=fila["lote_planeado"])
    lbl_centro.config(
        text=fila["centro_trabajo"] or "Sin asignar"
    )
    lbl_responsable.config(
        text=fila["responsable"] or "Sin asignar"
    )

    entry_cantidad.delete(0, "end")
    entry_cantidad.insert(0, str(pendiente))


def ejecutar():
    oid = orden_id()

    if not oid:
        messagebox.showerror(
            "Producción",
            "Seleccione una orden liberada o en proceso."
        )
        return

    try:
        fecha = entry_fecha.get().strip()
        datetime.strptime(fecha, "%Y-%m-%d")

        cantidad = valor_no_negativo(
            entry_cantidad.get(),
            "Cantidad producida"
        )

        if cantidad <= 0:
            raise ValueError(
                "Cantidad producida debe ser mayor que cero."
            )

        rechazada = valor_no_negativo(
            entry_rechazada.get(),
            "Cantidad rechazada"
        )
        merma = valor_no_negativo(
            entry_merma.get(),
            "Merma real"
        )
        mano_obra = valor_no_negativo(
            entry_mano_obra.get(),
            "Mano de obra"
        )
        indirectos = valor_no_negativo(
            entry_indirectos.get(),
            "Costos indirectos"
        )

    except ValueError as error:
        messagebox.showerror(
            "Producción",
            str(error)
        )
        return

    fila = ordenes_cache[oid]

    texto = (
        f"Orden: {fila['numero']}\n"
        f"Producto: {fila['producto']} / {fila['presentacion']}\n"
        f"Cantidad producida: {cantidad:,.4f}\n"
        f"Cantidad rechazada: {rechazada:,.4f}\n"
        f"Lote terminado: {fila['lote_planeado']}\n\n"
        "Se descontarán materias primas mediante FIFO, "
        "se actualizará el Kardex y se ingresará el "
        "producto terminado.\n\n"
        "¿Desea continuar?"
    )

    if not messagebox.askyesno(
        "Confirmar ejecución",
        texto
    ):
        return

    try:
        resultado = ejecutar_produccion(
            orden_id=oid,
            fecha=fecha,
            cantidad_producida=cantidad,
            cantidad_rechazada=rechazada,
            merma_real=merma,
            mano_obra_real=mano_obra,
            costos_indirectos_reales=indirectos,
            responsable=entry_responsable.get().strip(),
            observaciones=txt_observaciones.get(
                "1.0",
                "end"
            ).strip(),
        )

        contabilidad = resultado["contabilidad"]

        mensaje = (
            f"Ejecución: {resultado['numero_ejecucion']}\n"
            f"Orden: {resultado['orden']}\n"
            f"Estado de la orden: {resultado['estado_orden']}\n"
            f"Lote terminado: {resultado['lote_producto']}\n\n"
            f"Cantidad neta: {resultado['cantidad_neta']:,.4f}\n"
            f"Materiales: {moneda(resultado['costo_materiales'])}\n"
            f"Mano de obra: {moneda(resultado['mano_obra'])}\n"
            f"Indirectos: {moneda(resultado['costos_indirectos'])}\n"
            f"Costo total: {moneda(resultado['costo_total'])}\n"
            f"Costo unitario: {moneda(resultado['costo_unitario'])}\n\n"
            f"Contabilidad: {contabilidad['estado']}\n"
            f"{contabilidad['mensaje']}"
        )

        messagebox.showinfo(
            "Producción ejecutada",
            mensaje
        )

        limpiar_formulario()
        cargar_ordenes()
        cargar_historial()

    except Exception as error:
        messagebox.showerror(
            "No fue posible ejecutar",
            (
                "La operación fue revertida completamente.\n\n"
                f"{error}"
            )
        )


def limpiar_formulario():
    entry_fecha.delete(0, "end")
    entry_fecha.insert(0, hoy())

    for entrada in (
        entry_rechazada,
        entry_merma,
        entry_mano_obra,
        entry_indirectos,
    ):
        entrada.delete(0, "end")
        entrada.insert(0, "0")

    entry_responsable.delete(0, "end")
    txt_observaciones.delete("1.0", "end")


def cargar_historial():
    with conectar() as con:
        filas = con.execute("""
            SELECT
                e.id,
                e.numero_ejecucion,
                e.fecha,
                o.numero AS orden,
                p.nombre AS producto,
                p.presentacion,
                e.lote_producto,
                e.cantidad_producida,
                e.cantidad_rechazada,
                e.costo_materiales_real,
                e.mano_obra_real,
                e.costos_indirectos_reales,
                e.costo_total_real,
                e.costo_unitario_real,
                e.estado_contable,
                e.mensaje_contable
            FROM ejecuciones_produccion_v3 e
            INNER JOIN ordenes_produccion_v2 o
                ON o.id=e.orden_id
            INNER JOIN productos_produccion p
                ON p.id=o.producto_id
            ORDER BY e.id DESC
        """).fetchall()

    tabla_historial.delete(
        *tabla_historial.get_children()
    )

    for fila in filas:
        tabla_historial.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["numero_ejecucion"],
                fila["fecha"],
                fila["orden"],
                fila["producto"],
                fila["presentacion"],
                fila["lote_producto"],
                numero(fila["cantidad_producida"]),
                numero(fila["cantidad_rechazada"]),
                moneda(fila["costo_materiales_real"]),
                moneda(fila["mano_obra_real"]),
                moneda(fila["costos_indirectos_reales"]),
                moneda(fila["costo_total_real"]),
                moneda(fila["costo_unitario_real"]),
                fila["estado_contable"],
                fila["mensaje_contable"],
            )
        )


def ver_consumos():
    sel = tabla_historial.selection()

    if not sel:
        messagebox.showwarning(
            "Consumos",
            "Seleccione una ejecución."
        )
        return

    ejecucion_id = int(sel[0])

    with conectar() as con:
        filas = con.execute("""
            SELECT
                producto,
                presentacion,
                lote,
                cantidad,
                costo_unitario,
                costo_total,
                fecha_ingreso_lote
            FROM consumos_produccion_v3
            WHERE ejecucion_id=?
            ORDER BY id
        """, (ejecucion_id,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title("Consumos FIFO")
    top.geometry("1100x560")

    columnas = (
        "Producto",
        "Presentación",
        "Lote",
        "Cantidad",
        "Costo unitario",
        "Costo total",
        "Ingreso lote"
    )

    tv = ttk.Treeview(
        top,
        columns=columnas,
        show="headings"
    )

    for columna in columnas:
        tv.heading(columna, text=columna)

    tv.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=15
    )

    for fila in filas:
        tv.insert(
            "",
            "end",
            values=(
                fila["producto"],
                fila["presentacion"],
                fila["lote"],
                numero(fila["cantidad"]),
                moneda(fila["costo_unitario"]),
                moneda(fila["costo_total"]),
                fila["fecha_ingreso_lote"],
            )
        )


ventana = tk.Tk()
ventana.title(
    "SIGA ERP - Ejecución Real de Producción v3"
)
ventana.geometry("1550x900")
ventana.minsize(1200, 720)
ventana.configure(bg=C_FONDO)

try:
    ventana.state("zoomed")
except tk.TclError:
    pass

estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Treeview",
    rowheight=27,
    font=("Segoe UI", 9)
)
estilo.configure(
    "Treeview.Heading",
    font=("Segoe UI", 9, "bold")
)

header = tk.Frame(
    ventana,
    bg=C_OSCURO,
    height=84
)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="EJECUCIÓN REAL DE PRODUCCIÓN v3",
    bg=C_OSCURO,
    fg="white",
    font=("Segoe UI", 21, "bold")
).pack(anchor="w", padx=25, pady=(15, 0))

tk.Label(
    header,
    text=(
        "Consumo FIFO, Kardex, producto terminado, "
        "costos reales y trazabilidad"
    ),
    bg=C_OSCURO,
    fg="#BFDBFE",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=26, pady=(3, 0))

notebook = ttk.Notebook(ventana)
notebook.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=15
)

tab_ejecutar = tk.Frame(
    notebook,
    bg=C_FONDO
)
tab_historial = tk.Frame(
    notebook,
    bg=C_FONDO
)

notebook.add(
    tab_ejecutar,
    text="  Ejecutar producción  "
)
notebook.add(
    tab_historial,
    text="  Historial y consumos  "
)

frame_orden = tk.LabelFrame(
    tab_ejecutar,
    text="ORDEN LIBERADA O EN PROCESO",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_orden.pack(
    fill="x",
    padx=10,
    pady=10
)

tk.Label(
    frame_orden,
    text="Seleccionar orden",
    bg=C_BLANCO,
    fg=C_GRIS
).grid(row=0, column=0, sticky="w")

combo_orden = ttk.Combobox(
    frame_orden,
    state="readonly",
    width=90
)
combo_orden.grid(
    row=1,
    column=0,
    columnspan=4,
    sticky="ew",
    padx=(0, 8)
)
combo_orden.bind(
    "<<ComboboxSelected>>",
    cargar_orden_seleccionada
)

tk.Button(
    frame_orden,
    text="Actualizar órdenes",
    command=cargar_ordenes,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).grid(row=1, column=4, padx=5)

for i in range(5):
    frame_orden.columnconfigure(i, weight=1)

resumen = tk.Frame(
    frame_orden,
    bg=C_BLANCO
)
resumen.grid(
    row=2,
    column=0,
    columnspan=5,
    sticky="ew",
    pady=(12, 0)
)

for i in range(8):
    resumen.columnconfigure(i, weight=1)


def campo_resumen(columna, titulo):
    marco = tk.Frame(
        resumen,
        bg=C_BLANCO
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=5
    )

    tk.Label(
        marco,
        text=titulo,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="—",
        bg=C_BLANCO,
        fg=C_TEXTO,
        font=("Segoe UI", 10, "bold")
    )
    valor.pack(anchor="w")
    return valor


lbl_numero = campo_resumen(0, "ORDEN")
lbl_producto = campo_resumen(1, "PRODUCTO")
lbl_programada = campo_resumen(2, "PROGRAMADA")
lbl_producida = campo_resumen(3, "PRODUCIDA")
lbl_pendiente = campo_resumen(4, "PENDIENTE")
lbl_lote = campo_resumen(5, "LOTE")
lbl_centro = campo_resumen(6, "CENTRO")
lbl_responsable = campo_resumen(7, "RESPONSABLE")

frame_datos = tk.LabelFrame(
    tab_ejecutar,
    text="DATOS DE LA EJECUCIÓN",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_datos.pack(
    fill="x",
    padx=10,
    pady=(0, 10)
)

campos = [
    "Fecha",
    "Cantidad producida",
    "Cantidad rechazada",
    "Merma real",
    "Mano de obra",
    "Costos indirectos",
    "Responsable ejecución"
]

for i, texto in enumerate(campos):
    tk.Label(
        frame_datos,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS
    ).grid(row=0, column=i, sticky="w", padx=4)

entry_fecha = ttk.Entry(frame_datos)
entry_fecha.grid(row=1, column=0, sticky="ew", padx=4)

entry_cantidad = ttk.Entry(frame_datos)
entry_cantidad.grid(row=1, column=1, sticky="ew", padx=4)

entry_rechazada = ttk.Entry(frame_datos)
entry_rechazada.grid(row=1, column=2, sticky="ew", padx=4)

entry_merma = ttk.Entry(frame_datos)
entry_merma.grid(row=1, column=3, sticky="ew", padx=4)

entry_mano_obra = ttk.Entry(frame_datos)
entry_mano_obra.grid(row=1, column=4, sticky="ew", padx=4)

entry_indirectos = ttk.Entry(frame_datos)
entry_indirectos.grid(row=1, column=5, sticky="ew", padx=4)

entry_responsable = ttk.Entry(frame_datos)
entry_responsable.grid(row=1, column=6, sticky="ew", padx=4)

for i in range(7):
    frame_datos.columnconfigure(i, weight=1)

tk.Label(
    frame_datos,
    text="Observaciones / motivo de merma",
    bg=C_BLANCO,
    fg=C_GRIS
).grid(
    row=2,
    column=0,
    sticky="w",
    pady=(10, 0)
)

txt_observaciones = tk.Text(
    frame_datos,
    height=3,
    relief="solid",
    bd=1
)
txt_observaciones.grid(
    row=3,
    column=0,
    columnspan=7,
    sticky="ew"
)

acciones = tk.Frame(
    tab_ejecutar,
    bg=C_FONDO
)
acciones.pack(
    fill="x",
    padx=10,
    pady=(0, 10)
)

tk.Button(
    acciones,
    text="EJECUTAR PRODUCCIÓN",
    command=ejecutar,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 11, "bold"),
    padx=24,
    pady=10
).pack(side="left")

tk.Button(
    acciones,
    text="Limpiar datos",
    command=limpiar_formulario,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=10
).pack(side="left", padx=8)

tk.Label(
    tab_ejecutar,
    text=(
        "La ejecución valida el período antes de modificar datos. "
        "Si ocurre un error, inventario, Kardex, costos y trazabilidad "
        "se revierten completamente."
    ),
    bg=C_FONDO,
    fg=C_GRIS,
    font=("Segoe UI", 9)
).pack(anchor="w", padx=12)

# HISTORIAL
barra = tk.Frame(
    tab_historial,
    bg=C_BLANCO
)
barra.pack(
    fill="x",
    padx=10,
    pady=10
)

tk.Button(
    barra,
    text="Actualizar",
    command=cargar_historial,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="left", padx=5)

tk.Button(
    barra,
    text="Ver consumos FIFO",
    command=ver_consumos,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

columnas_historial = (
    "Ejecución",
    "Fecha",
    "Orden",
    "Producto",
    "Presentación",
    "Lote PT",
    "Producida",
    "Rechazada",
    "Materiales",
    "Mano de obra",
    "Indirectos",
    "Costo total",
    "Costo unitario",
    "Contabilidad",
    "Mensaje contable"
)

tabla_historial = ttk.Treeview(
    tab_historial,
    columns=columnas_historial,
    show="headings"
)

for columna in columnas_historial:
    tabla_historial.heading(
        columna,
        text=columna
    )

tabla_historial.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

limpiar_formulario()
cargar_ordenes()
cargar_historial()

ventana.mainloop()
