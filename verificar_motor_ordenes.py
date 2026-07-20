import json
from datetime import datetime
from pathlib import Path
from motor_ordenes_produccion import MotorOrdenesProduccion

BASE = Path(r"C:\Users\jrive\visual")
DB = BASE / "erp_cafe.db"
INFORME = BASE / "resultado_verificacion_motor_ordenes.txt"
lineas = []

def escribir(texto=""):
    lineas.append(str(texto)); print(texto)
def titulo(texto):
    escribir(); escribir("="*84); escribir(texto); escribir("="*84)

titulo("VERIFICACIÓN MOTOR DE ÓRDENES — SIGA ERP")
escribir(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}")
escribir(f"Base de datos: {DB}")
try:
    motor = MotorOrdenesProduccion(DB, usuario="jrive")
    titulo("1. RESUMEN")
    escribir(json.dumps(motor.resumen(), indent=2, ensure_ascii=False))

    titulo("2. ÓRDENES ACTUALES")
    ordenes = motor.listar_ordenes(limite=20)
    if not ordenes: escribir("No hay órdenes en ordenes_produccion_v2.")
    for o in ordenes: escribir(json.dumps(o, ensure_ascii=False, default=str))

    titulo("3. PRODUCTOS Y FÓRMULAS")
    with motor.conexion() as con:
        productos = con.execute("SELECT id,codigo,nombre,presentacion,unidad,estado FROM productos_produccion ORDER BY id").fetchall()
        formulas = con.execute("SELECT id,producto_id,codigo,version,cantidad_base,unidad_base,estado,costo_estandar_total FROM formulas_produccion ORDER BY id").fetchall()
    escribir("PRODUCTOS:")
    for f in productos: escribir(dict(f))
    escribir("\nFÓRMULAS:")
    for f in formulas: escribir(dict(f))

    titulo("4. COMPONENTES DE CADA FÓRMULA")
    for formula in formulas:
        escribir(f"\n{formula['codigo']}:")
        componentes = motor.componentes_formula(formula["id"])
        if not componentes: escribir("  Sin componentes.")
        for c in componentes: escribir(f"  {c}")

    titulo("5. PRUEBA TRANSACCIONAL SEGURA")
    escribir("Se crea una orden temporal y se revierte con ROLLBACK.")
    with motor.conexion() as con:
        con.execute("BEGIN IMMEDIATE")
        formula = con.execute("SELECT id,producto_id FROM formulas_produccion WHERE UPPER(estado)='ACTIVA' ORDER BY id LIMIT 1").fetchone()
        producto = con.execute("SELECT id,unidad FROM productos_produccion WHERE id=?", (formula["producto_id"],)).fetchone() if formula else None
        if not producto or not formula:
            escribir("No se pudo probar: falta producto o fórmula activa."); con.rollback()
        else:
            numero = f"TEST-{datetime.now():%Y%m%d%H%M%S}"
            cur = con.execute("""
                INSERT INTO ordenes_produccion_v2 (
                    numero,fecha_emision,fecha_programada,producto_id,formula_id,
                    cantidad_programada,cantidad_producida,unidad,lote_planeado,
                    prioridad,estado,creada_por,creada_en,actualizada_en
                ) VALUES (?,date('now'),date('now'),?,?,1,0,?,?,'NORMAL','BORRADOR','VERIFICADOR',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            """, (numero, producto["id"], formula["id"], producto["unidad"], numero))
            escribir(f"Registro temporal creado: ID {cur.lastrowid}")
            con.rollback()
            existe = con.execute("SELECT COUNT(*) FROM ordenes_produccion_v2 WHERE numero=?", (numero,)).fetchone()[0]
            escribir("Rollback confirmado: " + ("SÍ" if existe == 0 else "NO — REVISAR"))

    titulo("RESULTADO")
    escribir("MOTOR VERIFICADO SIN MODIFICAR DATOS PERMANENTES.")
except Exception as error:
    titulo("ERROR")
    escribir(f"{type(error).__name__}: {error}")

INFORME.write_text("\n".join(lineas), encoding="utf-8")
escribir(f"\nInforme creado en: {INFORME}")
input("\nPresione ENTER para cerrar...")
