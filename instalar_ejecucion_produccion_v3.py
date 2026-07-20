
"""
SIGA ERP - Instalador Ejecución Real de Producción v3
Archivo: instalar_ejecucion_produccion_v3.py
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
        "erp_cafe_antes_ejecucion_v3_"
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

        requeridas = [
            "productos_produccion",
            "formulas_produccion",
            "formulas_componentes",
            "ordenes_produccion_v2",
            "ordenes_requerimientos_v2",
            "ordenes_historial_v2",
            "inventario",
            "kardex",
        ]

        existentes = {
            fila[0]
            for fila in cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
            """).fetchall()
        }

        faltantes = [
            tabla
            for tabla in requeridas
            if tabla not in existentes
        ]

        if faltantes:
            raise RuntimeError(
                "Faltan tablas de las entregas anteriores: "
                + ", ".join(faltantes)
            )

        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "costo_materiales_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "costo_mano_obra_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "costo_indirecto_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "costo_total_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "costo_unitario_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "merma_real",
            "REAL NOT NULL DEFAULT 0"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "comprobante_id",
            "INTEGER"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "estado_contable",
            "TEXT NOT NULL DEFAULT 'NO APLICA'"
        )
        agregar_columna(
            cur,
            "ordenes_produccion_v2",
            "mensaje_contable",
            "TEXT DEFAULT ''"
        )

        cur.executescript("""
        CREATE TABLE IF NOT EXISTS ejecuciones_produccion_v3(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            numero_ejecucion TEXT NOT NULL UNIQUE,
            fecha TEXT NOT NULL,
            cantidad_producida REAL NOT NULL,
            cantidad_rechazada REAL NOT NULL DEFAULT 0,
            merma_real REAL NOT NULL DEFAULT 0,
            mano_obra_real REAL NOT NULL DEFAULT 0,
            costos_indirectos_reales REAL NOT NULL DEFAULT 0,
            costo_materiales_real REAL NOT NULL DEFAULT 0,
            costo_total_real REAL NOT NULL DEFAULT 0,
            costo_unitario_real REAL NOT NULL DEFAULT 0,
            lote_producto TEXT NOT NULL,
            responsable TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            usuario TEXT DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'EJECUTADA',
            comprobante_id INTEGER,
            estado_contable TEXT NOT NULL DEFAULT 'PENDIENTE',
            mensaje_contable TEXT DEFAULT '',
            creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(orden_id)
                REFERENCES ordenes_produccion_v2(id)
        );

        CREATE TABLE IF NOT EXISTS consumos_produccion_v3(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejecucion_id INTEGER NOT NULL,
            orden_id INTEGER NOT NULL,
            requerimiento_id INTEGER,
            inventario_id INTEGER NOT NULL,
            producto TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            lote TEXT DEFAULT '',
            cantidad REAL NOT NULL,
            costo_unitario REAL NOT NULL DEFAULT 0,
            costo_total REAL NOT NULL DEFAULT 0,
            fecha_ingreso_lote TEXT DEFAULT '',
            FOREIGN KEY(ejecucion_id)
                REFERENCES ejecuciones_produccion_v3(id)
                ON DELETE CASCADE,
            FOREIGN KEY(orden_id)
                REFERENCES ordenes_produccion_v2(id)
        );

        CREATE TABLE IF NOT EXISTS trazabilidad_produccion_v3(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejecucion_id INTEGER NOT NULL,
            orden_id INTEGER NOT NULL,
            lote_producto_terminado TEXT NOT NULL,
            producto_terminado TEXT NOT NULL,
            presentacion_terminada TEXT NOT NULL,
            lote_materia_prima TEXT NOT NULL,
            materia_prima TEXT NOT NULL,
            presentacion_materia_prima TEXT NOT NULL,
            cantidad_consumida REAL NOT NULL,
            costo_consumido REAL NOT NULL DEFAULT 0,
            fecha TEXT NOT NULL,
            FOREIGN KEY(ejecucion_id)
                REFERENCES ejecuciones_produccion_v3(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS mermas_produccion_v3(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejecucion_id INTEGER NOT NULL,
            orden_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'MERMA GENERAL',
            cantidad REAL NOT NULL DEFAULT 0,
            unidad TEXT DEFAULT '',
            costo_estimado REAL NOT NULL DEFAULT 0,
            motivo TEXT DEFAULT '',
            responsable TEXT DEFAULT '',
            FOREIGN KEY(ejecucion_id)
                REFERENCES ejecuciones_produccion_v3(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_ejecucion_orden_v3
        ON ejecuciones_produccion_v3(orden_id);

        CREATE INDEX IF NOT EXISTS idx_consumo_ejecucion_v3
        ON consumos_produccion_v3(ejecucion_id);

        CREATE INDEX IF NOT EXISTS idx_trazabilidad_lote_pt_v3
        ON trazabilidad_produccion_v3(lote_producto_terminado);

        CREATE INDEX IF NOT EXISTS idx_trazabilidad_lote_mp_v3
        ON trazabilidad_produccion_v3(lote_materia_prima);
        """)

        con.commit()
        return copia

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


if __name__ == "__main__":
    print("=" * 74)
    print("SIGA ERP - INSTALACIÓN EJECUCIÓN REAL DE PRODUCCIÓN v3")
    print("=" * 74)

    try:
        copia = instalar()
        print("\nInstalación completada correctamente.")
        print(f"\nRespaldo creado:\n{copia}")
        print("\nTablas verificadas:")
        print(" - ejecuciones_produccion_v3")
        print(" - consumos_produccion_v3")
        print(" - trazabilidad_produccion_v3")
        print(" - mermas_produccion_v3")
        print(" - ordenes_produccion_v2 ampliada")
    except Exception as error:
        print("\nERROR:")
        print(error)

    input("\nPresione ENTER para cerrar...")
