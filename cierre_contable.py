"""
BME-ERP - Cierre Contable
Archivo: cierre_contable.py

Versión corregida:
- Migra automáticamente estructuras antiguas.
- Consulta y valida períodos.
- Calcula ingresos, costos, gastos y resultado.
- Cierra y bloquea períodos.
- Registra auditoría.
- Permite reapertura controlada.
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")
USUARIO = (
    os.environ.get("ERP_USUARIO", "").strip()
    or os.environ.get("USERNAME", "SISTEMA")
)

COLOR_FONDO = "#EEF3F8"
COLOR_TARJETA = "#FFFFFF"
COLOR_AZUL = "#0F5C8E"
COLOR_VERDE = "#15803D"
COLOR_ROJO = "#B42318"
COLOR_NARANJA = "#C56A00"
COLOR_TEXTO = "#1F2937"
COLOR_SUAVE = "#64748B"
COLOR_BORDE = "#D7E0E8"

CLAVE_REAPERTURA = "BME2026"
CUENTA_RESULTADO = "360505"


# ============================================================
# BASE DE DATOS Y MIGRACIÓN
# ============================================================

def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )

    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def tabla_existe(cursor, tabla):
    cursor.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla,))
    return cursor.fetchone() is not None


def columnas_tabla(cursor, tabla):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return {fila["name"] for fila in cursor.fetchall()}


def agregar_columna(cursor, tabla, nombre, definicion):
    if nombre not in columnas_tabla(cursor, tabla):
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"
        )


def preparar_estructura():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cierres_contables (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)

        columnas_cierre = {
            "periodo_id": "INTEGER",
            "fecha_inicio": "TEXT DEFAULT ''",
            "fecha_fin": "TEXT DEFAULT ''",
            "anio": "INTEGER DEFAULT 0",
            "mes": "INTEGER DEFAULT 0",
            "ingresos": "REAL DEFAULT 0",
            "costos": "REAL DEFAULT 0",
            "gastos": "REAL DEFAULT 0",
            "resultado": "REAL DEFAULT 0",
            "comprobantes": "INTEGER DEFAULT 0",
            "movimientos": "INTEGER DEFAULT 0",
            "total_debitos": "REAL DEFAULT 0",
            "total_credito": "REAL DEFAULT 0",
            "total_creditos": "REAL DEFAULT 0",
            "estado": "TEXT DEFAULT 'CERRADO'",
            "usuario": "TEXT DEFAULT ''",
            "usuario_cierre": "TEXT DEFAULT ''",
            "fecha_cierre": "TEXT DEFAULT ''",
            "usuario_reapertura": "TEXT DEFAULT ''",
            "fecha_reapertura": "TEXT DEFAULT ''",
            "observaciones": "TEXT DEFAULT ''"
        }

        for nombre, definicion in columnas_cierre.items():
            agregar_columna(
                cursor,
                "cierres_contables",
                nombre,
                definicion
            )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoria_cierres (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)

        columnas_auditoria = {
            "cierre_id": "INTEGER",
            "accion": "TEXT DEFAULT ''",
            "usuario": "TEXT DEFAULT ''",
            "fecha": "TEXT DEFAULT ''",
            "detalle": "TEXT DEFAULT ''"
        }

        for nombre, definicion in columnas_auditoria.items():
            agregar_columna(
                cursor,
                "auditoria_cierres",
                nombre,
                definicion
            )

        if not tabla_existe(cursor, "periodos_contables"):
            raise RuntimeError(
                "No existe la tabla periodos_contables. "
                "Ejecute primero bd_contabilidad.py."
            )

        columnas_periodo = {
            "estado": "TEXT DEFAULT 'ABIERTO'",
            "fecha_cierre": "TEXT DEFAULT ''",
            "usuario_cierre": "TEXT DEFAULT ''"
        }

        for nombre, definicion in columnas_periodo.items():
            agregar_columna(
                cursor,
                "periodos_contables",
                nombre,
                definicion
            )

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cierres_periodo
            ON cierres_contables(periodo_id, estado)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auditoria_cierre
            ON auditoria_cierres(cierre_id, fecha)
        """)

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def moneda(valor):
    return f"${float(valor or 0):,.2f}"


def fecha_hora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# PERÍODOS
# ============================================================

def cargar_periodos():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        columnas = columnas_tabla(cursor, "periodos_contables")

        requeridas = {
            "id",
            "anio",
            "mes",
            "fecha_inicio",
            "fecha_fin",
            "estado"
        }

        faltantes = requeridas - columnas

        if faltantes:
            raise RuntimeError(
                "La tabla periodos_contables no tiene las columnas: "
                + ", ".join(sorted(faltantes))
            )

        cursor.execute("""
            SELECT
                id,
                anio,
                mes,
                fecha_inicio,
                fecha_fin,
                COALESCE(estado, 'ABIERTO') AS estado
            FROM periodos_contables
            ORDER BY anio DESC, mes DESC
        """)

        registros = cursor.fetchall()

    finally:
        conexion.close()

    tabla_periodos.delete(*tabla_periodos.get_children())

    for fila in registros:
        tabla_periodos.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["anio"],
                f"{int(fila['mes']):02d}",
                fila["fecha_inicio"],
                fila["fecha_fin"],
                fila["estado"]
            )
        )

    limpiar_resumen()


def periodo_seleccionado():
    seleccion = tabla_periodos.selection()

    if not seleccion:
        raise ValueError("Seleccione un período contable.")

    periodo_id = int(seleccion[0])
    valores = tabla_periodos.item(seleccion[0])["values"]

    return {
        "id": periodo_id,
        "anio": int(valores[0]),
        "mes": int(valores[1]),
        "fecha_inicio": str(valores[2]),
        "fecha_fin": str(valores[3]),
        "estado": str(valores[4]).upper()
    }


# ============================================================
# CÁLCULO Y VALIDACIÓN
# ============================================================

def calcular_periodo(periodo):
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS cantidad,
                IFNULL(SUM(total_debito), 0) AS debitos,
                IFNULL(SUM(total_credito), 0) AS creditos
            FROM comprobantes
            WHERE date(fecha) BETWEEN date(?) AND date(?)
              AND estado='CONTABILIZADO'
        """, (
            periodo["fecha_inicio"],
            periodo["fecha_fin"]
        ))

        encabezado = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) AS cantidad
            FROM comprobantes
            WHERE date(fecha) BETWEEN date(?) AND date(?)
              AND estado IN ('BORRADOR', 'PENDIENTE')
        """, (
            periodo["fecha_inicio"],
            periodo["fecha_fin"]
        ))

        pendientes = int(cursor.fetchone()["cantidad"] or 0)

        cursor.execute("""
            SELECT COUNT(*) AS cantidad
            FROM comprobantes
            WHERE date(fecha) BETWEEN date(?) AND date(?)
              AND estado='CONTABILIZADO'
              AND ABS(
                    COALESCE(total_debito, 0)
                    - COALESCE(total_credito, 0)
                  ) > 0.01
        """, (
            periodo["fecha_inicio"],
            periodo["fecha_fin"]
        ))

        descuadrados = int(cursor.fetchone()["cantidad"] or 0)

        cursor.execute("""
            SELECT
                pc.codigo,
                SUM(d.debito) AS debitos,
                SUM(d.credito) AS creditos,
                COUNT(*) AS movimientos
            FROM detalle_comprobante d
            INNER JOIN comprobantes c
                ON c.id=d.comprobante_id
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            WHERE date(c.fecha) BETWEEN date(?) AND date(?)
              AND c.estado='CONTABILIZADO'
              AND (
                    pc.codigo LIKE '4%'
                    OR pc.codigo LIKE '5%'
                    OR pc.codigo LIKE '6%'
              )
            GROUP BY pc.codigo
        """, (
            periodo["fecha_inicio"],
            periodo["fecha_fin"]
        ))

        ingresos = 0.0
        costos = 0.0
        gastos = 0.0
        movimientos = 0

        for fila in cursor.fetchall():
            codigo = str(fila["codigo"])
            debitos = float(fila["debitos"] or 0)
            creditos = float(fila["creditos"] or 0)
            movimientos += int(fila["movimientos"] or 0)

            if codigo.startswith("4"):
                ingresos += creditos - debitos
            elif codigo.startswith("5"):
                gastos += debitos - creditos
            elif codigo.startswith("6"):
                costos += debitos - creditos

        resultado = ingresos - costos - gastos

        cursor.execute("""
            SELECT id
            FROM plan_cuentas
            WHERE codigo=?
              AND estado='ACTIVA'
            LIMIT 1
        """, (CUENTA_RESULTADO,))

        cuenta_resultado_existe = cursor.fetchone() is not None

        return {
            "comprobantes": int(encabezado["cantidad"] or 0),
            "debitos": float(encabezado["debitos"] or 0),
            "creditos": float(encabezado["creditos"] or 0),
            "pendientes": pendientes,
            "descuadrados": descuadrados,
            "ingresos": ingresos,
            "costos": costos,
            "gastos": gastos,
            "resultado": resultado,
            "movimientos": movimientos,
            "cuenta_resultado_existe": cuenta_resultado_existe
        }

    finally:
        conexion.close()


def validar_periodo():
    try:
        periodo = periodo_seleccionado()
        datos = calcular_periodo(periodo)
        mostrar_resumen(periodo, datos)

    except Exception as error:
        messagebox.showerror(
            "Validación del período",
            str(error)
        )


def mostrar_resumen(periodo, datos):
    lbl_periodo.config(
        text=(
            f"{periodo['anio']}-{periodo['mes']:02d} "
            f"({periodo['fecha_inicio']} a {periodo['fecha_fin']})"
        )
    )

    lbl_estado_periodo.config(text=periodo["estado"])
    lbl_comprobantes.config(text=str(datos["comprobantes"]))
    lbl_movimientos.config(text=str(datos["movimientos"]))
    lbl_debitos.config(text=moneda(datos["debitos"]))
    lbl_creditos.config(text=moneda(datos["creditos"]))
    lbl_ingresos.config(text=moneda(datos["ingresos"]))
    lbl_costos.config(text=moneda(datos["costos"]))
    lbl_gastos.config(text=moneda(datos["gastos"]))
    lbl_resultado.config(text=moneda(datos["resultado"]))
    lbl_pendientes.config(text=str(datos["pendientes"]))
    lbl_descuadrados.config(text=str(datos["descuadrados"]))

    diferencia = datos["debitos"] - datos["creditos"]
    lbl_diferencia.config(text=moneda(diferencia))

    errores = []

    if datos["pendientes"]:
        errores.append(
            f"{datos['pendientes']} comprobante(s) pendiente(s)"
        )

    if datos["descuadrados"]:
        errores.append(
            f"{datos['descuadrados']} comprobante(s) descuadrado(s)"
        )

    if abs(diferencia) > 0.01:
        errores.append(
            f"diferencia total {moneda(diferencia)}"
        )

    if not datos["cuenta_resultado_existe"]:
        errores.append(
            f"no existe la cuenta {CUENTA_RESULTADO}"
        )

    if errores:
        lbl_validacion.config(
            text="NO APTO PARA CIERRE: " + " · ".join(errores),
            fg=COLOR_ROJO
        )
    elif periodo["estado"] == "CERRADO":
        lbl_validacion.config(
            text="PERÍODO CERRADO",
            fg=COLOR_NARANJA
        )
    else:
        lbl_validacion.config(
            text="PERÍODO APTO PARA CIERRE",
            fg=COLOR_VERDE
        )

    lbl_resultado.config(
        fg=COLOR_VERDE if datos["resultado"] >= 0 else COLOR_ROJO
    )


def limpiar_resumen():
    lbl_periodo.config(text="Sin selección")
    lbl_estado_periodo.config(text="—")
    lbl_comprobantes.config(text="0")
    lbl_movimientos.config(text="0")
    lbl_debitos.config(text="$0.00")
    lbl_creditos.config(text="$0.00")
    lbl_ingresos.config(text="$0.00")
    lbl_costos.config(text="$0.00")
    lbl_gastos.config(text="$0.00")
    lbl_resultado.config(text="$0.00", fg=COLOR_TEXTO)
    lbl_pendientes.config(text="0")
    lbl_descuadrados.config(text="0")
    lbl_diferencia.config(text="$0.00")
    lbl_validacion.config(
        text="Seleccione y valide un período",
        fg=COLOR_SUAVE
    )


# ============================================================
# CIERRE
# ============================================================

def obtener_empresa_periodo(cursor, periodo_id):
    cursor.execute("""
        SELECT empresa_id
        FROM periodos_contables
        WHERE id=?
        LIMIT 1
    """, (periodo_id,))

    fila = cursor.fetchone()

    if not fila or fila["empresa_id"] is None:
        raise ValueError(
            "El período seleccionado no tiene empresa contable asociada."
        )

    return int(fila["empresa_id"])


def periodo_ya_cerrado(cursor, empresa_id, periodo_id):
    cursor.execute("""
        SELECT id
        FROM cierres_contables
        WHERE empresa_id=?
          AND periodo_id=?
          AND estado='CERRADO'
        LIMIT 1
    """, (empresa_id, periodo_id))

    return cursor.fetchone() is not None


def ejecutar_cierre():
    try:
        periodo = periodo_seleccionado()

        if periodo["estado"] == "CERRADO":
            raise ValueError("El período ya está cerrado.")

        datos = calcular_periodo(periodo)
        mostrar_resumen(periodo, datos)

        if datos["pendientes"] > 0:
            raise ValueError(
                "Existen comprobantes pendientes o en borrador."
            )

        if datos["descuadrados"] > 0:
            raise ValueError(
                "Existen comprobantes descuadrados."
            )

        if abs(datos["debitos"] - datos["creditos"]) > 0.01:
            raise ValueError(
                "Los débitos y créditos del período no son iguales."
            )

        if not datos["cuenta_resultado_existe"]:
            raise ValueError(
                f"No existe la cuenta {CUENTA_RESULTADO} "
                "para el resultado del ejercicio."
            )

        confirmacion = messagebox.askyesno(
            "Ejecutar cierre contable",
            (
                f"Período: {periodo['anio']}-{periodo['mes']:02d}\n"
                f"Resultado: {moneda(datos['resultado'])}\n\n"
                "El período quedará bloqueado.\n\n"
                "¿Desea continuar?"
            )
        )

        if not confirmacion:
            return

        conexion = conectar()

        try:
            cursor = conexion.cursor()
            cursor.execute("BEGIN IMMEDIATE")

            empresa_id = obtener_empresa_periodo(
                cursor,
                periodo["id"]
            )

            if periodo_ya_cerrado(
                cursor,
                empresa_id,
                periodo["id"]
            ):
                raise ValueError(
                    "Ya existe un cierre activo para este período."
                )

            ahora = fecha_hora()

            cursor.execute("""
                SELECT id
                FROM cierres_contables
                WHERE empresa_id=?
                  AND periodo_id=?
                LIMIT 1
            """, (empresa_id, periodo["id"]))

            cierre_existente = cursor.fetchone()

            if cierre_existente:
                cierre_id = int(cierre_existente["id"])

                cursor.execute("""
                    UPDATE cierres_contables
                    SET
                        fecha_inicio=?,
                        fecha_fin=?,
                        anio=?,
                        mes=?,
                        ingresos=?,
                        costos=?,
                        gastos=?,
                        resultado=?,
                        comprobantes=?,
                        movimientos=?,
                        total_debitos=?,
                        total_creditos=?,
                        estado='CERRADO',
                        usuario=?,
                        usuario_cierre=?,
                        fecha_cierre=?,
                        usuario_reapertura='',
                        fecha_reapertura='',
                        observaciones=?
                    WHERE id=?
                """, (
                    periodo["fecha_inicio"],
                    periodo["fecha_fin"],
                    periodo["anio"],
                    periodo["mes"],
                    datos["ingresos"],
                    datos["costos"],
                    datos["gastos"],
                    datos["resultado"],
                    datos["comprobantes"],
                    datos["movimientos"],
                    datos["debitos"],
                    datos["creditos"],
                    USUARIO,
                    USUARIO,
                    ahora,
                    "Cierre validado por el módulo contable.",
                    cierre_id
                ))

            else:
                cursor.execute("""
                    INSERT INTO cierres_contables(
                        empresa_id,
                        periodo_id,
                        fecha_inicio,
                        fecha_fin,
                        anio,
                        mes,
                        ingresos,
                        costos,
                        gastos,
                        resultado,
                        comprobantes,
                        movimientos,
                        total_debitos,
                        total_credito,
                        total_creditos,
                        estado,
                        usuario,
                        usuario_cierre,
                        fecha_cierre,
                        observaciones
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        'CERRADO', ?, ?, ?, ?
                    )
                """, (
                    empresa_id,
                    periodo["id"],
                    periodo["fecha_inicio"],
                    periodo["fecha_fin"],
                    periodo["anio"],
                    periodo["mes"],
                    datos["ingresos"],
                    datos["costos"],
                    datos["gastos"],
                    datos["resultado"],
                    datos["comprobantes"],
                    datos["movimientos"],
                    datos["debitos"],
                    datos["creditos"],
                    datos["creditos"],
                    USUARIO,
                    USUARIO,
                    ahora,
                    "Cierre validado por el módulo contable."
                ))

                cierre_id = int(cursor.lastrowid)

            cursor.execute("""
                UPDATE periodos_contables
                SET
                    estado='CERRADO',
                    fecha_cierre=?,
                    usuario_cierre=?
                WHERE id=?
            """, (
                ahora,
                USUARIO,
                periodo["id"]
            ))

            cursor.execute("""
                INSERT INTO auditoria_cierres(
                    cierre_id,
                    accion,
                    usuario,
                    fecha,
                    detalle
                )
                VALUES (?, 'CIERRE', ?, ?, ?)
            """, (
                cierre_id,
                USUARIO,
                ahora,
                (
                    f"Resultado {datos['resultado']:.2f}; "
                    f"débitos {datos['debitos']:.2f}; "
                    f"créditos {datos['creditos']:.2f}"
                )
            ))

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        finally:
            conexion.close()

        messagebox.showinfo(
            "Cierre contable",
            (
                "Período cerrado correctamente.\n\n"
                f"Resultado: {moneda(datos['resultado'])}\n"
                f"Usuario: {USUARIO}\n"
                f"Fecha: {ahora}"
            )
        )

        cargar_periodos()
        cargar_historial()

    except Exception as error:
        messagebox.showerror(
            "No fue posible cerrar el período",
            str(error)
        )


# ============================================================
# REAPERTURA
# ============================================================

def reabrir_periodo():
    try:
        periodo = periodo_seleccionado()

        if periodo["estado"] != "CERRADO":
            raise ValueError(
                "El período seleccionado no está cerrado."
            )

        clave = simpledialog.askstring(
            "Reapertura controlada",
            "Ingrese la clave administrativa:",
            show="*"
        )

        if clave is None:
            return

        if clave != CLAVE_REAPERTURA:
            raise ValueError("Clave administrativa incorrecta.")

        motivo = simpledialog.askstring(
            "Motivo de reapertura",
            "Indique el motivo de la reapertura:"
        )

        if not motivo or not motivo.strip():
            raise ValueError(
                "Debe registrar el motivo de la reapertura."
            )

        if not messagebox.askyesno(
            "Confirmar reapertura",
            (
                f"Se reabrirá el período "
                f"{periodo['anio']}-{periodo['mes']:02d}.\n\n"
                "La acción quedará registrada en auditoría.\n\n"
                "¿Desea continuar?"
            )
        ):
            return

        conexion = conectar()

        try:
            cursor = conexion.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            ahora = fecha_hora()

            empresa_id = obtener_empresa_periodo(
                cursor,
                periodo["id"]
            )

            cursor.execute("""
                SELECT id
                FROM cierres_contables
                WHERE empresa_id=?
                  AND periodo_id=?
                  AND estado='CERRADO'
                ORDER BY id DESC
                LIMIT 1
            """, (empresa_id, periodo["id"]))

            cierre = cursor.fetchone()

            if not cierre:
                raise ValueError(
                    "No se encontró el cierre activo del período."
                )

            cierre_id = int(cierre["id"])

            cursor.execute("""
                UPDATE cierres_contables
                SET
                    estado='REABIERTO',
                    usuario_reapertura=?,
                    fecha_reapertura=?,
                    observaciones=
                        COALESCE(observaciones, '')
                        || ?
                WHERE id=?
            """, (
                USUARIO,
                ahora,
                f"\nReapertura: {motivo.strip()}",
                cierre_id
            ))

            cursor.execute("""
                UPDATE periodos_contables
                SET
                    estado='ABIERTO',
                    fecha_cierre='',
                    usuario_cierre=''
                WHERE id=?
            """, (periodo["id"],))

            cursor.execute("""
                INSERT INTO auditoria_cierres(
                    cierre_id,
                    accion,
                    usuario,
                    fecha,
                    detalle
                )
                VALUES (?, 'REAPERTURA', ?, ?, ?)
            """, (
                cierre_id,
                USUARIO,
                ahora,
                motivo.strip()
            ))

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        finally:
            conexion.close()

        messagebox.showinfo(
            "Reapertura",
            "El período fue reabierto correctamente."
        )

        cargar_periodos()
        cargar_historial()

    except Exception as error:
        messagebox.showerror(
            "No fue posible reabrir el período",
            str(error)
        )


# ============================================================
# HISTORIAL
# ============================================================

def cargar_historial():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id,
                anio,
                mes,
                fecha_inicio,
                fecha_fin,
                resultado,
                estado,
                usuario_cierre,
                fecha_cierre,
                COALESCE(usuario_reapertura, '') AS usuario_reapertura,
                COALESCE(fecha_reapertura, '') AS fecha_reapertura
            FROM cierres_contables
            ORDER BY
                COALESCE(anio, 0) DESC,
                COALESCE(mes, 0) DESC,
                id DESC
        """)

        registros = cursor.fetchall()

    finally:
        conexion.close()

    tabla_historial.delete(*tabla_historial.get_children())

    for fila in registros:
        anio = int(fila["anio"] or 0)
        mes = int(fila["mes"] or 0)

        periodo_texto = (
            f"{anio}-{mes:02d}"
            if anio > 0 and mes > 0
            else "Sin período"
        )

        tabla_historial.insert(
            "",
            "end",
            values=(
                fila["id"],
                periodo_texto,
                fila["fecha_inicio"],
                fila["fecha_fin"],
                moneda(fila["resultado"]),
                fila["estado"],
                fila["usuario_cierre"],
                fila["fecha_cierre"],
                fila["usuario_reapertura"],
                fila["fecha_reapertura"]
            )
        )


# ============================================================
# INTERFAZ
# ============================================================

preparar_estructura()

ventana = tk.Tk()
ventana.title("BME-ERP - Cierre Contable")
ventana.geometry("1500x900")
ventana.minsize(1180, 740)
ventana.configure(bg=COLOR_FONDO)

estilo = ttk.Style()

try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Treeview",
    rowheight=27,
    font=("Segoe UI", 9),
    background="white",
    fieldbackground="white"
)

estilo.configure(
    "Treeview.Heading",
    background="#E8EEF4",
    foreground=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold")
)

estilo.map(
    "Treeview",
    background=[("selected", COLOR_AZUL)],
    foreground=[("selected", "white")]
)

cabecera = tk.Frame(
    ventana,
    bg=COLOR_AZUL,
    height=88
)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="CIERRE CONTABLE",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Validación, bloqueo y reapertura controlada de períodos",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=29, pady=(3, 0))

contenedor = tk.Frame(
    ventana,
    bg=COLOR_FONDO
)
contenedor.pack(
    fill="both",
    expand=True,
    padx=18,
    pady=18
)

panel_periodos = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_periodos.pack(
    fill="both",
    expand=True,
    pady=(0, 12)
)

tk.Label(
    panel_periodos,
    text="Períodos contables",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(10, 5))

columnas_periodos = (
    "Año",
    "Mes",
    "Fecha inicio",
    "Fecha fin",
    "Estado"
)

tabla_periodos = ttk.Treeview(
    panel_periodos,
    columns=columnas_periodos,
    show="headings",
    height=7
)

anchos_periodos = {
    "Año": 90,
    "Mes": 80,
    "Fecha inicio": 130,
    "Fecha fin": 130,
    "Estado": 120
}

for columna in columnas_periodos:
    tabla_periodos.heading(columna, text=columna)
    tabla_periodos.column(
        columna,
        width=anchos_periodos[columna]
    )

tabla_periodos.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 10)
)

botones = tk.Frame(
    panel_periodos,
    bg=COLOR_TARJETA
)
botones.pack(
    fill="x",
    padx=14,
    pady=(0, 12)
)

tk.Button(
    botones,
    text="Validar período",
    command=validar_periodo,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    padx=(0, 6),
    ipadx=18,
    ipady=8
)

tk.Button(
    botones,
    text="Ejecutar cierre",
    command=ejecutar_cierre,
    bg=COLOR_VERDE,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    padx=6,
    ipadx=18,
    ipady=8
)

tk.Button(
    botones,
    text="Reabrir período",
    command=reabrir_periodo,
    bg=COLOR_NARANJA,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    padx=6,
    ipadx=18,
    ipady=8
)

tk.Button(
    botones,
    text="Actualizar",
    command=lambda: (
        cargar_periodos(),
        cargar_historial()
    ),
    bg="#64748B",
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2"
).pack(
    side="left",
    padx=6,
    ipadx=18,
    ipady=8
)

panel_resumen = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_resumen.pack(
    fill="x",
    pady=(0, 12)
)

encabezado = tk.Frame(
    panel_resumen,
    bg=COLOR_TARJETA
)
encabezado.pack(
    fill="x",
    padx=14,
    pady=(10, 4)
)

lbl_periodo = tk.Label(
    encabezado,
    text="Sin selección",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
)
lbl_periodo.pack(side="left")

lbl_estado_periodo = tk.Label(
    encabezado,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 10, "bold")
)
lbl_estado_periodo.pack(side="right")

lbl_validacion = tk.Label(
    panel_resumen,
    text="Seleccione y valide un período",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 10, "bold")
)
lbl_validacion.pack(
    anchor="w",
    padx=14,
    pady=(0, 10)
)

resumen = tk.Frame(
    panel_resumen,
    bg=COLOR_TARJETA
)
resumen.pack(
    fill="x",
    padx=14,
    pady=(0, 12)
)

for columna in range(12):
    resumen.columnconfigure(columna, weight=1)


def tarjeta(columna, titulo):
    marco = tk.Frame(
        resumen,
        bg="#F8FAFC",
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=3
    )

    tk.Label(
        marco,
        text=titulo,
        bg="#F8FAFC",
        fg=COLOR_SUAVE,
        font=("Segoe UI", 7, "bold")
    ).pack(
        anchor="w",
        padx=8,
        pady=(8, 2)
    )

    valor = tk.Label(
        marco,
        text="0",
        bg="#F8FAFC",
        fg=COLOR_TEXTO,
        font=("Segoe UI", 10, "bold")
    )
    valor.pack(
        anchor="w",
        padx=8,
        pady=(0, 8)
    )

    return valor


lbl_comprobantes = tarjeta(0, "COMPROBANTES")
lbl_movimientos = tarjeta(1, "MOVIMIENTOS")
lbl_debitos = tarjeta(2, "DÉBITOS")
lbl_creditos = tarjeta(3, "CRÉDITOS")
lbl_diferencia = tarjeta(4, "DIFERENCIA")
lbl_ingresos = tarjeta(5, "INGRESOS")
lbl_costos = tarjeta(6, "COSTOS")
lbl_gastos = tarjeta(7, "GASTOS")
lbl_resultado = tarjeta(8, "RESULTADO")
lbl_pendientes = tarjeta(9, "PENDIENTES")
lbl_descuadrados = tarjeta(10, "DESCUADRADOS")
tarjeta(11, "CUENTA RESULTADO").config(
    text=CUENTA_RESULTADO
)

panel_historial = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_historial.pack(
    fill="both",
    expand=True
)

tk.Label(
    panel_historial,
    text="Historial de cierres",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(
    anchor="w",
    padx=14,
    pady=(10, 5)
)

columnas_historial = (
    "ID",
    "Período",
    "Inicio",
    "Fin",
    "Resultado",
    "Estado",
    "Usuario cierre",
    "Fecha cierre",
    "Usuario reapertura",
    "Fecha reapertura"
)

tabla_historial = ttk.Treeview(
    panel_historial,
    columns=columnas_historial,
    show="headings",
    height=8
)

anchos_historial = {
    "ID": 55,
    "Período": 90,
    "Inicio": 105,
    "Fin": 105,
    "Resultado": 120,
    "Estado": 100,
    "Usuario cierre": 120,
    "Fecha cierre": 145,
    "Usuario reapertura": 140,
    "Fecha reapertura": 145
}

for columna in columnas_historial:
    tabla_historial.heading(
        columna,
        text=columna
    )
    tabla_historial.column(
        columna,
        width=anchos_historial[columna]
    )

tabla_historial.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 12)
)

tk.Label(
    ventana,
    text=(
        f"Base: {RUTA_DB} | Usuario: {USUARIO} | "
        f"Clave inicial de reapertura: {CLAVE_REAPERTURA}"
    ),
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

cargar_periodos()
cargar_historial()

ventana.mainloop()
