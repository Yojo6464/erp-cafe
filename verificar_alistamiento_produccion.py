from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "erp_cafe.db"
SALIDA = BASE / "resultado_alistamiento_produccion.txt"

TABLAS = [
    "productos_produccion", "formulas_produccion", "formulas_componentes",
    "ordenes_produccion_v2", "ordenes_requerimientos_v2", "ordenes_historial_v2",
    "ejecuciones_produccion_v3", "consumos_produccion_v3",
    "trazabilidad_produccion_v3", "mermas_produccion_v3", "inventario", "kardex",
]

lineas: list[str] = []
def out(texto=""):
    print(texto)
    lineas.append(str(texto))

def titulo(texto):
    out("\n" + "=" * 88)
    out(texto)
    out("=" * 88)


def columnas(con, tabla):
    return {r[1] for r in con.execute(f'PRAGMA table_info("{tabla}")')}


def main():
    titulo("ALISTAMIENTO OPERATIVO DE PRODUCCIÓN — SIGA ERP")
    out(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}")
    out(f"Base: {DB}")

    if not DB.exists():
        raise FileNotFoundError(f"No se encontró {DB}")

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        titulo("1. INTEGRIDAD Y ESTRUCTURA")
        integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
        out(f"integrity_check: {integridad}")
        existentes = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        faltantes = [t for t in TABLAS if t not in existentes]
        for t in TABLAS:
            out(f"{'OK' if t in existentes else 'FALTA':5}  {t}")

        titulo("2. PRODUCTOS Y FÓRMULAS")
        productos = con.execute("""
            SELECT id,codigo,nombre,presentacion,unidad,estado
            FROM productos_produccion ORDER BY id
        """).fetchall() if "productos_produccion" in existentes else []
        formulas = con.execute("""
            SELECT id,producto_id,codigo,version,cantidad_base,unidad_base,
                   estado,costo_estandar_total
            FROM formulas_produccion ORDER BY producto_id,version
        """).fetchall() if "formulas_produccion" in existentes else []
        for r in productos: out(dict(r))
        out("Fórmulas:")
        for r in formulas: out(dict(r))

        titulo("3. VALIDACIONES DE NEGOCIO")
        alertas = []
        activas = [r for r in formulas if str(r['estado']).upper() == 'ACTIVA']
        if not activas:
            alertas.append("No existe ninguna fórmula ACTIVA.")

        for f in activas:
            componentes = con.execute("""
                SELECT * FROM formulas_componentes
                WHERE formula_id=? ORDER BY id
            """, (f['id'],)).fetchall()
            if not componentes:
                alertas.append(f"La fórmula activa {f['codigo']} no tiene componentes.")
                continue
            prod = con.execute("SELECT nombre,presentacion FROM productos_produccion WHERE id=?", (f['producto_id'],)).fetchone()
            for c in componentes:
                comp = str(c['componente'] or '').strip().upper()
                pres = str(c['presentacion'] or '').strip().upper()
                if prod and comp == str(prod['nombre']).strip().upper() and pres == str(prod['presentacion']).strip().upper():
                    alertas.append(
                        f"La fórmula {f['codigo']} usa como materia prima el mismo producto terminado "
                        f"({c['componente']} / {c['presentacion']}). Revisar BOM."
                    )
                costo = 0.0
                for nombre in ('costo_unitario_estandar','costo_unitario','costo'):
                    if nombre in c.keys() and c[nombre] is not None:
                        costo = float(c[nombre] or 0)
                        break
                if costo <= 0:
                    alertas.append(
                        f"Componente sin costo estándar en {f['codigo']}: "
                        f"{c['componente']} / {c['presentacion']}."
                    )

        if "inventario" in existentes:
            inv = con.execute("""
                SELECT producto,presentacion,SUM(cantidad) cantidad,
                       MAX(COALESCE(costo_unitario,costo,0)) costo
                FROM inventario
                GROUP BY producto,presentacion
                ORDER BY producto,presentacion
            """).fetchall()
            out("Inventario disponible:")
            for r in inv: out(dict(r))

        titulo("4. PREPARACIÓN PARA EJECUCIÓN REAL")
        ordenes = con.execute("""
            SELECT id,numero,estado,cantidad_programada,cantidad_producida,
                   producto_id,formula_id,lote_planeado
            FROM ordenes_produccion_v2 ORDER BY id DESC LIMIT 20
        """).fetchall() if "ordenes_produccion_v2" in existentes else []
        out(f"Órdenes registradas: {len(ordenes)}")
        for r in ordenes: out(dict(r))

        if "ordenes_requerimientos_v2" in existentes:
            requerimientos = con.execute("SELECT COUNT(*) FROM ordenes_requerimientos_v2").fetchone()[0]
            out(f"Requerimientos calculados: {requerimientos}")
        if "ejecuciones_produccion_v3" in existentes:
            ejecuciones = con.execute("SELECT COUNT(*) FROM ejecuciones_produccion_v3").fetchone()[0]
            out(f"Ejecuciones reales: {ejecuciones}")

        titulo("5. RESULTADO")
        if faltantes:
            out("NO APTO: faltan tablas requeridas: " + ", ".join(faltantes))
        elif alertas:
            out("ESTRUCTURA APTA, PERO REQUIERE CORREGIR DATOS MAESTROS:")
            for i, alerta in enumerate(dict.fromkeys(alertas), 1):
                out(f"{i}. {alerta}")
        else:
            out("APTO PARA PRUEBA OPERATIVA CONTROLADA.")

    finally:
        con.close()
        SALIDA.write_text("\n".join(lineas), encoding="utf-8")
        out(f"\nInforme creado en: {SALIDA}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        titulo("ERROR")
        out(f"{type(exc).__name__}: {exc}")
        SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    input("\nPresione ENTER para cerrar...")
