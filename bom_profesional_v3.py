
"""
SIGA ERP - BOM Profesional v3
Archivo: bom_profesional_v3.py
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

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

componentes = []
recursos = []
formula_actual_id = None


def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )
    con = sqlite3.connect(RUTA_DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 10000")
    return con


def usuario():
    return (
        os.environ.get("ERP_USUARIO", "").strip()
        or os.environ.get("USERNAME", "usuario_local")
    )


def hoy():
    return datetime.now().strftime("%Y-%m-%d")


def moneda(valor):
    return f"${float(valor or 0):,.2f}"


def numero(valor):
    return f"{float(valor or 0):,.4f}"


def a_numero(valor, nombre, permitir_cero=False):
    texto = str(valor).replace(",", "").strip()
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
            usuario,
            accion,
            entidad,
            entidad_id,
            detalle
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        usuario(),
        accion,
        entidad,
        entidad_id,
        detalle,
    ))


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

        centros = con.execute("""
            SELECT
                codigo,
                nombre
            FROM centros_trabajo_produccion
            WHERE estado='ACTIVO'
            ORDER BY nombre
        """).fetchall()

    combo_componente["values"] = [
        f"{f['producto']} | {f['presentacion']}"
        for f in inventario
    ]

    combo_producto["values"] = [
        (
            f"{f['id']} | {f['codigo']} | "
            f"{f['nombre']} | {f['presentacion']} | "
            f"{f['unidad']}"
        )
        for f in productos
    ]

    combo_centro["values"] = [
        f"{f['codigo']} | {f['nombre']}"
        for f in centros
    ]


def producto_id():
    valor = combo_producto.get().strip()
    if not valor:
        return None
    try:
        return int(valor.split("|")[0].strip())
    except Exception:
        return None


def siguiente_version(pid):
    with conectar() as con:
        fila = con.execute("""
            SELECT IFNULL(MAX(version), 0) + 1 AS siguiente
            FROM formulas_produccion
            WHERE producto_id=?
        """, (pid,)).fetchone()

    return int(fila["siguiente"] or 1)


def cambio_producto(evento=None):
    pid = producto_id()
    if not pid:
        return

    version = siguiente_version(pid)

    entry_version.delete(0, "end")
    entry_version.insert(0, str(version))

    partes = combo_producto.get().split("|")
    codigo_producto = partes[1].strip()
    unidad = partes[4].strip()

    entry_codigo_formula.delete(0, "end")
    entry_codigo_formula.insert(
        0,
        f"F-{codigo_producto}-V{version}"
    )

    combo_unidad_base.set(unidad)


def costo_promedio(producto, presentacion):
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

    return float(fila["costo"] or 0)


def seleccionar_componente(evento=None):
    valor = combo_componente.get().strip()

    if " | " not in valor:
        return

    producto, presentacion = valor.split(" | ", 1)
    costo = costo_promedio(
        producto.strip(),
        presentacion.strip()
    )

    entry_costo_unitario.delete(0, "end")
    entry_costo_unitario.insert(0, str(round(costo, 6)))


def agregar_componente():
    valor = combo_componente.get().strip()

    if " | " not in valor:
        messagebox.showerror(
            "Componente",
            "Seleccione un componente del inventario."
        )
        return

    producto, presentacion = valor.split(" | ", 1)

    try:
        cantidad = a_numero(
            entry_cantidad_comp.get(),
            "Cantidad"
        )
        merma = a_numero(
            entry_merma_comp.get() or 0,
            "Merma",
            permitir_cero=True
        )
        factor = a_numero(
            entry_factor.get() or 1,
            "Factor de conversión"
        )
        costo = a_numero(
            entry_costo_unitario.get() or 0,
            "Costo unitario",
            permitir_cero=True
        )
        recuperacion = a_numero(
            entry_recuperacion.get() or 0,
            "Recuperación",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror(
            "Componente",
            str(error)
        )
        return

    cantidad_convertida = cantidad * factor
    cantidad_con_merma = cantidad_convertida * (
        1 + merma / 100
    )
    total = cantidad_con_merma * costo

    componentes.append({
        "componente": producto.strip(),
        "presentacion": presentacion.strip(),
        "tipo": combo_tipo_comp.get().strip(),
        "cantidad": cantidad,
        "unidad": combo_unidad_comp.get().strip(),
        "factor": factor,
        "unidad_inventario": combo_unidad_inventario.get().strip(),
        "cantidad_convertida": cantidad_convertida,
        "merma": merma,
        "costo_unitario": costo,
        "costo_total": total,
        "es_sustituto": 1 if combo_sustituto.get() == "SÍ" else 0,
        "sustituye": entry_sustituye.get().strip(),
        "es_critico": 1 if combo_critico.get() == "SÍ" else 0,
        "es_subproducto": 1 if combo_subproducto.get() == "SÍ" else 0,
        "recuperacion": recuperacion,
        "observaciones": txt_obs_comp.get("1.0", "end").strip(),
    })

    mostrar_componentes()
    limpiar_componente()


def limpiar_componente():
    combo_componente.set("")
    combo_tipo_comp.set("MATERIA PRIMA")
    entry_cantidad_comp.delete(0, "end")
    combo_unidad_comp.set("UND")
    entry_factor.delete(0, "end")
    entry_factor.insert(0, "1")
    combo_unidad_inventario.set("UND")
    entry_merma_comp.delete(0, "end")
    entry_merma_comp.insert(0, "0")
    entry_costo_unitario.delete(0, "end")
    entry_costo_unitario.insert(0, "0")
    combo_sustituto.set("NO")
    entry_sustituye.delete(0, "end")
    combo_critico.set("NO")
    combo_subproducto.set("NO")
    entry_recuperacion.delete(0, "end")
    entry_recuperacion.insert(0, "0")
    txt_obs_comp.delete("1.0", "end")


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
                numero(item["factor"]),
                item["unidad_inventario"],
                numero(item["cantidad_convertida"]),
                f"{item['merma']:.2f}%",
                moneda(item["costo_unitario"]),
                moneda(item["costo_total"]),
                "SÍ" if item["es_critico"] else "NO",
                "SÍ" if item["es_sustituto"] else "NO",
                "SÍ" if item["es_subproducto"] else "NO",
            )
        )

    lbl_materiales.config(text=moneda(total))
    actualizar_costo_total()


def agregar_recurso():
    try:
        cantidad = a_numero(
            entry_recurso_cantidad.get(),
            "Cantidad del recurso"
        )
        costo_unitario = a_numero(
            entry_recurso_costo.get() or 0,
            "Costo unitario del recurso",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror(
            "Recurso",
            str(error)
        )
        return

    recurso = entry_recurso_nombre.get().strip()

    if not recurso:
        messagebox.showerror(
            "Recurso",
            "Ingrese el nombre del recurso."
        )
        return

    total = cantidad * costo_unitario

    recursos.append({
        "tipo": combo_tipo_recurso.get().strip(),
        "recurso": recurso,
        "cantidad": cantidad,
        "unidad": combo_recurso_unidad.get().strip(),
        "costo_unitario": costo_unitario,
        "costo_total": total,
        "observaciones": txt_recurso_obs.get("1.0", "end").strip(),
    })

    mostrar_recursos()
    limpiar_recurso()


def limpiar_recurso():
    combo_tipo_recurso.set("MANO DE OBRA")
    entry_recurso_nombre.delete(0, "end")
    entry_recurso_cantidad.delete(0, "end")
    combo_recurso_unidad.set("HORA")
    entry_recurso_costo.delete(0, "end")
    entry_recurso_costo.insert(0, "0")
    txt_recurso_obs.delete("1.0", "end")


def eliminar_recurso():
    sel = tabla_recursos.selection()

    if not sel:
        messagebox.showwarning(
            "Recurso",
            "Seleccione un recurso."
        )
        return

    recursos.pop(int(sel[0]))
    mostrar_recursos()


def mostrar_recursos():
    tabla_recursos.delete(
        *tabla_recursos.get_children()
    )

    for i, item in enumerate(recursos):
        tabla_recursos.insert(
            "",
            "end",
            iid=str(i),
            values=(
                i + 1,
                item["tipo"],
                item["recurso"],
                numero(item["cantidad"]),
                item["unidad"],
                moneda(item["costo_unitario"]),
                moneda(item["costo_total"]),
            )
        )

    actualizar_costo_total()


def totales_recursos():
    mano_obra = sum(
        r["costo_total"]
        for r in recursos
        if r["tipo"] == "MANO DE OBRA"
    )
    cif = sum(
        r["costo_total"]
        for r in recursos
        if r["tipo"] == "CIF"
    )
    servicios = sum(
        r["costo_total"]
        for r in recursos
        if r["tipo"] in ("SERVICIO", "ENERGÍA", "GAS", "AGUA")
    )
    return mano_obra, cif, servicios


def actualizar_costo_total():
    materiales = sum(
        item["costo_total"]
        for item in componentes
    )
    mano_obra, cif, servicios = totales_recursos()
    total = materiales + mano_obra + cif + servicios

    lbl_materiales.config(text=moneda(materiales))
    lbl_mano_obra.config(text=moneda(mano_obra))
    lbl_cif.config(text=moneda(cif))
    lbl_servicios.config(text=moneda(servicios))
    lbl_total.config(text=moneda(total))


def guardar_formula():
    pid = producto_id()

    if not pid:
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
        version = int(entry_version.get())
        cantidad_base = a_numero(
            entry_cantidad_base.get(),
            "Cantidad base"
        )
        rendimiento = a_numero(
            entry_rendimiento.get(),
            "Rendimiento"
        )
        merma = a_numero(
            entry_merma_formula.get() or 0,
            "Merma estándar",
            permitir_cero=True
        )
        preparacion = a_numero(
            entry_preparacion.get() or 0,
            "Tiempo de preparación",
            permitir_cero=True
        )
        proceso = a_numero(
            entry_proceso.get() or 0,
            "Tiempo de proceso",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror(
            "Fórmula",
            str(error)
        )
        return

    materiales = sum(
        item["costo_total"]
        for item in componentes
    )
    mano_obra, cif, servicios = totales_recursos()
    total = materiales + mano_obra + cif + servicios

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
                costo_mano_obra_estandar,
                costo_cif_estandar,
                costo_servicios_estandar,
                costo_estandar_total,
                tiempo_preparacion_min,
                tiempo_proceso_min,
                centro_trabajo,
                estado,
                vigente_desde,
                vigente_hasta,
                observaciones,
                instrucciones_tecnicas,
                creado_por
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'BORRADOR', ?, ?, ?, ?, ?)
        """, (
            pid,
            entry_codigo_formula.get().strip().upper(),
            version,
            cantidad_base,
            combo_unidad_base.get().strip(),
            rendimiento,
            merma,
            materiales,
            mano_obra,
            cif,
            servicios,
            total,
            preparacion,
            proceso,
            combo_centro.get().strip(),
            entry_desde.get().strip(),
            entry_hasta.get().strip(),
            txt_observaciones.get("1.0", "end").strip(),
            txt_instrucciones.get("1.0", "end").strip(),
            usuario(),
        ))

        formula_id = int(cur.lastrowid)

        for orden, item in enumerate(componentes, 1):
            con.execute("""
                INSERT INTO formulas_componentes(
                    formula_id,
                    componente,
                    presentacion,
                    tipo_componente,
                    cantidad,
                    unidad,
                    factor_conversion,
                    unidad_inventario,
                    cantidad_convertida,
                    merma_pct,
                    costo_unitario_estandar,
                    costo_total_estandar,
                    es_sustituto,
                    componente_sustituido,
                    es_critico,
                    es_subproducto,
                    porcentaje_recuperacion,
                    orden,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                formula_id,
                item["componente"],
                item["presentacion"],
                item["tipo"],
                item["cantidad"],
                item["unidad"],
                item["factor"],
                item["unidad_inventario"],
                item["cantidad_convertida"],
                item["merma"],
                item["costo_unitario"],
                item["costo_total"],
                item["es_sustituto"],
                item["sustituye"],
                item["es_critico"],
                item["es_subproducto"],
                item["recuperacion"],
                orden,
                item["observaciones"],
            ))

        for item in recursos:
            con.execute("""
                INSERT INTO recursos_formula_produccion(
                    formula_id,
                    tipo_recurso,
                    recurso,
                    cantidad,
                    unidad,
                    costo_unitario,
                    costo_total,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                formula_id,
                item["tipo"],
                item["recurso"],
                item["cantidad"],
                item["unidad"],
                item["costo_unitario"],
                item["costo_total"],
                item["observaciones"],
            ))

        auditoria(
            con,
            "CREAR",
            "FORMULA PROFESIONAL",
            formula_id,
            (
                f"{entry_codigo_formula.get().strip()} "
                f"v{version}; costo total {total:.2f}"
            )
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            "Fórmula profesional creada en estado BORRADOR."
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
            str(error)
        )

    finally:
        con.close()


def limpiar_formula():
    global componentes, recursos, formula_actual_id

    componentes = []
    recursos = []
    formula_actual_id = None

    combo_producto.set("")
    entry_codigo_formula.delete(0, "end")
    entry_version.delete(0, "end")
    entry_version.insert(0, "1")
    entry_cantidad_base.delete(0, "end")
    entry_cantidad_base.insert(0, "1")
    combo_unidad_base.set("UND")
    entry_rendimiento.delete(0, "end")
    entry_rendimiento.insert(0, "100")
    entry_merma_formula.delete(0, "end")
    entry_merma_formula.insert(0, "0")
    entry_preparacion.delete(0, "end")
    entry_preparacion.insert(0, "0")
    entry_proceso.delete(0, "end")
    entry_proceso.insert(0, "0")
    combo_centro.set("")
    entry_desde.delete(0, "end")
    entry_desde.insert(0, hoy())
    entry_hasta.delete(0, "end")
    txt_observaciones.delete("1.0", "end")
    txt_instrucciones.delete("1.0", "end")

    limpiar_componente()
    limpiar_recurso()
    mostrar_componentes()
    mostrar_recursos()


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
            f.costo_estandar_materiales,
            f.costo_mano_obra_estandar,
            f.costo_cif_estandar,
            f.costo_servicios_estandar,
            f.costo_estandar_total,
            f.centro_trabajo,
            f.estado,
            f.vigente_desde,
            f.vigente_hasta
        FROM formulas_produccion f
        INNER JOIN productos_produccion p
            ON p.id=f.producto_id
        WHERE 1=1
    """
    params = []

    if estado and estado != "TODOS":
        sql += " AND f.estado=?"
        params.append(estado)

    sql += """
        ORDER BY
            p.nombre,
            p.presentacion,
            f.version DESC
    """

    with conectar() as con:
        filas = con.execute(sql, params).fetchall()

    tabla_formulas.delete(
        *tabla_formulas.get_children()
    )

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
                moneda(fila["costo_estandar_materiales"]),
                moneda(fila["costo_mano_obra_estandar"]),
                moneda(fila["costo_cif_estandar"]),
                moneda(fila["costo_servicios_estandar"]),
                moneda(fila["costo_estandar_total"]),
                fila["centro_trabajo"],
                fila["estado"],
                fila["vigente_desde"],
                fila["vigente_hasta"],
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
            "La versión seleccionada quedará ACTIVA y las demás "
            "versiones del producto quedarán INACTIVAS.\n\n"
            "¿Desea continuar?"
        )
    ):
        return

    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        fila = con.execute("""
            SELECT producto_id, codigo, version
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
            "FORMULA PROFESIONAL",
            formula_id,
            f"{fila['codigo']} v{fila['version']}"
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            (
                f"La fórmula {fila['codigo']} versión "
                f"{fila['version']} quedó ACTIVA."
            )
        )

        cargar_formulas()

    except Exception as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            str(error)
        )

    finally:
        con.close()


def crear_centro():
    codigo = simpledialog.askstring(
        "Centro de trabajo",
        "Código:"
    )

    if not codigo:
        return

    nombre = simpledialog.askstring(
        "Centro de trabajo",
        "Nombre:"
    )

    if not nombre:
        return

    capacidad = simpledialog.askfloat(
        "Centro de trabajo",
        "Capacidad por hora:",
        minvalue=0
    )

    costo = simpledialog.askfloat(
        "Centro de trabajo",
        "Costo por hora:",
        minvalue=0
    )

    with conectar() as con:
        con.execute("""
            INSERT INTO centros_trabajo_produccion(
                codigo,
                nombre,
                capacidad_hora,
                costo_hora,
                estado
            )
            VALUES (?, ?, ?, ?, 'ACTIVO')
        """, (
            codigo.strip().upper(),
            nombre.strip(),
            capacidad or 0,
            costo or 0,
        ))
        con.commit()

    cargar_catalogos()


# ------------------------------------------------------------
# INTERFAZ
# ------------------------------------------------------------

ventana = tk.Tk()
ventana.title("SIGA ERP - BOM Profesional v3")
ventana.geometry("1280x760")
ventana.minsize(900, 600)
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
    height=86
)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="BOM PROFESIONAL v3",
    bg=C_OSCURO,
    fg="white",
    font=("Segoe UI", 21, "bold")
).pack(anchor="w", padx=25, pady=(15, 0))

tk.Label(
    header,
    text=(
        "Materiales, empaques, insumos, servicios, mano de obra, "
        "CIF, conversiones, sustitutos y subproductos"
    ),
    bg=C_OSCURO,
    fg="#BFDBFE",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=26, pady=(3, 0))

# ============================================================
# ÁREA PRINCIPAL RESPONSIVA CON DESPLAZAMIENTO EN DOS DIRECCIONES
# ============================================================

contenedor_principal = tk.Frame(ventana, bg=C_FONDO)
contenedor_principal.pack(fill="both", expand=True)
contenedor_principal.grid_rowconfigure(0, weight=1)
contenedor_principal.grid_columnconfigure(0, weight=1)

canvas_principal = tk.Canvas(
    contenedor_principal,
    bg=C_FONDO,
    highlightthickness=0
)
canvas_principal.grid(row=0, column=0, sticky="nsew")

scroll_vertical_principal = ttk.Scrollbar(
    contenedor_principal,
    orient="vertical",
    command=canvas_principal.yview
)
scroll_vertical_principal.grid(row=0, column=1, sticky="ns")

scroll_horizontal_principal = ttk.Scrollbar(
    contenedor_principal,
    orient="horizontal",
    command=canvas_principal.xview
)
scroll_horizontal_principal.grid(row=1, column=0, sticky="ew")

canvas_principal.configure(
    yscrollcommand=scroll_vertical_principal.set,
    xscrollcommand=scroll_horizontal_principal.set
)

contenido_principal = tk.Frame(
    canvas_principal,
    bg=C_FONDO
)

ventana_canvas = canvas_principal.create_window(
    (0, 0),
    window=contenido_principal,
    anchor="nw"
)

def actualizar_region_scroll(evento=None):
    canvas_principal.configure(
        scrollregion=canvas_principal.bbox("all")
    )

def ajustar_ancho_minimo(evento):
    # La interfaz puede crecer horizontalmente, pero nunca queda inaccesible.
    ancho_requerido = max(
        contenido_principal.winfo_reqwidth(),
        evento.width
    )
    canvas_principal.itemconfigure(
        ventana_canvas,
        width=ancho_requerido
    )

def scroll_rueda(evento):
    canvas_principal.yview_scroll(
        int(-1 * (evento.delta / 120)),
        "units"
    )

def scroll_horizontal_rueda(evento):
    canvas_principal.xview_scroll(
        int(-1 * (evento.delta / 120)),
        "units"
    )

contenido_principal.bind(
    "<Configure>",
    actualizar_region_scroll
)
canvas_principal.bind(
    "<Configure>",
    ajustar_ancho_minimo
)
canvas_principal.bind_all(
    "<MouseWheel>",
    scroll_rueda
)
canvas_principal.bind_all(
    "<Shift-MouseWheel>",
    scroll_horizontal_rueda
)

notebook = ttk.Notebook(contenido_principal)
notebook.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=15
)

tab_formula = tk.Frame(notebook, bg=C_FONDO)
tab_consulta = tk.Frame(notebook, bg=C_FONDO)

notebook.add(
    tab_formula,
    text="  Nueva BOM profesional  "
)
notebook.add(
    tab_consulta,
    text="  Versiones y activación  "
)

# Encabezado
frame_enc = tk.LabelFrame(
    tab_formula,
    text="ENCABEZADO DE LA BOM",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8
)
frame_enc.pack(fill="x", padx=10, pady=10)

campos = [
    "Producto",
    "Código fórmula",
    "Versión",
    "Cantidad base",
    "Unidad",
    "Rendimiento %",
    "Merma %",
    "Preparación min",
    "Proceso min",
    "Centro de trabajo",
    "Vigente desde",
    "Vigente hasta"
]

for i, texto in enumerate(campos):
    tk.Label(
        frame_enc,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8)
    ).grid(row=0, column=i, sticky="w", padx=3)

combo_producto = ttk.Combobox(
    frame_enc,
    state="readonly",
    width=30
)
combo_producto.grid(row=1, column=0, sticky="ew", padx=3)
combo_producto.bind(
    "<<ComboboxSelected>>",
    cambio_producto
)

entry_codigo_formula = ttk.Entry(frame_enc)
entry_codigo_formula.grid(row=1, column=1, sticky="ew", padx=3)

entry_version = ttk.Entry(frame_enc, width=8)
entry_version.grid(row=1, column=2, sticky="ew", padx=3)

entry_cantidad_base = ttk.Entry(frame_enc, width=10)
entry_cantidad_base.grid(row=1, column=3, sticky="ew", padx=3)

combo_unidad_base = ttk.Combobox(
    frame_enc,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
    width=8
)
combo_unidad_base.grid(row=1, column=4, sticky="ew", padx=3)

entry_rendimiento = ttk.Entry(frame_enc, width=10)
entry_rendimiento.grid(row=1, column=5, sticky="ew", padx=3)

entry_merma_formula = ttk.Entry(frame_enc, width=10)
entry_merma_formula.grid(row=1, column=6, sticky="ew", padx=3)

entry_preparacion = ttk.Entry(frame_enc, width=10)
entry_preparacion.grid(row=1, column=7, sticky="ew", padx=3)

entry_proceso = ttk.Entry(frame_enc, width=10)
entry_proceso.grid(row=1, column=8, sticky="ew", padx=3)

combo_centro = ttk.Combobox(
    frame_enc,
    width=22
)
combo_centro.grid(row=1, column=9, sticky="ew", padx=3)

entry_desde = ttk.Entry(frame_enc, width=12)
entry_desde.grid(row=1, column=10, sticky="ew", padx=3)

entry_hasta = ttk.Entry(frame_enc, width=12)
entry_hasta.grid(row=1, column=11, sticky="ew", padx=3)

for i in range(12):
    frame_enc.columnconfigure(i, weight=1)

tk.Button(
    frame_enc,
    text="Nuevo centro de trabajo",
    command=crear_centro,
    bg=C_NARANJA,
    fg="white",
    relief="flat",
    padx=12,
    pady=5
).grid(
    row=2,
    column=9,
    columnspan=3,
    sticky="e",
    pady=(8, 0)
)

# Contenido tabs
sub = ttk.Notebook(tab_formula)
sub.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)

tab_componentes = tk.Frame(sub, bg=C_FONDO)
tab_recursos = tk.Frame(sub, bg=C_FONDO)
tab_tecnica = tk.Frame(sub, bg=C_FONDO)

sub.add(tab_componentes, text="  Componentes  ")
sub.add(tab_recursos, text="  Mano de obra, CIF y servicios  ")
sub.add(tab_tecnica, text="  Instrucciones técnicas  ")

# Componentes
frame_comp = tk.LabelFrame(
    tab_componentes,
    text="COMPONENTES ILIMITADOS",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8
)
frame_comp.pack(fill="both", expand=True, padx=5, pady=5)

linea = tk.Frame(frame_comp, bg=C_BLANCO)
linea.pack(fill="x")

titulos = [
    "Componente",
    "Tipo",
    "Cantidad",
    "Unidad fórmula",
    "Factor conversión",
    "Unidad inventario",
    "Merma %",
    "Costo unitario",
    "Crítico",
    "Sustituto",
    "Sustituye a",
    "Subproducto",
    "Recuperación %"
]

for i, texto in enumerate(titulos):
    tk.Label(
        linea,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8)
    ).grid(row=0, column=i, sticky="w", padx=2)

combo_componente = ttk.Combobox(
    linea,
    state="readonly",
    width=24
)
combo_componente.grid(row=1, column=0, sticky="ew", padx=2)
combo_componente.bind(
    "<<ComboboxSelected>>",
    seleccionar_componente
)

combo_tipo_comp = ttk.Combobox(
    linea,
    values=[
        "MATERIA PRIMA",
        "MATERIAL DE EMPAQUE",
        "INSUMO",
        "SEMIPROCESADO",
        "SERVICIO",
        "MANO DE OBRA",
        "CIF",
        "ENERGÍA",
        "GAS",
        "AGUA"
    ],
    state="readonly",
    width=16
)
combo_tipo_comp.grid(row=1, column=1, sticky="ew", padx=2)
combo_tipo_comp.set("MATERIA PRIMA")

entry_cantidad_comp = ttk.Entry(linea, width=9)
entry_cantidad_comp.grid(row=1, column=2, sticky="ew", padx=2)

combo_unidad_comp = ttk.Combobox(
    linea,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3", "HORA"],
    state="readonly",
    width=8
)
combo_unidad_comp.grid(row=1, column=3, sticky="ew", padx=2)
combo_unidad_comp.set("UND")

entry_factor = ttk.Entry(linea, width=9)
entry_factor.grid(row=1, column=4, sticky="ew", padx=2)

combo_unidad_inventario = ttk.Combobox(
    linea,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3", "HORA"],
    state="readonly",
    width=8
)
combo_unidad_inventario.grid(row=1, column=5, sticky="ew", padx=2)
combo_unidad_inventario.set("UND")

entry_merma_comp = ttk.Entry(linea, width=8)
entry_merma_comp.grid(row=1, column=6, sticky="ew", padx=2)

entry_costo_unitario = ttk.Entry(linea, width=10)
entry_costo_unitario.grid(row=1, column=7, sticky="ew", padx=2)

combo_critico = ttk.Combobox(
    linea,
    values=["NO", "SÍ"],
    state="readonly",
    width=6
)
combo_critico.grid(row=1, column=8, sticky="ew", padx=2)
combo_critico.set("NO")

combo_sustituto = ttk.Combobox(
    linea,
    values=["NO", "SÍ"],
    state="readonly",
    width=6
)
combo_sustituto.grid(row=1, column=9, sticky="ew", padx=2)
combo_sustituto.set("NO")

entry_sustituye = ttk.Entry(linea, width=12)
entry_sustituye.grid(row=1, column=10, sticky="ew", padx=2)

combo_subproducto = ttk.Combobox(
    linea,
    values=["NO", "SÍ"],
    state="readonly",
    width=6
)
combo_subproducto.grid(row=1, column=11, sticky="ew", padx=2)
combo_subproducto.set("NO")

entry_recuperacion = ttk.Entry(linea, width=8)
entry_recuperacion.grid(row=1, column=12, sticky="ew", padx=2)

tk.Button(
    linea,
    text="Agregar",
    command=agregar_componente,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=12,
    pady=5
).grid(row=1, column=13, padx=5)

for i in range(13):
    linea.columnconfigure(i, weight=1)

tk.Label(
    frame_comp,
    text="Observación del componente",
    bg=C_BLANCO,
    fg=C_GRIS
).pack(anchor="w", pady=(8, 0))

txt_obs_comp = tk.Text(
    frame_comp,
    height=2,
    relief="solid",
    bd=1
)
txt_obs_comp.pack(fill="x", pady=(0, 8))

cols_comp = (
    "N",
    "Componente",
    "Presentación",
    "Tipo",
    "Cantidad",
    "Unidad",
    "Factor",
    "Unidad inventario",
    "Convertida",
    "Merma",
    "Costo unitario",
    "Costo total",
    "Crítico",
    "Sustituto",
    "Subproducto"
)

frame_scroll_tabla_componentes = tk.Frame(
    frame_comp,
    bg=C_BLANCO
)
frame_scroll_tabla_componentes.pack(
    fill="both",
    expand=True
)
frame_scroll_tabla_componentes.grid_rowconfigure(0, weight=1)
frame_scroll_tabla_componentes.grid_columnconfigure(0, weight=1)

tabla_componentes = ttk.Treeview(
    frame_scroll_tabla_componentes,
    columns=cols_comp,
    show="headings"
)

anchos_componentes = {
    "N": 45,
    "Componente": 180,
    "Presentación": 110,
    "Tipo": 145,
    "Cantidad": 90,
    "Unidad": 80,
    "Factor": 80,
    "Unidad inventario": 115,
    "Convertida": 95,
    "Merma": 75,
    "Costo unitario": 110,
    "Costo total": 110,
    "Crítico": 70,
    "Sustituto": 75,
    "Subproducto": 90,
}

for c in cols_comp:
    tabla_componentes.heading(c, text=c)
    tabla_componentes.column(
        c,
        width=anchos_componentes.get(c, 100),
        minwidth=60,
        stretch=False
    )

scroll_y_tabla_componentes = ttk.Scrollbar(
    frame_scroll_tabla_componentes,
    orient="vertical",
    command=tabla_componentes.yview
)
scroll_x_tabla_componentes = ttk.Scrollbar(
    frame_scroll_tabla_componentes,
    orient="horizontal",
    command=tabla_componentes.xview
)

tabla_componentes.configure(
    yscrollcommand=scroll_y_tabla_componentes.set,
    xscrollcommand=scroll_x_tabla_componentes.set
)

tabla_componentes.grid(
    row=0,
    column=0,
    sticky="nsew"
)
scroll_y_tabla_componentes.grid(
    row=0,
    column=1,
    sticky="ns"
)
scroll_x_tabla_componentes.grid(
    row=1,
    column=0,
    sticky="ew"
)

pie_comp = tk.Frame(frame_comp, bg=C_BLANCO)
pie_comp.pack(fill="x", pady=(8, 0))

tk.Button(
    pie_comp,
    text="Eliminar componente",
    command=eliminar_componente,
    bg=C_ROJO,
    fg="white",
    relief="flat",
    padx=12,
    pady=5
).pack(side="left")

# Recursos
frame_rec = tk.LabelFrame(
    tab_recursos,
    text="RECURSOS Y COSTOS ESTÁNDAR",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8
)
frame_rec.pack(fill="both", expand=True, padx=5, pady=5)

linea_rec = tk.Frame(frame_rec, bg=C_BLANCO)
linea_rec.pack(fill="x")

for i, texto in enumerate([
    "Tipo",
    "Recurso",
    "Cantidad",
    "Unidad",
    "Costo unitario"
]):
    tk.Label(
        linea_rec,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS
    ).grid(row=0, column=i, sticky="w", padx=3)

combo_tipo_recurso = ttk.Combobox(
    linea_rec,
    values=[
        "MANO DE OBRA",
        "CIF",
        "SERVICIO",
        "ENERGÍA",
        "GAS",
        "AGUA"
    ],
    state="readonly"
)
combo_tipo_recurso.grid(row=1, column=0, sticky="ew", padx=3)
combo_tipo_recurso.set("MANO DE OBRA")

entry_recurso_nombre = ttk.Entry(linea_rec)
entry_recurso_nombre.grid(row=1, column=1, sticky="ew", padx=3)

entry_recurso_cantidad = ttk.Entry(linea_rec)
entry_recurso_cantidad.grid(row=1, column=2, sticky="ew", padx=3)

combo_recurso_unidad = ttk.Combobox(
    linea_rec,
    values=["HORA", "MINUTO", "UND", "KG", "L", "KWH", "M3"],
    state="readonly"
)
combo_recurso_unidad.grid(row=1, column=3, sticky="ew", padx=3)
combo_recurso_unidad.set("HORA")

entry_recurso_costo = ttk.Entry(linea_rec)
entry_recurso_costo.grid(row=1, column=4, sticky="ew", padx=3)

tk.Button(
    linea_rec,
    text="Agregar recurso",
    command=agregar_recurso,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=12,
    pady=5
).grid(row=1, column=5, padx=5)

for i in range(5):
    linea_rec.columnconfigure(i, weight=1)

tk.Label(
    frame_rec,
    text="Observaciones",
    bg=C_BLANCO,
    fg=C_GRIS
).pack(anchor="w", pady=(8, 0))

txt_recurso_obs = tk.Text(
    frame_rec,
    height=2,
    relief="solid",
    bd=1
)
txt_recurso_obs.pack(fill="x", pady=(0, 8))

cols_rec = (
    "N",
    "Tipo",
    "Recurso",
    "Cantidad",
    "Unidad",
    "Costo unitario",
    "Costo total"
)

frame_scroll_tabla_recursos = tk.Frame(
    frame_rec,
    bg=C_BLANCO
)
frame_scroll_tabla_recursos.pack(
    fill="both",
    expand=True
)
frame_scroll_tabla_recursos.grid_rowconfigure(0, weight=1)
frame_scroll_tabla_recursos.grid_columnconfigure(0, weight=1)

tabla_recursos = ttk.Treeview(
    frame_scroll_tabla_recursos,
    columns=cols_rec,
    show="headings"
)

anchos_recursos = {
    "N": 45,
    "Tipo": 130,
    "Recurso": 220,
    "Cantidad": 100,
    "Unidad": 90,
    "Costo unitario": 130,
    "Costo total": 130,
}

for c in cols_rec:
    tabla_recursos.heading(c, text=c)
    tabla_recursos.column(
        c,
        width=anchos_recursos.get(c, 110),
        minwidth=60,
        stretch=False
    )

scroll_y_tabla_recursos = ttk.Scrollbar(
    frame_scroll_tabla_recursos,
    orient="vertical",
    command=tabla_recursos.yview
)
scroll_x_tabla_recursos = ttk.Scrollbar(
    frame_scroll_tabla_recursos,
    orient="horizontal",
    command=tabla_recursos.xview
)

tabla_recursos.configure(
    yscrollcommand=scroll_y_tabla_recursos.set,
    xscrollcommand=scroll_x_tabla_recursos.set
)

tabla_recursos.grid(
    row=0,
    column=0,
    sticky="nsew"
)
scroll_y_tabla_recursos.grid(
    row=0,
    column=1,
    sticky="ns"
)
scroll_x_tabla_recursos.grid(
    row=1,
    column=0,
    sticky="ew"
)

tk.Button(
    frame_rec,
    text="Eliminar recurso",
    command=eliminar_recurso,
    bg=C_ROJO,
    fg="white",
    relief="flat",
    padx=12,
    pady=5
).pack(anchor="w", pady=(8, 0))

# Técnica
frame_tec = tk.LabelFrame(
    tab_tecnica,
    text="INSTRUCCIONES Y OBSERVACIONES",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8
)
frame_tec.pack(fill="both", expand=True, padx=5, pady=5)

tk.Label(
    frame_tec,
    text="Instrucciones técnicas",
    bg=C_BLANCO,
    fg=C_GRIS
).pack(anchor="w")

txt_instrucciones = tk.Text(
    frame_tec,
    height=12,
    relief="solid",
    bd=1
)
txt_instrucciones.pack(fill="both", expand=True, pady=(0, 10))

tk.Label(
    frame_tec,
    text="Observaciones generales",
    bg=C_BLANCO,
    fg=C_GRIS
).pack(anchor="w")

txt_observaciones = tk.Text(
    frame_tec,
    height=7,
    relief="solid",
    bd=1
)
txt_observaciones.pack(fill="both", expand=True)

# Costos y acciones
barra_costos = tk.Frame(
    tab_formula,
    bg=C_BLANCO,
    highlightbackground=C_BORDE,
    highlightthickness=1
)
barra_costos.pack(fill="x", padx=10, pady=(0, 8))

for titulo in [
    "Materiales",
    "Mano de obra",
    "CIF",
    "Servicios",
    "Costo total estándar"
]:
    pass

def kpi(parent, titulo):
    marco = tk.Frame(parent, bg=C_BLANCO)
    marco.pack(side="left", padx=18, pady=8)

    tk.Label(
        marco,
        text=titulo,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="$0.00",
        bg=C_BLANCO,
        fg=C_TEXTO,
        font=("Segoe UI", 12, "bold")
    )
    valor.pack(anchor="w")
    return valor

lbl_materiales = kpi(barra_costos, "MATERIALES")
lbl_mano_obra = kpi(barra_costos, "MANO DE OBRA")
lbl_cif = kpi(barra_costos, "CIF")
lbl_servicios = kpi(barra_costos, "SERVICIOS")
lbl_total = kpi(barra_costos, "COSTO TOTAL ESTÁNDAR")

acciones = tk.Frame(tab_formula, bg=C_FONDO)
acciones.pack(fill="x", padx=10, pady=(0, 10))

tk.Button(
    acciones,
    text="Guardar BOM en borrador",
    command=guardar_formula,
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
    command=limpiar_formula,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=8
).pack(side="left", padx=8)

# Consulta
barra_consulta = tk.Frame(tab_consulta, bg=C_BLANCO)
barra_consulta.pack(fill="x", padx=10, pady=10)

tk.Label(
    barra_consulta,
    text="Estado:",
    bg=C_BLANCO,
    fg=C_TEXTO
).pack(side="left", padx=(10, 5))

combo_filtro_estado = ttk.Combobox(
    barra_consulta,
    values=["TODOS", "BORRADOR", "ACTIVA", "INACTIVA"],
    state="readonly",
    width=14
)
combo_filtro_estado.pack(side="left")
combo_filtro_estado.set("TODOS")

tk.Button(
    barra_consulta,
    text="Actualizar",
    command=cargar_formulas,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6
).pack(side="left", padx=5)

tk.Button(
    barra_consulta,
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
    "Materiales",
    "Mano obra",
    "CIF",
    "Servicios",
    "Costo total",
    "Centro",
    "Estado",
    "Desde",
    "Hasta"
)

frame_scroll_tabla_formulas = tk.Frame(
    tab_consulta,
    bg=C_BLANCO
)
frame_scroll_tabla_formulas.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)
frame_scroll_tabla_formulas.grid_rowconfigure(0, weight=1)
frame_scroll_tabla_formulas.grid_columnconfigure(0, weight=1)

tabla_formulas = ttk.Treeview(
    frame_scroll_tabla_formulas,
    columns=cols_formulas,
    show="headings"
)

anchos_formulas = {
    "Código": 180,
    "Versión": 70,
    "Cod. producto": 110,
    "Producto": 190,
    "Presentación": 110,
    "Base": 85,
    "Unidad": 75,
    "Rendimiento": 100,
    "Merma": 80,
    "Materiales": 115,
    "Mano obra": 110,
    "CIF": 100,
    "Servicios": 110,
    "Costo total": 120,
    "Centro": 160,
    "Estado": 95,
    "Desde": 100,
    "Hasta": 100,
}

for c in cols_formulas:
    tabla_formulas.heading(c, text=c)
    tabla_formulas.column(
        c,
        width=anchos_formulas.get(c, 110),
        minwidth=60,
        stretch=False
    )

scroll_y_tabla_formulas = ttk.Scrollbar(
    frame_scroll_tabla_formulas,
    orient="vertical",
    command=tabla_formulas.yview
)
scroll_x_tabla_formulas = ttk.Scrollbar(
    frame_scroll_tabla_formulas,
    orient="horizontal",
    command=tabla_formulas.xview
)

tabla_formulas.configure(
    yscrollcommand=scroll_y_tabla_formulas.set,
    xscrollcommand=scroll_x_tabla_formulas.set
)

tabla_formulas.grid(
    row=0,
    column=0,
    sticky="nsew"
)
scroll_y_tabla_formulas.grid(
    row=0,
    column=1,
    sticky="ns"
)
scroll_x_tabla_formulas.grid(
    row=1,
    column=0,
    sticky="ew"
)

tk.Label(
    contenido_principal,
    text=f"Base de datos: {RUTA_DB}",
    bg=C_FONDO,
    fg=C_GRIS,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

def ir_a_versiones(evento=None):
    notebook.select(tab_consulta)
    cargar_formulas()

def cerrar_modulo(evento=None):
    ventana.destroy()

ventana.bind("<Control-v>", ir_a_versiones)
ventana.bind("<Escape>", cerrar_modulo)

limpiar_formula()
cargar_catalogos()
cargar_formulas()

ventana.mainloop()
