"""
BME-ERP - Inicialización del módulo de Contabilidad
Archivo: bd_contabilidad.py

Este programa:
1. Verifica la base de datos erp_cafe.db.
2. Crea un respaldo antes de realizar cambios.
3. Crea las tablas contables que no existan.
4. Carga tipos de comprobante, períodos, PUC base y reglas iniciales.
5. No elimina ni reemplaza tablas o datos existentes.
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_BASE = Path(r"C:\Users\jrive\visual")
RUTA_DB = RUTA_BASE / "erp_cafe.db"
CARPETA_RESPALDOS = RUTA_BASE / "backups"

EMPRESA_CODIGO = "001"
EMPRESA_NOMBRE = "Café Alto de la Cruz"
MONEDA = "COP"


# ============================================================
# UTILIDADES
# ============================================================

def conectar():
    conexion = sqlite3.connect(RUTA_DB)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA journal_mode = WAL")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def crear_respaldo():
    CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = CARPETA_RESPALDOS / f"erp_cafe_antes_contabilidad_{marca}.db"
    shutil.copy2(RUTA_DB, destino)
    return destino


def tabla_existe(cursor, nombre):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (nombre,)
    )
    return cursor.fetchone()[0] > 0


def ejecutar_script(cursor):
    # ========================================================
    # EMPRESAS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            nit TEXT DEFAULT '',
            direccion TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            correo TEXT DEFAULT '',
            moneda TEXT NOT NULL DEFAULT 'COP',
            estado TEXT NOT NULL DEFAULT 'ACTIVA',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT
        )
    """)

    # ========================================================
    # PLAN DE CUENTAS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            nivel INTEGER NOT NULL DEFAULT 1,
            cuenta_padre_id INTEGER,
            naturaleza TEXT NOT NULL
                CHECK (naturaleza IN ('DEBITO','CREDITO')),
            tipo_cuenta TEXT NOT NULL
                CHECK (
                    tipo_cuenta IN (
                        'ACTIVO','PASIVO','PATRIMONIO',
                        'INGRESO','COSTO','GASTO',
                        'ORDEN_DEUDORA','ORDEN_ACREEDORA'
                    )
                ),
            permite_movimiento INTEGER NOT NULL DEFAULT 0
                CHECK (permite_movimiento IN (0,1)),
            requiere_tercero INTEGER NOT NULL DEFAULT 0
                CHECK (requiere_tercero IN (0,1)),
            requiere_centro_costo INTEGER NOT NULL DEFAULT 0
                CHECK (requiere_centro_costo IN (0,1)),
            requiere_documento INTEGER NOT NULL DEFAULT 0
                CHECK (requiere_documento IN (0,1)),
            estado TEXT NOT NULL DEFAULT 'ACTIVA'
                CHECK (estado IN ('ACTIVA','INACTIVA')),
            observaciones TEXT DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT,
            UNIQUE (empresa_id, codigo),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id),
            FOREIGN KEY (cuenta_padre_id)
                REFERENCES plan_cuentas(id)
        )
    """)

    # ========================================================
    # TERCEROS CONTABLES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terceros_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_documento TEXT NOT NULL DEFAULT 'NIT',
            numero_documento TEXT NOT NULL,
            digito_verificacion TEXT DEFAULT '',
            nombre_razon_social TEXT NOT NULL,
            tipo_tercero TEXT NOT NULL DEFAULT 'OTRO',
            direccion TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            correo TEXT DEFAULT '',
            ciudad TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            origen_modulo TEXT DEFAULT '',
            origen_id INTEGER,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT,
            UNIQUE (empresa_id, tipo_documento, numero_documento),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # CENTROS DE COSTO CONTABLES
    # Se usa un nombre diferente porque el ERP ya posee
    # la tabla centros_costos para el módulo de costos.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS centros_costo_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            responsable TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            observaciones TEXT DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (empresa_id, codigo),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # TIPOS DE COMPROBANTE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipos_comprobante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            prefijo TEXT NOT NULL,
            naturaleza TEXT NOT NULL DEFAULT 'GENERAL',
            consecutivo_actual INTEGER NOT NULL DEFAULT 0,
            longitud_consecutivo INTEGER NOT NULL DEFAULT 6,
            permite_edicion INTEGER NOT NULL DEFAULT 1,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (empresa_id, codigo),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # PERÍODOS CONTABLES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS periodos_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            anio INTEGER NOT NULL,
            mes INTEGER NOT NULL
                CHECK (mes BETWEEN 1 AND 12),
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'ABIERTO'
                CHECK (estado IN ('ABIERTO','CERRADO','BLOQUEADO')),
            cerrado_en TEXT,
            cerrado_por TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            UNIQUE (empresa_id, anio, mes),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # COMPROBANTES Y DETALLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comprobantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_comprobante_id INTEGER NOT NULL,
            periodo_id INTEGER,
            numero INTEGER NOT NULL,
            consecutivo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            concepto TEXT NOT NULL,
            tercero_id INTEGER,
            documento_referencia TEXT DEFAULT '',
            modulo_origen TEXT DEFAULT 'CONTABILIDAD',
            tabla_origen TEXT DEFAULT '',
            registro_origen_id INTEGER,
            estado TEXT NOT NULL DEFAULT 'BORRADOR'
                CHECK (
                    estado IN (
                        'BORRADOR','CONTABILIZADO',
                        'ANULADO','REVERTIDO'
                    )
                ),
            total_debito REAL NOT NULL DEFAULT 0,
            total_credito REAL NOT NULL DEFAULT 0,
            usuario TEXT DEFAULT '',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            contabilizado_en TEXT,
            anulado_en TEXT,
            motivo_anulacion TEXT DEFAULT '',
            comprobante_reversion_id INTEGER,
            UNIQUE (empresa_id, tipo_comprobante_id, numero),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id),
            FOREIGN KEY (tipo_comprobante_id)
                REFERENCES tipos_comprobante(id),
            FOREIGN KEY (periodo_id)
                REFERENCES periodos_contables(id),
            FOREIGN KEY (tercero_id)
                REFERENCES terceros_contables(id),
            FOREIGN KEY (comprobante_reversion_id)
                REFERENCES comprobantes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_comprobante (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comprobante_id INTEGER NOT NULL,
            secuencia INTEGER NOT NULL,
            cuenta_id INTEGER NOT NULL,
            tercero_id INTEGER,
            centro_costo_id INTEGER,
            descripcion TEXT NOT NULL,
            documento_referencia TEXT DEFAULT '',
            debito REAL NOT NULL DEFAULT 0
                CHECK (debito >= 0),
            credito REAL NOT NULL DEFAULT 0
                CHECK (credito >= 0),
            base_impuesto REAL NOT NULL DEFAULT 0,
            porcentaje_impuesto REAL NOT NULL DEFAULT 0,
            fecha_vencimiento TEXT,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (comprobante_id, secuencia),
            CHECK (
                (debito > 0 AND credito = 0)
                OR
                (credito > 0 AND debito = 0)
            ),
            FOREIGN KEY (comprobante_id)
                REFERENCES comprobantes(id)
                ON DELETE CASCADE,
            FOREIGN KEY (cuenta_id)
                REFERENCES plan_cuentas(id),
            FOREIGN KEY (tercero_id)
                REFERENCES terceros_contables(id),
            FOREIGN KEY (centro_costo_id)
                REFERENCES centros_costo_contables(id)
        )
    """)

    # ========================================================
    # REGLAS DE CONTABILIZACIÓN
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reglas_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            evento TEXT NOT NULL,
            secuencia INTEGER NOT NULL DEFAULT 1,
            tipo_movimiento TEXT NOT NULL
                CHECK (tipo_movimiento IN ('DEBITO','CREDITO')),
            cuenta_codigo TEXT NOT NULL,
            fuente_valor TEXT NOT NULL,
            condicion TEXT DEFAULT '',
            descripcion_linea TEXT DEFAULT '',
            requiere_tercero INTEGER NOT NULL DEFAULT 0,
            requiere_centro_costo INTEGER NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'ACTIVA',
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (empresa_id, codigo, secuencia),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # CONSECUTIVOS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consecutivos_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            tipo_comprobante_id INTEGER NOT NULL,
            anio INTEGER NOT NULL,
            ultimo_numero INTEGER NOT NULL DEFAULT 0,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (empresa_id, tipo_comprobante_id, anio),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id),
            FOREIGN KEY (tipo_comprobante_id)
                REFERENCES tipos_comprobante(id)
        )
    """)

    # ========================================================
    # CIERRES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cierres_contables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            periodo_id INTEGER NOT NULL,
            fecha_cierre TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'CERRADO',
            comprobante_cierre_id INTEGER,
            observaciones TEXT DEFAULT '',
            UNIQUE (empresa_id, periodo_id),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id),
            FOREIGN KEY (periodo_id)
                REFERENCES periodos_contables(id),
            FOREIGN KEY (comprobante_cierre_id)
                REFERENCES comprobantes(id)
        )
    """)

    # ========================================================
    # AUDITORÍA CONTABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria_contable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT '',
            accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            entidad_id INTEGER,
            detalle TEXT DEFAULT '',
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id)
        )
    """)

    # ========================================================
    # INTEGRACIÓN / CONTROL DE DUPLICADOS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integracion_contable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            modulo TEXT NOT NULL,
            tabla_origen TEXT NOT NULL,
            registro_origen_id INTEGER NOT NULL,
            evento TEXT NOT NULL,
            comprobante_id INTEGER,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            mensaje TEXT DEFAULT '',
            fecha_proceso TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (
                empresa_id,
                modulo,
                tabla_origen,
                registro_origen_id,
                evento
            ),
            FOREIGN KEY (empresa_id)
                REFERENCES empresas_contables(id),
            FOREIGN KEY (comprobante_id)
                REFERENCES comprobantes(id)
        )
    """)

    # ========================================================
    # ÍNDICES
    # ========================================================

    indices = [
        """
        CREATE INDEX IF NOT EXISTS idx_plan_cuentas_codigo
        ON plan_cuentas(empresa_id, codigo)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_comprobantes_fecha
        ON comprobantes(empresa_id, fecha)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_comprobantes_origen
        ON comprobantes(
            empresa_id, modulo_origen,
            tabla_origen, registro_origen_id
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_detalle_cuenta
        ON detalle_comprobante(cuenta_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_detalle_tercero
        ON detalle_comprobante(tercero_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_detalle_centro
        ON detalle_comprobante(centro_costo_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_terceros_documento
        ON terceros_contables(
            empresa_id, tipo_documento, numero_documento
        )
        """
    ]

    for sentencia in indices:
        cursor.execute(sentencia)


def obtener_empresa_id(cursor):
    cursor.execute("""
        INSERT OR IGNORE INTO empresas_contables(
            codigo, nombre, moneda, estado
        )
        VALUES (?, ?, ?, 'ACTIVA')
    """, (EMPRESA_CODIGO, EMPRESA_NOMBRE, MONEDA))

    cursor.execute("""
        SELECT id
        FROM empresas_contables
        WHERE codigo=?
    """, (EMPRESA_CODIGO,))

    return cursor.fetchone()[0]


def cargar_tipos_comprobante(cursor, empresa_id):
    tipos = [
        ("AP", "Comprobante de apertura", "AP", "APERTURA"),
        ("CC", "Comprobante de compras", "CC", "COMPRAS"),
        ("CV", "Comprobante de ventas", "CV", "VENTAS"),
        ("CE", "Comprobante de egreso", "CE", "EGRESO"),
        ("CI", "Comprobante de ingreso", "CI", "INGRESO"),
        ("NC", "Nota contable", "NC", "GENERAL"),
        ("AJ", "Comprobante de ajustes", "AJ", "AJUSTE"),
        ("CR", "Comprobante de reversión", "CR", "REVERSION"),
        ("CL", "Comprobante de cierre", "CL", "CIERRE")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO tipos_comprobante(
            empresa_id, codigo, nombre, prefijo,
            naturaleza, consecutivo_actual,
            longitud_consecutivo, permite_edicion, estado
        )
        VALUES (?, ?, ?, ?, ?, 0, 6, 1, 'ACTIVO')
    """, [
        (empresa_id, codigo, nombre, prefijo, naturaleza)
        for codigo, nombre, prefijo, naturaleza in tipos
    ])


def cargar_periodos(cursor, empresa_id):
    anio = datetime.now().year

    for mes in range(1, 13):
        if mes == 12:
            siguiente = datetime(anio + 1, 1, 1)
        else:
            siguiente = datetime(anio, mes + 1, 1)

        inicio = datetime(anio, mes, 1)
        fin = siguiente.replace(day=1)
        fin = fin.fromordinal(fin.toordinal() - 1)

        cursor.execute("""
            INSERT OR IGNORE INTO periodos_contables(
                empresa_id, anio, mes,
                fecha_inicio, fecha_fin, estado
            )
            VALUES (?, ?, ?, ?, ?, 'ABIERTO')
        """, (
            empresa_id,
            anio,
            mes,
            inicio.strftime("%Y-%m-%d"),
            fin.strftime("%Y-%m-%d")
        ))


def cargar_centros_costo(cursor, empresa_id):
    centros = [
        ("ADM", "Administración", "ACTIVO"),
        ("PROD", "Producción", "ACTIVO"),
        ("VENTAS", "Ventas y comercial", "ACTIVO"),
        ("PV", "Punto de venta", "ACTIVO")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO centros_costo_contables(
            empresa_id, codigo, nombre, estado
        )
        VALUES (?, ?, ?, ?)
    """, [
        (empresa_id, codigo, nombre, estado)
        for codigo, nombre, estado in centros
    ])


def cargar_puc_base(cursor, empresa_id):
    cuentas = [
        # código, nombre, nivel, padre, naturaleza, tipo, movimiento, tercero, centro
        ("1", "ACTIVO", 1, None, "DEBITO", "ACTIVO", 0, 0, 0),
        ("11", "DISPONIBLE", 2, "1", "DEBITO", "ACTIVO", 0, 0, 0),
        ("1105", "CAJA", 3, "11", "DEBITO", "ACTIVO", 0, 0, 0),
        ("110505", "Caja general", 4, "1105", "DEBITO", "ACTIVO", 1, 0, 0),
        ("1110", "BANCOS", 3, "11", "DEBITO", "ACTIVO", 0, 0, 0),
        ("111005", "Bancos moneda nacional", 4, "1110", "DEBITO", "ACTIVO", 1, 0, 0),
        ("13", "DEUDORES", 2, "1", "DEBITO", "ACTIVO", 0, 0, 0),
        ("1305", "CLIENTES", 3, "13", "DEBITO", "ACTIVO", 0, 0, 0),
        ("130505", "Clientes nacionales", 4, "1305", "DEBITO", "ACTIVO", 1, 1, 0),
        ("1355", "ANTICIPO DE IMPUESTOS", 3, "13", "DEBITO", "ACTIVO", 0, 0, 0),
        ("135515", "Retención en la fuente", 4, "1355", "DEBITO", "ACTIVO", 1, 1, 0),
        ("14", "INVENTARIOS", 2, "1", "DEBITO", "ACTIVO", 0, 0, 0),
        ("1405", "MATERIAS PRIMAS", 3, "14", "DEBITO", "ACTIVO", 0, 0, 0),
        ("140505", "Materias primas", 4, "1405", "DEBITO", "ACTIVO", 1, 0, 1),
        ("1435", "MERCANCÍAS NO FABRICADAS", 3, "14", "DEBITO", "ACTIVO", 0, 0, 0),
        ("143505", "Mercancías para la venta", 4, "1435", "DEBITO", "ACTIVO", 1, 0, 1),
        ("2", "PASIVO", 1, None, "CREDITO", "PASIVO", 0, 0, 0),
        ("22", "PROVEEDORES", 2, "2", "CREDITO", "PASIVO", 0, 0, 0),
        ("2205", "PROVEEDORES NACIONALES", 3, "22", "CREDITO", "PASIVO", 0, 0, 0),
        ("220505", "Proveedores nacionales", 4, "2205", "CREDITO", "PASIVO", 1, 1, 0),
        ("23", "CUENTAS POR PAGAR", 2, "2", "CREDITO", "PASIVO", 0, 0, 0),
        ("2335", "COSTOS Y GASTOS POR PAGAR", 3, "23", "CREDITO", "PASIVO", 0, 0, 0),
        ("233595", "Otros costos y gastos por pagar", 4, "2335", "CREDITO", "PASIVO", 1, 1, 1),
        ("24", "IMPUESTOS, GRAVÁMENES Y TASAS", 2, "2", "CREDITO", "PASIVO", 0, 0, 0),
        ("2408", "IMPUESTO SOBRE LAS VENTAS", 3, "24", "CREDITO", "PASIVO", 0, 0, 0),
        ("240805", "IVA generado", 4, "2408", "CREDITO", "PASIVO", 1, 1, 0),
        ("240810", "IVA descontable", 4, "2408", "DEBITO", "PASIVO", 1, 1, 0),
        ("3", "PATRIMONIO", 1, None, "CREDITO", "PATRIMONIO", 0, 0, 0),
        ("31", "CAPITAL SOCIAL", 2, "3", "CREDITO", "PATRIMONIO", 0, 0, 0),
        ("3105", "CAPITAL SUSCRITO Y PAGADO", 3, "31", "CREDITO", "PATRIMONIO", 0, 0, 0),
        ("310505", "Capital autorizado", 4, "3105", "CREDITO", "PATRIMONIO", 1, 0, 0),
        ("36", "RESULTADOS DEL EJERCICIO", 2, "3", "CREDITO", "PATRIMONIO", 0, 0, 0),
        ("3605", "UTILIDAD DEL EJERCICIO", 3, "36", "CREDITO", "PATRIMONIO", 0, 0, 0),
        ("360505", "Utilidad del ejercicio", 4, "3605", "CREDITO", "PATRIMONIO", 1, 0, 0),
        ("4", "INGRESOS", 1, None, "CREDITO", "INGRESO", 0, 0, 0),
        ("41", "OPERACIONALES", 2, "4", "CREDITO", "INGRESO", 0, 0, 0),
        ("4135", "COMERCIO AL POR MAYOR Y MENOR", 3, "41", "CREDITO", "INGRESO", 0, 0, 0),
        ("413595", "Venta de productos", 4, "4135", "CREDITO", "INGRESO", 1, 1, 1),
        ("42", "NO OPERACIONALES", 2, "4", "CREDITO", "INGRESO", 0, 0, 0),
        ("4210", "FINANCIEROS", 3, "42", "CREDITO", "INGRESO", 0, 0, 0),
        ("421005", "Rendimientos financieros", 4, "4210", "CREDITO", "INGRESO", 1, 0, 0),
        ("5", "GASTOS", 1, None, "DEBITO", "GASTO", 0, 0, 0),
        ("51", "OPERACIONALES DE ADMINISTRACIÓN", 2, "5", "DEBITO", "GASTO", 0, 0, 0),
        ("5105", "GASTOS DE PERSONAL", 3, "51", "DEBITO", "GASTO", 0, 0, 0),
        ("510506", "Sueldos", 4, "5105", "DEBITO", "GASTO", 1, 1, 1),
        ("5110", "HONORARIOS", 3, "51", "DEBITO", "GASTO", 0, 0, 0),
        ("511005", "Junta directiva", 4, "5110", "DEBITO", "GASTO", 1, 1, 1),
        ("5135", "SERVICIOS", 3, "51", "DEBITO", "GASTO", 0, 0, 0),
        ("513505", "Aseo y vigilancia", 4, "5135", "DEBITO", "GASTO", 1, 1, 1),
        ("513525", "Acueducto y alcantarillado", 4, "5135", "DEBITO", "GASTO", 1, 1, 1),
        ("513530", "Energía eléctrica", 4, "5135", "DEBITO", "GASTO", 1, 1, 1),
        ("513535", "Teléfono e internet", 4, "5135", "DEBITO", "GASTO", 1, 1, 1),
        ("52", "OPERACIONALES DE VENTAS", 2, "5", "DEBITO", "GASTO", 0, 0, 0),
        ("5295", "DIVERSOS", 3, "52", "DEBITO", "GASTO", 0, 0, 0),
        ("529595", "Otros gastos de ventas", 4, "5295", "DEBITO", "GASTO", 1, 1, 1),
        ("53", "NO OPERACIONALES", 2, "5", "DEBITO", "GASTO", 0, 0, 0),
        ("5305", "FINANCIEROS", 3, "53", "DEBITO", "GASTO", 0, 0, 0),
        ("530505", "Gastos bancarios", 4, "5305", "DEBITO", "GASTO", 1, 0, 0),
        ("6", "COSTOS DE VENTAS", 1, None, "DEBITO", "COSTO", 0, 0, 0),
        ("61", "COSTO DE VENTAS", 2, "6", "DEBITO", "COSTO", 0, 0, 0),
        ("6135", "COMERCIO AL POR MAYOR Y MENOR", 3, "61", "DEBITO", "COSTO", 0, 0, 0),
        ("613595", "Costo de productos vendidos", 4, "6135", "DEBITO", "COSTO", 1, 0, 1)
    ]

    ids_por_codigo = {}

    for cuenta in cuentas:
        (
            codigo, nombre, nivel, padre_codigo, naturaleza,
            tipo_cuenta, movimiento, tercero, centro
        ) = cuenta

        padre_id = ids_por_codigo.get(padre_codigo)

        cursor.execute("""
            INSERT OR IGNORE INTO plan_cuentas(
                empresa_id, codigo, nombre, nivel,
                cuenta_padre_id, naturaleza, tipo_cuenta,
                permite_movimiento, requiere_tercero,
                requiere_centro_costo, requiere_documento,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'ACTIVA')
        """, (
            empresa_id, codigo, nombre, nivel,
            padre_id, naturaleza, tipo_cuenta,
            movimiento, tercero, centro
        ))

        cursor.execute("""
            SELECT id
            FROM plan_cuentas
            WHERE empresa_id=? AND codigo=?
        """, (empresa_id, codigo))

        ids_por_codigo[codigo] = cursor.fetchone()[0]


def cargar_reglas_iniciales(cursor, empresa_id):
    reglas = [
        # código, nombre, evento, secuencia, movimiento, cuenta, fuente, condición, descripción
        ("VENTA_CONTADO", "Venta de contado", "VENTA_CONTADO", 1,
         "DEBITO", "110505", "total", "", "Ingreso de venta de contado"),
        ("VENTA_CONTADO", "Venta de contado", "VENTA_CONTADO", 2,
         "CREDITO", "413595", "subtotal_sin_iva", "", "Ingreso por venta"),
        ("VENTA_CONTADO", "Venta de contado", "VENTA_CONTADO", 3,
         "CREDITO", "240805", "iva", "iva > 0", "IVA generado"),
        ("VENTA_CONTADO", "Venta de contado", "VENTA_CONTADO", 4,
         "DEBITO", "613595", "costo_total", "costo_total > 0", "Costo de venta"),
        ("VENTA_CONTADO", "Venta de contado", "VENTA_CONTADO", 5,
         "CREDITO", "143505", "costo_total", "costo_total > 0", "Salida de inventario"),

        ("VENTA_CREDITO", "Venta a crédito", "VENTA_CREDITO", 1,
         "DEBITO", "130505", "total", "", "Cuenta por cobrar al cliente"),
        ("VENTA_CREDITO", "Venta a crédito", "VENTA_CREDITO", 2,
         "CREDITO", "413595", "subtotal_sin_iva", "", "Ingreso por venta"),
        ("VENTA_CREDITO", "Venta a crédito", "VENTA_CREDITO", 3,
         "CREDITO", "240805", "iva", "iva > 0", "IVA generado"),
        ("VENTA_CREDITO", "Venta a crédito", "VENTA_CREDITO", 4,
         "DEBITO", "613595", "costo_total", "costo_total > 0", "Costo de venta"),
        ("VENTA_CREDITO", "Venta a crédito", "VENTA_CREDITO", 5,
         "CREDITO", "143505", "costo_total", "costo_total > 0", "Salida de inventario"),

        ("COMPRA_CONTADO", "Compra de contado", "COMPRA_CONTADO", 1,
         "DEBITO", "143505", "subtotal", "", "Compra de inventario"),
        ("COMPRA_CONTADO", "Compra de contado", "COMPRA_CONTADO", 2,
         "DEBITO", "240810", "iva", "iva > 0", "IVA descontable"),
        ("COMPRA_CONTADO", "Compra de contado", "COMPRA_CONTADO", 3,
         "CREDITO", "111005", "total", "", "Pago de compra"),

        ("COMPRA_CREDITO", "Compra a crédito", "COMPRA_CREDITO", 1,
         "DEBITO", "143505", "subtotal", "", "Compra de inventario"),
        ("COMPRA_CREDITO", "Compra a crédito", "COMPRA_CREDITO", 2,
         "DEBITO", "240810", "iva", "iva > 0", "IVA descontable"),
        ("COMPRA_CREDITO", "Compra a crédito", "COMPRA_CREDITO", 3,
         "CREDITO", "220505", "total", "", "Cuenta por pagar al proveedor"),

        ("RECAUDO_CXC", "Recaudo de cartera", "RECAUDO_CXC", 1,
         "DEBITO", "111005", "valor", "", "Ingreso a bancos"),
        ("RECAUDO_CXC", "Recaudo de cartera", "RECAUDO_CXC", 2,
         "CREDITO", "130505", "valor", "", "Disminución de cartera"),

        ("PAGO_CXP", "Pago a proveedor", "PAGO_CXP", 1,
         "DEBITO", "220505", "valor", "", "Disminución de cuenta por pagar"),
        ("PAGO_CXP", "Pago a proveedor", "PAGO_CXP", 2,
         "CREDITO", "111005", "valor", "", "Salida de bancos")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO reglas_contables(
            empresa_id, codigo, nombre, evento,
            secuencia, tipo_movimiento, cuenta_codigo,
            fuente_valor, condicion, descripcion_linea,
            estado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVA')
    """, [
        (empresa_id,) + regla
        for regla in reglas
    ])


def registrar_auditoria(cursor, empresa_id, detalle):
    cursor.execute("""
        INSERT INTO auditoria_contable(
            empresa_id, usuario, accion,
            entidad, entidad_id, detalle
        )
        VALUES (?, ?, 'INICIALIZAR', 'BASE_CONTABLE', NULL, ?)
    """, (
        empresa_id,
        os.environ.get("USERNAME", "SISTEMA"),
        detalle
    ))


def validar_estructura(cursor):
    tablas_requeridas = [
        "empresas_contables",
        "plan_cuentas",
        "terceros_contables",
        "centros_costo_contables",
        "tipos_comprobante",
        "periodos_contables",
        "comprobantes",
        "detalle_comprobante",
        "reglas_contables",
        "consecutivos_contables",
        "cierres_contables",
        "auditoria_contable",
        "integracion_contable"
    ]

    faltantes = [
        nombre
        for nombre in tablas_requeridas
        if not tabla_existe(cursor, nombre)
    ]

    if faltantes:
        raise RuntimeError(
            "No se crearon correctamente estas tablas: "
            + ", ".join(faltantes)
        )

    return tablas_requeridas


def mostrar_resumen(cursor, tablas):
    print("\n" + "=" * 66)
    print("MÓDULO DE CONTABILIDAD INICIALIZADO CORRECTAMENTE")
    print("=" * 66)
    print(f"Base de datos : {RUTA_DB}")
    print(f"Empresa       : {EMPRESA_NOMBRE}")
    print(f"Tablas creadas/verificadas: {len(tablas)}")

    cursor.execute("SELECT COUNT(*) FROM plan_cuentas")
    print(f"Cuentas PUC   : {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM tipos_comprobante")
    print(f"Comprobantes  : {cursor.fetchone()[0]} tipos")

    cursor.execute("SELECT COUNT(*) FROM periodos_contables")
    print(f"Períodos      : {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM reglas_contables")
    print(f"Reglas        : {cursor.fetchone()[0]}")

    print("\nLa base contable quedó preparada para motor_contable.py")
    print("=" * 66)


def main():
    print("=" * 66)
    print("BME-ERP - INICIALIZACIÓN DE CONTABILIDAD")
    print("=" * 66)

    if not RUTA_DB.exists():
        print(f"\nERROR: No se encontró la base de datos:\n{RUTA_DB}")
        input("\nPresione ENTER para cerrar...")
        return

    respaldo = crear_respaldo()
    print(f"\nRespaldo creado:\n{respaldo}")

    conexion = None

    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        ejecutar_script(cursor)
        empresa_id = obtener_empresa_id(cursor)
        cargar_tipos_comprobante(cursor, empresa_id)
        cargar_periodos(cursor, empresa_id)
        cargar_centros_costo(cursor, empresa_id)
        cargar_puc_base(cursor, empresa_id)
        cargar_reglas_iniciales(cursor, empresa_id)

        tablas = validar_estructura(cursor)

        registrar_auditoria(
            cursor,
            empresa_id,
            "Creación y verificación inicial de la estructura contable."
        )

        conexion.commit()
        mostrar_resumen(cursor, tablas)

    except Exception as error:
        if conexion:
            conexion.rollback()

        print("\n" + "=" * 66)
        print("ERROR AL INICIALIZAR CONTABILIDAD")
        print("=" * 66)
        print(error)
        print("\nLa operación fue reversada. El respaldo permanece disponible.")

    finally:
        if conexion:
            conexion.close()

    input("\nPresione ENTER para cerrar...")


if __name__ == "__main__":
    main()
