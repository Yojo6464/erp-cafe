"""
SIGA ERP - Instalador Producción BOM v2
Archivo: instalar_produccion_bom_v2.py
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\Users\jrive\visual")
RUTA_DB = BASE_DIR / "erp_cafe.db"


def columnas(cursor, tabla):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return {fila[1] for fila in cursor.fetchall()}


def agregar_columna(cursor, tabla, nombre, definicion):
    if nombre not in columnas(cursor, tabla):
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"
        )


def respaldo():
    carpeta = BASE_DIR / "backups"
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / (
        "erp_cafe_antes_bom_v2_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".db"
    )
    shutil.copy2(RUTA_DB, destino)
    return destino


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

        cur.executescript("""
        CREATE TABLE IF NOT EXISTS productos_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            unidad TEXT NOT NULL DEFAULT 'UND',
            categoria TEXT DEFAULT '',
            tipo TEXT NOT NULL DEFAULT 'PRODUCTO TERMINADO',
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            observaciones TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS formulas_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            cantidad_base REAL NOT NULL DEFAULT 1,
            unidad_base TEXT NOT NULL DEFAULT 'UND',
            rendimiento_pct REAL NOT NULL DEFAULT 100,
            merma_estandar_pct REAL NOT NULL DEFAULT 0,
            costo_estandar_materiales REAL NOT NULL DEFAULT 0,
            costo_estandar_total REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'BORRADOR',
            vigente_desde TEXT DEFAULT '',
            vigente_hasta TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            creado_por TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(producto_id)
                REFERENCES productos_produccion(id),
            UNIQUE(producto_id, version)
        );

        CREATE TABLE IF NOT EXISTS formulas_componentes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            componente TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            tipo_componente TEXT NOT NULL DEFAULT 'MATERIA PRIMA',
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL DEFAULT 'UND',
            merma_pct REAL NOT NULL DEFAULT 0,
            costo_unitario_estandar REAL NOT NULL DEFAULT 0,
            costo_total_estandar REAL NOT NULL DEFAULT 0,
            es_sustituto INTEGER NOT NULL DEFAULT 0,
            componente_sustituido TEXT DEFAULT '',
            orden INTEGER NOT NULL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            FOREIGN KEY(formula_id)
                REFERENCES formulas_produccion(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS auditoria_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT '',
            accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            entidad_id INTEGER,
            detalle TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_formula_producto
        ON formulas_produccion(producto_id, version);

        CREATE INDEX IF NOT EXISTS idx_formula_estado
        ON formulas_produccion(estado);

        CREATE INDEX IF NOT EXISTS idx_formula_componentes
        ON formulas_componentes(formula_id);
        """)

        con.commit()
        return copia

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


if __name__ == "__main__":
    print("=" * 68)
    print("SIGA ERP - INSTALACIÓN PRODUCCIÓN BOM v2")
    print("=" * 68)

    try:
        copia = instalar()
        print("\nInstalación completada correctamente.")
        print(f"\nRespaldo creado:\n{copia}")
        print("\nTablas verificadas:")
        print(" - productos_produccion")
        print(" - formulas_produccion")
        print(" - formulas_componentes")
        print(" - auditoria_produccion")
    except Exception as error:
        print("\nERROR:")
        print(error)

    input("\nPresione ENTER para cerrar...")
