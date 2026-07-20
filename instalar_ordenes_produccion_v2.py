
"""
SIGA ERP - Instalador Órdenes de Producción v2
Archivo: instalar_ordenes_produccion_v2.py
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
        "erp_cafe_antes_ordenes_v2_"
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
        CREATE TABLE IF NOT EXISTS ordenes_produccion_v2(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            fecha_emision TEXT NOT NULL,
            fecha_programada TEXT NOT NULL,
            producto_id INTEGER NOT NULL,
            formula_id INTEGER NOT NULL,
            cantidad_programada REAL NOT NULL,
            cantidad_producida REAL NOT NULL DEFAULT 0,
            unidad TEXT NOT NULL,
            lote_planeado TEXT NOT NULL,
            centro_trabajo TEXT DEFAULT '',
            responsable TEXT DEFAULT '',
            prioridad TEXT NOT NULL DEFAULT 'NORMAL',
            estado TEXT NOT NULL DEFAULT 'BORRADOR',
            observaciones TEXT DEFAULT '',
            aprobada_por TEXT DEFAULT '',
            aprobada_en TEXT DEFAULT '',
            liberada_por TEXT DEFAULT '',
            liberada_en TEXT DEFAULT '',
            iniciada_por TEXT DEFAULT '',
            iniciada_en TEXT DEFAULT '',
            terminada_por TEXT DEFAULT '',
            terminada_en TEXT DEFAULT '',
            anulada_por TEXT DEFAULT '',
            anulada_en TEXT DEFAULT '',
            motivo_anulacion TEXT DEFAULT '',
            creada_por TEXT DEFAULT '',
            creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            actualizada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(producto_id)
                REFERENCES productos_produccion(id),
            FOREIGN KEY(formula_id)
                REFERENCES formulas_produccion(id)
        );

        CREATE TABLE IF NOT EXISTS ordenes_requerimientos_v2(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            componente TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            tipo_componente TEXT NOT NULL,
            cantidad_teorica REAL NOT NULL,
            cantidad_reservada REAL NOT NULL DEFAULT 0,
            cantidad_consumida REAL NOT NULL DEFAULT 0,
            unidad TEXT NOT NULL,
            merma_pct REAL NOT NULL DEFAULT 0,
            costo_unitario_estandar REAL NOT NULL DEFAULT 0,
            costo_total_estandar REAL NOT NULL DEFAULT 0,
            disponible_creacion REAL NOT NULL DEFAULT 0,
            estado_disponibilidad TEXT NOT NULL DEFAULT 'PENDIENTE',
            FOREIGN KEY(orden_id)
                REFERENCES ordenes_produccion_v2(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ordenes_historial_v2(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT '',
            estado_anterior TEXT DEFAULT '',
            estado_nuevo TEXT NOT NULL,
            accion TEXT NOT NULL,
            observaciones TEXT DEFAULT '',
            FOREIGN KEY(orden_id)
                REFERENCES ordenes_produccion_v2(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_op_v2_estado
        ON ordenes_produccion_v2(estado);

        CREATE INDEX IF NOT EXISTS idx_op_v2_fecha
        ON ordenes_produccion_v2(fecha_programada);

        CREATE INDEX IF NOT EXISTS idx_op_req_v2_orden
        ON ordenes_requerimientos_v2(orden_id);
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
    print("SIGA ERP - INSTALACIÓN ÓRDENES DE PRODUCCIÓN v2")
    print("=" * 72)

    try:
        copia = instalar()
        print("\nInstalación completada correctamente.")
        print(f"\nRespaldo creado:\n{copia}")
        print("\nTablas verificadas:")
        print(" - ordenes_produccion_v2")
        print(" - ordenes_requerimientos_v2")
        print(" - ordenes_historial_v2")
    except Exception as error:
        print("\nERROR:")
        print(error)

    input("\nPresione ENTER para cerrar...")
