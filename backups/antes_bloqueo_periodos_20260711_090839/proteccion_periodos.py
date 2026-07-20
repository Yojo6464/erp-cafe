"""
BME-ERP - Protección Central de Períodos Contables
Archivo: proteccion_periodos.py
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")
EMPRESA_CODIGO = "001"


class ErrorPeriodoContable(Exception):
    pass


class PeriodoCerradoError(ErrorPeriodoContable):
    pass


class PeriodoNoExisteError(ErrorPeriodoContable):
    pass


def conectar(ruta_db=RUTA_DB):
    ruta = Path(ruta_db)
    if not ruta.exists():
        raise ErrorPeriodoContable(
            f"No se encontró la base de datos:\n{ruta}"
        )
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def normalizar_fecha(fecha_valor=None):
    if fecha_valor is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(fecha_valor, datetime):
        return fecha_valor.strftime("%Y-%m-%d")
    if isinstance(fecha_valor, date):
        return fecha_valor.strftime("%Y-%m-%d")

    texto = str(fecha_valor).strip()
    if len(texto) < 10:
        raise ErrorPeriodoContable(
            f"Fecha contable inválida: {fecha_valor}"
        )

    try:
        datetime.strptime(texto[:10], "%Y-%m-%d")
    except ValueError as error:
        raise ErrorPeriodoContable(
            f"Fecha contable inválida: {fecha_valor}"
        ) from error

    return texto[:10]


def obtener_empresa_id(cursor, empresa_codigo=EMPRESA_CODIGO):
    cursor.execute("""
        SELECT id
        FROM empresas_contables
        WHERE codigo=?
          AND UPPER(COALESCE(estado, 'ACTIVA'))='ACTIVA'
        LIMIT 1
    """, (empresa_codigo,))
    fila = cursor.fetchone()
    if not fila:
        raise ErrorPeriodoContable(
            f"No existe empresa contable activa con código {empresa_codigo}."
        )
    return int(fila["id"])


def consultar_periodo(
    fecha_valor=None,
    empresa_codigo=EMPRESA_CODIGO,
    ruta_db=RUTA_DB
):
    fecha_texto = normalizar_fecha(fecha_valor)
    fecha_dt = datetime.strptime(fecha_texto, "%Y-%m-%d")

    conexion = conectar(ruta_db)
    try:
        cursor = conexion.cursor()
        empresa_id = obtener_empresa_id(cursor, empresa_codigo)

        cursor.execute("""
            SELECT
                id,
                empresa_id,
                anio,
                mes,
                fecha_inicio,
                fecha_fin,
                UPPER(COALESCE(estado, 'ABIERTO')) AS estado,
                COALESCE(fecha_cierre, '') AS fecha_cierre,
                COALESCE(usuario_cierre, '') AS usuario_cierre
            FROM periodos_contables
            WHERE empresa_id=?
              AND anio=?
              AND mes=?
            LIMIT 1
        """, (empresa_id, fecha_dt.year, fecha_dt.month))

        fila = cursor.fetchone()
        if not fila:
            raise PeriodoNoExisteError(
                f"No existe período contable para "
                f"{fecha_dt.year}-{fecha_dt.month:02d}."
            )
        return dict(fila)
    finally:
        conexion.close()


def validar_periodo_abierto(
    fecha_valor=None,
    empresa_codigo=EMPRESA_CODIGO,
    ruta_db=RUTA_DB
):
    fecha_texto = normalizar_fecha(fecha_valor)
    periodo = consultar_periodo(
        fecha_texto,
        empresa_codigo,
        ruta_db
    )

    estado = str(periodo["estado"]).upper()
    if estado != "ABIERTO":
        raise PeriodoCerradoError(
            "\n".join([
                "PERÍODO CONTABLE CERRADO",
                "",
                f"Fecha de la operación: {fecha_texto}",
                (
                    f"Período: {int(periodo['anio'])}-"
                    f"{int(periodo['mes']):02d}"
                ),
                f"Estado: {estado}",
                (
                    f"Fecha de cierre: "
                    f"{periodo.get('fecha_cierre') or 'No registrada'}"
                ),
                (
                    f"Usuario que cerró: "
                    f"{periodo.get('usuario_cierre') or 'No registrado'}"
                ),
                "",
                "No es posible registrar ni modificar movimientos.",
                "Solicite la reapertura al administrador."
            ])
        )
    return periodo


def periodo_abierto(
    fecha_valor=None,
    empresa_codigo=EMPRESA_CODIGO,
    ruta_db=RUTA_DB
):
    try:
        validar_periodo_abierto(
            fecha_valor,
            empresa_codigo,
            ruta_db
        )
        return True
    except ErrorPeriodoContable:
        return False


if __name__ == "__main__":
    fecha = datetime.now().strftime("%Y-%m-%d")
    try:
        periodo = validar_periodo_abierto(fecha)
        print("=" * 68)
        print("BME-ERP - PROTECCIÓN DE PERÍODOS")
        print("=" * 68)
        print(f"Fecha   : {fecha}")
        print(
            f"Período : {int(periodo['anio'])}-"
            f"{int(periodo['mes']):02d}"
        )
        print("Estado  : ABIERTO")
        print("=" * 68)
    except ErrorPeriodoContable as error:
        print(error)

    input("\nPresione ENTER para cerrar...")
