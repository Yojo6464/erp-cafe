
"""
SIGA ERP - Motor de Ejecución Real de Producción v3
Archivo: motor_ejecucion_produccion_v3.py
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from proteccion_periodos import validar_periodo_abierto

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"


class ErrorEjecucionProduccion(Exception):
    pass


def conectar() -> sqlite3.Connection:
    if not RUTA_DB.exists():
        raise ErrorEjecucionProduccion(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )

    con = sqlite3.connect(RUTA_DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 10000")
    return con


def usuario_actual() -> str:
    return (
        os.environ.get("ERP_USUARIO", "").strip()
        or os.environ.get("USERNAME", "usuario_local")
    )


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def numero_ejecucion(cursor: sqlite3.Cursor) -> str:
    fila = cursor.execute("""
        SELECT IFNULL(MAX(id), 0) + 1 AS siguiente
        FROM ejecuciones_produccion_v3
    """).fetchone()

    return (
        f"EP-{datetime.now().strftime('%Y%m%d')}-"
        f"{int(fila['siguiente']):05d}"
    )


def saldo_kardex(
    cursor: sqlite3.Cursor,
    producto: str,
    presentacion: str,
    lote: str,
) -> float:
    fila = cursor.execute("""
        SELECT IFNULL(SUM(entrada - salida), 0) AS saldo
        FROM kardex
        WHERE producto=?
          AND presentacion=?
          AND COALESCE(lote, '')=?
    """, (
        producto,
        presentacion,
        lote,
    )).fetchone()

    return float(fila["saldo"] or 0)


def registrar_kardex(
    cursor: sqlite3.Cursor,
    fecha: str,
    producto: str,
    presentacion: str,
    lote: str,
    movimiento: str,
    entrada: float,
    salida: float,
    costo: float,
    origen: str,
    observaciones: str,
) -> None:
    saldo = saldo_kardex(
        cursor,
        producto,
        presentacion,
        lote,
    )

    nuevo_saldo = saldo + entrada - salida

    cursor.execute("""
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fecha,
        producto,
        presentacion,
        movimiento,
        entrada,
        salida,
        nuevo_saldo,
        costo,
        lote,
        origen,
        observaciones,
    ))


def lotes_fifo(
    cursor: sqlite3.Cursor,
    producto: str,
    presentacion: str,
) -> list[sqlite3.Row]:
    return cursor.execute("""
        SELECT
            id,
            cantidad,
            COALESCE(lote, '') AS lote,
            COALESCE(costo_unitario, costo, 0) AS costo,
            COALESCE(fecha_ingreso, fecha, '') AS fecha_ingreso
        FROM inventario
        WHERE producto=?
          AND presentacion=?
          AND cantidad > 0
        ORDER BY
            CASE
                WHEN TRIM(COALESCE(fecha_ingreso, fecha, ''))=''
                THEN 1 ELSE 0
            END,
            date(COALESCE(fecha_ingreso, fecha, '')),
            id
    """, (
        producto,
        presentacion,
    )).fetchall()


def seleccionar_fifo(
    cursor: sqlite3.Cursor,
    producto: str,
    presentacion: str,
    cantidad_requerida: float,
) -> list[dict[str, Any]]:
    lotes = lotes_fifo(
        cursor,
        producto,
        presentacion,
    )

    disponible = sum(
        float(fila["cantidad"] or 0)
        for fila in lotes
    )

    if disponible + 1e-9 < cantidad_requerida:
        raise ErrorEjecucionProduccion(
            (
                f"Inventario insuficiente para "
                f"{producto} / {presentacion}.\n"
                f"Requerido: {cantidad_requerida:,.4f}\n"
                f"Disponible: {disponible:,.4f}"
            )
        )

    pendiente = cantidad_requerida
    seleccion = []

    for fila in lotes:
        if pendiente <= 1e-9:
            break

        usar = min(
            float(fila["cantidad"] or 0),
            pendiente,
        )

        seleccion.append({
            "inventario_id": int(fila["id"]),
            "cantidad": usar,
            "lote": str(fila["lote"] or ""),
            "costo": float(fila["costo"] or 0),
            "fecha_ingreso": str(
                fila["fecha_ingreso"] or ""
            ),
        })

        pendiente -= usar

    return seleccion


def obtener_orden(
    cursor: sqlite3.Cursor,
    orden_id: int,
) -> sqlite3.Row:
    fila = cursor.execute("""
        SELECT
            o.id,
            o.numero,
            o.fecha_emision,
            o.fecha_programada,
            o.producto_id,
            o.formula_id,
            o.cantidad_programada,
            o.cantidad_producida,
            o.unidad,
            o.lote_planeado,
            o.centro_trabajo,
            o.responsable,
            o.estado,
            p.nombre AS producto,
            p.presentacion,
            p.unidad AS unidad_producto,
            f.cantidad_base,
            f.rendimiento_pct,
            f.merma_estandar_pct
        FROM ordenes_produccion_v2 o
        INNER JOIN productos_produccion p
            ON p.id=o.producto_id
        INNER JOIN formulas_produccion f
            ON f.id=o.formula_id
        WHERE o.id=?
    """, (orden_id,)).fetchone()

    if not fila:
        raise ErrorEjecucionProduccion(
            "No se encontró la orden seleccionada."
        )

    if str(fila["estado"]).upper() not in (
        "LIBERADA",
        "EN PROCESO",
    ):
        raise ErrorEjecucionProduccion(
            (
                f"La orden está {fila['estado']}.\n"
                "Solo pueden ejecutarse órdenes LIBERADAS "
                "o EN PROCESO."
            )
        )

    return fila


def requerimientos_para_ejecucion(
    cursor: sqlite3.Cursor,
    orden_id: int,
    cantidad_producida: float,
    cantidad_programada: float,
) -> list[dict[str, Any]]:
    filas = cursor.execute("""
        SELECT
            id,
            componente,
            presentacion,
            tipo_componente,
            cantidad_teorica,
            unidad,
            merma_pct,
            costo_unitario_estandar
        FROM ordenes_requerimientos_v2
        WHERE orden_id=?
        ORDER BY id
    """, (orden_id,)).fetchall()

    if not filas:
        raise ErrorEjecucionProduccion(
            "La orden no tiene requerimientos calculados."
        )

    factor = (
        cantidad_producida / cantidad_programada
        if cantidad_programada > 0
        else 0
    )

    resultado = []

    for fila in filas:
        cantidad = float(
            fila["cantidad_teorica"] or 0
        ) * factor

        resultado.append({
            "requerimiento_id": int(fila["id"]),
            "producto": fila["componente"],
            "presentacion": fila["presentacion"],
            "tipo": fila["tipo_componente"],
            "cantidad": cantidad,
            "unidad": fila["unidad"],
            "merma_pct": float(fila["merma_pct"] or 0),
            "costo_estandar": float(
                fila["costo_unitario_estandar"] or 0
            ),
        })

    return resultado


def ejecutar_produccion(
    orden_id: int,
    fecha: str,
    cantidad_producida: float,
    cantidad_rechazada: float = 0,
    merma_real: float = 0,
    mano_obra_real: float = 0,
    costos_indirectos_reales: float = 0,
    responsable: str = "",
    observaciones: str = "",
) -> dict[str, Any]:
    fecha = str(fecha).strip()[:10]

    datetime.strptime(fecha, "%Y-%m-%d")

    if cantidad_producida <= 0:
        raise ErrorEjecucionProduccion(
            "La cantidad producida debe ser mayor que cero."
        )

    for nombre, valor in (
        ("Cantidad rechazada", cantidad_rechazada),
        ("Merma real", merma_real),
        ("Mano de obra", mano_obra_real),
        ("Costos indirectos", costos_indirectos_reales),
    ):
        if valor < 0:
            raise ErrorEjecucionProduccion(
                f"{nombre} no puede ser negativo."
            )

    validar_periodo_abierto(fecha)

    con = conectar()

    try:
        cur = con.cursor()
        cur.execute("BEGIN IMMEDIATE")

        orden = obtener_orden(cur, orden_id)

        pendiente_orden = (
            float(orden["cantidad_programada"] or 0)
            - float(orden["cantidad_producida"] or 0)
        )

        if cantidad_producida > pendiente_orden + 1e-9:
            raise ErrorEjecucionProduccion(
                (
                    "La cantidad producida supera el saldo "
                    "pendiente de la orden.\n\n"
                    f"Pendiente: {pendiente_orden:,.4f}"
                )
            )

        requerimientos = requerimientos_para_ejecucion(
            cur,
            orden_id,
            cantidad_producida,
            float(orden["cantidad_programada"]),
        )

        selecciones = []

        for req in requerimientos:
            lotes = seleccionar_fifo(
                cur,
                req["producto"],
                req["presentacion"],
                req["cantidad"],
            )

            selecciones.append((req, lotes))

        num_ejecucion = numero_ejecucion(cur)
        lote_pt = str(orden["lote_planeado"])

        ejecucion = cur.execute("""
            INSERT INTO ejecuciones_produccion_v3(
                orden_id,
                numero_ejecucion,
                fecha,
                cantidad_producida,
                cantidad_rechazada,
                merma_real,
                mano_obra_real,
                costos_indirectos_reales,
                lote_producto,
                responsable,
                observaciones,
                usuario,
                estado,
                estado_contable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'EJECUTADA', 'PENDIENTE')
        """, (
            orden_id,
            num_ejecucion,
            fecha,
            cantidad_producida,
            cantidad_rechazada,
            merma_real,
            mano_obra_real,
            costos_indirectos_reales,
            lote_pt,
            responsable,
            observaciones,
            usuario_actual(),
        ))

        ejecucion_id = int(ejecucion.lastrowid)
        costo_materiales = 0.0

        for req, lotes in selecciones:
            consumido_req = 0.0

            for lote in lotes:
                cantidad = float(lote["cantidad"])
                costo = float(lote["costo"])
                costo_total = cantidad * costo

                cur.execute("""
                    UPDATE inventario
                    SET cantidad=cantidad-?
                    WHERE id=?
                      AND cantidad>=?
                """, (
                    cantidad,
                    lote["inventario_id"],
                    cantidad,
                ))

                if cur.rowcount != 1:
                    raise ErrorEjecucionProduccion(
                        (
                            "El inventario cambió durante la operación. "
                            "Vuelva a intentarlo."
                        )
                    )

                cur.execute("""
                    INSERT INTO consumos_produccion_v3(
                        ejecucion_id,
                        orden_id,
                        requerimiento_id,
                        inventario_id,
                        producto,
                        presentacion,
                        lote,
                        cantidad,
                        costo_unitario,
                        costo_total,
                        fecha_ingreso_lote
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ejecucion_id,
                    orden_id,
                    req["requerimiento_id"],
                    lote["inventario_id"],
                    req["producto"],
                    req["presentacion"],
                    lote["lote"],
                    cantidad,
                    costo,
                    costo_total,
                    lote["fecha_ingreso"],
                ))

                registrar_kardex(
                    cur,
                    fecha,
                    req["producto"],
                    req["presentacion"],
                    lote["lote"],
                    "CONSUMO PRODUCCIÓN",
                    0,
                    cantidad,
                    costo,
                    orden["numero"],
                    f"Ejecución {num_ejecucion}",
                )

                cur.execute("""
                    INSERT INTO trazabilidad_produccion_v3(
                        ejecucion_id,
                        orden_id,
                        lote_producto_terminado,
                        producto_terminado,
                        presentacion_terminada,
                        lote_materia_prima,
                        materia_prima,
                        presentacion_materia_prima,
                        cantidad_consumida,
                        costo_consumido,
                        fecha
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ejecucion_id,
                    orden_id,
                    lote_pt,
                    orden["producto"],
                    orden["presentacion"],
                    lote["lote"],
                    req["producto"],
                    req["presentacion"],
                    cantidad,
                    costo_total,
                    fecha,
                ))

                consumido_req += cantidad
                costo_materiales += costo_total

            cur.execute("""
                UPDATE ordenes_requerimientos_v2
                SET cantidad_consumida=
                    COALESCE(cantidad_consumida, 0) + ?,
                    estado_disponibilidad='CONSUMIDO'
                WHERE id=?
            """, (
                consumido_req,
                req["requerimiento_id"],
            ))

        costo_total_real = (
            costo_materiales
            + mano_obra_real
            + costos_indirectos_reales
        )

        cantidad_neta = cantidad_producida - cantidad_rechazada

        if cantidad_neta <= 0:
            raise ErrorEjecucionProduccion(
                (
                    "La cantidad neta terminada debe ser mayor "
                    "que cero después de rechazos."
                )
            )

        costo_unitario_real = (
            costo_total_real / cantidad_neta
        )

        existente = cur.execute("""
            SELECT id, cantidad, COALESCE(costo_unitario, costo, 0) AS costo
            FROM inventario
            WHERE producto=?
              AND presentacion=?
              AND COALESCE(lote, '')=?
            LIMIT 1
        """, (
            orden["producto"],
            orden["presentacion"],
            lote_pt,
        )).fetchone()

        if existente:
            cantidad_anterior = float(
                existente["cantidad"] or 0
            )
            costo_anterior = float(
                existente["costo"] or 0
            )
            nueva_cantidad = cantidad_anterior + cantidad_neta
            nuevo_costo = (
                (
                    cantidad_anterior * costo_anterior
                    + cantidad_neta * costo_unitario_real
                )
                / nueva_cantidad
                if nueva_cantidad > 0
                else costo_unitario_real
            )

            cur.execute("""
                UPDATE inventario
                SET cantidad=?,
                    costo_unitario=?,
                    costo=?,
                    fecha_ingreso=?,
                    fecha=?,
                    numero_despacho=?,
                    despacho=?
                WHERE id=?
            """, (
                nueva_cantidad,
                nuevo_costo,
                nuevo_costo,
                fecha,
                fecha,
                orden["numero"],
                num_ejecucion,
                existente["id"],
            ))
        else:
            cur.execute("""
                INSERT INTO inventario(
                    producto,
                    presentacion,
                    cantidad,
                    lote,
                    costo_unitario,
                    fecha_ingreso,
                    numero_despacho,
                    stock_minimo,
                    costo,
                    fecha,
                    despacho
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """, (
                orden["producto"],
                orden["presentacion"],
                cantidad_neta,
                lote_pt,
                costo_unitario_real,
                fecha,
                orden["numero"],
                costo_unitario_real,
                fecha,
                num_ejecucion,
            ))

        registrar_kardex(
            cur,
            fecha,
            orden["producto"],
            orden["presentacion"],
            lote_pt,
            "ENTRADA PRODUCCIÓN",
            cantidad_neta,
            0,
            costo_unitario_real,
            orden["numero"],
            f"Ejecución {num_ejecucion}",
        )

        if merma_real > 0:
            cur.execute("""
                INSERT INTO mermas_produccion_v3(
                    ejecucion_id,
                    orden_id,
                    fecha,
                    tipo,
                    cantidad,
                    unidad,
                    costo_estimado,
                    motivo,
                    responsable
                )
                VALUES (?, ?, ?, 'MERMA GENERAL', ?, ?, ?, ?, ?)
            """, (
                ejecucion_id,
                orden_id,
                fecha,
                merma_real,
                orden["unidad"],
                (
                    merma_real * costo_unitario_real
                    if costo_unitario_real > 0
                    else 0
                ),
                observaciones,
                responsable,
            ))

        nueva_producida = (
            float(orden["cantidad_producida"] or 0)
            + cantidad_producida
        )

        estado_nuevo = (
            "TERMINADA"
            if nueva_producida
            >= float(orden["cantidad_programada"]) - 1e-9
            else "EN PROCESO"
        )

        cur.execute("""
            UPDATE ordenes_produccion_v2
            SET cantidad_producida=?,
                costo_materiales_real=
                    COALESCE(costo_materiales_real, 0) + ?,
                costo_mano_obra_real=
                    COALESCE(costo_mano_obra_real, 0) + ?,
                costo_indirecto_real=
                    COALESCE(costo_indirecto_real, 0) + ?,
                costo_total_real=
                    COALESCE(costo_total_real, 0) + ?,
                costo_unitario_real=?,
                merma_real=
                    COALESCE(merma_real, 0) + ?,
                estado=?,
                terminada_por=CASE
                    WHEN ?='TERMINADA'
                    THEN ? ELSE terminada_por END,
                terminada_en=CASE
                    WHEN ?='TERMINADA'
                    THEN ? ELSE terminada_en END,
                estado_contable='PENDIENTE',
                mensaje_contable='Pendiente de parametrización o proceso contable',
                actualizada_en=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            nueva_producida,
            costo_materiales,
            mano_obra_real,
            costos_indirectos_reales,
            costo_total_real,
            costo_unitario_real,
            merma_real,
            estado_nuevo,
            estado_nuevo,
            usuario_actual(),
            estado_nuevo,
            ahora(),
            orden_id,
        ))

        cur.execute("""
            UPDATE ejecuciones_produccion_v3
            SET costo_materiales_real=?,
                costo_total_real=?,
                costo_unitario_real=?
            WHERE id=?
        """, (
            costo_materiales,
            costo_total_real,
            costo_unitario_real,
            ejecucion_id,
        ))

        cur.execute("""
            INSERT INTO ordenes_historial_v2(
                orden_id,
                usuario,
                estado_anterior,
                estado_nuevo,
                accion,
                observaciones
            )
            VALUES (?, ?, ?, ?, 'EJECUTAR PRODUCCIÓN', ?)
        """, (
            orden_id,
            usuario_actual(),
            orden["estado"],
            estado_nuevo,
            (
                f"{num_ejecucion}; cantidad {cantidad_producida:.4f}; "
                f"costo {costo_total_real:.2f}"
            ),
        ))

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    contabilidad = contabilizar_si_configurado(
        ejecucion_id=ejecucion_id,
        orden_id=orden_id,
        fecha=fecha,
        numero_orden=orden["numero"],
        costo_materiales=costo_materiales,
        mano_obra=mano_obra_real,
        costos_indirectos=costos_indirectos_reales,
        costo_total=costo_total_real,
        centro_costo=orden["centro_trabajo"],
    )

    return {
        "ok": True,
        "ejecucion_id": ejecucion_id,
        "numero_ejecucion": num_ejecucion,
        "orden": orden["numero"],
        "estado_orden": estado_nuevo,
        "cantidad_bruta": cantidad_producida,
        "cantidad_neta": cantidad_neta,
        "cantidad_rechazada": cantidad_rechazada,
        "costo_materiales": costo_materiales,
        "mano_obra": mano_obra_real,
        "costos_indirectos": costos_indirectos_reales,
        "costo_total": costo_total_real,
        "costo_unitario": costo_unitario_real,
        "lote_producto": lote_pt,
        "contabilidad": contabilidad,
    }


def contabilizar_si_configurado(
    ejecucion_id: int,
    orden_id: int,
    fecha: str,
    numero_orden: str,
    costo_materiales: float,
    mano_obra: float,
    costos_indirectos: float,
    costo_total: float,
    centro_costo: str = "",
) -> dict[str, Any]:
    try:
        from motor_contable import contabilizar_evento
    except Exception as error:
        actualizar_estado_contable(
            ejecucion_id,
            orden_id,
            "PENDIENTE",
            f"No se pudo importar motor_contable.py: {error}",
        )
        return {
            "ok": False,
            "estado": "PENDIENTE",
            "mensaje": str(error),
        }

    con = conectar()

    try:
        fila = con.execute("""
            SELECT COUNT(*) AS cantidad
            FROM reglas_contables
            WHERE UPPER(evento)='PRODUCCION_TERMINADA'
              AND estado='ACTIVA'
        """).fetchone()

        configurado = int(fila["cantidad"] or 0) > 0

    finally:
        con.close()

    if not configurado:
        mensaje = (
            "No existen reglas contables activas para "
            "PRODUCCION_TERMINADA."
        )
        actualizar_estado_contable(
            ejecucion_id,
            orden_id,
            "PENDIENTE",
            mensaje,
        )
        return {
            "ok": False,
            "estado": "PENDIENTE",
            "mensaje": mensaje,
        }

    try:
        resultado = contabilizar_evento(
            evento="PRODUCCION_TERMINADA",
            valores={
                "costo_materiales": costo_materiales,
                "mano_obra": mano_obra,
                "costos_indirectos": costos_indirectos,
                "costo_total": costo_total,
            },
            concepto=(
                f"Terminación orden de producción {numero_orden}"
            ),
            modulo_origen="PRODUCCION",
            tabla_origen="ejecuciones_produccion_v3",
            registro_origen_id=ejecucion_id,
            documento_referencia=numero_orden,
            centro_costo=centro_costo or None,
            fecha=fecha,
            usuario=usuario_actual(),
        )

        actualizar_estado_contable(
            ejecucion_id,
            orden_id,
            "CONTABILIZADO",
            resultado.get("mensaje", ""),
            resultado.get("comprobante_id"),
        )

        return {
            "ok": True,
            "estado": "CONTABILIZADO",
            "mensaje": resultado.get("mensaje", ""),
            "comprobante_id": resultado.get(
                "comprobante_id"
            ),
        }

    except Exception as error:
        actualizar_estado_contable(
            ejecucion_id,
            orden_id,
            "PENDIENTE",
            str(error),
        )

        return {
            "ok": False,
            "estado": "PENDIENTE",
            "mensaje": str(error),
        }


def actualizar_estado_contable(
    ejecucion_id: int,
    orden_id: int,
    estado: str,
    mensaje: str,
    comprobante_id: int | None = None,
) -> None:
    con = conectar()

    try:
        con.execute("BEGIN IMMEDIATE")

        con.execute("""
            UPDATE ejecuciones_produccion_v3
            SET estado_contable=?,
                mensaje_contable=?,
                comprobante_id=?
            WHERE id=?
        """, (
            estado,
            mensaje,
            comprobante_id,
            ejecucion_id,
        ))

        con.execute("""
            UPDATE ordenes_produccion_v2
            SET estado_contable=?,
                mensaje_contable=?,
                comprobante_id=COALESCE(?, comprobante_id)
            WHERE id=?
        """, (
            estado,
            mensaje,
            comprobante_id,
            orden_id,
        ))

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()
