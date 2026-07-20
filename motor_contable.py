"""
BME-ERP - Motor Contable Automático
Archivo: motor_contable.py

Este módulo:
- Genera comprobantes contables desde eventos del ERP.
- Aplica reglas parametrizadas desde reglas_contables.
- Valida débitos y créditos.
- Evita contabilizaciones duplicadas.
- Maneja consecutivos por tipo de comprobante y año.
- Registra auditoría e integración contable.
- Puede ser importado desde ventas.py, compras.py, pagos_cxc.py,
  pagos_cxp.py y movimientos_bancos.py.

Uso básico:

    from motor_contable import contabilizar_evento

    resultado = contabilizar_evento(
        evento="VENTA_CONTADO",
        valores={
            "total": 119000,
            "subtotal_sin_iva": 100000,
            "iva": 19000,
            "costo_total": 60000
        },
        concepto="Venta de café",
        modulo_origen="VENTAS",
        tabla_origen="ventas",
        registro_origen_id=15,
        tercero={
            "tipo_documento": "CC",
            "numero_documento": "12345678",
            "nombre_razon_social": "Cliente contado",
            "tipo_tercero": "CLIENTE"
        },
        usuario="admin"
    )

    print(resultado)
"""

import os
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

# BME-PROTECCION-PERIODOS - IMPORT
from proteccion_periodos import validar_periodo_abierto

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"
EMPRESA_CODIGO = "001"

TOLERANCIA_DESCUADRE = Decimal("0.01")


# ============================================================
# EXCEPCIONES
# ============================================================

class ErrorContable(Exception):
    """Error controlado del motor contable."""


class PeriodoCerradoError(ErrorContable):
    """La fecha pertenece a un período contable no disponible."""


class AsientoDescuadradoError(ErrorContable):
    """La suma de débitos y créditos no coincide."""


class ReglaContableError(ErrorContable):
    """Las reglas del evento son inválidas o están incompletas."""


class ContabilizacionDuplicadaError(ErrorContable):
    """El registro de origen ya fue contabilizado."""


# ============================================================
# UTILIDADES NUMÉRICAS
# ============================================================

def decimalizar(valor):
    if valor is None or valor == "":
        return Decimal("0.00")

    if isinstance(valor, Decimal):
        return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    try:
        return Decimal(str(valor)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError):
        raise ErrorContable(f"Valor numérico inválido: {valor}")


def a_float(valor):
    return float(decimalizar(valor))


# ============================================================
# CONEXIÓN
# ============================================================

def conectar(ruta_db=RUTA_DB):
    ruta = Path(ruta_db)

    if not ruta.exists():
        raise ErrorContable(
            f"No se encontró la base de datos:\n{ruta}"
        )

    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


# ============================================================
# CONSULTAS BASE
# ============================================================

def obtener_empresa_id(cursor, codigo=EMPRESA_CODIGO):
    cursor.execute("""
        SELECT id
        FROM empresas_contables
        WHERE codigo=? AND estado='ACTIVA'
    """, (codigo,))

    fila = cursor.fetchone()

    if not fila:
        raise ErrorContable(
            f"No existe una empresa contable activa con código {codigo}."
        )

    return int(fila["id"])


def obtener_periodo(cursor, empresa_id, fecha):
    fecha_dt = datetime.strptime(fecha[:10], "%Y-%m-%d")
    anio = fecha_dt.year
    mes = fecha_dt.month

    cursor.execute("""
        SELECT id, estado
        FROM periodos_contables
        WHERE empresa_id=? AND anio=? AND mes=?
    """, (empresa_id, anio, mes))

    fila = cursor.fetchone()

    if not fila:
        raise ErrorContable(
            f"No existe período contable para {anio}-{mes:02d}."
        )

    estado = str(fila["estado"]).upper()

    if estado != "ABIERTO":
        raise PeriodoCerradoError(
            f"El período {anio}-{mes:02d} está {estado}."
        )

    return int(fila["id"])


def obtener_tipo_comprobante(cursor, empresa_id, codigo):
    cursor.execute("""
        SELECT id, prefijo, longitud_consecutivo
        FROM tipos_comprobante
        WHERE empresa_id=? AND codigo=? AND estado='ACTIVO'
    """, (empresa_id, codigo))

    fila = cursor.fetchone()

    if not fila:
        raise ErrorContable(
            f"No existe el tipo de comprobante activo {codigo}."
        )

    return dict(fila)


def tipo_comprobante_por_evento(evento):
    mapa = {
        "VENTA_CONTADO": "CV",
        "VENTA_CREDITO": "CV",
        "COMPRA_CONTADO": "CC",
        "COMPRA_CREDITO": "CC",
        "RECAUDO_CXC": "CI",
        "PAGO_CXP": "CE",
        "CONSIGNACION": "CI",
        "RETIRO": "CE",
        "AJUSTE_CONTABLE": "AJ",
        "APERTURA": "AP",
        "CIERRE": "CL",
        "REVERSIÓN": "CR",
        "REVERSION": "CR"
    }

    return mapa.get(evento.upper(), "NC")


def obtener_reglas(cursor, empresa_id, evento):
    cursor.execute("""
        SELECT
            id,
            codigo,
            nombre,
            evento,
            secuencia,
            tipo_movimiento,
            cuenta_codigo,
            fuente_valor,
            condicion,
            descripcion_linea,
            requiere_tercero,
            requiere_centro_costo
        FROM reglas_contables
        WHERE empresa_id=?
          AND UPPER(evento)=UPPER(?)
          AND estado='ACTIVA'
        ORDER BY secuencia
    """, (empresa_id, evento))

    reglas = [dict(fila) for fila in cursor.fetchall()]

    if not reglas:
        raise ReglaContableError(
            f"No existen reglas contables activas para el evento {evento}."
        )

    return reglas


def obtener_cuenta(cursor, empresa_id, codigo):
    cursor.execute("""
        SELECT
            id,
            codigo,
            nombre,
            permite_movimiento,
            requiere_tercero,
            requiere_centro_costo,
            estado
        FROM plan_cuentas
        WHERE empresa_id=? AND codigo=?
    """, (empresa_id, codigo))

    fila = cursor.fetchone()

    if not fila:
        raise ReglaContableError(
            f"La cuenta {codigo} no existe en el plan de cuentas."
        )

    if str(fila["estado"]).upper() != "ACTIVA":
        raise ReglaContableError(
            f"La cuenta {codigo} está inactiva."
        )

    if int(fila["permite_movimiento"]) != 1:
        raise ReglaContableError(
            f"La cuenta {codigo} no permite movimientos."
        )

    return dict(fila)


# ============================================================
# TERCEROS Y CENTROS DE COSTO
# ============================================================

def obtener_o_crear_tercero(cursor, empresa_id, tercero):
    if not tercero:
        return None

    if isinstance(tercero, int):
        cursor.execute("""
            SELECT id
            FROM terceros_contables
            WHERE id=? AND empresa_id=?
        """, (tercero, empresa_id))

        fila = cursor.fetchone()

        if not fila:
            raise ErrorContable(
                f"No existe el tercero contable con ID {tercero}."
            )

        return int(fila["id"])

    tipo_documento = str(
        tercero.get("tipo_documento", "NIT")
    ).strip().upper()

    numero_documento = str(
        tercero.get("numero_documento", "")
    ).strip()

    nombre = str(
        tercero.get("nombre_razon_social", "")
    ).strip()

    if not numero_documento:
        raise ErrorContable(
            "El tercero debe tener número de documento."
        )

    if not nombre:
        raise ErrorContable(
            "El tercero debe tener nombre o razón social."
        )

    cursor.execute("""
        SELECT id
        FROM terceros_contables
        WHERE empresa_id=?
          AND tipo_documento=?
          AND numero_documento=?
    """, (
        empresa_id,
        tipo_documento,
        numero_documento
    ))

    fila = cursor.fetchone()

    if fila:
        tercero_id = int(fila["id"])

        cursor.execute("""
            UPDATE terceros_contables
            SET
                nombre_razon_social=?,
                tipo_tercero=?,
                direccion=?,
                telefono=?,
                correo=?,
                ciudad=?,
                estado='ACTIVO',
                actualizado_en=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            nombre,
            str(tercero.get("tipo_tercero", "OTRO")).upper(),
            str(tercero.get("direccion", "")),
            str(tercero.get("telefono", "")),
            str(tercero.get("correo", "")),
            str(tercero.get("ciudad", "")),
            tercero_id
        ))

        return tercero_id

    cursor.execute("""
        INSERT INTO terceros_contables(
            empresa_id,
            tipo_documento,
            numero_documento,
            digito_verificacion,
            nombre_razon_social,
            tipo_tercero,
            direccion,
            telefono,
            correo,
            ciudad,
            estado,
            origen_modulo,
            origen_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVO', ?, ?)
    """, (
        empresa_id,
        tipo_documento,
        numero_documento,
        str(tercero.get("digito_verificacion", "")),
        nombre,
        str(tercero.get("tipo_tercero", "OTRO")).upper(),
        str(tercero.get("direccion", "")),
        str(tercero.get("telefono", "")),
        str(tercero.get("correo", "")),
        str(tercero.get("ciudad", "")),
        str(tercero.get("origen_modulo", "")),
        tercero.get("origen_id")
    ))

    return int(cursor.lastrowid)


def obtener_centro_costo_id(cursor, empresa_id, centro_costo):
    if centro_costo is None or centro_costo == "":
        return None

    if isinstance(centro_costo, int):
        cursor.execute("""
            SELECT id
            FROM centros_costo_contables
            WHERE id=? AND empresa_id=? AND estado='ACTIVO'
        """, (centro_costo, empresa_id))
    else:
        cursor.execute("""
            SELECT id
            FROM centros_costo_contables
            WHERE empresa_id=?
              AND UPPER(codigo)=UPPER(?)
              AND estado='ACTIVO'
        """, (empresa_id, str(centro_costo).strip()))

    fila = cursor.fetchone()

    if not fila:
        raise ErrorContable(
            f"No existe el centro de costo {centro_costo}."
        )

    return int(fila["id"])


# ============================================================
# CONDICIONES DE REGLAS
# ============================================================

def evaluar_condicion(condicion, valores):
    condicion = str(condicion or "").strip()

    if condicion == "":
        return True

    operadores = [">=", "<=", "!=", "==", ">", "<"]

    operador = next(
        (op for op in operadores if op in condicion),
        None
    )

    if not operador:
        raise ReglaContableError(
            f"Condición no soportada: {condicion}"
        )

    izquierda, derecha = condicion.split(operador, 1)
    izquierda = izquierda.strip()
    derecha = derecha.strip()

    valor_izquierda = decimalizar(valores.get(izquierda, 0))

    try:
        valor_derecha = decimalizar(derecha)
    except ErrorContable:
        valor_derecha = decimalizar(valores.get(derecha, 0))

    comparaciones = {
        ">": valor_izquierda > valor_derecha,
        "<": valor_izquierda < valor_derecha,
        ">=": valor_izquierda >= valor_derecha,
        "<=": valor_izquierda <= valor_derecha,
        "==": valor_izquierda == valor_derecha,
        "!=": valor_izquierda != valor_derecha
    }

    return comparaciones[operador]


# ============================================================
# CONSECUTIVOS
# ============================================================

def siguiente_consecutivo(
    cursor,
    empresa_id,
    tipo_comprobante_id,
    anio
):
    cursor.execute("""
        INSERT OR IGNORE INTO consecutivos_contables(
            empresa_id,
            tipo_comprobante_id,
            anio,
            ultimo_numero
        )
        VALUES (?, ?, ?, 0)
    """, (
        empresa_id,
        tipo_comprobante_id,
        anio
    ))

    cursor.execute("""
        UPDATE consecutivos_contables
        SET
            ultimo_numero=ultimo_numero+1,
            actualizado_en=CURRENT_TIMESTAMP
        WHERE empresa_id=?
          AND tipo_comprobante_id=?
          AND anio=?
    """, (
        empresa_id,
        tipo_comprobante_id,
        anio
    ))

    cursor.execute("""
        SELECT ultimo_numero
        FROM consecutivos_contables
        WHERE empresa_id=?
          AND tipo_comprobante_id=?
          AND anio=?
    """, (
        empresa_id,
        tipo_comprobante_id,
        anio
    ))

    return int(cursor.fetchone()["ultimo_numero"])


# ============================================================
# CONTROL DE DUPLICADOS
# ============================================================

def buscar_integracion_existente(
    cursor,
    empresa_id,
    modulo,
    tabla_origen,
    registro_origen_id,
    evento
):
    cursor.execute("""
        SELECT
            id,
            comprobante_id,
            estado,
            mensaje
        FROM integracion_contable
        WHERE empresa_id=?
          AND UPPER(modulo)=UPPER(?)
          AND UPPER(tabla_origen)=UPPER(?)
          AND registro_origen_id=?
          AND UPPER(evento)=UPPER(?)
    """, (
        empresa_id,
        modulo,
        tabla_origen,
        registro_origen_id,
        evento
    ))

    fila = cursor.fetchone()
    return dict(fila) if fila else None


def registrar_integracion(
    cursor,
    empresa_id,
    modulo,
    tabla_origen,
    registro_origen_id,
    evento,
    comprobante_id,
    estado,
    mensaje=""
):
    cursor.execute("""
        INSERT INTO integracion_contable(
            empresa_id,
            modulo,
            tabla_origen,
            registro_origen_id,
            evento,
            comprobante_id,
            estado,
            mensaje,
            fecha_proceso
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        empresa_id,
        modulo,
        tabla_origen,
        registro_origen_id,
        evento,
        comprobante_id,
        estado,
        mensaje
    ))


# ============================================================
# AUDITORÍA
# ============================================================

def registrar_auditoria(
    cursor,
    empresa_id,
    usuario,
    accion,
    entidad,
    entidad_id,
    detalle
):
    cursor.execute("""
        INSERT INTO auditoria_contable(
            empresa_id,
            usuario,
            accion,
            entidad,
            entidad_id,
            detalle
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        empresa_id,
        usuario,
        accion,
        entidad,
        entidad_id,
        detalle
    ))


# ============================================================
# GENERACIÓN DE MOVIMIENTOS
# ============================================================

def construir_movimientos(
    cursor,
    empresa_id,
    reglas,
    valores,
    tercero_id=None,
    centro_costo_id=None,
    documento_referencia=""
):
    movimientos = []

    for regla in reglas:
        if not evaluar_condicion(regla["condicion"], valores):
            continue

        fuente = str(regla["fuente_valor"]).strip()

        if fuente not in valores:
            raise ReglaContableError(
                f"La regla {regla['codigo']} requiere el valor '{fuente}'."
            )

        valor = decimalizar(valores[fuente])

        if valor == 0:
            continue

        if valor < 0:
            raise ReglaContableError(
                f"El valor '{fuente}' no puede ser negativo."
            )

        cuenta = obtener_cuenta(
            cursor,
            empresa_id,
            regla["cuenta_codigo"]
        )

        requiere_tercero = (
            int(cuenta["requiere_tercero"]) == 1
            or int(regla["requiere_tercero"]) == 1
        )

        requiere_centro = (
            int(cuenta["requiere_centro_costo"]) == 1
            or int(regla["requiere_centro_costo"]) == 1
        )

        if requiere_tercero and not tercero_id:
            raise ReglaContableError(
                f"La cuenta {cuenta['codigo']} requiere tercero."
            )

        if requiere_centro and not centro_costo_id:
            raise ReglaContableError(
                f"La cuenta {cuenta['codigo']} requiere centro de costo."
            )

        debito = Decimal("0.00")
        credito = Decimal("0.00")

        if regla["tipo_movimiento"] == "DEBITO":
            debito = valor
        else:
            credito = valor

        descripcion = (
            str(regla["descripcion_linea"]).strip()
            or str(regla["nombre"]).strip()
        )

        movimientos.append({
            "secuencia": int(regla["secuencia"]),
            "cuenta_id": int(cuenta["id"]),
            "cuenta_codigo": cuenta["codigo"],
            "cuenta_nombre": cuenta["nombre"],
            "tercero_id": tercero_id,
            "centro_costo_id": centro_costo_id,
            "descripcion": descripcion,
            "documento_referencia": documento_referencia,
            "debito": debito,
            "credito": credito
        })

    if not movimientos:
        raise ReglaContableError(
            "Las reglas no generaron movimientos contables."
        )

    total_debito = sum(
        (m["debito"] for m in movimientos),
        Decimal("0.00")
    )

    total_credito = sum(
        (m["credito"] for m in movimientos),
        Decimal("0.00")
    )

    diferencia = abs(total_debito - total_credito)

    if diferencia > TOLERANCIA_DESCUADRE:
        raise AsientoDescuadradoError(
            f"Asiento descuadrado. "
            f"Débitos: {total_debito:,.2f} - "
            f"Créditos: {total_credito:,.2f} - "
            f"Diferencia: {diferencia:,.2f}"
        )

    return movimientos, total_debito, total_credito


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def contabilizar_evento(
    evento,
    valores,
    concepto,
    modulo_origen,
    tabla_origen,
    registro_origen_id,
    tercero=None,
    centro_costo=None,
    fecha=None,
    documento_referencia="",
    usuario="",
    empresa_codigo=EMPRESA_CODIGO,
    tipo_comprobante_codigo=None,
    ruta_db=RUTA_DB,
    conexion_externa=None
):
    """
    Genera un comprobante contable automático.

    Retorna un diccionario con:
    - ok
    - comprobante_id
    - consecutivo
    - total_debito
    - total_credito
    - mensaje
    """

    if not evento:
        raise ErrorContable("Debe indicar el evento contable.")

    if not concepto:
        raise ErrorContable("Debe indicar el concepto del comprobante.")

    if registro_origen_id is None:
        raise ErrorContable(
            "Debe indicar el ID del registro de origen."
        )

    evento = str(evento).strip().upper()
    modulo_origen = str(modulo_origen).strip().upper()
    tabla_origen = str(tabla_origen).strip()
    usuario = (
        str(usuario).strip()
        or os.environ.get("ERP_USUARIO", "")
        or os.environ.get("USERNAME", "SISTEMA")
    )

    fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datetime.strptime(fecha[:10], "%Y-%m-%d")

    conexion = None
    conexion_propia = conexion_externa is None
    row_factory_anterior = None

    try:
        if conexion_propia:
            # BME-PROTECCION-PERIODOS - MOTOR
            validar_periodo_abierto(
                fecha,
                empresa_codigo=empresa_codigo,
                ruta_db=ruta_db
            )

            conexion = conectar(ruta_db)
            cursor = conexion.cursor()
            cursor.execute("BEGIN IMMEDIATE")
        else:
            conexion = conexion_externa
            row_factory_anterior = conexion.row_factory
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

        empresa_id = obtener_empresa_id(
            cursor,
            empresa_codigo
        )

        existente = buscar_integracion_existente(
            cursor,
            empresa_id,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            evento
        )

        if existente:
            if existente["estado"] == "CONTABILIZADO":
                return {
                    "ok": True,
                    "duplicado": True,
                    "comprobante_id": existente["comprobante_id"],
                    "consecutivo": None,
                    "total_debito": 0,
                    "total_credito": 0,
                    "mensaje": (
                        "El registro ya había sido contabilizado."
                    )
                }

            raise ContabilizacionDuplicadaError(
                "Ya existe un intento de integración para este registro."
            )

        periodo_id = obtener_periodo(
            cursor,
            empresa_id,
            fecha
        )

        tercero_id = obtener_o_crear_tercero(
            cursor,
            empresa_id,
            tercero
        )

        centro_costo_id = obtener_centro_costo_id(
            cursor,
            empresa_id,
            centro_costo
        )

        reglas = obtener_reglas(
            cursor,
            empresa_id,
            evento
        )

        movimientos, total_debito, total_credito = construir_movimientos(
            cursor,
            empresa_id,
            reglas,
            valores,
            tercero_id,
            centro_costo_id,
            documento_referencia
        )

        codigo_tipo = (
            tipo_comprobante_codigo
            or tipo_comprobante_por_evento(evento)
        )

        tipo = obtener_tipo_comprobante(
            cursor,
            empresa_id,
            codigo_tipo
        )

        anio = int(fecha[:4])

        numero = siguiente_consecutivo(
            cursor,
            empresa_id,
            int(tipo["id"]),
            anio
        )

        consecutivo = (
            f"{tipo['prefijo']}-"
            f"{anio}-"
            f"{numero:0{int(tipo['longitud_consecutivo'])}d}"
        )

        cursor.execute("""
            INSERT INTO comprobantes(
                empresa_id,
                tipo_comprobante_id,
                periodo_id,
                numero,
                consecutivo,
                fecha,
                concepto,
                tercero_id,
                documento_referencia,
                modulo_origen,
                tabla_origen,
                registro_origen_id,
                estado,
                total_debito,
                total_credito,
                usuario,
                contabilizado_en
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'CONTABILIZADO', ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (
            empresa_id,
            int(tipo["id"]),
            periodo_id,
            numero,
            consecutivo,
            fecha,
            concepto,
            tercero_id,
            documento_referencia,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            a_float(total_debito),
            a_float(total_credito),
            usuario
        ))

        comprobante_id = int(cursor.lastrowid)

        for movimiento in movimientos:
            cursor.execute("""
                INSERT INTO detalle_comprobante(
                    comprobante_id,
                    secuencia,
                    cuenta_id,
                    tercero_id,
                    centro_costo_id,
                    descripcion,
                    documento_referencia,
                    debito,
                    credito
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comprobante_id,
                movimiento["secuencia"],
                movimiento["cuenta_id"],
                movimiento["tercero_id"],
                movimiento["centro_costo_id"],
                movimiento["descripcion"],
                movimiento["documento_referencia"],
                a_float(movimiento["debito"]),
                a_float(movimiento["credito"])
            ))

        registrar_integracion(
            cursor,
            empresa_id,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            evento,
            comprobante_id,
            "CONTABILIZADO",
            consecutivo
        )

        registrar_auditoria(
            cursor,
            empresa_id,
            usuario,
            "CONTABILIZAR",
            "COMPROBANTE",
            comprobante_id,
            (
                f"{consecutivo} | Evento {evento} | "
                f"Origen {modulo_origen}.{tabla_origen} "
                f"#{registro_origen_id}"
            )
        )

        if conexion_propia:
            conexion.commit()

        return {
            "ok": True,
            "duplicado": False,
            "comprobante_id": comprobante_id,
            "consecutivo": consecutivo,
            "total_debito": a_float(total_debito),
            "total_credito": a_float(total_credito),
            "mensaje": (
                f"Comprobante {consecutivo} generado correctamente."
            )
        }

    except Exception:
        if conexion and conexion_propia:
            conexion.rollback()
        raise

    finally:
        if conexion and not conexion_propia:
            conexion.row_factory = row_factory_anterior

        if conexion and conexion_propia:
            conexion.close()



# ============================================================
# REVERSIÓN DE COMPROBANTES
# ============================================================

def reversar_comprobante_origen(
    modulo_origen,
    tabla_origen,
    registro_origen_id,
    concepto,
    fecha=None,
    documento_referencia="",
    usuario="",
    empresa_codigo=EMPRESA_CODIGO,
    evento_origen=None,
    evento_reversion="REVERSIÓN_VENTA",
    ruta_db=RUTA_DB,
    conexion_externa=None
):
    """
    Genera un comprobante inverso del comprobante asociado al origen.
    Con conexion_externa participa en la transacción del módulo llamador.
    """

    fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datetime.strptime(fecha[:10], "%Y-%m-%d")

    modulo_origen = str(modulo_origen).strip().upper()
    tabla_origen = str(tabla_origen).strip()
    evento_reversion = str(evento_reversion).strip().upper()
    usuario = (
        str(usuario).strip()
        or os.environ.get("ERP_USUARIO", "")
        or os.environ.get("USERNAME", "SISTEMA")
    )

    conexion = None
    conexion_propia = conexion_externa is None
    row_factory_anterior = None

    try:
        if conexion_propia:
            validar_periodo_abierto(
                fecha,
                empresa_codigo=empresa_codigo,
                ruta_db=ruta_db
            )
            conexion = conectar(ruta_db)
            cursor = conexion.cursor()
            cursor.execute("BEGIN IMMEDIATE")
        else:
            conexion = conexion_externa
            row_factory_anterior = conexion.row_factory
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

        empresa_id = obtener_empresa_id(cursor, empresa_codigo)

        existente = buscar_integracion_existente(
            cursor,
            empresa_id,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            evento_reversion
        )

        if existente and existente["estado"] == "CONTABILIZADO":
            return {
                "ok": True,
                "duplicado": True,
                "comprobante_id": existente["comprobante_id"],
                "consecutivo": None,
                "mensaje": "La reversión ya había sido contabilizada."
            }

        parametros = [
            empresa_id,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id)
        ]

        sql = """
            SELECT
                ic.evento,
                ic.comprobante_id,
                c.consecutivo,
                c.tercero_id
            FROM integracion_contable ic
            INNER JOIN comprobantes c
                ON c.id = ic.comprobante_id
            WHERE ic.empresa_id=?
              AND UPPER(ic.modulo)=UPPER(?)
              AND UPPER(ic.tabla_origen)=UPPER(?)
              AND ic.registro_origen_id=?
              AND ic.estado='CONTABILIZADO'
        """

        if evento_origen:
            sql += " AND UPPER(ic.evento)=UPPER(?)"
            parametros.append(str(evento_origen).strip().upper())

        sql += " ORDER BY ic.id DESC LIMIT 1"

        cursor.execute(sql, parametros)
        origen = cursor.fetchone()

        if not origen:
            raise ErrorContable(
                "No se encontró el comprobante contable original de la venta."
            )

        cursor.execute("""
            SELECT
                secuencia,
                cuenta_id,
                tercero_id,
                centro_costo_id,
                descripcion,
                documento_referencia,
                debito,
                credito
            FROM detalle_comprobante
            WHERE comprobante_id=?
            ORDER BY secuencia
        """, (int(origen["comprobante_id"]),))

        detalles = cursor.fetchall()

        if not detalles:
            raise ErrorContable(
                "El comprobante original no tiene movimientos."
            )

        periodo_id = obtener_periodo(cursor, empresa_id, fecha)
        tipo = obtener_tipo_comprobante(cursor, empresa_id, "CR")
        anio = int(fecha[:4])

        numero = siguiente_consecutivo(
            cursor,
            empresa_id,
            int(tipo["id"]),
            anio
        )

        consecutivo = (
            f"{tipo['prefijo']}-"
            f"{anio}-"
            f"{numero:0{int(tipo['longitud_consecutivo'])}d}"
        )

        total_debito = sum(
            decimalizar(fila["credito"])
            for fila in detalles
        )
        total_credito = sum(
            decimalizar(fila["debito"])
            for fila in detalles
        )

        cursor.execute("""
            INSERT INTO comprobantes(
                empresa_id,
                tipo_comprobante_id,
                periodo_id,
                numero,
                consecutivo,
                fecha,
                concepto,
                tercero_id,
                documento_referencia,
                modulo_origen,
                tabla_origen,
                registro_origen_id,
                estado,
                total_debito,
                total_credito,
                usuario,
                contabilizado_en
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'CONTABILIZADO', ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (
            empresa_id,
            int(tipo["id"]),
            periodo_id,
            numero,
            consecutivo,
            fecha,
            concepto,
            origen["tercero_id"],
            documento_referencia or origen["consecutivo"],
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            a_float(total_debito),
            a_float(total_credito),
            usuario
        ))

        comprobante_id = int(cursor.lastrowid)

        for fila in detalles:
            cursor.execute("""
                INSERT INTO detalle_comprobante(
                    comprobante_id,
                    secuencia,
                    cuenta_id,
                    tercero_id,
                    centro_costo_id,
                    descripcion,
                    documento_referencia,
                    debito,
                    credito
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comprobante_id,
                int(fila["secuencia"]),
                int(fila["cuenta_id"]),
                fila["tercero_id"],
                fila["centro_costo_id"],
                f"REVERSIÓN: {fila['descripcion']}",
                documento_referencia or fila["documento_referencia"],
                a_float(fila["credito"]),
                a_float(fila["debito"])
            ))

        registrar_integracion(
            cursor,
            empresa_id,
            modulo_origen,
            tabla_origen,
            int(registro_origen_id),
            evento_reversion,
            comprobante_id,
            "CONTABILIZADO",
            consecutivo
        )

        registrar_auditoria(
            cursor,
            empresa_id,
            usuario,
            "REVERSAR",
            "COMPROBANTE",
            comprobante_id,
            (
                f"{consecutivo} revierte {origen['consecutivo']} | "
                f"Origen {modulo_origen}.{tabla_origen} "
                f"#{registro_origen_id}"
            )
        )

        if conexion_propia:
            conexion.commit()

        return {
            "ok": True,
            "duplicado": False,
            "comprobante_id": comprobante_id,
            "consecutivo": consecutivo,
            "comprobante_origen_id": int(origen["comprobante_id"]),
            "consecutivo_origen": origen["consecutivo"],
            "total_debito": a_float(total_debito),
            "total_credito": a_float(total_credito),
            "mensaje": (
                f"Comprobante de reversión {consecutivo} "
                "generado correctamente."
            )
        }

    except Exception:
        if conexion and conexion_propia:
            conexion.rollback()
        raise

    finally:
        if conexion and not conexion_propia:
            conexion.row_factory = row_factory_anterior

        if conexion and conexion_propia:
            conexion.close()


# ============================================================
# CONSULTA DE COMPROBANTE
# ============================================================

def consultar_comprobante(comprobante_id, ruta_db=RUTA_DB):
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
                tc.codigo AS tipo_codigo,
                tc.nombre AS tipo_nombre,
                t.nombre_razon_social AS tercero
            FROM comprobantes c
            INNER JOIN tipos_comprobante tc
                ON tc.id=c.tipo_comprobante_id
            LEFT JOIN terceros_contables t
                ON t.id=c.tercero_id
            WHERE c.id=?
        """, (comprobante_id,))

        encabezado = cursor.fetchone()

        if not encabezado:
            return None

        cursor.execute("""
            SELECT
                d.secuencia,
                pc.codigo AS cuenta_codigo,
                pc.nombre AS cuenta_nombre,
                d.descripcion,
                d.documento_referencia,
                d.debito,
                d.credito,
                t.nombre_razon_social AS tercero,
                cc.codigo AS centro_codigo,
                cc.nombre AS centro_nombre
            FROM detalle_comprobante d
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            LEFT JOIN terceros_contables t
                ON t.id=d.tercero_id
            LEFT JOIN centros_costo_contables cc
                ON cc.id=d.centro_costo_id
            WHERE d.comprobante_id=?
            ORDER BY d.secuencia
        """, (comprobante_id,))

        detalle = [dict(fila) for fila in cursor.fetchall()]

        return {
            "encabezado": dict(encabezado),
            "detalle": detalle
        }

    finally:
        conexion.close()


# ============================================================
# PRUEBA DEL MOTOR
# ============================================================

def probar_motor():
    """
    Ejecuta una prueba sin guardar datos.
    Verifica estructura, empresa, reglas y balance del asiento.
    """

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        empresa_id = obtener_empresa_id(cursor)
        reglas = obtener_reglas(
            cursor,
            empresa_id,
            "VENTA_CONTADO"
        )

        valores = {
            "total": 119000,
            "subtotal_sin_iva": 100000,
            "iva": 19000,
            "costo_total": 60000
        }

        # Para la prueba se usan IDs válidos de centro y tercero temporalmente nulos.
        # Como las reglas requieren centro y tercero en algunas cuentas,
        # se crean referencias solo dentro de una transacción que se revierte.
        cursor.execute("BEGIN")

        tercero_id = obtener_o_crear_tercero(
            cursor,
            empresa_id,
            {
                "tipo_documento": "CC",
                "numero_documento": "PRUEBA-MOTOR",
                "nombre_razon_social": "Tercero de prueba",
                "tipo_tercero": "CLIENTE"
            }
        )

        centro_id = obtener_centro_costo_id(
            cursor,
            empresa_id,
            "VENTAS"
        )

        movimientos, debito, credito = construir_movimientos(
            cursor,
            empresa_id,
            reglas,
            valores,
            tercero_id,
            centro_id,
            "PRUEBA"
        )

        conexion.rollback()

        print("=" * 68)
        print("PRUEBA DEL MOTOR CONTABLE")
        print("=" * 68)

        for movimiento in movimientos:
            print(
                f"{movimiento['secuencia']:>2}  "
                f"{movimiento['cuenta_codigo']:<8} "
                f"{movimiento['cuenta_nombre']:<32} "
                f"D {movimiento['debito']:>12,.2f}  "
                f"C {movimiento['credito']:>12,.2f}"
            )

        print("-" * 68)
        print(f"TOTAL DÉBITO : {debito:,.2f}")
        print(f"TOTAL CRÉDITO: {credito:,.2f}")
        print("RESULTADO     : MOTOR CONTABLE FUNCIONANDO")
        print("=" * 68)

    finally:
        conexion.close()


if __name__ == "__main__":
    try:
        probar_motor()
    except Exception as error:
        print("=" * 68)
        print("ERROR EN EL MOTOR CONTABLE")
        print("=" * 68)
        print(error)
        print("=" * 68)

    input("\nPresione ENTER para cerrar...")
