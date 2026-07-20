"""
SIGA ERP - Maestro de Productos y Fórmulas BOM v2
Archivo: formulas_produccion_v2.py
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"

C_FONDO = "#EEF3F8"
C_BLANCO = "#FFFFFF"
C_OSCURO = "#153B5B"
C_AZUL = "#0F5C8E"
C_VERDE = "#15803D"
C_NARANJA = "#C56A00"
C_ROJO = "#B42318"
C_TEXTO = "#1F2937"
C_SUAVE = "#64748B"
C_BORDE = "#D7E0E8"

componentes = []
formula_actual_id = None


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


def hoy():
    return datetime.now().strftime("%Y-%m-%d")


def usuario():
    return (
        os.environ.get("ERP_USUARIO", "").strip()
        or os.environ.get("USERNAME", "usuario_local")
    )


def moneda(valor):
    return f"${float(valor or 0):,.2f}"


def numero(valor):
    return f"{float(valor or 0):,.4f}"


def a_numero(valor, nombre, permitir_cero=False):
    texto = str(valor).strip().replace(",", "")
    try:
        n = float(texto)
    except ValueError as error:
        raise ValueError(
            f"{nombre} debe ser numérico."
        ) from error

    if permitir_cero:
        if n < 0:
            raise ValueError(
                f"{nombre} no puede ser negativo."
            )
    elif n <= 0:
        raise ValueError(
            f"{nombre} debe ser mayor que cero."
        )
    return n


def auditoria(con, accion, entidad, entidad_id, detalle=""):
    con.execute("""
        INSERT INTO auditoria_produccion(
            usuario, accion, entidad, entidad_id, detalle
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        usuario(),
        accion,
        entidad,
        entidad_id,
        detalle
    ))


def costo_promedio_inventario(producto, presentacion):
    with conectar() as con:
        fila = con.execute("""
            SELECT
                CASE
                    WHEN SUM(cantidad) > 0
                    THEN SUM(
                        cantidad
                        * COALESCE(costo_unitario, costo, 0)
                    ) / SUM(cantidad)
                    ELSE 0
                END AS costo
            FROM inventario
            WHERE producto=?
              AND presentacion=?
        """, (producto, presentacion)).fetchone()

    return float(fila["costo"] or 0) if fila else 0.0


def cargar_catalogos():
    with conectar() as con:
        inventario = con.execute("""
            SELECT DISTINCT
                producto,
                presentacion
            FROM inventario
            WHERE TRIM(COALESCE(producto, '')) <> ''
            ORDER BY producto, presentacion
        """).fetchall()

        productos = con.execute("""
            SELECT
                id,
                codigo,
                nombre,
                presentacion,
                unidad
            FROM productos_produccion
            WHERE estado='ACTIVO'
            ORDER BY nombre, presentacion
        """).fetchall()

    combo_componente["values"] = [
        f"{f['producto']} | {f['presentacion']}"
        for f in inventario
    ]

    combo_producto_formula["values"] = [
        (
            f"{f['id']} | {f['codigo']} | "
            f"{f['nombre']} | {f['presentacion']} | {f['unidad']}"
        )
        for f in productos
    ]


def limpiar_producto():
    entry_prod_codigo.delete(0, "end")
    entry_prod_nombre.delete(0, "end")
    entry_prod_presentacion.delete(0, "end")
    combo_prod_unidad.set("UND")
    combo_prod_categoria.set("")
    combo_prod_tipo.set("PRODUCTO TERMINADO")
    txt_prod_obs.delete("1.0", "end")


def guardar_producto():
    codigo = entry_prod_codigo.get().strip().upper()
    nombre = entry_prod_nombre.get().strip()
    presentacion = entry_prod_presentacion.get().strip()
    unidad = combo_prod_unidad.get().strip()
    categoria = combo_prod_categoria.get().strip()
    tipo = combo_prod_tipo.get().strip()

    if not codigo or not nombre or not presentacion or not unidad:
        messagebox.showerror(
            "Producto",
            "Código, nombre, presentación y unidad son obligatorios."
        )
        return

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO productos_produccion(
                codigo, nombre, presentacion, unidad,
                categoria, tipo, estado, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVO', ?)
        """, (
            codigo,
            nombre,
            presentacion,
            unidad,
            categoria,
            tipo,
            txt_prod_obs.get("1.0", "end").strip()
        ))

        auditoria(
            con,
            "CREAR",
            "PRODUCTO",
            cur.lastrowid,
            f"{codigo} - {nombre}/{presentacion}"
        )

        con.commit()

        messagebox.showinfo(
            "Producto",
            "Producto creado correctamente."
        )

        limpiar_producto()
        cargar_productos()
        cargar_catalogos()

    except sqlite3.IntegrityError:
        con.rollback()
        messagebox.showerror(
            "Producto",
            "Ya existe un producto con ese código."
        )

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Producto",
            f"No fue posible guardar.\n\n{error}"
        )

    finally:
        con.close()


def cargar_productos():
    with conectar() as con:
        filas = con.execute("""
            SELECT
                id,
                codigo,
                nombre,
                presentacion,
                unidad,
                categoria,
                tipo,
                estado
            FROM productos_produccion
            ORDER BY id DESC
        """).fetchall()

    tabla_productos.delete(*tabla_productos.get_children())

    for fila in filas:
        tabla_productos.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["codigo"],
                fila["nombre"],
                fila["presentacion"],
                fila["unidad"],
                fila["categoria"],
                fila["tipo"],
                fila["estado"]
            )
        )


def desactivar_producto():
    sel = tabla_productos.selection()

    if not sel:
        messagebox.showwarning(
            "Producto",
            "Seleccione un producto."
        )
        return

    producto_id = int(sel[0])

    if not messagebox.askyesno(
        "Producto",
        "¿Desea cambiar el estado del producto?"
    ):
        return

    with conectar() as con:
        estado = con.execute("""
            SELECT estado
            FROM productos_produccion
            WHERE id=?
        """, (producto_id,)).fetchone()["estado"]

        nuevo = "INACTIVO" if estado == "ACTIVO" else "ACTIVO"

        con.execute("""
            UPDATE productos_produccion
            SET estado=?,
                actualizado_en=CURRENT_TIMESTAMP
            WHERE id=?
        """, (nuevo, producto_id))

        auditoria(
            con,
            "CAMBIAR ESTADO",
            "PRODUCTO",
            producto_id,
            f"{estado} -> {nuevo}"
        )

        con.commit()

    cargar_productos()
    cargar_catalogos()


def producto_formula_id():
    valor = combo_producto_formula.get().strip()

    if not valor:
        return None

    try:
        return int(valor.split("|")[0].strip())
    except Exception:
        return None


def siguiente_version(producto_id):
    with conectar() as con:
        fila = con.execute("""
            SELECT IFNULL(MAX(version), 0) + 1 AS siguiente
            FROM formulas_produccion
            WHERE producto_id=?
        """, (producto_id,)).fetchone()

    return int(fila["siguiente"] or 1)


def limpiar_formula():
    global componentes, formula_actual_id

    componentes = []
    formula_actual_id = None

    combo_producto_formula.set("")
    entry_formula_codigo.delete(0, "end")
    entry_formula_version.delete(0, "end")
    entry_formula_version.insert(0, "1")
    entry_formula_base.delete(0, "end")
    entry_formula_base.insert(0, "1")
    combo_formula_unidad.set("UND")
    entry_rendimiento.delete(0, "end")
    entry_rendimiento.insert(0, "100")
    entry_merma_formula.delete(0, "end")
    entry_merma_formula.insert(0, "0")
    entry_vigente_desde.delete(0, "end")
    entry_vigente_desde.insert(0, hoy())
    entry_vigente_hasta.delete(0, "end")
    txt_formula_obs.delete("1.0", "end")

    limpiar_componente()
    mostrar_componentes()
    lbl_costo_materiales.config(text="$0.00")


def cambio_producto_formula(evento=None):
    producto_id = producto_formula_id()

    if not producto_id:
        return

    version = siguiente_version(producto_id)

    entry_formula_version.delete(0, "end")
    entry_formula_version.insert(0, str(version))

    partes = combo_producto_formula.get().split("|")
    codigo_producto = partes[1].strip()

    entry_formula_codigo.delete(0, "end")
    entry_formula_codigo.insert(
        0,
        f"F-{codigo_producto}-V{version}"
    )

    unidad = partes[4].strip()
    combo_formula_unidad.set(unidad)


def limpiar_componente():
    combo_componente.set("")
    combo_tipo_componente.set("MATERIA PRIMA")
    entry_comp_cantidad.delete(0, "end")
    combo_comp_unidad.set("UND")
    entry_comp_merma.delete(0, "end")
    entry_comp_merma.insert(0, "0")
    entry_comp_costo.delete(0, "end")
    entry_comp_costo.insert(0, "0")
    combo_comp_sustituto.set("NO")
    entry_comp_sustituye.delete(0, "end")
    txt_comp_obs.delete("1.0", "end")


def cargar_costo_componente(evento=None):
    valor = combo_componente.get().strip()

    if " | " not in valor:
        return

    producto, presentacion = valor.split(" | ", 1)

    costo = costo_promedio_inventario(
        producto.strip(),
        presentacion.strip()
    )

    entry_comp_costo.delete(0, "end")
    entry_comp_costo.insert(0, str(round(costo, 4)))


def agregar_componente():
    valor = combo_componente.get().strip()

    if " | " not in valor:
        messagebox.showerror(
            "Componente",
            "Seleccione materia prima y presentación."
        )
        return

    producto, presentacion = valor.split(" | ", 1)

    try:
        cantidad = a_numero(
            entry_comp_cantidad.get(),
            "Cantidad"
        )
        merma = a_numero(
            entry_comp_merma.get() or 0,
            "Merma",
            permitir_cero=True
        )
        costo = a_numero(
            entry_comp_costo.get() or 0,
            "Costo unitario",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror(
            "Componente",
            str(error)
        )
        return

    cantidad_con_merma = cantidad * (1 + merma / 100)
    total = cantidad_con_merma * costo

    componentes.append({
        "componente": producto.strip(),
        "presentacion": presentacion.strip(),
        "tipo": combo_tipo_componente.get().strip(),
        "cantidad": cantidad,
        "unidad": combo_comp_unidad.get().strip(),
        "merma_pct": merma,
        "costo_unitario": costo,
        "costo_total": total,
        "es_sustituto": 1 if combo_comp_sustituto.get() == "SÍ" else 0,
        "sustituye": entry_comp_sustituye.get().strip(),
        "observaciones": txt_comp_obs.get("1.0", "end").strip()
    })

    mostrar_componentes()
    limpiar_componente()


def eliminar_componente():
    sel = tabla_componentes.selection()

    if not sel:
        messagebox.showwarning(
            "Componente",
            "Seleccione un componente."
        )
        return

    componentes.pop(int(sel[0]))
    mostrar_componentes()


def mostrar_componentes():
    tabla_componentes.delete(
        *tabla_componentes.get_children()
    )

    total = 0.0

    for i, item in enumerate(componentes):
        total += item["costo_total"]

        tabla_componentes.insert(
            "",
            "end",
            iid=str(i),
            values=(
                i + 1,
                item["componente"],
                item["presentacion"],
                item["tipo"],
                numero(item["cantidad"]),
                item["unidad"],
                f"{item['merma_pct']:.2f}%",
                moneda(item["costo_unitario"]),
                moneda(item["costo_total"]),
                "SÍ" if item["es_sustituto"] else "NO",
                item["sustituye"]
            )
        )

    lbl_costo_materiales.config(text=moneda(total))


def guardar_formula():
    producto_id = producto_formula_id()

    if not producto_id:
        messagebox.showerror(
            "Fórmula",
            "Seleccione un producto."
        )
        return

    if not componentes:
        messagebox.showerror(
            "Fórmula",
            "Agregue al menos un componente."
        )
        return

    try:
        version = int(entry_formula_version.get())
        base = a_numero(
            entry_formula_base.get(),
            "Cantidad base"
        )
        rendimiento = a_numero(
            entry_rendimiento.get(),
            "Rendimiento"
        )
        merma_formula = a_numero(
            entry_merma_formula.get() or 0,
            "Merma estándar",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror(
            "Fórmula",
            str(error)
        )
        return

    costo_materiales = sum(
        item["costo_total"]
        for item in componentes
    )

    costo_total = costo_materiales

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        cur = con.execute("""
            INSERT INTO formulas_produccion(
                producto_id,
                codigo,
                version,
                cantidad_base,
                unidad_base,
                rendimiento_pct,
                merma_estandar_pct,
                costo_estandar_materiales,
                costo_estandar_total,
                estado,
                vigente_desde,
                vigente_hasta,
                observaciones,
                creado_por
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'BORRADOR', ?, ?, ?, ?)
        """, (
            producto_id,
            entry_formula_codigo.get().strip().upper(),
            version,
            base,
            combo_formula_unidad.get().strip(),
            rendimiento,
            merma_formula,
            costo_materiales,
            costo_total,
            entry_vigente_desde.get().strip(),
            entry_vigente_hasta.get().strip(),
            txt_formula_obs.get("1.0", "end").strip(),
            usuario()
        ))

        formula_id = cur.lastrowid

        for orden, item in enumerate(componentes, 1):
            con.execute("""
                INSERT INTO formulas_componentes(
                    formula_id,
                    componente,
                    presentacion,
                    tipo_componente,
                    cantidad,
                    unidad,
                    merma_pct,
                    costo_unitario_estandar,
                    costo_total_estandar,
                    es_sustituto,
                    componente_sustituido,
                    orden,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                formula_id,
                item["componente"],
                item["presentacion"],
                item["tipo"],
                item["cantidad"],
                item["unidad"],
                item["merma_pct"],
                item["costo_unitario"],
                item["costo_total"],
                item["es_sustituto"],
                item["sustituye"],
                orden,
                item["observaciones"]
            ))

        auditoria(
            con,
            "CREAR",
            "FORMULA",
            formula_id,
            (
                f"{entry_formula_codigo.get().strip()} "
                f"v{version}; costo {costo_total:.2f}"
            )
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            "Fórmula creada correctamente en estado BORRADOR."
        )

        limpiar_formula()
        cargar_formulas()

    except sqlite3.IntegrityError as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            (
                "Ya existe esa versión para el producto "
                f"o el código está duplicado.\n\n{error}"
            )
        )

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            f"No fue posible guardar.\n\n{error}"
        )

    finally:
        con.close()


def cargar_formulas():
    estado = combo_filtro_estado.get().strip()

    sql = """
        SELECT
            f.id,
            f.codigo,
            f.version,
            p.codigo AS producto_codigo,
            p.nombre,
            p.presentacion,
            f.cantidad_base,
            f.unidad_base,
            f.rendimiento_pct,
            f.merma_estandar_pct,
            f.costo_estandar_total,
            f.estado,
            f.vigente_desde
        FROM formulas_produccion f
        INNER JOIN productos_produccion p
            ON p.id=f.producto_id
        WHERE 1=1
    """
    params = []

    if estado and estado != "TODOS":
        sql += " AND f.estado=?"
        params.append(estado)

    sql += " ORDER BY p.nombre, p.presentacion, f.version DESC"

    with conectar() as con:
        filas = con.execute(sql, params).fetchall()

    tabla_formulas.delete(*tabla_formulas.get_children())

    for fila in filas:
        tabla_formulas.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["codigo"],
                fila["version"],
                fila["producto_codigo"],
                fila["nombre"],
                fila["presentacion"],
                numero(fila["cantidad_base"]),
                fila["unidad_base"],
                f"{fila['rendimiento_pct']:.2f}%",
                f"{fila['merma_estandar_pct']:.2f}%",
                moneda(fila["costo_estandar_total"]),
                fila["estado"],
                fila["vigente_desde"]
            )
        )


def ver_detalle_formula():
    sel = tabla_formulas.selection()

    if not sel:
        messagebox.showwarning(
            "Fórmula",
            "Seleccione una fórmula."
        )
        return

    formula_id = int(sel[0])

    with conectar() as con:
        cab = con.execute("""
            SELECT
                f.codigo,
                f.version,
                p.nombre,
                p.presentacion,
                f.cantidad_base,
                f.unidad_base,
                f.rendimiento_pct,
                f.merma_estandar_pct,
                f.costo_estandar_total,
                f.estado,
                f.observaciones
            FROM formulas_produccion f
            INNER JOIN productos_produccion p
                ON p.id=f.producto_id
            WHERE f.id=?
        """, (formula_id,)).fetchone()

        det = con.execute("""
            SELECT
                componente,
                presentacion,
                tipo_componente,
                cantidad,
                unidad,
                merma_pct,
                costo_unitario_estandar,
                costo_total_estandar,
                es_sustituto,
                componente_sustituido
            FROM formulas_componentes
            WHERE formula_id=?
            ORDER BY orden, id
        """, (formula_id,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title(f"Fórmula {cab['codigo']}")
    top.geometry("1200x650")
    top.configure(bg=C_FONDO)

    tk.Label(
        top,
        text=(
            f"FÓRMULA {cab['codigo']} · VERSIÓN {cab['version']}"
        ),
        bg=C_OSCURO,
        fg="white",
        font=("Segoe UI", 17, "bold"),
        pady=14
    ).pack(fill="x")

    info = (
        f"Producto: {cab['nombre']} / {cab['presentacion']}   |   "
        f"Base: {numero(cab['cantidad_base'])} {cab['unidad_base']}   |   "
        f"Rendimiento: {cab['rendimiento_pct']:.2f}%   |   "
        f"Merma: {cab['merma_estandar_pct']:.2f}%   |   "
        f"Costo estándar: {moneda(cab['costo_estandar_total'])}   |   "
        f"Estado: {cab['estado']}"
    )

    tk.Label(
        top,
        text=info,
        bg=C_BLANCO,
        fg=C_TEXTO,
        anchor="w",
        padx=15,
        pady=12
    ).pack(fill="x", padx=15, pady=15)

    cols = (
        "Componente",
        "Presentación",
        "Tipo",
        "Cantidad",
        "Unidad",
        "Merma",
        "Costo unitario",
        "Costo total",
        "Sustituto",
        "Sustituye"
    )

    tv = ttk.Treeview(
        top,
        columns=cols,
        show="headings"
    )

    for c in cols:
        tv.heading(c, text=c)

    tv.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    for fila in det:
        tv.insert(
            "",
            "end",
            values=(
                fila["componente"],
                fila["presentacion"],
                fila["tipo_componente"],
                numero(fila["cantidad"]),
                fila["unidad"],
                f"{fila['merma_pct']:.2f}%",
                moneda(fila["costo_unitario_estandar"]),
                moneda(fila["costo_total_estandar"]),
                "SÍ" if fila["es_sustituto"] else "NO",
                fila["componente_sustituido"]
            )
        )


def activar_formula():
    sel = tabla_formulas.selection()

    if not sel:
        messagebox.showwarning(
            "Fórmula",
            "Seleccione una fórmula."
        )
        return

    formula_id = int(sel[0])

    if not messagebox.askyesno(
        "Activar fórmula",
        (
            "Esta fórmula quedará ACTIVA y las demás versiones "
            "del mismo producto quedarán INACTIVAS.\n\n"
            "¿Desea continuar?"
        )
    ):
        return

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        fila = con.execute("""
            SELECT producto_id, estado
            FROM formulas_produccion
            WHERE id=?
        """, (formula_id,)).fetchone()

        con.execute("""
            UPDATE formulas_produccion
            SET estado='INACTIVA',
                actualizado_en=CURRENT_TIMESTAMP
            WHERE producto_id=?
        """, (fila["producto_id"],))

        con.execute("""
            UPDATE formulas_produccion
            SET estado='ACTIVA',
                actualizado_en=CURRENT_TIMESTAMP
            WHERE id=?
        """, (formula_id,))

        auditoria(
            con,
            "ACTIVAR",
            "FORMULA",
            formula_id,
            "Versión marcada como activa"
        )

        con.commit()

        cargar_formulas()

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            str(error)
        )

    finally:
        con.close()


def copiar_formula():
    sel = tabla_formulas.selection()

    if not sel:
        messagebox.showwarning(
            "Fórmula",
            "Seleccione una fórmula."
        )
        return

    origen_id = int(sel[0])

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        origen = con.execute("""
            SELECT *
            FROM formulas_produccion
            WHERE id=?
        """, (origen_id,)).fetchone()

        nueva_version = siguiente_version(
            origen["producto_id"]
        )

        nuevo_codigo = (
            origen["codigo"].rsplit("-V", 1)[0]
            + f"-V{nueva_version}"
        )

        cur = con.execute("""
            INSERT INTO formulas_produccion(
                producto_id,
                codigo,
                version,
                cantidad_base,
                unidad_base,
                rendimiento_pct,
                merma_estandar_pct,
                costo_estandar_materiales,
                costo_estandar_total,
                estado,
                vigente_desde,
                vigente_hasta,
                observaciones,
                creado_por
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'BORRADOR', ?, ?, ?, ?)
        """, (
            origen["producto_id"],
            nuevo_codigo,
            nueva_version,
            origen["cantidad_base"],
            origen["unidad_base"],
            origen["rendimiento_pct"],
            origen["merma_estandar_pct"],
            origen["costo_estandar_materiales"],
            origen["costo_estandar_total"],
            hoy(),
            "",
            f"Copia de fórmula {origen['codigo']}",
            usuario()
        ))

        nuevo_id = cur.lastrowid

        componentes_origen = con.execute("""
            SELECT *
            FROM formulas_componentes
            WHERE formula_id=?
            ORDER BY orden, id
        """, (origen_id,)).fetchall()

        for item in componentes_origen:
            con.execute("""
                INSERT INTO formulas_componentes(
                    formula_id,
                    componente,
                    presentacion,
                    tipo_componente,
                    cantidad,
                    unidad,
                    merma_pct,
                    costo_unitario_estandar,
                    costo_total_estandar,
                    es_sustituto,
                    componente_sustituido,
                    orden,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nuevo_id,
                item["componente"],
                item["presentacion"],
                item["tipo_componente"],
                item["cantidad"],
                item["unidad"],
                item["merma_pct"],
                item["costo_unitario_estandar"],
                item["costo_total_estandar"],
                item["es_sustituto"],
                item["componente_sustituido"],
                item["orden"],
                item["observaciones"]
            ))

        auditoria(
            con,
            "COPIAR",
            "FORMULA",
            nuevo_id,
            f"Origen {origen_id}; nueva versión {nueva_version}"
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            f"Nueva versión {nueva_version} creada en BORRADOR."
        )

        cargar_formulas()

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            f"No fue posible copiar.\n\n{error}"
        )

    finally:
        con.close()


# ------------------------------------------------------------
# INTERFAZ
# ------------------------------------------------------------

ventana = tk.Tk()
ventana.title("SIGA ERP - Maestro de Producción y Fórmulas BOM v2")
ventana.geometry("1500x900")
ventana.minsize(1180, 720)
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
    text="MAESTRO DE PRODUCCIÓN Y FÓRMULAS BOM",
    bg=C_OSCURO,
    fg="white",
    font=("Segoe UI", 21, "bold")
).pack(anchor="w", padx=25, pady=(15, 0))

tk.Label(
    header,
    text=(
        "Productos, versiones, componentes, rendimiento, "
        "mermas y costo estándar"
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

tab_productos = tk.Frame(notebook, bg=C_FONDO)
tab_formula = tk.Frame(notebook, bg=C_FONDO)
tab_historial = tk.Frame(notebook, bg=C_FONDO)

notebook.add(tab_productos, text="  Productos de producción  ")
notebook.add(tab_formula, text="  Nueva fórmula BOM  ")
notebook.add(tab_historial, text="  Versiones y consulta  ")

# PRODUCTOS
frame_prod = tk.LabelFrame(
    tab_productos,
    text="DATOS DEL PRODUCTO",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_prod.pack(fill="x", padx=10, pady=10)

labels = [
    "Código",
    "Nombre",
    "Presentación",
    "Unidad",
    "Categoría",
    "Tipo"
]

for i, texto in enumerate(labels):
    tk.Label(
        frame_prod,
        text=texto,
        bg=C_BLANCO,
        fg=C_SUAVE
    ).grid(row=0, column=i, sticky="w", padx=4)

entry_prod_codigo = ttk.Entry(frame_prod)
entry_prod_codigo.grid(row=1, column=0, sticky="ew", padx=4)

entry_prod_nombre = ttk.Entry(frame_prod)
entry_prod_nombre.grid(row=1, column=1, sticky="ew", padx=4)

entry_prod_presentacion = ttk.Entry(frame_prod)
entry_prod_presentacion.grid(row=1, column=2, sticky="ew", padx=4)

combo_prod_unidad = ttk.Combobox(
    frame_prod,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly"
)
combo_prod_unidad.grid(row=1, column=3, sticky="ew", padx=4)
combo_prod_unidad.set("UND")

combo_prod_categoria = ttk.Combobox(
    frame_prod,
    values=[
        "CAFÉ",
        "ASEO",
        "ALIMENTOS",
        "METALMECÁNICA",
        "OTROS"
    ]
)
combo_prod_categoria.grid(row=1, column=4, sticky="ew", padx=4)

combo_prod_tipo = ttk.Combobox(
    frame_prod,
    values=[
        "PRODUCTO TERMINADO",
        "SEMIPROCESADO",
        "SUBPRODUCTO"
    ],
    state="readonly"
)
combo_prod_tipo.grid(row=1, column=5, sticky="ew", padx=4)
combo_prod_tipo.set("PRODUCTO TERMINADO")

for i in range(6):
    frame_prod.columnconfigure(i, weight=1)

tk.Label(
    frame_prod,
    text="Observaciones",
    bg=C_BLANCO,
    fg=C_SUAVE
).grid(row=2, column=0, sticky="w", pady=(10, 0))

txt_prod_obs = tk.Text(
    frame_prod,
    height=2,
    relief="solid",
    bd=1
)
txt_prod_obs.grid(
    row=3,
    column=0,
    columnspan=6,
    sticky="ew",
    padx=4
)

acciones_prod = tk.Frame(tab_productos, bg=C_FONDO)
acciones_prod.pack(fill="x", padx=10, pady=(0, 10))

tk.Button(
    acciones_prod,
    text="Guardar producto",
    command=guardar_producto,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    padx=18,
    pady=7
).pack(side="left")

tk.Button(
    acciones_prod,
    text="Limpiar",
    command=limpiar_producto,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=7
).pack(side="left", padx=8)

tk.Button(
    acciones_prod,
    text="Activar / Inactivar",
    command=desactivar_producto,
    bg=C_NARANJA,
    fg="white",
    relief="flat",
    padx=18,
    pady=7
).pack(side="right")

cols_prod = (
    "Código",
    "Nombre",
    "Presentación",
    "Unidad",
    "Categoría",
    "Tipo",
    "Estado"
)

tabla_productos = ttk.Treeview(
    tab_productos,
    columns=cols_prod,
    show="headings"
)

for c in cols_prod:
    tabla_productos.heading(c, text=c)

tabla_productos.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

# FORMULA
frame_formula = tk.LabelFrame(
    tab_formula,
    text="ENCABEZADO DE LA FÓRMULA",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_formula.pack(fill="x", padx=10, pady=10)

campos = [
    "Producto",
    "Código fórmula",
    "Versión",
    "Cantidad base",
    "Unidad",
    "Rendimiento %",
    "Merma estándar %",
    "Vigente desde",
    "Vigente hasta"
]

for i, texto in enumerate(campos):
    tk.Label(
        frame_formula,
        text=texto,
        bg=C_BLANCO,
        fg=C_SUAVE
    ).grid(row=0, column=i, sticky="w", padx=3)

combo_producto_formula = ttk.Combobox(
    frame_formula,
    state="readonly",
    width=34
)
combo_producto_formula.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=3
)
combo_producto_formula.bind(
    "<<ComboboxSelected>>",
    cambio_producto_formula
)

entry_formula_codigo = ttk.Entry(frame_formula)
entry_formula_codigo.grid(row=1, column=1, sticky="ew", padx=3)

entry_formula_version = ttk.Entry(frame_formula, width=8)
entry_formula_version.grid(row=1, column=2, sticky="ew", padx=3)

entry_formula_base = ttk.Entry(frame_formula, width=12)
entry_formula_base.grid(row=1, column=3, sticky="ew", padx=3)

combo_formula_unidad = ttk.Combobox(
    frame_formula,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
    width=10
)
combo_formula_unidad.grid(row=1, column=4, sticky="ew", padx=3)

entry_rendimiento = ttk.Entry(frame_formula, width=12)
entry_rendimiento.grid(row=1, column=5, sticky="ew", padx=3)

entry_merma_formula = ttk.Entry(frame_formula, width=12)
entry_merma_formula.grid(row=1, column=6, sticky="ew", padx=3)

entry_vigente_desde = ttk.Entry(frame_formula, width=14)
entry_vigente_desde.grid(row=1, column=7, sticky="ew", padx=3)

entry_vigente_hasta = ttk.Entry(frame_formula, width=14)
entry_vigente_hasta.grid(row=1, column=8, sticky="ew", padx=3)

for i in range(9):
    frame_formula.columnconfigure(i, weight=1)

tk.Label(
    frame_formula,
    text="Observaciones",
    bg=C_BLANCO,
    fg=C_SUAVE
).grid(row=2, column=0, sticky="w", pady=(10, 0))

txt_formula_obs = tk.Text(
    frame_formula,
    height=2,
    relief="solid",
    bd=1
)
txt_formula_obs.grid(
    row=3,
    column=0,
    columnspan=9,
    sticky="ew"
)

frame_comp = tk.LabelFrame(
    tab_formula,
    text="COMPONENTES DE LA FÓRMULA",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10
)
frame_comp.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

linea = tk.Frame(frame_comp, bg=C_BLANCO)
linea.pack(fill="x", pady=(0, 8))

titulos = [
    "Componente",
    "Tipo",
    "Cantidad",
    "Unidad",
    "Merma %",
    "Costo unitario",
    "¿Sustituto?",
    "Sustituye a"
]

for i, texto in enumerate(titulos):
    tk.Label(
        linea,
        text=texto,
        bg=C_BLANCO,
        fg=C_SUAVE
    ).grid(row=0, column=i, sticky="w", padx=3)

combo_componente = ttk.Combobox(
    linea,
    state="readonly",
    width=30
)
combo_componente.grid(row=1, column=0, sticky="ew", padx=3)
combo_componente.bind(
    "<<ComboboxSelected>>",
    cargar_costo_componente
)

combo_tipo_componente = ttk.Combobox(
    linea,
    values=[
        "MATERIA PRIMA",
        "MATERIAL DE EMPAQUE",
        "INSUMO",
        "SEMIPROCESADO"
    ],
    state="readonly",
    width=20
)
combo_tipo_componente.grid(row=1, column=1, sticky="ew", padx=3)
combo_tipo_componente.set("MATERIA PRIMA")

entry_comp_cantidad = ttk.Entry(linea, width=12)
entry_comp_cantidad.grid(row=1, column=2, sticky="ew", padx=3)

combo_comp_unidad = ttk.Combobox(
    linea,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
    width=10
)
combo_comp_unidad.grid(row=1, column=3, sticky="ew", padx=3)
combo_comp_unidad.set("UND")

entry_comp_merma = ttk.Entry(linea, width=10)
entry_comp_merma.grid(row=1, column=4, sticky="ew", padx=3)

entry_comp_costo = ttk.Entry(linea, width=14)
entry_comp_costo.grid(row=1, column=5, sticky="ew", padx=3)

combo_comp_sustituto = ttk.Combobox(
    linea,
    values=["NO", "SÍ"],
    state="readonly",
    width=10
)
combo_comp_sustituto.grid(row=1, column=6, sticky="ew", padx=3)
combo_comp_sustituto.set("NO")

entry_comp_sustituye = ttk.Entry(linea, width=18)
entry_comp_sustituye.grid(row=1, column=7, sticky="ew", padx=3)

tk.Button(
    linea,
    text="Agregar",
    command=agregar_componente,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    padx=13,
    pady=6
).grid(row=1, column=8, padx=7)

for i in range(8):
    linea.columnconfigure(i, weight=1)

tk.Label(
    frame_comp,
    text="Observación del componente",
    bg=C_BLANCO,
    fg=C_SUAVE
).pack(anchor="w")

txt_comp_obs = tk.Text(
    frame_comp,
    height=2,
    relief="solid",
    bd=1
)
txt_comp_obs.pack(fill="x", pady=(0, 8))

cols_comp = (
    "N",
    "Componente",
    "Presentación",
    "Tipo",
    "Cantidad",
    "Unidad",
    "Merma",
    "Costo unitario",
    "Costo total",
    "Sustituto",
    "Sustituye"
)

tabla_componentes = ttk.Treeview(
    frame_comp,
    columns=cols_comp,
    show="headings"
)

for c in cols_comp:
    tabla_componentes.heading(c, text=c)

tabla_componentes.pack(fill="both", expand=True)

pie = tk.Frame(frame_comp, bg=C_BLANCO)
pie.pack(fill="x", pady=(8, 0))

tk.Button(
    pie,
    text="Eliminar componente",
    command=eliminar_componente,
    bg=C_ROJO,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="left")

tk.Label(
    pie,
    text="Costo estándar de materiales:",
    bg=C_BLANCO,
    fg=C_SUAVE,
    font=("Segoe UI", 9, "bold")
).pack(side="right", padx=(15, 5))

lbl_costo_materiales = tk.Label(
    pie,
    text="$0.00",
    bg=C_BLANCO,
    fg=C_VERDE,
    font=("Segoe UI", 13, "bold")
)
lbl_costo_materiales.pack(side="right")

acciones_formula = tk.Frame(tab_formula, bg=C_FONDO)
acciones_formula.pack(fill="x", padx=10, pady=(0, 10))

tk.Button(
    acciones_formula,
    text="Guardar fórmula en borrador",
    command=guardar_formula,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 10, "bold"),
    padx=20,
    pady=8
).pack(side="left")

tk.Button(
    acciones_formula,
    text="Nueva / limpiar",
    command=limpiar_formula,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=8
).pack(side="left", padx=8)

# HISTORIAL
barra_hist = tk.Frame(tab_historial, bg=C_BLANCO)
barra_hist.pack(fill="x", padx=10, pady=10)

tk.Label(
    barra_hist,
    text="Estado:",
    bg=C_BLANCO,
    fg=C_TEXTO
).pack(side="left", padx=(12, 5))

combo_filtro_estado = ttk.Combobox(
    barra_hist,
    values=["TODOS", "BORRADOR", "ACTIVA", "INACTIVA"],
    state="readonly",
    width=14
)
combo_filtro_estado.pack(side="left", padx=5)
combo_filtro_estado.set("TODOS")

tk.Button(
    barra_hist,
    text="Actualizar",
    command=cargar_formulas,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="left", padx=5)

tk.Button(
    barra_hist,
    text="Ver detalle",
    command=ver_detalle_formula,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

tk.Button(
    barra_hist,
    text="Copiar como nueva versión",
    command=copiar_formula,
    bg=C_NARANJA,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="right", padx=5)

tk.Button(
    barra_hist,
    text="Activar fórmula",
    command=activar_formula,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    padx=14,
    pady=6
).pack(side="right", padx=5)

cols_formulas = (
    "Código",
    "Versión",
    "Cod. producto",
    "Producto",
    "Presentación",
    "Base",
    "Unidad",
    "Rendimiento",
    "Merma",
    "Costo estándar",
    "Estado",
    "Vigente desde"
)

tabla_formulas = ttk.Treeview(
    tab_historial,
    columns=cols_formulas,
    show="headings"
)

for c in cols_formulas:
    tabla_formulas.heading(c, text=c)

tabla_formulas.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

tk.Label(
    ventana,
    text=f"Base de datos: {RUTA_DB}",
    bg=C_FONDO,
    fg=C_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

limpiar_producto()
limpiar_formula()
cargar_productos()
cargar_formulas()
cargar_catalogos()

ventana.mainloop()
