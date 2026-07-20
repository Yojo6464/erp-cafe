from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "erp_cafe.db"

DDL = """
CREATE TABLE IF NOT EXISTS ejecuciones_produccion_v3(
 id INTEGER PRIMARY KEY AUTOINCREMENT, orden_id INTEGER NOT NULL,
 numero_ejecucion TEXT NOT NULL UNIQUE, fecha TEXT NOT NULL,
 cantidad_producida REAL NOT NULL, cantidad_rechazada REAL NOT NULL DEFAULT 0,
 merma_real REAL NOT NULL DEFAULT 0, mano_obra_real REAL NOT NULL DEFAULT 0,
 costos_indirectos_reales REAL NOT NULL DEFAULT 0,
 costo_materiales_real REAL NOT NULL DEFAULT 0, costo_total_real REAL NOT NULL DEFAULT 0,
 costo_unitario_real REAL NOT NULL DEFAULT 0, lote_producto TEXT NOT NULL,
 responsable TEXT DEFAULT '', observaciones TEXT DEFAULT '', usuario TEXT DEFAULT '',
 estado TEXT NOT NULL DEFAULT 'EJECUTADA', comprobante_id INTEGER,
 estado_contable TEXT NOT NULL DEFAULT 'PENDIENTE', mensaje_contable TEXT DEFAULT '',
 creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(orden_id) REFERENCES ordenes_produccion_v2(id)
);
CREATE TABLE IF NOT EXISTS consumos_produccion_v3(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ejecucion_id INTEGER NOT NULL,
 orden_id INTEGER NOT NULL, requerimiento_id INTEGER, inventario_id INTEGER NOT NULL,
 producto TEXT NOT NULL, presentacion TEXT NOT NULL, lote TEXT DEFAULT '',
 cantidad REAL NOT NULL, costo_unitario REAL NOT NULL DEFAULT 0,
 costo_total REAL NOT NULL DEFAULT 0, fecha_ingreso_lote TEXT DEFAULT '',
 FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones_produccion_v3(id) ON DELETE CASCADE,
 FOREIGN KEY(orden_id) REFERENCES ordenes_produccion_v2(id)
);
CREATE TABLE IF NOT EXISTS trazabilidad_produccion_v3(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ejecucion_id INTEGER NOT NULL,
 orden_id INTEGER NOT NULL, lote_producto_terminado TEXT NOT NULL,
 producto_terminado TEXT NOT NULL, presentacion_terminada TEXT NOT NULL,
 lote_materia_prima TEXT NOT NULL, materia_prima TEXT NOT NULL,
 presentacion_materia_prima TEXT NOT NULL, cantidad_consumida REAL NOT NULL,
 costo_consumido REAL NOT NULL DEFAULT 0, fecha TEXT NOT NULL,
 FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones_produccion_v3(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS mermas_produccion_v3(
 id INTEGER PRIMARY KEY AUTOINCREMENT, ejecucion_id INTEGER NOT NULL,
 orden_id INTEGER NOT NULL, fecha TEXT NOT NULL,
 tipo TEXT NOT NULL DEFAULT 'MERMA GENERAL', cantidad REAL NOT NULL DEFAULT 0,
 unidad TEXT DEFAULT '', costo_estimado REAL NOT NULL DEFAULT 0,
 motivo TEXT DEFAULT '', responsable TEXT DEFAULT '',
 FOREIGN KEY(ejecucion_id) REFERENCES ejecuciones_produccion_v3(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ejecucion_orden_v3 ON ejecuciones_produccion_v3(orden_id);
CREATE INDEX IF NOT EXISTS idx_consumo_ejecucion_v3 ON consumos_produccion_v3(ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_trazabilidad_lote_pt_v3 ON trazabilidad_produccion_v3(lote_producto_terminado);
CREATE INDEX IF NOT EXISTS idx_trazabilidad_lote_mp_v3 ON trazabilidad_produccion_v3(lote_materia_prima);
"""

COLUMNAS_ORDEN = {
 "costo_materiales_real": "REAL NOT NULL DEFAULT 0",
 "costo_mano_obra_real": "REAL NOT NULL DEFAULT 0",
 "costo_indirecto_real": "REAL NOT NULL DEFAULT 0",
 "costo_total_real": "REAL NOT NULL DEFAULT 0",
 "costo_unitario_real": "REAL NOT NULL DEFAULT 0",
 "merma_real": "REAL NOT NULL DEFAULT 0",
 "comprobante_id": "INTEGER",
 "estado_contable": "TEXT NOT NULL DEFAULT 'NO APLICA'",
 "mensaje_contable": "TEXT DEFAULT ''",
}

def main():
    if not DB.exists():
        raise FileNotFoundError(f"No se encontró {DB}")
    backup = DB.with_name(f"erp_cafe_backup_avance2_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB, backup)
    con = sqlite3.connect(DB, timeout=30)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("BEGIN IMMEDIATE")
        tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        requeridas = {"ordenes_produccion_v2", "inventario", "kardex"}
        faltan = requeridas - tablas
        if faltan:
            raise RuntimeError("Faltan tablas base: " + ", ".join(sorted(faltan)))
        cols = {r[1] for r in con.execute("PRAGMA table_info(ordenes_produccion_v2)")}
        for nombre, tipo in COLUMNAS_ORDEN.items():
            if nombre not in cols:
                con.execute(f'ALTER TABLE ordenes_produccion_v2 ADD COLUMN "{nombre}" {tipo}')
        con.executescript(DDL)
        integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
        if str(integridad).lower() != "ok":
            raise RuntimeError(f"integrity_check: {integridad}")
        con.commit()
        print("INSTALACIÓN/VERIFICACIÓN COMPLETADA")
        print(f"Respaldo: {backup}")
        print("No se borraron ni modificaron registros existentes.")
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
    input("\nPresione ENTER para cerrar...")
