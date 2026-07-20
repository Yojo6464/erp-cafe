
"""
SIGA ERP - Instalador MRP Profesional v1
Archivo: instalar_mrp_produccion_v1.py
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
        "erp_cafe_antes_mrp_v1_"
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

        requeridas = {
            "ordenes_produccion_v2",
            "ordenes_requerimientos_v2",
            "inventario",
        }

        existentes = {
            fila[0]
            for fila in cur.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
            """).fetchall()
        }

        faltantes = sorted(requeridas - existentes)

        if faltantes:
            raise RuntimeError(
                "Faltan tablas requeridas: "
                + ", ".join(faltantes)
            )

        cur.executescript("""
        CREATE TABLE IF NOT EXISTS mrp_ejecuciones(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            fecha_desde TEXT DEFAULT '',
            fecha_hasta TEXT DEFAULT '',
            estados_incluidos TEXT DEFAULT '',
            costo_total_proyectado REAL NOT NULL DEFAULT 0,
            componentes_totales INTEGER NOT NULL DEFAULT 0,
            componentes_faltantes INTEGER NOT NULL DEFAULT 0,
            usuario TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mrp_resultados(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrp_id INTEGER NOT NULL,
            componente TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            tipo_componente TEXT DEFAULT '',
            unidad TEXT NOT NULL DEFAULT '',
            cantidad_requerida REAL NOT NULL DEFAULT 0,
            inventario_disponible REAL NOT NULL DEFAULT 0,
            inventario_reservado REAL NOT NULL DEFAULT 0,
            disponible_neto REAL NOT NULL DEFAULT 0,
            faltante REAL NOT NULL DEFAULT 0,
            costo_unitario_estandar REAL NOT NULL DEFAULT 0,
            costo_proyectado REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'OK',
            FOREIGN KEY(mrp_id)
                REFERENCES mrp_ejecuciones(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reservas_materiales_mrp(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            requerimiento_id INTEGER NOT NULL,
            componente TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            cantidad_reservada REAL NOT NULL DEFAULT 0,
            unidad TEXT NOT NULL DEFAULT '',
            estado TEXT NOT NULL DEFAULT 'ACTIVA',
            creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            liberada_en TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            UNIQUE(orden_id, requerimiento_id)
        );

        CREATE TABLE IF NOT EXISTS sugerencias_compra_mrp(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrp_id INTEGER NOT NULL,
            componente TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            cantidad_sugerida REAL NOT NULL,
            unidad TEXT NOT NULL DEFAULT '',
            costo_unitario_estimado REAL NOT NULL DEFAULT 0,
            costo_total_estimado REAL NOT NULL DEFAULT 0,
            prioridad TEXT NOT NULL DEFAULT 'NORMAL',
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            observaciones TEXT DEFAULT '',
            creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(mrp_id)
                REFERENCES mrp_ejecuciones(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_mrp_resultados_mrp
        ON mrp_resultados(mrp_id);

        CREATE INDEX IF NOT EXISTS idx_reservas_orden
        ON reservas_materiales_mrp(orden_id);

        CREATE INDEX IF NOT EXISTS idx_sugerencias_mrp
        ON sugerencias_compra_mrp(mrp_id);
        """)

        con.commit()
        return copia

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


if __name__ == "__main__":
    print("=" * 70)
    print("SIGA ERP - INSTALACIÓN MRP PROFESIONAL v1")
    print("=" * 70)

    try:
        copia = instalar()
        print("\nInstalación completada correctamente.")
        print(f"\nRespaldo creado:\n{copia}")
        print("\nTablas verificadas:")
        print(" - mrp_ejecuciones")
        print(" - mrp_resultados")
        print(" - reservas_materiales_mrp")
        print(" - sugerencias_compra_mrp")
    except Exception as error:
        print("\nERROR:")
        print(error)

    input("\nPresione ENTER para cerrar...")
