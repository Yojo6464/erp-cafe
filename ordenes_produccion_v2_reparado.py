
"""
SIGA ERP - Órdenes de Producción v2
Archivo: ordenes_produccion_v2.py
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from motor_ordenes_produccion import MotorOrdenesProduccion

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"

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

requerimientos_actuales = []
orden_actual_id = None


def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )
    con = sqlite3.connect(RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 5000")
    return con


def usuario():
    return (
        os.environ.get("ERP_USUARIO", "").strip()
        or os.environ.get("USERNAME", "usuario_local")
    )


def hoy():
    return datetime.now().strftime("%Y-%m-%d")


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def numero(valor):
    return f"{float(valor or 0):,.4f}"


def moneda(valor):
    return f"${float(valor or 0):,.2f}"


def a_numero(valor, nombre):
    try:
        n = float(str(valor).replace(",", "").strip())
    except ValueError as error:
        raise ValueError(
            f"{nombre} debe ser numérico."
        ) from error

    if n <= 0:
        raise ValueError(
            f"{nombre} debe ser mayor que cero."
        )
    return n


def numero_orden():
    with conectar() as con:
        fila = con.execute("""
            SELECT IFNULL(MAX(id), 0) + 1 AS siguiente
            FROM ordenes_produccion_v2
        """).fetchone()

    return (
        f"OP-{datetime.now().strftime('%Y%m%d')}-"
        f"{int(fila['siguiente']):05d}"
    )


def lote_planeado():
    with conectar() as con:
        fila = con.execute("""
            SELECT IFNULL(MAX(id), 0) + 1 AS siguiente
            FROM ordenes_produccion_v2
        """).fetchone()

    return (
        f"PT-{datetime.now().strftime('%Y%m%d')}-"
        f"{int(fila['siguiente']):05d}"
    )


def cargar_formulas():
    with conectar() as con:
        filas = con.execute("""
            SELECT
                f.id,
                f.codigo,
                f.version,
                p.codigo AS producto_codigo,
                p.nombre,
                p.presentacion,
                p.unidad,
                f.cantidad_base,
                f.unidad_base,
                f.rendimiento_pct,
                f.merma_estandar_pct
            FROM formulas_produccion f
            INNER JOIN productos_produccion p
                ON p.id=f.producto_id
            WHERE f.estado='ACTIVA'
              AND p.estado='ACTIVO'
            ORDER BY p.nombre, p.presentacion
        """).fetchall()

    valores = [
        (
            f"{f['id']} | {f['codigo']} | V{f['version']} | "
            f"{f['producto_codigo']} | {f['nombre']} | "
            f"{f['presentacion']} | {f['unidad']}"
        )
        for f in filas
    ]
    combo_formula["values"] = valores
    if valores:
        combo_formula.current(0)
        ventana.after(100, cargar_formula)


def formula_id():
    valor = combo_formula.get().strip()

    if not valor:
        return None

    try:
        return int(valor.split("|")[0].strip())
    except Exception:
        return None


def inventario_disponible(producto, presentacion):
    with conectar() as con:
        fila = con.execute("""
            SELECT IFNULL(SUM(cantidad), 0) AS disponible
            FROM inventario
            WHERE producto=?
              AND presentacion=?
        """, (producto, presentacion)).fetchone()

    return float(fila["disponible"] or 0)


def cargar_formula(evento=None):
    fid = formula_id()

    if not fid:
        return

    with conectar() as con:
        fila = con.execute("""
            SELECT
                p.nombre,
                p.presentacion,
                p.unidad,
                f.cantidad_base,
                f.unidad_base,
                f.rendimiento_pct,
                f.merma_estandar_pct
            FROM formulas_produccion f
            INNER JOIN productos_produccion p
                ON p.id=f.producto_id
            WHERE f.id=?
        """, (fid,)).fetchone()

    lbl_producto.config(
        text=f"{fila['nombre']} / {fila['presentacion']}"
    )
    lbl_formula_base.config(
        text=(
            f"Base: {numero(fila['cantidad_base'])} "
            f"{fila['unidad_base']}  |  "
            f"Rendimiento: {fila['rendimiento_pct']:.2f}%  |  "
            f"Merma estándar: {fila['merma_estandar_pct']:.2f}%"
        )
    )

    calcular_requerimientos()


def calcular_requerimientos(evento=None):
    global requerimientos_actuales

    requerimientos_actuales = []
    tabla_requerimientos.delete(
        *tabla_requerimientos.get_children()
    )

    fid = formula_id()

    if not fid:
        return

    try:
        cantidad = a_numero(
            entry_cantidad.get(),
            "Cantidad programada"
        )
    except ValueError:
        return

    with conectar() as con:
        cab = con.execute("""
            SELECT cantidad_base
            FROM formulas_produccion
            WHERE id=?
        """, (fid,)).fetchone()

        componentes = con.execute("""
            SELECT
                componente,
                presentacion,
                tipo_componente,
                cantidad,
                unidad,
                merma_pct,
                costo_unitario_estandar,
                costo_total_estandar
            FROM formulas_componentes
            WHERE formula_id=?
            ORDER BY orden, id
        """, (fid,)).fetchall()

    factor = cantidad / float(cab["cantidad_base"] or 1)

    for i, item in enumerate(componentes, 1):
        teorica_base = float(item["cantidad"] or 0) * factor
        teorica = teorica_base * (
            1 + float(item["merma_pct"] or 0) / 100
        )

        disponible = inventario_disponible(
            item["componente"],
            item["presentacion"]
        )

        estado = (
            "DISPONIBLE"
            if disponible >= teorica
            else "FALTANTE"
        )

        costo_total = (
            teorica
            * float(item["costo_unitario_estandar"] or 0)
        )

        fila = {
            "componente": item["componente"],
            "presentacion": item["presentacion"],
            "tipo": item["tipo_componente"],
            "cantidad_teorica": teorica,
            "unidad": item["unidad"],
            "merma_pct": float(item["merma_pct"] or 0),
            "disponible": disponible,
            "estado": estado,
            "costo_unitario": float(
                item["costo_unitario_estandar"] or 0
            ),
            "costo_total": costo_total
        }

        requerimientos_actuales.append(fila)

        tabla_requerimientos.insert(
            "",
            "end",
            values=(
                i,
                fila["componente"],
                fila["presentacion"],
                fila["tipo"],
                numero(fila["cantidad_teorica"]),
                fila["unidad"],
                numero(fila["disponible"]),
                fila["estado"],
                moneda(fila["costo_unitario"]),
                moneda(fila["costo_total"])
            ),
            tags=(
                "ok"
                if estado == "DISPONIBLE"
                else "faltante"
            )
        )

    actualizar_totales_requerimientos()


def actualizar_totales_requerimientos():
    costo = sum(
        fila["costo_total"]
        for fila in requerimientos_actuales
    )
    faltantes = sum(
        1
        for fila in requerimientos_actuales
        if fila["estado"] == "FALTANTE"
    )

    lbl_costo_estandar.config(text=moneda(costo))
    lbl_faltantes.config(text=str(faltantes))


def limpiar():
    global requerimientos_actuales, orden_actual_id

    requerimientos_actuales = []
    orden_actual_id = None

    lbl_numero.config(text=numero_orden())
    entry_fecha.delete(0, "end")
    entry_fecha.insert(0, hoy())
    entry_fecha_programada.delete(0, "end")
    entry_fecha_programada.insert(0, hoy())
    if combo_formula["values"]:
        combo_formula.current(0)
    else:
        combo_formula.set("")
    entry_cantidad.delete(0, "end")
    entry_lote.delete(0, "end")
    entry_lote.insert(0, lote_planeado())
    combo_centro.set("")
    entry_responsable.delete(0, "end")
    combo_prioridad.set("NORMAL")
    txt_observaciones.delete("1.0", "end")

    lbl_producto.config(text="Seleccione una fórmula activa")
    lbl_formula_base.config(text="")
    lbl_costo_estandar.config(text="$0.00")
    lbl_faltantes.config(text="0")

    tabla_requerimientos.delete(
        *tabla_requerimientos.get_children()
    )


def crear_orden():
    fid = formula_id()

    if not fid:
        messagebox.showerror(
            "Orden",
            "Seleccione una fórmula activa."
        )
        return

    if not requerimientos_actuales:
        messagebox.showerror(
            "Orden",
            "Calcule primero los requerimientos."
        )
        return

    try:
        cantidad = a_numero(
            entry_cantidad.get(),
            "Cantidad programada"
        )
        datetime.strptime(
            entry_fecha.get().strip(),
            "%Y-%m-%d"
        )
        datetime.strptime(
            entry_fecha_programada.get().strip(),
            "%Y-%m-%d"
        )
    except ValueError as error:
        messagebox.showerror(
            "Orden",
            str(error)
        )
        return

    lote = entry_lote.get().strip()

    if not lote:
        messagebox.showerror(
            "Orden",
            "Ingrese el lote planeado."
        )
        return

    with conectar() as con:
        datos = con.execute("""
            SELECT
                f.producto_id,
                p.unidad
            FROM formulas_produccion f
            INNER JOIN productos_produccion p
                ON p.id=f.producto_id
            WHERE f.id=?
              AND f.estado='ACTIVA'
        """, (fid,)).fetchone()

    if not datos:
        messagebox.showerror(
            "Orden",
            "La fórmula seleccionada ya no está activa."
        )
        return

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO ordenes_produccion_v2(
                numero,
                fecha_emision,
                fecha_programada,
                producto_id,
                formula_id,
                cantidad_programada,
                unidad,
                lote_planeado,
                centro_trabajo,
                responsable,
                prioridad,
                estado,
                observaciones,
                creada_por
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'BORRADOR', ?, ?)
        """, (
            lbl_numero.cget("text"),
            entry_fecha.get().strip(),
            entry_fecha_programada.get().strip(),
            datos["producto_id"],
            fid,
            cantidad,
            datos["unidad"],
            lote,
            combo_centro.get().strip(),
            entry_responsable.get().strip(),
            combo_prioridad.get().strip(),
            txt_observaciones.get(
                "1.0",
                "end"
            ).strip(),
            usuario()
        ))

        orden_id = cur.lastrowid

        for fila in requerimientos_actuales:
            con.execute("""
                INSERT INTO ordenes_requerimientos_v2(
                    orden_id,
                    componente,
                    presentacion,
                    tipo_componente,
                    cantidad_teorica,
                    cantidad_reservada,
                    cantidad_consumida,
                    unidad,
                    merma_pct,
                    costo_unitario_estandar,
                    costo_total_estandar,
                    disponible_creacion,
                    estado_disponibilidad
                )
                VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?)
            """, (
                orden_id,
                fila["componente"],
                fila["presentacion"],
                fila["tipo"],
                fila["cantidad_teorica"],
                fila["unidad"],
                fila["merma_pct"],
                fila["costo_unitario"],
                fila["costo_total"],
                fila["disponible"],
                fila["estado"]
            ))

        con.execute("""
            INSERT INTO ordenes_historial_v2(
                orden_id,
                usuario,
                estado_anterior,
                estado_nuevo,
                accion,
                observaciones
            )
            VALUES (?, ?, '', 'BORRADOR', 'CREAR ORDEN', ?)
        """, (
            orden_id,
            usuario(),
            txt_observaciones.get(
                "1.0",
                "end"
            ).strip()
        ))

        con.commit()

        messagebox.showinfo(
            "Orden",
            (
                f"Orden {lbl_numero.cget('text')} creada "
                "correctamente en estado BORRADOR."
            )
        )

        limpiar()
        cargar_ordenes()

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Orden",
            (
                "No fue posible crear la orden.\n\n"
                f"{error}"
            )
        )

    finally:
        con.close()


def cargar_ordenes():
    estado = combo_filtro_estado.get().strip()

    sql = """
        SELECT
            o.id,
            o.numero,
            o.fecha_emision,
            o.fecha_programada,
            p.codigo AS producto_codigo,
            p.nombre,
            p.presentacion,
            o.cantidad_programada,
            o.cantidad_producida,
            o.unidad,
            o.lote_planeado,
            o.centro_trabajo,
            o.responsable,
            o.prioridad,
            o.estado,
            f.codigo AS formula_codigo,
            f.version AS formula_version
        FROM ordenes_produccion_v2 o
        INNER JOIN productos_produccion p
            ON p.id=o.producto_id
        INNER JOIN formulas_produccion f
            ON f.id=o.formula_id
        WHERE 1=1
    """
    params = []

    if estado and estado != "TODOS":
        sql += " AND o.estado=?"
        params.append(estado)

    sql += " ORDER BY o.id DESC"

    with conectar() as con:
        filas = con.execute(sql, params).fetchall()

    tabla_ordenes.delete(*tabla_ordenes.get_children())

    for fila in filas:
        tabla_ordenes.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["numero"],
                fila["fecha_emision"],
                fila["fecha_programada"],
                fila["producto_codigo"],
                fila["nombre"],
                fila["presentacion"],
                numero(fila["cantidad_programada"]),
                numero(fila["cantidad_producida"]),
                fila["unidad"],
                fila["lote_planeado"],
                fila["centro_trabajo"],
                fila["responsable"],
                fila["prioridad"],
                fila["estado"],
                (
                    f"{fila['formula_codigo']} "
                    f"V{fila['formula_version']}"
                )
            ),
            tags=(fila["estado"].lower(),)
        )

    actualizar_kpis()


def orden_seleccionada():
    sel = tabla_ordenes.selection()

    if not sel:
        messagebox.showwarning(
            "Orden",
            "Seleccione una orden."
        )
        return None

    return int(sel[0])


def regenerar_requerimientos():
    orden_id = orden_seleccionada()
    if not orden_id:
        return

    try:
        motor = MotorOrdenesProduccion(RUTA_DB, usuario())
        filas = motor.generar_requerimientos(orden_id, reemplazar=True)
        messagebox.showinfo(
            "Requerimientos",
            f"Se regeneraron {len(filas)} requerimientos correctamente."
        )
        cargar_ordenes()
    except Exception as error:
        messagebox.showerror("Requerimientos", str(error))


def asegurar_requerimientos_y_disponibilidad(orden_id, estado_nuevo):
    if estado_nuevo not in ("APROBADA", "LIBERADA"):
        return
    motor = MotorOrdenesProduccion(RUTA_DB, usuario())
    with conectar() as con:
        cantidad = int(con.execute(
            "SELECT COUNT(*) FROM ordenes_requerimientos_v2 WHERE orden_id=?",
            (orden_id,),
        ).fetchone()[0])
    if cantidad == 0:
        motor.generar_requerimientos(orden_id)
    if estado_nuevo == "LIBERADA":
        faltantes = [x for x in motor.validar_disponibilidad(orden_id) if not x.cumple]
        if faltantes:
            detalle = "; ".join(
                f"{x.componente}: faltan {x.faltante:,.4f} {x.unidad}"
                for x in faltantes
            )
            raise ValueError("No se puede liberar por falta de materiales. " + detalle)


def cambiar_estado(estado_nuevo):
    orden_id = orden_seleccionada()

    if not orden_id:
        return

    with conectar() as con:
        orden = con.execute("""
            SELECT numero, estado
            FROM ordenes_produccion_v2
            WHERE id=?
        """, (orden_id,)).fetchone()

    transiciones = {
        "BORRADOR": ["APROBADA", "ANULADA"],
        "APROBADA": ["LIBERADA", "ANULADA"],
        "LIBERADA": ["EN PROCESO", "ANULADA"],
        "EN PROCESO": ["TERMINADA", "SUSPENDIDA"],
        "SUSPENDIDA": ["EN PROCESO", "ANULADA"],
        "TERMINADA": [],
        "ANULADA": []
    }

    if estado_nuevo not in transiciones.get(
        orden["estado"],
        []
    ):
        messagebox.showerror(
            "Orden",
            (
                f"No se permite cambiar de {orden['estado']} "
                f"a {estado_nuevo}."
            )
        )
        return

    observacion = simpledialog.askstring(
        "Cambio de estado",
        (
            f"Orden: {orden['numero']}\n"
            f"{orden['estado']} → {estado_nuevo}\n\n"
            "Observación:"
        )
    )

    if observacion is None:
        return

    try:
        asegurar_requerimientos_y_disponibilidad(orden_id, estado_nuevo)
    except Exception as error:
        messagebox.showerror("Orden", str(error))
        return

    campos = {
        "APROBADA": ("aprobada_por", "aprobada_en"),
        "LIBERADA": ("liberada_por", "liberada_en"),
        "EN PROCESO": ("iniciada_por", "iniciada_en"),
        "TERMINADA": ("terminada_por", "terminada_en"),
        "ANULADA": ("anulada_por", "anulada_en")
    }

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        if estado_nuevo in campos:
            campo_usuario, campo_fecha = campos[estado_nuevo]

            con.execute(f"""
                UPDATE ordenes_produccion_v2
                SET estado=?,
                    {campo_usuario}=?,
                    {campo_fecha}=?,
                    actualizada_en=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                estado_nuevo,
                usuario(),
                ahora(),
                orden_id
            ))
        else:
            con.execute("""
                UPDATE ordenes_produccion_v2
                SET estado=?,
                    actualizada_en=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                estado_nuevo,
                orden_id
            ))

        if estado_nuevo == "ANULADA":
            con.execute("""
                UPDATE ordenes_produccion_v2
                SET motivo_anulacion=?
                WHERE id=?
            """, (
                observacion,
                orden_id
            ))

        con.execute("""
            INSERT INTO ordenes_historial_v2(
                orden_id,
                usuario,
                estado_anterior,
                estado_nuevo,
                accion,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            orden_id,
            usuario(),
            orden["estado"],
            estado_nuevo,
            f"CAMBIAR ESTADO A {estado_nuevo}",
            observacion
        ))

        con.commit()

        messagebox.showinfo(
            "Orden",
            f"Orden actualizada a {estado_nuevo}."
        )

        cargar_ordenes()

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Orden",
            str(error)
        )

    finally:
        con.close()


def ver_requerimientos():
    orden_id = orden_seleccionada()

    if not orden_id:
        return

    with conectar() as con:
        orden = con.execute("""
            SELECT numero, estado
            FROM ordenes_produccion_v2
            WHERE id=?
        """, (orden_id,)).fetchone()

        filas = con.execute("""
            SELECT
                componente,
                presentacion,
                tipo_componente,
                cantidad_teorica,
                cantidad_reservada,
                cantidad_consumida,
                unidad,
                disponible_creacion,
                estado_disponibilidad,
                costo_unitario_estandar,
                costo_total_estandar
            FROM ordenes_requerimientos_v2
            WHERE orden_id=?
            ORDER BY id
        """, (orden_id,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title(
        f"Requerimientos {orden['numero']}"
    )
    top.geometry("1200x600")
    top.configure(bg=C_FONDO)

    tk.Label(
        top,
        text=(
            f"REQUERIMIENTOS - {orden['numero']} "
            f"· {orden['estado']}"
        ),
        bg=C_OSCURO,
        fg="white",
        font=("Segoe UI", 17, "bold"),
        pady=14
    ).pack(fill="x")

    columnas = (
        "Componente",
        "Presentación",
        "Tipo",
        "Teórica",
        "Reservada",
        "Consumida",
        "Unidad",
        "Disponible creación",
        "Estado",
        "Costo unitario",
        "Costo total"
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
                fila["componente"],
                fila["presentacion"],
                fila["tipo_componente"],
                numero(fila["cantidad_teorica"]),
                numero(fila["cantidad_reservada"]),
                numero(fila["cantidad_consumida"]),
                fila["unidad"],
                numero(fila["disponible_creacion"]),
                fila["estado_disponibilidad"],
                moneda(fila["costo_unitario_estandar"]),
                moneda(fila["costo_total_estandar"])
            )
        )


def ver_historial():
    orden_id = orden_seleccionada()

    if not orden_id:
        return

    with conectar() as con:
        orden = con.execute("""
            SELECT numero
            FROM ordenes_produccion_v2
            WHERE id=?
        """, (orden_id,)).fetchone()

        filas = con.execute("""
            SELECT
                fecha_hora,
                usuario,
                estado_anterior,
                estado_nuevo,
                accion,
                observaciones
            FROM ordenes_historial_v2
            WHERE orden_id=?
            ORDER BY id
        """, (orden_id,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title(
        f"Historial {orden['numero']}"
    )
    top.geometry("1050x550")
    top.configure(bg=C_FONDO)

    tk.Label(
        top,
        text=f"HISTORIAL - {orden['numero']}",
        bg=C_OSCURO,
        fg="white",
        font=("Segoe UI", 17, "bold"),
        pady=14
    ).pack(fill="x")

    columnas = (
        "Fecha",
        "Usuario",
        "Estado anterior",
        "Estado nuevo",
        "Acción",
        "Observaciones"
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
                fila["fecha_hora"],
                fila["usuario"],
                fila["estado_anterior"],
                fila["estado_nuevo"],
                fila["accion"],
                fila["observaciones"]
            )
        )


def actualizar_kpis():
    with conectar() as con:
        totales = con.execute("""
            SELECT
                SUM(CASE WHEN estado='BORRADOR' THEN 1 ELSE 0 END) AS borrador,
                SUM(CASE WHEN estado='APROBADA' THEN 1 ELSE 0 END) AS aprobadas,
                SUM(CASE WHEN estado='LIBERADA' THEN 1 ELSE 0 END) AS liberadas,
                SUM(CASE WHEN estado='EN PROCESO' THEN 1 ELSE 0 END) AS proceso,
                SUM(CASE WHEN estado='TERMINADA' THEN 1 ELSE 0 END) AS terminadas
            FROM ordenes_produccion_v2
        """).fetchone()

    lbl_kpi_borrador.config(
        text=str(int(totales["borrador"] or 0))
    )
    lbl_kpi_aprobadas.config(
        text=str(int(totales["aprobadas"] or 0))
    )
    lbl_kpi_liberadas.config(
        text=str(int(totales["liberadas"] or 0))
    )
    lbl_kpi_proceso.config(
        text=str(int(totales["proceso"] or 0))
    )
    lbl_kpi_terminadas.config(
        text=str(int(totales["terminadas"] or 0))
    )


# INTERFAZ
ventana = tk.Tk()
ventana.title("SIGA ERP - Órdenes de Producción v2")
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
    text="ÓRDENES DE PRODUCCIÓN v2",
    bg=C_OSCURO,
    fg="white",
    font=("Segoe UI", 21, "bold")
).pack(anchor="w", padx=25, pady=(15, 0))

tk.Label(
    header,
    text=(
        "Planificación, requerimientos, aprobación, "
        "liberación y seguimiento"
    ),
    bg=C_OSCURO,
    fg="#BFDBFE",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=26, pady=(3, 0))

kpis = tk.Frame(ventana, bg=C_FONDO)
kpis.pack(fill="x", padx=15, pady=(12, 7))

for i in range(5):
    kpis.columnconfigure(i, weight=1)


def tarjeta(columna, titulo, color):
    marco = tk.Frame(
        kpis,
        bg=C_BLANCO,
        highlightbackground=C_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=4
    )

    tk.Frame(
        marco,
        bg=color,
        width=5
    ).pack(side="left", fill="y")

    contenido = tk.Frame(marco, bg=C_BLANCO)
    contenido.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=8
    )

    tk.Label(
        contenido,
        text=titulo,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        contenido,
        text="0",
        bg=C_BLANCO,
        fg=C_TEXTO,
        font=("Segoe UI", 15, "bold")
    )
    valor.pack(anchor="w", pady=(2, 0))
    return valor


lbl_kpi_borrador = tarjeta(
    0, "BORRADOR", C_GRIS
)
lbl_kpi_aprobadas = tarjeta(
    1, "APROBADAS", C_AZUL
)
lbl_kpi_liberadas = tarjeta(
    2, "LIBERADAS", C_NARANJA
)
lbl_kpi_proceso = tarjeta(
    3, "EN PROCESO", "#7C3AED"
)
lbl_kpi_terminadas = tarjeta(
    4, "TERMINADAS", C_VERDE
)

notebook = ttk.Notebook(ventana)
notebook.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=(0, 15)
)

tab_nueva = tk.Frame(notebook, bg=C_FONDO)
tab_historial = tk.Frame(notebook, bg=C_FONDO)

notebook.add(tab_nueva, text="  Nueva orden  ")
notebook.add(tab_historial, text="  Seguimiento de órdenes  ")

frame_datos = tk.LabelFrame(
    tab_nueva,
    text="DATOS DE LA ORDEN",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_datos.pack(fill="x", padx=10, pady=10)

campos = [
    "Número",
    "Fecha emisión",
    "Fecha programada",
    "Fórmula activa",
    "Cantidad programada",
    "Lote planeado",
    "Centro de trabajo",
    "Responsable",
    "Prioridad"
]

for i, texto in enumerate(campos):
    tk.Label(
        frame_datos,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS
    ).grid(
        row=0,
        column=i,
        sticky="w",
        padx=3
    )

lbl_numero = tk.Label(
    frame_datos,
    text=numero_orden(),
    bg=C_BLANCO,
    fg=C_AZUL,
    font=("Segoe UI", 9, "bold")
)
lbl_numero.grid(row=1, column=0, sticky="w", padx=3)

entry_fecha = ttk.Entry(frame_datos, width=13)
entry_fecha.grid(row=1, column=1, sticky="ew", padx=3)

entry_fecha_programada = ttk.Entry(frame_datos, width=13)
entry_fecha_programada.grid(row=1, column=2, sticky="ew", padx=3)

combo_formula = ttk.Combobox(
    frame_datos,
    state="readonly",
    width=36
)
combo_formula.grid(row=1, column=3, sticky="ew", padx=3)
combo_formula.bind(
    "<<ComboboxSelected>>",
    cargar_formula
)

entry_cantidad = ttk.Entry(frame_datos, width=14)
entry_cantidad.grid(row=1, column=4, sticky="ew", padx=3)
entry_cantidad.bind(
    "<KeyRelease>",
    calcular_requerimientos
)

entry_lote = ttk.Entry(frame_datos, width=18)
entry_lote.grid(row=1, column=5, sticky="ew", padx=3)

combo_centro = ttk.Combobox(
    frame_datos,
    values=[
        "MEZCLADO",
        "TOSTIÓN",
        "MOLIENDA",
        "ENVASADO",
        "EMPAQUE",
        "CORTE",
        "SOLDADURA",
        "PINTURA",
        "OTRO"
    ]
)
combo_centro.grid(row=1, column=6, sticky="ew", padx=3)

entry_responsable = ttk.Entry(frame_datos, width=18)
entry_responsable.grid(row=1, column=7, sticky="ew", padx=3)

combo_prioridad = ttk.Combobox(
    frame_datos,
    values=["BAJA", "NORMAL", "ALTA", "URGENTE"],
    state="readonly",
    width=12
)
combo_prioridad.grid(row=1, column=8, sticky="ew", padx=3)

for i in range(9):
    frame_datos.columnconfigure(i, weight=1)

lbl_producto = tk.Label(
    frame_datos,
    text="Seleccione una fórmula activa",
    bg=C_BLANCO,
    fg=C_AZUL,
    font=("Segoe UI", 10, "bold")
)
lbl_producto.grid(
    row=2,
    column=0,
    columnspan=4,
    sticky="w",
    padx=3,
    pady=(10, 0)
)

lbl_formula_base = tk.Label(
    frame_datos,
    text="",
    bg=C_BLANCO,
    fg=C_GRIS
)
lbl_formula_base.grid(
    row=2,
    column=4,
    columnspan=5,
    sticky="w",
    padx=3,
    pady=(10, 0)
)

tk.Label(
    frame_datos,
    text="Observaciones",
    bg=C_BLANCO,
    fg=C_GRIS
).grid(
    row=3,
    column=0,
    sticky="w",
    padx=3,
    pady=(10, 0)
)

txt_observaciones = tk.Text(
    frame_datos,
    height=2,
    relief="solid",
    bd=1
)
txt_observaciones.grid(
    row=4,
    column=0,
    columnspan=9,
    sticky="ew",
    padx=3
)

frame_req = tk.LabelFrame(
    tab_nueva,
    text="REQUERIMIENTOS CALCULADOS",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold")
)
frame_req.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

columnas_req = (
    "N",
    "Componente",
    "Presentación",
    "Tipo",
    "Cantidad teórica",
    "Unidad",
    "Disponible",
    "Estado",
    "Costo unitario",
    "Costo total"
)

tabla_requerimientos = ttk.Treeview(
    frame_req,
    columns=columnas_req,
    show="headings"
)

for columna in columnas_req:
    tabla_requerimientos.heading(
        columna,
        text=columna
    )

tabla_requerimientos.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

tabla_requerimientos.tag_configure(
    "ok",
    foreground=C_VERDE
)
tabla_requerimientos.tag_configure(
    "faltante",
    foreground=C_ROJO
)

pie_req = tk.Frame(frame_req, bg=C_BLANCO)
pie_req.pack(fill="x", padx=10, pady=(0, 10))

tk.Label(
    pie_req,
    text="Costo estándar estimado:",
    bg=C_BLANCO,
    fg=C_GRIS,
    font=("Segoe UI", 9, "bold")
).pack(side="left")

lbl_costo_estandar = tk.Label(
    pie_req,
    text="$0.00",
    bg=C_BLANCO,
    fg=C_VERDE,
    font=("Segoe UI", 12, "bold")
)
lbl_costo_estandar.pack(side="left", padx=(5, 25))

tk.Label(
    pie_req,
    text="Componentes faltantes:",
    bg=C_BLANCO,
    fg=C_GRIS,
    font=("Segoe UI", 9, "bold")
).pack(side="left")

lbl_faltantes = tk.Label(
    pie_req,
    text="0",
    bg=C_BLANCO,
    fg=C_ROJO,
    font=("Segoe UI", 12, "bold")
)
lbl_faltantes.pack(side="left", padx=5)

acciones = tk.Frame(tab_nueva, bg=C_FONDO)
acciones.pack(fill="x", padx=10, pady=(0, 10))

tk.Button(
    acciones,
    text="Crear orden en borrador",
    command=crear_orden,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 10, "bold"),
    padx=20,
    pady=8
).pack(side="left")

tk.Button(
    acciones,
    text="Nueva / limpiar",
    command=limpiar,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=8
).pack(side="left", padx=8)

# HISTORIAL
barra = tk.Frame(tab_historial, bg=C_BLANCO)
barra.pack(fill="x", padx=10, pady=10)

tk.Label(
    barra,
    text="Estado:",
    bg=C_BLANCO,
    fg=C_TEXTO
).pack(side="left", padx=(12, 5))

combo_filtro_estado = ttk.Combobox(
    barra,
    values=[
        "TODOS",
        "BORRADOR",
        "APROBADA",
        "LIBERADA",
        "EN PROCESO",
        "SUSPENDIDA",
        "TERMINADA",
        "ANULADA"
    ],
    state="readonly",
    width=16
)
combo_filtro_estado.pack(side="left", padx=5)
combo_filtro_estado.set("TODOS")

tk.Button(
    barra,
    text="Actualizar",
    command=cargar_ordenes,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="left", padx=5)

tk.Button(
    barra,
    text="Ver requerimientos",
    command=ver_requerimientos,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

tk.Button(
    barra,
    text="Regenerar requerimientos",
    command=regenerar_requerimientos,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

tk.Button(
    barra,
    text="Ver historial",
    command=ver_historial,
    bg=C_GRIS,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

for texto, estado, color in [
    ("Aprobar", "APROBADA", C_AZUL),
    ("Liberar", "LIBERADA", C_NARANJA),
    ("Iniciar", "EN PROCESO", "#7C3AED"),
    ("Suspender", "SUSPENDIDA", C_GRIS),
    ("Terminar", "TERMINADA", C_VERDE),
    ("Anular", "ANULADA", C_ROJO)
]:
    tk.Button(
        barra,
        text=texto,
        command=lambda e=estado: cambiar_estado(e),
        bg=color,
        fg="white",
        relief="flat",
        padx=12,
        pady=6
    ).pack(side="left", padx=3)

columnas_op = (
    "Número",
    "Emisión",
    "Programada",
    "Cod. producto",
    "Producto",
    "Presentación",
    "Programada",
    "Producida",
    "Unidad",
    "Lote",
    "Centro",
    "Responsable",
    "Prioridad",
    "Estado",
    "Fórmula"
)

tabla_ordenes = ttk.Treeview(
    tab_historial,
    columns=columnas_op,
    show="headings"
)

for columna in columnas_op:
    tabla_ordenes.heading(
        columna,
        text=columna
    )

tabla_ordenes.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

for estado, color in {
    "borrador": C_GRIS,
    "aprobada": C_AZUL,
    "liberada": C_NARANJA,
    "en proceso": "#7C3AED",
    "suspendida": C_GRIS,
    "terminada": C_VERDE,
    "anulada": C_ROJO
}.items():
    tabla_ordenes.tag_configure(
        estado,
        foreground=color
    )

tk.Label(
    ventana,
    text=f"Base de datos: {RUTA_DB}",
    bg=C_FONDO,
    fg=C_GRIS,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

cargar_formulas()
limpiar()
cargar_ordenes()

ventana.mainloop()
