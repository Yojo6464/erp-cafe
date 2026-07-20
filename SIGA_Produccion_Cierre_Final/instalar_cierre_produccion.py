from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent
DESTINO = Path(r"C:\Users\jrive\visual")
ARCHIVOS = [
    "motor_ordenes_produccion.py",
    "ordenes_produccion_v2.py",
    "ejecucion_produccion_v3.py",
]


def main() -> None:
    if not DESTINO.exists():
        raise FileNotFoundError(f"No existe la carpeta de SIGA: {DESTINO}")
    db = DESTINO / "erp_cafe.db"
    if not db.exists():
        raise FileNotFoundError(f"No existe la base de datos: {db}")

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    respaldo = DESTINO / "respaldos" / f"produccion_cierre_{marca}"
    respaldo.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SIGA ERP - CIERRE FINAL DE PRODUCCION")
    print("=" * 70)
    print(f"Destino: {DESTINO}")
    print(f"Respaldo: {respaldo}")

    shutil.copy2(db, respaldo / db.name)
    for nombre in ARCHIVOS:
        actual = DESTINO / nombre
        if actual.exists():
            shutil.copy2(actual, respaldo / nombre)
        origen = PAQUETE / nombre
        if not origen.exists():
            raise FileNotFoundError(f"Falta en el paquete: {origen}")
        shutil.copy2(origen, actual)
        print(f"Actualizado: {nombre}")

    sys.path.insert(0, str(DESTINO))
    from motor_ordenes_produccion import MotorOrdenesProduccion

    motor = MotorOrdenesProduccion(db, usuario="instalador_siga")
    with motor.conexion() as con:
        ordenes = [
            int(f[0])
            for f in con.execute(
                """
                SELECT o.id
                FROM ordenes_produccion_v2 o
                LEFT JOIN ordenes_requerimientos_v2 r ON r.orden_id=o.id
                GROUP BY o.id
                HAVING COUNT(r.id)=0
                ORDER BY o.id
                """
            ).fetchall()
        ]

    reparadas = 0
    for orden_id in ordenes:
        filas = motor.generar_requerimientos(orden_id)
        reparadas += 1
        print(f"Orden {orden_id}: {len(filas)} requerimientos generados")

    with sqlite3.connect(db) as con:
        integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
        pendientes = con.execute(
            """
            SELECT COUNT(*)
            FROM ordenes_produccion_v2 o
            WHERE NOT EXISTS (
                SELECT 1 FROM ordenes_requerimientos_v2 r
                WHERE r.orden_id=o.id
            )
            """
        ).fetchone()[0]

    if str(integridad).lower() != "ok" or pendientes:
        raise RuntimeError(
            f"Validacion final fallida. Integridad={integridad}; pendientes={pendientes}"
        )

    print("\nRESULTADO")
    print(f"Ordenes reparadas: {reparadas}")
    print(f"Integridad SQLite: {integridad}")
    print("Produccion instalada y requerimientos validados correctamente.")
    input("\nPresione ENTER para cerrar...")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\nERROR: no fue posible completar la instalacion.")
        print(error)
        input("\nPresione ENTER para cerrar...")
        raise
