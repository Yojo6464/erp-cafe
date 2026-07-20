
"""
SIGA ERP - Integración contable de Producción Terminada
Instala cuentas y reglas para PRODUCCION_TERMINADA y contabiliza
ejecuciones anteriores que quedaron PENDIENTES.

Ejecutar desde C:\\Users\\jrive\\visual
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"
RESPALDOS = BASE_DIR / "backups"

EVENTO = "PRODUCCION_TERMINADA"
EMPRESA_CODIGO = "001"
CENTRO_COSTO = "PROD"


def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(f"No se encontró la base de datos:\n{RUTA_DB}")
    con = sqlite3.connect(RUTA_DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 10000")
    return con


def respaldo():
    RESPALDOS.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = RESPALDOS / f"erp_cafe_antes_integracion_produccion_{marca}.db"
    shutil.copy2(RUTA_DB, destino)
    return destino


def columnas(con, tabla):
    return {fila["name"] for fila in con.execute(f"PRAGMA table_info({tabla})")}


def tabla_existe(con, tabla):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (tabla,)
    ).fetchone() is not None


def empresa_id(con):
    fila = con.execute("""
        SELECT id
        FROM empresas_contables
        WHERE codigo=? AND UPPER(estado)='ACTIVA'
    """, (EMPRESA_CODIGO,)).fetchone()
    if not fila:
        raise RuntimeError(
            f"No existe empresa contable activa con código {EMPRESA_CODIGO}."
        )
    return int(fila["id"])


def cuenta_id(con, emp_id, codigo):
    fila = con.execute("""
        SELECT id FROM plan_cuentas
        WHERE empresa_id=? AND codigo=?
    """, (emp_id, codigo)).fetchone()
    return int(fila["id"]) if fila else None


def insertar_cuenta(
    con, emp_id, codigo, nombre, nivel, padre_codigo,
    naturaleza, tipo_cuenta, movimiento, tercero=0, centro=0
):
    padre_id = cuenta_id(con, emp_id, padre_codigo) if padre_codigo else None
    con.execute("""
        INSERT OR IGNORE INTO plan_cuentas(
            empresa_id, codigo, nombre, nivel, cuenta_padre_id,
            naturaleza, tipo_cuenta, permite_movimiento,
            requiere_tercero, requiere_centro_costo,
            requiere_documento, estado, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'ACTIVA', ?)
    """, (
        emp_id, codigo, nombre, nivel, padre_id,
        naturaleza, tipo_cuenta, movimiento,
        tercero, centro, "Integración automática de Producción SIGA ERP"
    ))
    con.execute("""
        UPDATE plan_cuentas
        SET nombre=?, nivel=?, cuenta_padre_id=?, naturaleza=?,
            tipo_cuenta=?, permite_movimiento=?,
            requiere_tercero=?, requiere_centro_costo=?,
            estado='ACTIVA'
        WHERE empresa_id=? AND codigo=?
    """, (
        nombre, nivel, padre_id, naturaleza, tipo_cuenta,
        movimiento, tercero, centro, emp_id, codigo
    ))


def instalar_cuentas(con, emp_id):
    # Inventario de productos terminados.
    insertar_cuenta(
        con, emp_id, "1430", "PRODUCTOS TERMINADOS", 3, "14",
        "DEBITO", "ACTIVO", 0
    )
    insertar_cuenta(
        con, emp_id, "143005", "Productos terminados", 4, "1430",
        "DEBITO", "ACTIVO", 1, centro=1
    )

    # Cuentas puente de costos aplicados.
    insertar_cuenta(
        con, emp_id, "72", "MANO DE OBRA DIRECTA", 2, None,
        "DEBITO", "COSTO", 0
    )
    insertar_cuenta(
        con, emp_id, "7205", "MANO DE OBRA APLICADA", 3, "72",
        "DEBITO", "COSTO", 0
    )
    insertar_cuenta(
        con, emp_id, "720505", "Mano de obra aplicada a producción", 4, "7205",
        "DEBITO", "COSTO", 1, centro=1
    )

    insertar_cuenta(
        con, emp_id, "73", "COSTOS INDIRECTOS DE FABRICACIÓN", 2, None,
        "DEBITO", "COSTO", 0
    )
    insertar_cuenta(
        con, emp_id, "7305", "CIF APLICADOS", 3, "73",
        "DEBITO", "COSTO", 0
    )
    insertar_cuenta(
        con, emp_id, "730505", "Costos indirectos aplicados", 4, "7305",
        "DEBITO", "COSTO", 1, centro=1
    )

    # Garantizar que materia prima permita movimiento y centro de costo.
    if cuenta_id(con, emp_id, "140505") is None:
        raise RuntimeError(
            "No existe la cuenta 140505 Materias primas. "
            "Ejecute primero bd_contabilidad.py."
        )
    con.execute("""
        UPDATE plan_cuentas
        SET permite_movimiento=1,
            requiere_centro_costo=1,
            estado='ACTIVA'
        WHERE empresa_id=? AND codigo='140505'
    """, (emp_id,))


def instalar_centro(con, emp_id):
    con.execute("""
        INSERT OR IGNORE INTO centros_costo_contables(
            empresa_id, codigo, nombre, responsable, estado, observaciones
        )
        VALUES (?, 'PROD', 'Producción', '', 'ACTIVO',
                'Centro de costo de producción')
    """, (emp_id,))
    con.execute("""
        UPDATE centros_costo_contables
        SET estado='ACTIVO'
        WHERE empresa_id=? AND codigo='PROD'
    """, (emp_id,))


def instalar_reglas(con, emp_id):
    # Se reemplazan únicamente las reglas del evento de producción.
    con.execute("""
        DELETE FROM reglas_contables
        WHERE empresa_id=? AND UPPER(evento)=?
    """, (emp_id, EVENTO))

    reglas = [
        (
            "PROD-PT", "Entrada de producto terminado", EVENTO, 1,
            "DEBITO", "143005", "costo_total", "costo_total > 0",
            "Ingreso de producto terminado al costo real", 0, 1
        ),
        (
            "PROD-MP", "Consumo de materias primas", EVENTO, 2,
            "CREDITO", "140505", "costo_materiales", "costo_materiales > 0",
            "Salida de materias primas consumidas", 0, 1
        ),
        (
            "PROD-MO", "Mano de obra aplicada", EVENTO, 3,
            "CREDITO", "720505", "mano_obra", "mano_obra > 0",
            "Aplicación de mano de obra directa", 0, 1
        ),
        (
            "PROD-CIF", "CIF aplicado", EVENTO, 4,
            "CREDITO", "730505", "costos_indirectos",
            "costos_indirectos > 0",
            "Aplicación de costos indirectos de fabricación", 0, 1
        ),
    ]

    con.executemany("""
        INSERT INTO reglas_contables(
            empresa_id, codigo, nombre, evento, secuencia,
            tipo_movimiento, cuenta_codigo, fuente_valor,
            condicion, descripcion_linea,
            requiere_tercero, requiere_centro_costo, estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVA')
    """, [(emp_id,) + r for r in reglas])


def validar_instalacion(con, emp_id):
    cuentas = {
        f["codigo"] for f in con.execute("""
            SELECT codigo FROM plan_cuentas
            WHERE empresa_id=? AND codigo IN
                ('140505','143005','720505','730505')
              AND estado='ACTIVA'
              AND permite_movimiento=1
        """, (emp_id,))
    }
    faltan = {"140505", "143005", "720505", "730505"} - cuentas
    if faltan:
        raise RuntimeError(
            "No quedaron activas las cuentas: " + ", ".join(sorted(faltan))
        )

    reglas = con.execute("""
        SELECT COUNT(*) AS n
        FROM reglas_contables
        WHERE empresa_id=?
          AND UPPER(evento)=?
          AND estado='ACTIVA'
    """, (emp_id, EVENTO)).fetchone()["n"]
    if int(reglas) != 4:
        raise RuntimeError(
            f"Se esperaban 4 reglas de producción y quedaron {reglas}."
        )

    tipo_nc = con.execute("""
        SELECT id FROM tipos_comprobante
        WHERE empresa_id=? AND codigo='NC' AND estado='ACTIVO'
    """, (emp_id,)).fetchone()
    if not tipo_nc:
        raise RuntimeError(
            "No existe el tipo de comprobante NC activo. "
            "Ejecute primero bd_contabilidad.py."
        )


def contabilizar_pendientes():
    # Importación después de instalar las reglas.
    sys.path.insert(0, str(BASE_DIR))
    from motor_contable import contabilizar_evento

    with conectar() as con:
        cols_e = columnas(con, "ejecuciones_produccion_v3")
        requeridas = {
            "id", "orden_id", "numero_ejecucion", "fecha",
            "costo_materiales_real", "mano_obra_real",
            "costos_indirectos_reales", "costo_total_real",
            "estado_contable"
        }
        faltantes = requeridas - cols_e
        if faltantes:
            raise RuntimeError(
                "Faltan columnas en ejecuciones_produccion_v3: "
                + ", ".join(sorted(faltantes))
            )

        pendientes = con.execute("""
            SELECT
                e.id,
                e.orden_id,
                e.numero_ejecucion,
                e.fecha,
                e.costo_materiales_real,
                e.mano_obra_real,
                e.costos_indirectos_reales,
                e.costo_total_real,
                o.numero AS orden_numero,
                o.lote_planeado
            FROM ejecuciones_produccion_v3 e
            INNER JOIN ordenes_produccion_v2 o ON o.id=e.orden_id
            WHERE UPPER(COALESCE(e.estado_contable,'PENDIENTE'))
                  <> 'CONTABILIZADO'
              AND COALESCE(e.costo_total_real,0) > 0
            ORDER BY e.id
        """).fetchall()

    resultados = []
    for e in pendientes:
        valores = {
            "costo_total": float(e["costo_total_real"] or 0),
            "costo_materiales": float(e["costo_materiales_real"] or 0),
            "mano_obra": float(e["mano_obra_real"] or 0),
            "costos_indirectos": float(e["costos_indirectos_reales"] or 0),
        }

        resultado = contabilizar_evento(
            evento=EVENTO,
            valores=valores,
            concepto=(
                f"Terminación de producción {e['orden_numero']} "
                f"- lote {e['lote_planeado']}"
            ),
            modulo_origen="PRODUCCION",
            tabla_origen="ejecuciones_produccion_v3",
            registro_origen_id=int(e["id"]),
            centro_costo=CENTRO_COSTO,
            fecha=str(e["fecha"]),
            documento_referencia=str(e["numero_ejecucion"]),
            usuario=(
                os.environ.get("ERP_USUARIO", "").strip()
                or os.environ.get("USERNAME", "SISTEMA")
            ),
            tipo_comprobante_codigo="NC",
            ruta_db=RUTA_DB,
        )

        comprobante_id = resultado.get("comprobante_id")
        consecutivo = resultado.get("consecutivo") or "YA CONTABILIZADO"
        mensaje = resultado.get("mensaje", "Contabilización correcta.")

        with conectar() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("""
                UPDATE ejecuciones_produccion_v3
                SET estado_contable='CONTABILIZADO',
                    mensaje_contable=?,
                    comprobante_id=?
                WHERE id=?
            """, (
                f"{mensaje} Comprobante: {consecutivo}",
                comprobante_id,
                int(e["id"])
            ))

            cols_o = columnas(con, "ordenes_produccion_v2")
            asignaciones = [
                "estado_contable='CONTABILIZADO'",
                "mensaje_contable=?"
            ]
            params = [f"{mensaje} Comprobante: {consecutivo}"]
            if "comprobante_id" in cols_o:
                asignaciones.append("comprobante_id=?")
                params.append(comprobante_id)
            params.append(int(e["orden_id"]))

            con.execute(f"""
                UPDATE ordenes_produccion_v2
                SET {', '.join(asignaciones)}
                WHERE id=?
            """, params)
            con.commit()

        resultados.append(
            f"{e['numero_ejecucion']} -> {consecutivo} "
            f"(${valores['costo_total']:,.2f})"
        )

    return resultados


def main():
    print("=" * 72)
    print("SIGA ERP - INTEGRACIÓN CONTABLE DE PRODUCCIÓN")
    print("=" * 72)
    print(f"Base de datos: {RUTA_DB}")

    copia = respaldo()
    print(f"Respaldo: {copia}")

    con = conectar()
    try:
        necesarias = {
            "empresas_contables", "plan_cuentas", "reglas_contables",
            "tipos_comprobante", "periodos_contables",
            "centros_costo_contables", "comprobantes",
            "detalle_comprobante", "integracion_contable",
            "ejecuciones_produccion_v3", "ordenes_produccion_v2"
        }
        faltan = [t for t in necesarias if not tabla_existe(con, t)]
        if faltan:
            raise RuntimeError(
                "Faltan tablas necesarias: " + ", ".join(sorted(faltan))
            )

        con.execute("BEGIN IMMEDIATE")
        emp_id = empresa_id(con)
        instalar_centro(con, emp_id)
        instalar_cuentas(con, emp_id)
        instalar_reglas(con, emp_id)
        validar_instalacion(con, emp_id)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    contabilizadas = contabilizar_pendientes()

    with conectar() as con:
        integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
        reglas = con.execute("""
            SELECT secuencia, tipo_movimiento, cuenta_codigo,
                   fuente_valor, condicion
            FROM reglas_contables
            WHERE UPPER(evento)=?
              AND estado='ACTIVA'
            ORDER BY secuencia
        """, (EVENTO,)).fetchall()

    print("\nREGLAS INSTALADAS")
    for r in reglas:
        print(
            f"{r['secuencia']}. {r['tipo_movimiento']:<7} "
            f"{r['cuenta_codigo']:<8} <- {r['fuente_valor']} "
            f"[{r['condicion']}]"
        )

    print("\nEJECUCIONES PENDIENTES CONTABILIZADAS")
    if contabilizadas:
        for linea in contabilizadas:
            print("- " + linea)
    else:
        print("- No había ejecuciones pendientes.")

    print(f"\nIntegridad SQLite: {integridad}")
    print("=" * 72)
    print("INTEGRACIÓN CONTABLE DE PRODUCCIÓN INSTALADA CORRECTAMENTE")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n" + "=" * 72)
        print("ERROR - NO SE COMPLETÓ LA INTEGRACIÓN")
        print("=" * 72)
        print(error)
        print("\nLa base original permanece respaldada.")
        raise
    finally:
        input("\nPresione ENTER para cerrar...")
