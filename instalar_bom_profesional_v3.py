
"""
SIGA ERP - Instalador BOM Profesional v3
Archivo: instalar_bom_profesional_v3.py
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\Users\jrive\visual")
RUTA_DB = BASE_DIR / "erp_cafe.db"


def respaldo():
    carpeta = BASE_DIR / "backups"
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / (
        "erp_cafe_antes_bom_profesional_v3_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".db"
    )
    shutil.copy2(RUTA_DB, destino)
    return destino


def columnas(cursor, tabla):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return {fila[1] for fila in cursor.fetchall()}


def agregar_columna(cursor, tabla, nombre, definicion):
    if nombre not in columnas(cursor, tabla):
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"
        )


def instalar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )

    copia = respaldo()
    con = sqlite3.connect(RUTA_DB)

    try:
        cur = con.cursor()
        cur.execute("BEGIN IMMEDIATE")

        necesarias = {
            "productos_produccion",
            "formulas_produccion",
            "formulas_componentes",
            "auditoria_produccion",
        }

        existentes = {
            fila[0]
            for fila in cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
            """).fetchall()
        }

        faltantes = sorted(necesarias - existentes)

        if faltantes:
            raise RuntimeError(
                "Faltan tablas de BOM v2: "
                + ", ".join(faltantes)
            )

        # Productos
        agregar_columna(
            cur,
            "productos_produccion",
            "codigo_barras",
            "TEXT DEFAULT ''"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "vida_util_dias",
            "INTEGER NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "tiempo_estandar_min",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "temperatura_min",
            "REAL"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "temperatura_max",
            "REAL"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "humedad_min",
            "REAL"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "humedad_max",
            "REAL"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "ficha_tecnica",
            "TEXT DEFAULT ''"
        )
        agregar_columna(
            cur,
            "productos_produccion",
            "instrucciones",
            "TEXT DEFAULT ''"
        )

        # Fórmulas
        agregar_columna(
            cur,
            "formulas_produccion",
            "costo_mano_obra_estandar",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "costo_cif_estandar",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "costo_servicios_estandar",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "tiempo_preparacion_min",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "tiempo_proceso_min",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "centro_trabajo",
            "TEXT DEFAULT ''"
        )
        agregar_columna(
            cur,
            "formulas_produccion",
            "instrucciones_tecnicas",
            "TEXT DEFAULT ''"
        )

        # Componentes
        agregar_columna(
            cur,
            "formulas_componentes",
            "factor_conversion",
            "REAL NOT NULL DEFAULT 1"
        )
        agregar_columna(
            cur,
            "formulas_componentes",
            "unidad_inventario",
            "TEXT DEFAULT ''"
        )
        agregar_columna(
            cur,
            "formulas_componentes",
            "cantidad_convertida",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_componentes",
            "es_critico",
            "INTEGER NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_componentes",
            "es_subproducto",
            "INTEGER NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "formulas_componentes",
            "porcentaje_recuperacion",
            "REAL NOT NULL DEFAULT 0"
        )

        cur.executescript("""
        CREATE TABLE IF NOT EXISTS centros_trabajo_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            tipo TEXT DEFAULT '',
            capacidad_hora REAL NOT NULL DEFAULT 0,
            costo_hora REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            observaciones TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recursos_formula_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            tipo_recurso TEXT NOT NULL,
            recurso TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 0,
            unidad TEXT NOT NULL DEFAULT 'HORA',
            costo_unitario REAL NOT NULL DEFAULT 0,
            costo_total REAL NOT NULL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            FOREIGN KEY(formula_id)
                REFERENCES formulas_produccion(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documentos_producto_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tipo_documento TEXT NOT NULL,
            nombre TEXT NOT NULL,
            ruta TEXT NOT NULL,
            version TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(producto_id)
                REFERENCES productos_produccion(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS parametros_calidad_producto(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            parametro TEXT NOT NULL,
            valor_minimo REAL,
            valor_objetivo REAL,
            valor_maximo REAL,
            unidad TEXT DEFAULT '',
            metodo_inspeccion TEXT DEFAULT '',
            es_obligatorio INTEGER NOT NULL DEFAULT 1,
            observaciones TEXT DEFAULT '',
            FOREIGN KEY(producto_id)
                REFERENCES productos_produccion(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_recursos_formula
        ON recursos_formula_produccion(formula_id);

        CREATE INDEX IF NOT EXISTS idx_documentos_producto
        ON documentos_producto_produccion(producto_id);

        CREATE INDEX IF NOT EXISTS idx_calidad_producto
        ON parametros_calidad_producto(producto_id);
        """)

        # Recalcular costo total de fórmulas antiguas.
        cur.execute("""
            UPDATE formulas_produccion
            SET costo_estandar_total=
                COALESCE(costo_estandar_materiales, 0)
                + COALESCE(costo_mano_obra_estandar, 0)
                + COALESCE(costo_cif_estandar, 0)
                + COALESCE(costo_servicios_estandar, 0)
        """)

        con.commit()
        return copia

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


if __name__ == "__main__":
    print("=" * 72)
    print("SIGA ERP - INSTALACIÓN BOM PROFESIONAL v3")
    print("=" * 72)

    try:
        copia = instalar()
        print("\nInstalación completada correctamente.")
        print(f"\nRespaldo creado:\n{copia}")
        print("\nEstructura ampliada:")
        print(" - productos_produccion")
        print(" - formulas_produccion")
        print(" - formulas_componentes")
        print(" - centros_trabajo_produccion")
        print(" - recursos_formula_produccion")
        print(" - documentos_producto_produccion")
        print(" - parametros_calidad_producto")
    except Exception as error:
        print("\nERROR:")
        print(error)

    input("\nPresione ENTER para cerrar...")
