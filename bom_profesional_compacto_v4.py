
"""
SIGA ERP - BOM Profesional Compacto v4
Archivo: bom_profesional_compacto_v4.py

Rediseño orientado a monitores Full HD y resoluciones menores.
Conserva las tablas y datos creados por BOM Profesional v3.
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

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


def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(f"No se encontró la base de datos:\n{RUTA_DB}")

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
    try:
        n = float(str(valor).replace(",", "").strip())
    except ValueError as error:
        raise ValueError(f"{nombre} debe ser numérico.") from error

    if permitir_cero:
        if n < 0:
            raise ValueError(f"{nombre} no puede ser negativo.")
    elif n <= 0:
        raise ValueError(f"{nombre} debe ser mayor que cero.")

    return n


def auditoria(con, accion, entidad, entidad_id, detalle=""):
    con.execute("""
        INSERT INTO auditoria_produccion(
            usuario, accion, entidad, entidad_id, detalle
        )
        VALUES (?, ?, ?, ?, ?)
    """, (usuario(), accion, entidad, entidad_id, detalle))


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


def cargar_catalogos():
    with conectar() as con:
        productos = con.execute("""
            SELECT id, codigo, nombre, presentacion, unidad
            FROM productos_produccion
            WHERE estado='ACTIVO'
            ORDER BY nombre, presentacion
        """).fetchall()

        inventario = con.execute("""
            SELECT DISTINCT producto, presentacion
            FROM inventario
            WHERE TRIM(COALESCE(producto, '')) <> ''
            ORDER BY producto, presentacion
        """).fetchall()

        centros = con.execute("""
            SELECT codigo, nombre
            FROM centros_trabajo_produccion
            WHERE estado='ACTIVO'
            ORDER BY nombre
        """).fetchall()

    combo_producto["values"] = [
        f"{f['id']} | {f['codigo']} | {f['nombre']} | {f['presentacion']} | {f['unidad']}"
        for f in productos
    ]

    combo_componente["values"] = [
        f"{f['producto']} | {f['presentacion']}"
        for f in inventario
    ]

    combo_centro["values"] = [
        f"{f['codigo']} | {f['nombre']}"
        for f in centros
    ]


def cambio_producto(evento=None):
    pid = producto_id()
    if not pid:
        return

    version = siguiente_version(pid)
    partes = combo_producto.get().split("|")

    entry_version.delete(0, "end")
    entry_version.insert(0, str(version))

    entry_codigo.delete(0, "end")
    entry_codigo.insert(0, f"F-{partes[1].strip()}-V{version}")

    combo_unidad_base.set(partes[4].strip())


def costo_promedio(producto, presentacion):
    with conectar() as con:
        fila = con.execute("""
            SELECT
                CASE
                    WHEN SUM(cantidad) > 0
                    THEN SUM(
                        cantidad * COALESCE(costo_unitario, costo, 0)
                    ) / SUM(cantidad)
                    ELSE 0
                END AS costo
            FROM inventario
            WHERE producto=? AND presentacion=?
        """, (producto, presentacion)).fetchone()

    return float(fila["costo"] or 0)


def seleccionar_componente(evento=None):
    valor = combo_componente.get().strip()
    if " | " not in valor:
        return

    producto, presentacion = valor.split(" | ", 1)
    costo = costo_promedio(producto.strip(), presentacion.strip())

    entry_costo.delete(0, "end")
    entry_costo.insert(0, str(round(costo, 6)))


def limpiar_componente():
    combo_componente.set("")
    combo_tipo.set("MATERIA PRIMA")
    entry_cantidad.delete(0, "end")
    combo_unidad_formula.set("UND")
    entry_factor.delete(0, "end")
    entry_factor.insert(0, "1")
    combo_unidad_inventario.set("UND")
    entry_merma.delete(0, "end")
    entry_merma.insert(0, "0")
    entry_costo.delete(0, "end")
    entry_costo.insert(0, "0")
    combo_critico.set("NO")
    combo_sustituto.set("NO")
    entry_sustituye.delete(0, "end")
    combo_subproducto.set("NO")
    entry_recuperacion.delete(0, "end")
    entry_recuperacion.insert(0, "0")
    txt_observacion_componente.delete("1.0", "end")


def agregar_componente():
    valor = combo_componente.get().strip()

    if " | " not in valor:
        messagebox.showerror("Componente", "Seleccione un componente.")
        return

    producto, presentacion = valor.split(" | ", 1)

    try:
        cantidad = a_numero(entry_cantidad.get(), "Cantidad")
        factor = a_numero(entry_factor.get() or 1, "Factor")
        merma = a_numero(entry_merma.get() or 0, "Merma", permitir_cero=True)
        costo = a_numero(entry_costo.get() or 0, "Costo", permitir_cero=True)
        recuperacion = a_numero(
            entry_recuperacion.get() or 0,
            "Recuperación",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror("Componente", str(error))
        return

    convertida = cantidad * factor
    total = convertida * (1 + merma / 100) * costo

    componentes.append({
        "componente": producto.strip(),
        "presentacion": presentacion.strip(),
        "tipo": combo_tipo.get().strip(),
        "cantidad": cantidad,
        "unidad": combo_unidad_formula.get().strip(),
        "factor": factor,
        "unidad_inventario": combo_unidad_inventario.get().strip(),
        "cantidad_convertida": convertida,
        "merma": merma,
        "costo_unitario": costo,
        "costo_total": total,
        "critico": 1 if combo_critico.get() == "SÍ" else 0,
        "sustituto": 1 if combo_sustituto.get() == "SÍ" else 0,
        "sustituye": entry_sustituye.get().strip(),
        "subproducto": 1 if combo_subproducto.get() == "SÍ" else 0,
        "recuperacion": recuperacion,
        "observaciones": txt_observacion_componente.get("1.0", "end").strip(),
    })

    mostrar_componentes()
    limpiar_componente()


def mostrar_componentes():
    tabla_componentes.delete(*tabla_componentes.get_children())

    for i, item in enumerate(componentes):
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
                moneda(item["costo_unitario"]),
                moneda(item["costo_total"]),
            ),
        )

    actualizar_costos()


def eliminar_componente():
    sel = tabla_componentes.selection()
    if not sel:
        messagebox.showwarning("Componente", "Seleccione un componente.")
        return

    componentes.pop(int(sel[0]))
    mostrar_componentes()


def ver_detalle_componente():
    sel = tabla_componentes.selection()
    if not sel:
        messagebox.showwarning("Detalle", "Seleccione un componente.")
        return

    item = componentes[int(sel[0])]

    detalle = (
        f"Componente: {item['componente']}\n"
        f"Presentación: {item['presentacion']}\n"
        f"Tipo: {item['tipo']}\n"
        f"Cantidad fórmula: {numero(item['cantidad'])} {item['unidad']}\n"
        f"Factor conversión: {numero(item['factor'])}\n"
        f"Unidad inventario: {item['unidad_inventario']}\n"
        f"Cantidad convertida: {numero(item['cantidad_convertida'])}\n"
        f"Merma: {item['merma']:.2f}%\n"
        f"Crítico: {'SÍ' if item['critico'] else 'NO'}\n"
        f"Sustituto: {'SÍ' if item['sustituto'] else 'NO'}\n"
        f"Sustituye a: {item['sustituye']}\n"
        f"Subproducto: {'SÍ' if item['subproducto'] else 'NO'}\n"
        f"Recuperación: {item['recuperacion']:.2f}%\n"
        f"Observaciones: {item['observaciones']}"
    )

    messagebox.showinfo("Detalle del componente", detalle)


def limpiar_recurso():
    combo_tipo_recurso.set("MANO DE OBRA")
    entry_recurso.delete(0, "end")
    entry_cantidad_recurso.delete(0, "end")
    combo_unidad_recurso.set("HORA")
    entry_costo_recurso.delete(0, "end")
    entry_costo_recurso.insert(0, "0")
    txt_observacion_recurso.delete("1.0", "end")


def agregar_recurso():
    recurso = entry_recurso.get().strip()
    if not recurso:
        messagebox.showerror("Recurso", "Ingrese el nombre del recurso.")
        return

    try:
        cantidad = a_numero(entry_cantidad_recurso.get(), "Cantidad")
        costo = a_numero(
            entry_costo_recurso.get() or 0,
            "Costo unitario",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror("Recurso", str(error))
        return

    recursos.append({
        "tipo": combo_tipo_recurso.get().strip(),
        "recurso": recurso,
        "cantidad": cantidad,
        "unidad": combo_unidad_recurso.get().strip(),
        "costo_unitario": costo,
        "costo_total": cantidad * costo,
        "observaciones": txt_observacion_recurso.get("1.0", "end").strip(),
    })

    mostrar_recursos()
    limpiar_recurso()


def mostrar_recursos():
    tabla_recursos.delete(*tabla_recursos.get_children())

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
            ),
        )

    actualizar_costos()


def eliminar_recurso():
    sel = tabla_recursos.selection()
    if not sel:
        messagebox.showwarning("Recurso", "Seleccione un recurso.")
        return

    recursos.pop(int(sel[0]))
    mostrar_recursos()


def totales_recursos():
    mano_obra = sum(
        r["costo_total"] for r in recursos
        if r["tipo"] == "MANO DE OBRA"
    )
    cif = sum(
        r["costo_total"] for r in recursos
        if r["tipo"] == "CIF"
    )
    servicios = sum(
        r["costo_total"] for r in recursos
        if r["tipo"] in ("SERVICIO", "ENERGÍA", "GAS", "AGUA")
    )
    return mano_obra, cif, servicios


def actualizar_costos():
    materiales = sum(c["costo_total"] for c in componentes)
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
        messagebox.showerror("Fórmula", "Seleccione un producto.")
        return

    if not componentes:
        messagebox.showerror("Fórmula", "Agregue al menos un componente.")
        return

    try:
        version = int(entry_version.get())
        cantidad_base = a_numero(entry_base.get(), "Cantidad base")
        rendimiento = a_numero(entry_rendimiento.get(), "Rendimiento")
        merma_formula = a_numero(
            entry_merma_formula.get() or 0,
            "Merma general",
            permitir_cero=True
        )
        preparacion = a_numero(
            entry_preparacion.get() or 0,
            "Preparación",
            permitir_cero=True
        )
        proceso = a_numero(
            entry_proceso.get() or 0,
            "Proceso",
            permitir_cero=True
        )
    except ValueError as error:
        messagebox.showerror("Fórmula", str(error))
        return

    materiales = sum(c["costo_total"] for c in componentes)
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
            entry_codigo.get().strip().upper(),
            version,
            cantidad_base,
            combo_unidad_base.get().strip(),
            rendimiento,
            merma_formula,
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
                item["sustituto"],
                item["sustituye"],
                item["critico"],
                item["subproducto"],
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
            f"{entry_codigo.get().strip()} v{version}; costo {total:.2f}",
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            "BOM guardada correctamente en estado BORRADOR."
        )

        limpiar_formula()
        cargar_formulas()

    except sqlite3.IntegrityError as error:
        con.rollback()
        messagebox.showerror(
            "Fórmula",
            f"Ya existe esa versión o código.\n\n{error}"
        )
    except Exception as error:
        con.rollback()
        messagebox.showerror("Fórmula", str(error))
    finally:
        con.close()


def limpiar_formula():
    global componentes, recursos

    componentes = []
    recursos = []

    combo_producto.set("")
    entry_codigo.delete(0, "end")
    entry_version.delete(0, "end")
    entry_version.insert(0, "1")
    entry_base.delete(0, "end")
    entry_base.insert(0, "1")
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
    txt_instrucciones.delete("1.0", "end")
    txt_observaciones.delete("1.0", "end")

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
            f.costo_estandar_total,
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
                moneda(fila["costo_estandar_total"]),
                fila["estado"],
                fila["vigente_desde"],
                fila["vigente_hasta"],
            ),
            tags=(fila["estado"].lower(),),
        )


def activar_formula():
    sel = tabla_formulas.selection()
    if not sel:
        messagebox.showwarning("Fórmula", "Seleccione una fórmula.")
        return

    formula_id = int(sel[0])

    if not messagebox.askyesno(
        "Activar fórmula",
        "La versión seleccionada quedará ACTIVA y las demás quedarán INACTIVAS.\n\n¿Desea continuar?"
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
            f"{fila['codigo']} v{fila['version']}",
        )

        con.commit()

        messagebox.showinfo(
            "Fórmula",
            f"La fórmula {fila['codigo']} versión {fila['version']} quedó ACTIVA."
        )

        cargar_formulas()

    except Exception as error:
        con.rollback()
        messagebox.showerror("Fórmula", str(error))
    finally:
        con.close()


# ------------------------------------------------------------
# INTERFAZ
# ------------------------------------------------------------

ventana = tk.Tk()
ventana.title("SIGA ERP - BOM Profesional Compacto v4")
ventana.geometry("1280x760")
ventana.minsize(1050, 680)
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

estilo.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
estilo.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

header = tk.Frame(ventana, bg=C_OSCURO, height=82)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="BOM PROFESIONAL COMPACTO v4",
    bg=C_OSCURO,
    fg="white",
    font=("Segoe UI", 20, "bold"),
).pack(anchor="w", padx=24, pady=(14, 0))

tk.Label(
    header,
    text="Lista de materiales, recursos, costos estándar y versiones",
    bg=C_OSCURO,
    fg="#BFDBFE",
    font=("Segoe UI", 9),
).pack(anchor="w", padx=25, pady=(3, 0))

notebook = ttk.Notebook(ventana)
notebook.pack(fill="both", expand=True, padx=12, pady=(10, 6))

tab_bom = tk.Frame(notebook, bg=C_FONDO)
tab_versiones = tk.Frame(notebook, bg=C_FONDO)

notebook.add(tab_bom, text="  Nueva BOM  ")
notebook.add(tab_versiones, text="  Versiones y activación  ")

# Encabezado compacto en dos filas
frame_enc = tk.LabelFrame(
    tab_bom,
    text="ENCABEZADO",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8,
)
frame_enc.pack(fill="x", padx=8, pady=8)

for i in range(6):
    frame_enc.columnconfigure(i, weight=1)

labels_fila1 = [
    "Producto",
    "Código fórmula",
    "Versión",
    "Cantidad base",
    "Unidad",
    "Centro de trabajo",
]

for i, texto in enumerate(labels_fila1):
    tk.Label(frame_enc, text=texto, bg=C_BLANCO, fg=C_GRIS).grid(
        row=0, column=i, sticky="w", padx=4
    )

combo_producto = ttk.Combobox(frame_enc, state="readonly", width=32)
combo_producto.grid(row=1, column=0, sticky="ew", padx=4)
combo_producto.bind("<<ComboboxSelected>>", cambio_producto)

entry_codigo = ttk.Entry(frame_enc)
entry_codigo.grid(row=1, column=1, sticky="ew", padx=4)

entry_version = ttk.Entry(frame_enc)
entry_version.grid(row=1, column=2, sticky="ew", padx=4)

entry_base = ttk.Entry(frame_enc)
entry_base.grid(row=1, column=3, sticky="ew", padx=4)

combo_unidad_base = ttk.Combobox(
    frame_enc,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
)
combo_unidad_base.grid(row=1, column=4, sticky="ew", padx=4)

combo_centro = ttk.Combobox(frame_enc)
combo_centro.grid(row=1, column=5, sticky="ew", padx=4)

labels_fila2 = [
    "Rendimiento %",
    "Merma general %",
    "Preparación min",
    "Proceso min",
    "Vigente desde",
    "Vigente hasta",
]

for i, texto in enumerate(labels_fila2):
    tk.Label(frame_enc, text=texto, bg=C_BLANCO, fg=C_GRIS).grid(
        row=2, column=i, sticky="w", padx=4, pady=(8, 0)
    )

entry_rendimiento = ttk.Entry(frame_enc)
entry_rendimiento.grid(row=3, column=0, sticky="ew", padx=4)

entry_merma_formula = ttk.Entry(frame_enc)
entry_merma_formula.grid(row=3, column=1, sticky="ew", padx=4)

entry_preparacion = ttk.Entry(frame_enc)
entry_preparacion.grid(row=3, column=2, sticky="ew", padx=4)

entry_proceso = ttk.Entry(frame_enc)
entry_proceso.grid(row=3, column=3, sticky="ew", padx=4)

entry_desde = ttk.Entry(frame_enc)
entry_desde.grid(row=3, column=4, sticky="ew", padx=4)

entry_hasta = ttk.Entry(frame_enc)
entry_hasta.grid(row=3, column=5, sticky="ew", padx=4)

sub = ttk.Notebook(tab_bom)
sub.pack(fill="both", expand=True, padx=8, pady=(0, 8))

tab_componentes = tk.Frame(sub, bg=C_FONDO)
tab_avanzado = tk.Frame(sub, bg=C_FONDO)
tab_recursos = tk.Frame(sub, bg=C_FONDO)
tab_tecnica = tk.Frame(sub, bg=C_FONDO)

sub.add(tab_componentes, text="  Componentes  ")
sub.add(tab_avanzado, text="  Datos avanzados  ")
sub.add(tab_recursos, text="  Recursos y costos  ")
sub.add(tab_tecnica, text="  Instrucciones  ")

# Componentes: vista diaria compacta
frame_comp_form = tk.Frame(tab_componentes, bg=C_BLANCO)
frame_comp_form.pack(fill="x", padx=6, pady=6)

for i in range(7):
    frame_comp_form.columnconfigure(i, weight=1)

for i, texto in enumerate([
    "Componente", "Tipo", "Cantidad", "Unidad", "Merma %", "Costo unitario", ""
]):
    tk.Label(
        frame_comp_form,
        text=texto,
        bg=C_BLANCO,
        fg=C_GRIS
    ).grid(row=0, column=i, sticky="w", padx=3)

combo_componente = ttk.Combobox(frame_comp_form, state="readonly")
combo_componente.grid(row=1, column=0, sticky="ew", padx=3)
combo_componente.bind("<<ComboboxSelected>>", seleccionar_componente)

combo_tipo = ttk.Combobox(
    frame_comp_form,
    values=[
        "MATERIA PRIMA",
        "MATERIAL DE EMPAQUE",
        "INSUMO",
        "SEMIPROCESADO",
    ],
    state="readonly",
)
combo_tipo.grid(row=1, column=1, sticky="ew", padx=3)

entry_cantidad = ttk.Entry(frame_comp_form)
entry_cantidad.grid(row=1, column=2, sticky="ew", padx=3)

combo_unidad_formula = ttk.Combobox(
    frame_comp_form,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
)
combo_unidad_formula.grid(row=1, column=3, sticky="ew", padx=3)

entry_merma = ttk.Entry(frame_comp_form)
entry_merma.grid(row=1, column=4, sticky="ew", padx=3)

entry_costo = ttk.Entry(frame_comp_form)
entry_costo.grid(row=1, column=5, sticky="ew", padx=3)

tk.Button(
    frame_comp_form,
    text="Agregar",
    command=agregar_componente,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6,
).grid(row=1, column=6, padx=5)

frame_tabla_comp = tk.Frame(tab_componentes, bg=C_BLANCO)
frame_tabla_comp.pack(fill="both", expand=True, padx=6, pady=(0, 6))
frame_tabla_comp.grid_rowconfigure(0, weight=1)
frame_tabla_comp.grid_columnconfigure(0, weight=1)

cols_comp = (
    "N", "Componente", "Presentación", "Tipo",
    "Cantidad", "Unidad", "Costo unitario", "Costo total"
)

tabla_componentes = ttk.Treeview(
    frame_tabla_comp,
    columns=cols_comp,
    show="headings"
)

anchos = {
    "N": 45,
    "Componente": 220,
    "Presentación": 120,
    "Tipo": 150,
    "Cantidad": 90,
    "Unidad": 80,
    "Costo unitario": 120,
    "Costo total": 120,
}

for c in cols_comp:
    tabla_componentes.heading(c, text=c)
    tabla_componentes.column(c, width=anchos[c], stretch=True)

scroll_comp = ttk.Scrollbar(
    frame_tabla_comp,
    orient="vertical",
    command=tabla_componentes.yview
)
tabla_componentes.configure(yscrollcommand=scroll_comp.set)

tabla_componentes.grid(row=0, column=0, sticky="nsew")
scroll_comp.grid(row=0, column=1, sticky="ns")

barra_comp = tk.Frame(tab_componentes, bg=C_FONDO)
barra_comp.pack(fill="x", padx=6, pady=(0, 6))

tk.Button(
    barra_comp,
    text="Eliminar",
    command=eliminar_componente,
    bg=C_ROJO,
    fg="white",
    relief="flat",
    padx=14,
    pady=5,
).pack(side="left")

tk.Button(
    barra_comp,
    text="Ver detalle",
    command=ver_detalle_componente,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=14,
    pady=5,
).pack(side="left", padx=6)

# Datos avanzados del componente
frame_adv = tk.LabelFrame(
    tab_avanzado,
    text="DATOS AVANZADOS DEL PRÓXIMO COMPONENTE",
    bg=C_BLANCO,
    fg=C_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=12,
    pady=10,
)
frame_adv.pack(fill="both", expand=True, padx=8, pady=8)

for i in range(4):
    frame_adv.columnconfigure(i, weight=1)

campos_adv = [
    "Factor conversión",
    "Unidad inventario",
    "Componente crítico",
    "Es sustituto",
]

for i, texto in enumerate(campos_adv):
    tk.Label(frame_adv, text=texto, bg=C_BLANCO, fg=C_GRIS).grid(
        row=0, column=i, sticky="w", padx=5
    )

entry_factor = ttk.Entry(frame_adv)
entry_factor.grid(row=1, column=0, sticky="ew", padx=5)

combo_unidad_inventario = ttk.Combobox(
    frame_adv,
    values=["UND", "KG", "G", "L", "ML", "M", "M2", "M3"],
    state="readonly",
)
combo_unidad_inventario.grid(row=1, column=1, sticky="ew", padx=5)

combo_critico = ttk.Combobox(
    frame_adv,
    values=["NO", "SÍ"],
    state="readonly",
)
combo_critico.grid(row=1, column=2, sticky="ew", padx=5)

combo_sustituto = ttk.Combobox(
    frame_adv,
    values=["NO", "SÍ"],
    state="readonly",
)
combo_sustituto.grid(row=1, column=3, sticky="ew", padx=5)

for i, texto in enumerate([
    "Sustituye a",
    "Es subproducto",
    "Recuperación %",
    "Observación",
]):
    tk.Label(frame_adv, text=texto, bg=C_BLANCO, fg=C_GRIS).grid(
        row=2, column=i, sticky="w", padx=5, pady=(12, 0)
    )

entry_sustituye = ttk.Entry(frame_adv)
entry_sustituye.grid(row=3, column=0, sticky="ew", padx=5)

combo_subproducto = ttk.Combobox(
    frame_adv,
    values=["NO", "SÍ"],
    state="readonly",
)
combo_subproducto.grid(row=3, column=1, sticky="ew", padx=5)

entry_recuperacion = ttk.Entry(frame_adv)
entry_recuperacion.grid(row=3, column=2, sticky="ew", padx=5)

txt_observacion_componente = tk.Text(frame_adv, height=5, relief="solid", bd=1)
txt_observacion_componente.grid(
    row=3,
    column=3,
    sticky="nsew",
    padx=5,
)
frame_adv.rowconfigure(3, weight=1)

# Recursos
frame_rec_form = tk.Frame(tab_recursos, bg=C_BLANCO)
frame_rec_form.pack(fill="x", padx=6, pady=6)

for i in range(6):
    frame_rec_form.columnconfigure(i, weight=1)

for i, texto in enumerate([
    "Tipo", "Recurso", "Cantidad", "Unidad", "Costo unitario", ""
]):
    tk.Label(frame_rec_form, text=texto, bg=C_BLANCO, fg=C_GRIS).grid(
        row=0, column=i, sticky="w", padx=3
    )

combo_tipo_recurso = ttk.Combobox(
    frame_rec_form,
    values=["MANO DE OBRA", "CIF", "SERVICIO", "ENERGÍA", "GAS", "AGUA"],
    state="readonly",
)
combo_tipo_recurso.grid(row=1, column=0, sticky="ew", padx=3)

entry_recurso = ttk.Entry(frame_rec_form)
entry_recurso.grid(row=1, column=1, sticky="ew", padx=3)

entry_cantidad_recurso = ttk.Entry(frame_rec_form)
entry_cantidad_recurso.grid(row=1, column=2, sticky="ew", padx=3)

combo_unidad_recurso = ttk.Combobox(
    frame_rec_form,
    values=["HORA", "MINUTO", "UND", "KG", "L", "KWH", "M3"],
    state="readonly",
)
combo_unidad_recurso.grid(row=1, column=3, sticky="ew", padx=3)

entry_costo_recurso = ttk.Entry(frame_rec_form)
entry_costo_recurso.grid(row=1, column=4, sticky="ew", padx=3)

tk.Button(
    frame_rec_form,
    text="Agregar",
    command=agregar_recurso,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6,
).grid(row=1, column=5, padx=5)

tk.Label(
    tab_recursos,
    text="Observación del recurso",
    bg=C_FONDO,
    fg=C_GRIS
).pack(anchor="w", padx=8)

txt_observacion_recurso = tk.Text(
    tab_recursos,
    height=2,
    relief="solid",
    bd=1
)
txt_observacion_recurso.pack(fill="x", padx=8, pady=(0, 6))

frame_tabla_rec = tk.Frame(tab_recursos, bg=C_BLANCO)
frame_tabla_rec.pack(fill="both", expand=True, padx=6, pady=(0, 6))
frame_tabla_rec.grid_rowconfigure(0, weight=1)
frame_tabla_rec.grid_columnconfigure(0, weight=1)

cols_rec = (
    "N", "Tipo", "Recurso", "Cantidad",
    "Unidad", "Costo unitario", "Costo total"
)

tabla_recursos = ttk.Treeview(
    frame_tabla_rec,
    columns=cols_rec,
    show="headings"
)

for c in cols_rec:
    tabla_recursos.heading(c, text=c)
    tabla_recursos.column(c, width=120, stretch=True)

scroll_rec = ttk.Scrollbar(
    frame_tabla_rec,
    orient="vertical",
    command=tabla_recursos.yview
)
tabla_recursos.configure(yscrollcommand=scroll_rec.set)

tabla_recursos.grid(row=0, column=0, sticky="nsew")
scroll_rec.grid(row=0, column=1, sticky="ns")

tk.Button(
    tab_recursos,
    text="Eliminar recurso",
    command=eliminar_recurso,
    bg=C_ROJO,
    fg="white",
    relief="flat",
    padx=14,
    pady=5,
).pack(anchor="w", padx=6, pady=(0, 6))

# Técnica
frame_tec = tk.Frame(tab_tecnica, bg=C_FONDO)
frame_tec.pack(fill="both", expand=True, padx=8, pady=8)

tk.Label(
    frame_tec,
    text="Instrucciones técnicas",
    bg=C_FONDO,
    fg=C_GRIS
).pack(anchor="w")

txt_instrucciones = tk.Text(frame_tec, height=10, relief="solid", bd=1)
txt_instrucciones.pack(fill="both", expand=True, pady=(0, 8))

tk.Label(
    frame_tec,
    text="Observaciones generales",
    bg=C_FONDO,
    fg=C_GRIS
).pack(anchor="w")

txt_observaciones = tk.Text(frame_tec, height=6, relief="solid", bd=1)
txt_observaciones.pack(fill="both", expand=True)

# Costos siempre visibles
barra_costos = tk.Frame(
    tab_bom,
    bg=C_BLANCO,
    highlightbackground=C_BORDE,
    highlightthickness=1,
)
barra_costos.pack(fill="x", padx=8, pady=(0, 6))


def tarjeta(parent, titulo):
    marco = tk.Frame(parent, bg=C_BLANCO)
    marco.pack(side="left", padx=18, pady=6)

    tk.Label(
        marco,
        text=titulo,
        bg=C_BLANCO,
        fg=C_GRIS,
        font=("Segoe UI", 8, "bold"),
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="$0.00",
        bg=C_BLANCO,
        fg=C_TEXTO,
        font=("Segoe UI", 11, "bold"),
    )
    valor.pack(anchor="w")
    return valor


lbl_materiales = tarjeta(barra_costos, "MATERIALES")
lbl_mano_obra = tarjeta(barra_costos, "MANO DE OBRA")
lbl_cif = tarjeta(barra_costos, "CIF")
lbl_servicios = tarjeta(barra_costos, "SERVICIOS")
lbl_total = tarjeta(barra_costos, "COSTO TOTAL")

barra_acciones = tk.Frame(tab_bom, bg=C_FONDO)
barra_acciones.pack(fill="x", padx=8, pady=(0, 8))

tk.Button(
    barra_acciones,
    text="Guardar BOM en borrador",
    command=guardar_formula,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 10, "bold"),
    padx=20,
    pady=8,
).pack(side="left")

tk.Button(
    barra_acciones,
    text="Nueva / limpiar",
    command=limpiar_formula,
    bg=C_OSCURO,
    fg="white",
    relief="flat",
    padx=18,
    pady=8,
).pack(side="left", padx=8)

# Versiones
barra_versiones = tk.Frame(tab_versiones, bg=C_BLANCO)
barra_versiones.pack(fill="x", padx=8, pady=8)

tk.Label(
    barra_versiones,
    text="Estado:",
    bg=C_BLANCO,
    fg=C_TEXTO
).pack(side="left", padx=(8, 5))

combo_filtro_estado = ttk.Combobox(
    barra_versiones,
    values=["TODOS", "BORRADOR", "ACTIVA", "INACTIVA"],
    state="readonly",
    width=14,
)
combo_filtro_estado.pack(side="left")
combo_filtro_estado.set("TODOS")

tk.Button(
    barra_versiones,
    text="Actualizar",
    command=cargar_formulas,
    bg=C_AZUL,
    fg="white",
    relief="flat",
    padx=14,
    pady=6,
).pack(side="left", padx=5)

tk.Button(
    barra_versiones,
    text="Activar fórmula",
    command=activar_formula,
    bg=C_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    padx=14,
    pady=6,
).pack(side="right", padx=5)

frame_tabla_form = tk.Frame(tab_versiones, bg=C_BLANCO)
frame_tabla_form.pack(fill="both", expand=True, padx=8, pady=(0, 8))
frame_tabla_form.grid_rowconfigure(0, weight=1)
frame_tabla_form.grid_columnconfigure(0, weight=1)

cols_formulas = (
    "Código", "Versión", "Cod. producto", "Producto",
    "Presentación", "Base", "Unidad", "Costo total",
    "Estado", "Desde", "Hasta"
)

tabla_formulas = ttk.Treeview(
    frame_tabla_form,
    columns=cols_formulas,
    show="headings"
)

anchos_form = {
    "Código": 180,
    "Versión": 70,
    "Cod. producto": 110,
    "Producto": 200,
    "Presentación": 120,
    "Base": 80,
    "Unidad": 70,
    "Costo total": 120,
    "Estado": 90,
    "Desde": 100,
    "Hasta": 100,
}

for c in cols_formulas:
    tabla_formulas.heading(c, text=c)
    tabla_formulas.column(c, width=anchos_form[c], stretch=True)

scroll_y_form = ttk.Scrollbar(
    frame_tabla_form,
    orient="vertical",
    command=tabla_formulas.yview
)
scroll_x_form = ttk.Scrollbar(
    frame_tabla_form,
    orient="horizontal",
    command=tabla_formulas.xview
)

tabla_formulas.configure(
    yscrollcommand=scroll_y_form.set,
    xscrollcommand=scroll_x_form.set,
)

tabla_formulas.grid(row=0, column=0, sticky="nsew")
scroll_y_form.grid(row=0, column=1, sticky="ns")
scroll_x_form.grid(row=1, column=0, sticky="ew")

tabla_formulas.tag_configure("activa", foreground=C_VERDE)
tabla_formulas.tag_configure("inactiva", foreground=C_GRIS)
tabla_formulas.tag_configure("borrador", foreground=C_NARANJA)

status = tk.Label(
    ventana,
    text=f"Base de datos: {RUTA_DB}",
    bg=C_OSCURO,
    fg="white",
    anchor="w",
    padx=12,
    pady=4,
    font=("Segoe UI", 8),
)
status.pack(fill="x")

limpiar_formula()
cargar_catalogos()
cargar_formulas()

ventana.mainloop()
