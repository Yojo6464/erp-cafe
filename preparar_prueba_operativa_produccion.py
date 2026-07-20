from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path

BASE = Path(r"C:\Users\jrive\visual")
DB = BASE / "erp_cafe.db"
FORMULA_OBJETIVO = "F-PT-CAFE-001-V2"
CANTIDAD_PRUEBA = 10.0
USUARIO = "jrive"


def pausa():
    input("\nPresione ENTER para cerrar...")


def columnas(con, tabla):
    return {r["name"].lower() for r in con.execute(f'PRAGMA table_info("{tabla}")')}


def tabla_existe(con, tabla):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (tabla,),
    ).fetchone() is not None


def normalizar(texto):
    return str(texto or "").strip().upper()


def costo_promedio_inventario(con, producto, presentacion):
    fila = con.execute(
        """
        SELECT
            COALESCE(SUM(cantidad), 0) AS cantidad,
            CASE
                WHEN COALESCE(SUM(cantidad), 0) = 0 THEN 0
                ELSE SUM(cantidad * costo) / SUM(cantidad)
            END AS costo_promedio
        FROM inventario
        WHERE UPPER(TRIM(producto)) = UPPER(TRIM(?))
          AND UPPER(TRIM(presentacion)) = UPPER(TRIM(?))
        """,
        (producto, presentacion),
    ).fetchone()
    return float(fila["cantidad"] or 0), float(fila["costo_promedio"] or 0)


def siguiente_numero(con):
    anio = datetime.now().year
    prefijo = f"OP-{anio}-"
    fila = con.execute(
        """
        SELECT numero
        FROM ordenes_produccion_v2
        WHERE numero LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"{prefijo}%",),
    ).fetchone()
    ultimo = 0
    if fila:
        try:
            ultimo = int(str(fila["numero"]).split("-")[-1])
        except Exception:
            ultimo = 0
    return f"{prefijo}{ultimo + 1:06d}"


def registrar_historial(con, orden_id, estado_nuevo, observacion):
    cols = columnas(con, "ordenes_historial_v2")
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    posibles = {
        "orden_id": orden_id,
        "fecha": ahora,
        "fecha_evento": ahora,
        "estado_anterior": "",
        "estado_nuevo": estado_nuevo,
        "accion": "CREAR ORDEN DE PRUEBA",
        "evento": "CREAR ORDEN DE PRUEBA",
        "usuario": USUARIO,
        "creado_por": USUARIO,
        "observacion": observacion,
        "observaciones": observacion,
        "detalle": observacion,
        "creado_en": ahora,
    }
    datos = {k: v for k, v in posibles.items() if k in cols}
    if "orden_id" not in datos:
        raise RuntimeError("ordenes_historial_v2 no contiene orden_id.")
    nombres = list(datos)
    con.execute(
        f"""
        INSERT INTO ordenes_historial_v2 ({", ".join(nombres)})
        VALUES ({", ".join("?" for _ in nombres)})
        """,
        [datos[n] for n in nombres],
    )


def main():
    print("=" * 88)
    print("SIGA ERP — PREPARACIÓN DE PRUEBA OPERATIVA DE PRODUCCIÓN")
    print("=" * 88)
    print(f"Base de datos: {DB}")
    print(f"Fórmula objetivo: {FORMULA_OBJETIVO}")
    print(f"Cantidad de prueba: {CANTIDAD_PRUEBA:.0f} unidades")

    if not DB.exists():
        print(f"\nERROR: No existe la base de datos: {DB}")
        pausa()
        return

    con = sqlite3.connect(str(DB), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    try:
        integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
        if str(integridad).lower() != "ok":
            raise RuntimeError(f"integrity_check: {integridad}")

        requeridas = [
            "productos_produccion",
            "formulas_produccion",
            "formulas_componentes",
            "ordenes_produccion_v2",
            "ordenes_historial_v2",
            "inventario",
        ]
        faltantes = [t for t in requeridas if not tabla_existe(con, t)]
        if faltantes:
            raise RuntimeError("Faltan tablas: " + ", ".join(faltantes))

        formula = con.execute(
            """
            SELECT f.*, p.codigo AS producto_codigo, p.nombre AS producto_nombre,
                   p.presentacion AS producto_presentacion, p.unidad AS producto_unidad
            FROM formulas_produccion f
            JOIN productos_produccion p ON p.id = f.producto_id
            WHERE f.codigo = ?
            """,
            (FORMULA_OBJETIVO,),
        ).fetchone()

        if not formula:
            raise RuntimeError(f"No se encontró la fórmula {FORMULA_OBJETIVO}.")

        componentes = con.execute(
            """
            SELECT *
            FROM formulas_componentes
            WHERE formula_id = ?
            ORDER BY id
            """,
            (formula["id"],),
        ).fetchall()

        if not componentes:
            raise RuntimeError("La fórmula objetivo no tiene componentes.")

        cols_comp = columnas(con, "formulas_componentes")
        nombre_col = next(
            (c for c in ["componente", "producto", "nombre_componente", "material", "descripcion"] if c in cols_comp),
            None,
        )
        presentacion_col = next(
            (c for c in ["presentacion", "componente_presentacion", "referencia"] if c in cols_comp),
            None,
        )
        cantidad_col = next(
            (c for c in ["cantidad", "cantidad_base", "cantidad_requerida"] if c in cols_comp),
            None,
        )
        merma_col = next(
            (c for c in ["merma_pct", "merma", "porcentaje_merma"] if c in cols_comp),
            None,
        )
        costo_col = next(
            (c for c in ["costo_unitario", "costo", "costo_estandar"] if c in cols_comp),
            None,
        )

        if not nombre_col or not presentacion_col or not cantidad_col:
            raise RuntimeError(
                "La estructura de formulas_componentes no contiene las columnas mínimas."
            )

        print("\nPRODUCTO TERMINADO")
        print(
            f"{formula['producto_codigo']} | {formula['producto_nombre']} | "
            f"{formula['producto_presentacion']}"
        )

        print("\nVALIDACIÓN DE MATERIALES")
        detalle = []
        costo_unitario_formula = 0.0
        apto = True

        for comp in componentes:
            nombre = str(comp[nombre_col] or "").strip()
            presentacion = str(comp[presentacion_col] or "").strip()
            cantidad_base = float(comp[cantidad_col] or 0)
            merma = float(comp[merma_col] or 0) if merma_col else 0.0
            cantidad_unidad = cantidad_base * (1 + merma / 100)
            requerido = cantidad_unidad * CANTIDAD_PRUEBA

            disponible, costo_promedio = costo_promedio_inventario(
                con, nombre, presentacion
            )
            faltante = max(0.0, requerido - disponible)
            cumple = faltante <= 0.000001
            apto = apto and cumple
            costo_componente = cantidad_unidad * costo_promedio
            costo_unitario_formula += costo_componente

            detalle.append(
                {
                    "id": comp["id"],
                    "nombre": nombre,
                    "presentacion": presentacion,
                    "cantidad_unidad": cantidad_unidad,
                    "requerido": requerido,
                    "disponible": disponible,
                    "faltante": faltante,
                    "costo_promedio": costo_promedio,
                    "costo_componente": costo_componente,
                    "cumple": cumple,
                }
            )

            estado = "OK" if cumple else "FALTANTE"
            print(
                f"{estado:8} {nombre:24} {presentacion:10} "
                f"Req.: {requerido:10.4f} | Disp.: {disponible:10.4f} | "
                f"Costo prom.: ${costo_promedio:,.2f}"
            )

        print("\nCOSTEO PROYECTADO")
        print(f"Costo unitario de materiales: ${costo_unitario_formula:,.2f}")
        print(
            f"Costo de materiales para {CANTIDAD_PRUEBA:.0f} unidades: "
            f"${costo_unitario_formula * CANTIDAD_PRUEBA:,.2f}"
        )

        if not apto:
            print("\nRESULTADO: NO APTO. Hay materiales insuficientes.")
            print("No se realizará ningún cambio.")
            pausa()
            return

        existentes = con.execute(
            """
            SELECT id, numero, estado
            FROM ordenes_produccion_v2
            WHERE lote_planeado LIKE 'PRUEBA-OPERATIVA-%'
              AND UPPER(estado) NOT IN ('ANULADA', 'CERRADA')
            ORDER BY id DESC
            """
        ).fetchall()
        if existentes:
            print("\nATENCIÓN: Ya existe una orden de prueba operativa abierta:")
            for r in existentes:
                print(dict(r))
            print("No se creará una orden duplicada.")
            pausa()
            return

        print("\nACCIONES PROPUESTAS")
        print("1. Crear respaldo automático de la base de datos.")
        print(f"2. Activar la fórmula {FORMULA_OBJETIVO}.")
        print("3. Pasar las demás fórmulas del mismo producto a BORRADOR.")
        if costo_col:
            print("4. Actualizar el costo unitario de cada componente desde Inventario.")
        else:
            print("4. La tabla no tiene columna de costo unitario; se omite ese ajuste.")
        print("5. Actualizar el costo estándar total de la fórmula.")
        print("6. Crear una orden PLANEADA por 10 unidades.")
        print("7. Registrar el historial de la orden.")
        print("\nNo se descontará inventario todavía.")

        confirmacion = input(
            "\nPara ejecutar escriba exactamente ACTIVAR: "
        ).strip().upper()

        if confirmacion != "ACTIVAR":
            print("\nOperación cancelada. No se realizaron cambios.")
            pausa()
            return

        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = BASE / f"erp_cafe_backup_pre_prueba_produccion_{sello}.db"
        shutil.copy2(DB, respaldo)
        print(f"\nRespaldo creado: {respaldo}")

        con.execute("BEGIN IMMEDIATE")
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        con.execute(
            """
            UPDATE formulas_produccion
            SET estado = 'BORRADOR'
            WHERE producto_id = ? AND id <> ?
            """,
            (formula["producto_id"], formula["id"]),
        )
        con.execute(
            """
            UPDATE formulas_produccion
            SET estado = 'ACTIVA', costo_estandar_total = ?
            WHERE id = ?
            """,
            (round(costo_unitario_formula, 6), formula["id"]),
        )

        if costo_col:
            for item in detalle:
                con.execute(
                    f"""
                    UPDATE formulas_componentes
                    SET {costo_col} = ?
                    WHERE id = ?
                    """,
                    (round(item["costo_promedio"], 6), item["id"]),
                )

        numero = siguiente_numero(con)
        lote = f"PRUEBA-OPERATIVA-{datetime.now():%Y%m%d}-001"

        cursor = con.execute(
            """
            INSERT INTO ordenes_produccion_v2 (
                numero, fecha_emision, fecha_programada,
                producto_id, formula_id, cantidad_programada,
                cantidad_producida, unidad, lote_planeado,
                centro_trabajo, responsable, prioridad, estado,
                observaciones, creada_por, creada_en, actualizada_en
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 'PLANEADA', ?, ?, ?, ?)
            """,
            (
                numero,
                date.today().isoformat(),
                date.today().isoformat(),
                formula["producto_id"],
                formula["id"],
                CANTIDAD_PRUEBA,
                formula["producto_unidad"],
                lote,
                "PRODUCCIÓN CAFÉ",
                USUARIO,
                "NORMAL",
                "Orden controlada para validar el flujo integral de Producción.",
                USUARIO,
                ahora,
                ahora,
            ),
        )
        orden_id = int(cursor.lastrowid)

        registrar_historial(
            con,
            orden_id,
            "PLANEADA",
            "Orden controlada creada por el alistamiento operativo.",
        )

        con.commit()

        print("\n" + "=" * 88)
        print("OPERACIÓN COMPLETADA")
        print("=" * 88)
        print(f"Fórmula activa: {FORMULA_OBJETIVO}")
        print(f"Costo estándar actualizado: ${costo_unitario_formula:,.2f}")
        print(f"Orden creada: {numero}")
        print(f"ID de orden: {orden_id}")
        print(f"Lote planeado: {lote}")
        print("Estado: PLANEADA")
        print("\nInventario no descontado. La orden queda lista para aprobación y liberación.")

    except Exception as exc:
        try:
            con.rollback()
        except Exception:
            pass
        print("\nERROR:")
        print(f"{type(exc).__name__}: {exc}")
        print("No se consolidaron cambios.")
    finally:
        con.close()
        pausa()


if __name__ == "__main__":
    main()
