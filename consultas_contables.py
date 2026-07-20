"""
BME-ERP - Motor reutilizable de consultas contables
Archivo: consultas_contables.py

Versión compatible con la estructura real:
- comprobantes.tipo_comprobante_id
- tipos_comprobante.codigo / nombre
- comprobantes.documento_referencia
- comprobantes.modulo_origen
- comprobantes.tabla_origen
- comprobantes.tercero_id
- detalle_comprobante.tercero_id
- detalle_comprobante.centro_costo_id
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")


class ErrorConsultaContable(Exception):
    pass


def conectar(ruta_db: Path | str = RUTA_DB) -> sqlite3.Connection:
    ruta = Path(ruta_db)

    if not ruta.exists():
        raise ErrorConsultaContable(
            f"No se encontró la base de datos:\n{ruta}"
        )

    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def tabla_existe(cursor: sqlite3.Cursor, tabla: str) -> bool:
    cursor.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type='table' AND name=?
    """, (tabla,))
    return cursor.fetchone() is not None


def validar_estructura(ruta_db: Path | str = RUTA_DB) -> None:
    requeridas = {
        "comprobantes",
        "detalle_comprobante",
        "plan_cuentas",
        "tipos_comprobante",
        "terceros_contables",
        "centros_costo_contables",
    }

    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()

        faltantes = [
            tabla
            for tabla in sorted(requeridas)
            if not tabla_existe(cursor, tabla)
        ]

        if faltantes:
            raise ErrorConsultaContable(
                "Faltan tablas contables: "
                + ", ".join(faltantes)
            )

    finally:
        conexion.close()


def listar_tipos_comprobante(
    ruta_db: Path | str = RUTA_DB
) -> list[str]:
    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT DISTINCT codigo
            FROM tipos_comprobante
            WHERE UPPER(COALESCE(estado, 'ACTIVO'))='ACTIVO'
              AND TRIM(COALESCE(codigo, '')) <> ''
            ORDER BY codigo
        """)

        return [str(fila["codigo"]) for fila in cursor.fetchall()]

    finally:
        conexion.close()


def listar_modulos(
    ruta_db: Path | str = RUTA_DB
) -> list[str]:
    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT DISTINCT modulo_origen
            FROM comprobantes
            WHERE TRIM(COALESCE(modulo_origen, '')) <> ''
            ORDER BY modulo_origen
        """)

        return [
            str(fila["modulo_origen"])
            for fila in cursor.fetchall()
        ]

    finally:
        conexion.close()


def listar_cuentas(
    ruta_db: Path | str = RUTA_DB
) -> list[dict[str, Any]]:
    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                id,
                codigo,
                nombre
            FROM plan_cuentas
            WHERE UPPER(COALESCE(estado, 'ACTIVA'))='ACTIVA'
            ORDER BY codigo
        """)

        return [
            {
                "id": int(fila["id"]),
                "codigo": str(fila["codigo"]),
                "nombre": str(fila["nombre"]),
            }
            for fila in cursor.fetchall()
        ]

    finally:
        conexion.close()


def consultar_libro_diario(
    desde: str = "",
    hasta: str = "",
    tipo: str = "",
    modulo: str = "",
    cuenta_codigo: str = "",
    tercero: str = "",
    buscar: str = "",
    ruta_db: Path | str = RUTA_DB,
) -> list[dict[str, Any]]:
    validar_estructura(ruta_db)

    sql = """
        SELECT
            c.id AS comprobante_id,
            c.fecha,
            c.consecutivo,
            tc.codigo AS tipo,
            COALESCE(c.documento_referencia, '') AS documento,
            COALESCE(c.modulo_origen, '') AS modulo,
            COALESCE(c.estado, '') AS estado,
            COALESCE(tc.nombre, '') AS tipo_nombre,
            COALESCE(tc.empresa_id, c.empresa_id) AS empresa_id,
            COALESCE(t_comp.nombre_razon_social, '') AS tercero_comprobante,
            COALESCE(c.concepto, '') AS concepto,
            COALESCE(c.tabla_origen, '') AS tabla_origen,
            COALESCE(c.registro_origen_id, 0) AS registro_origen_id,
            COALESCE(c.usuario, '') AS usuario,
            d.id AS detalle_id,
            COALESCE(d.secuencia, 0) AS secuencia,
            pc.codigo AS cuenta,
            pc.nombre AS nombre_cuenta,
            COALESCE(d.descripcion, '') AS descripcion,
            COALESCE(
                t_det.nombre_razon_social,
                t_comp.nombre_razon_social,
                ''
            ) AS tercero,
            COALESCE(cc.codigo, '') AS centro_costo,
            COALESCE(cc.nombre, '') AS centro_costo_nombre,
            COALESCE(d.documento_referencia, '') AS documento_detalle,
            COALESCE(d.debito, 0) AS debito,
            COALESCE(d.credito, 0) AS credito
        FROM detalle_comprobante d
        INNER JOIN comprobantes c
            ON c.id=d.comprobante_id
        INNER JOIN tipos_comprobante tc
            ON tc.id=c.tipo_comprobante_id
        INNER JOIN plan_cuentas pc
            ON pc.id=d.cuenta_id
        LEFT JOIN terceros_contables t_comp
            ON t_comp.id=c.tercero_id
        LEFT JOIN terceros_contables t_det
            ON t_det.id=d.tercero_id
        LEFT JOIN centros_costo_contables cc
            ON cc.id=d.centro_costo_id
        WHERE 1=1
    """

    parametros: list[Any] = []

    if desde:
        sql += " AND date(c.fecha) >= date(?)"
        parametros.append(desde)

    if hasta:
        sql += " AND date(c.fecha) <= date(?)"
        parametros.append(hasta)

    if tipo and tipo != "TODOS":
        sql += " AND tc.codigo=?"
        parametros.append(tipo)

    if modulo and modulo != "TODOS":
        sql += " AND c.modulo_origen=?"
        parametros.append(modulo)

    if cuenta_codigo:
        sql += " AND pc.codigo LIKE ?"
        parametros.append(f"{cuenta_codigo}%")

    if tercero:
        sql += """
            AND (
                COALESCE(t_det.nombre_razon_social, '') LIKE ?
                OR COALESCE(t_comp.nombre_razon_social, '') LIKE ?
                OR COALESCE(t_det.numero_documento, '') LIKE ?
                OR COALESCE(t_comp.numero_documento, '') LIKE ?
            )
        """
        patron = f"%{tercero}%"
        parametros.extend([patron, patron, patron, patron])

    if buscar:
        sql += """
            AND (
                COALESCE(c.consecutivo, '') LIKE ?
                OR COALESCE(c.documento_referencia, '') LIKE ?
                OR COALESCE(c.concepto, '') LIKE ?
                OR COALESCE(c.tabla_origen, '') LIKE ?
                OR COALESCE(c.modulo_origen, '') LIKE ?
                OR COALESCE(d.descripcion, '') LIKE ?
                OR COALESCE(d.documento_referencia, '') LIKE ?
                OR pc.codigo LIKE ?
                OR pc.nombre LIKE ?
                OR COALESCE(t_det.nombre_razon_social, '') LIKE ?
                OR COALESCE(t_comp.nombre_razon_social, '') LIKE ?
            )
        """
        patron = f"%{buscar}%"
        parametros.extend([patron] * 11)

    sql += """
        ORDER BY
            datetime(c.fecha),
            c.id,
            d.secuencia,
            d.id
    """

    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)

        return [dict(fila) for fila in cursor.fetchall()]

    finally:
        conexion.close()


def consultar_comprobante(
    comprobante_id: int,
    ruta_db: Path | str = RUTA_DB,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    conexion = conectar(ruta_db)

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                c.id,
                c.consecutivo,
                c.fecha,
                c.concepto,
                c.documento_referencia,
                c.modulo_origen,
                c.tabla_origen,
                c.registro_origen_id,
                c.estado,
                c.total_debito,
                c.total_credito,
                c.usuario,
                c.contabilizado_en,
                tc.codigo AS tipo,
                tc.nombre AS tipo_nombre,
                COALESCE(t.nombre_razon_social, '') AS tercero
            FROM comprobantes c
            INNER JOIN tipos_comprobante tc
                ON tc.id=c.tipo_comprobante_id
            LEFT JOIN terceros_contables t
                ON t.id=c.tercero_id
            WHERE c.id=?
        """, (comprobante_id,))

        encabezado = cursor.fetchone()

        if not encabezado:
            raise ErrorConsultaContable(
                "No se encontró el comprobante seleccionado."
            )

        cursor.execute("""
            SELECT
                COALESCE(d.secuencia, 0) AS secuencia,
                pc.codigo AS cuenta,
                pc.nombre AS nombre_cuenta,
                COALESCE(d.descripcion, '') AS descripcion,
                COALESCE(t.nombre_razon_social, '') AS tercero,
                COALESCE(cc.codigo, '') AS centro_costo,
                COALESCE(cc.nombre, '') AS centro_costo_nombre,
                COALESCE(d.documento_referencia, '') AS documento_referencia,
                COALESCE(d.debito, 0) AS debito,
                COALESCE(d.credito, 0) AS credito
            FROM detalle_comprobante d
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            LEFT JOIN terceros_contables t
                ON t.id=d.tercero_id
            LEFT JOIN centros_costo_contables cc
                ON cc.id=d.centro_costo_id
            WHERE d.comprobante_id=?
            ORDER BY d.secuencia, d.id
        """, (comprobante_id,))

        detalle = [dict(fila) for fila in cursor.fetchall()]

        encabezado_dict = dict(encabezado)

        # Alias que espera la interfaz del Libro Diario.
        encabezado_dict["documento"] = (
            encabezado_dict.get("documento_referencia", "")
        )
        encabezado_dict["modulo"] = (
            encabezado_dict.get("modulo_origen", "")
        )
        encabezado_dict["origen"] = (
            f"{encabezado_dict.get('tabla_origen', '')}"
            f" #{encabezado_dict.get('registro_origen_id', '')}"
        ).strip()

        return encabezado_dict, detalle

    finally:
        conexion.close()
