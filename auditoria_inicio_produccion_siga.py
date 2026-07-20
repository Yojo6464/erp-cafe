import sqlite3
from datetime import datetime
from pathlib import Path

RUTA_VISUAL = Path(r"C:\Users\jrive\visual")
RUTA_DB = RUTA_VISUAL / "erp_cafe.db"
SALIDA = RUTA_VISUAL / "auditoria_produccion_siga.txt"

PALABRAS = (
    "produccion", "producción", "bom", "formula", "fórmula",
    "orden", "ejecucion", "ejecución", "mrp", "costo", "lote"
)

TABLAS_PRIORITARIAS = (
    "productos_produccion",
    "formulas_produccion",
    "componentes_formula",
    "ordenes_produccion_v2",
    "requerimientos_v2",
    "historial_v2",
    "inventario",
    "kardex",
    "comprobantes",
    "detalle_comprobantes",
    "periodos_contables"
)

contenido = []

def escribir(texto=""):
    contenido.append(str(texto))

def titulo(texto):
    escribir()
    escribir("=" * 88)
    escribir(texto)
    escribir("=" * 88)

def columnas(conexion, tabla):
    return conexion.execute(f'PRAGMA table_info("{tabla}")').fetchall()

def indices(conexion, tabla):
    return conexion.execute(f'PRAGMA index_list("{tabla}")').fetchall()

def foraneas(conexion, tabla):
    return conexion.execute(f'PRAGMA foreign_key_list("{tabla}")').fetchall()

def contar(conexion, tabla):
    try:
        return conexion.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
    except sqlite3.Error as error:
        return f"ERROR: {error}"

escribir("AUDITORÍA DE INICIO — MÓDULO DE PRODUCCIÓN SIGA ERP")
escribir(f"Fecha y hora: {datetime.now():%Y-%m-%d %H:%M:%S}")
escribir(f"Carpeta: {RUTA_VISUAL}")
escribir(f"Base de datos: {RUTA_DB}")

titulo("1. VALIDACIÓN DE RUTAS")
escribir(f"Existe carpeta visual: {'SÍ' if RUTA_VISUAL.exists() else 'NO'}")
escribir(f"Existe base de datos: {'SÍ' if RUTA_DB.exists() else 'NO'}")

if not RUTA_VISUAL.exists():
    SALIDA = Path(__file__).resolve().parent / "auditoria_produccion_siga.txt"
    escribir("No se encontró C:\\Users\\jrive\\visual.")
    SALIDA.write_text("\n".join(contenido), encoding="utf-8")
    print("\n".join(contenido))
    print(f"\nInforme: {SALIDA}")
    input("\nPresione ENTER para cerrar...")
    raise SystemExit(1)

titulo("2. ARCHIVOS PYTHON RELACIONADOS")
archivos = []
for ruta in sorted(RUTA_VISUAL.glob("*.py")):
    if any(p in ruta.name.lower() for p in PALABRAS):
        archivos.append(ruta)

if archivos:
    for ruta in archivos:
        modificado = datetime.fromtimestamp(ruta.stat().st_mtime)
        escribir(
            f"- {ruta.name} | {ruta.stat().st_size:,} bytes | "
            f"{modificado:%Y-%m-%d %H:%M:%S}"
        )
else:
    escribir("No se encontraron archivos relacionados por nombre.")

if not RUTA_DB.exists():
    titulo("RESULTADO")
    escribir("No se encontró erp_cafe.db. No se modificó ningún archivo.")
    SALIDA.write_text("\n".join(contenido), encoding="utf-8")
    print("\n".join(contenido))
    print(f"\nInforme: {SALIDA}")
    input("\nPresione ENTER para cerrar...")
    raise SystemExit(1)

try:
    conexion = sqlite3.connect(str(RUTA_DB), timeout=20)
    conexion.execute("PRAGMA foreign_keys = ON")

    titulo("3. INTEGRIDAD SQLITE")
    escribir(f"integrity_check: {conexion.execute('PRAGMA integrity_check').fetchone()[0]}")
    escribir(f"Versión SQLite: {sqlite3.sqlite_version}")
    escribir(f"foreign_keys: {conexion.execute('PRAGMA foreign_keys').fetchone()[0]}")

    tablas = [
        fila[0]
        for fila in conexion.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    escribir(f"Cantidad total de tablas: {len(tablas)}")

    titulo("4. TABLAS RELACIONADAS CON PRODUCCIÓN")
    relacionadas = [
        tabla for tabla in tablas
        if any(p in tabla.lower() for p in PALABRAS)
    ]
    if relacionadas:
        for tabla in relacionadas:
            escribir(f"- {tabla}: {contar(conexion, tabla)} registros")
    else:
        escribir("No se encontraron tablas relacionadas por nombre.")

    titulo("5. ESTRUCTURA DE TABLAS PRIORITARIAS")
    existentes = []
    for tabla in TABLAS_PRIORITARIAS:
        if tabla not in tablas:
            escribir(f"\n[NO EXISTE] {tabla}")
            continue

        existentes.append(tabla)
        escribir(f"\n[TABLA] {tabla} — {contar(conexion, tabla)} registros")
        escribir("Columnas:")
        for fila in columnas(conexion, tabla):
            cid, nombre, tipo, no_nulo, predeterminado, pk = fila
            escribir(
                f"  {cid:02d}. {nombre} | {tipo or 'SIN TIPO'} | "
                f"NOT NULL={no_nulo} | DEFAULT={predeterminado} | PK={pk}"
            )

        escribir("Índices:")
        lista_indices = indices(conexion, tabla)
        if lista_indices:
            for indice in lista_indices:
                escribir(f"  {indice}")
        else:
            escribir("  Ninguno")

        escribir("Claves foráneas:")
        lista_foraneas = foraneas(conexion, tabla)
        if lista_foraneas:
            for clave in lista_foraneas:
                escribir(f"  {clave}")
        else:
            escribir("  Ninguna")

    titulo("6. MUESTRA DE DATOS")
    for tabla in existentes:
        escribir(f"\n[MUESTRA] {tabla}")
        cursor = conexion.execute(f'SELECT * FROM "{tabla}" LIMIT 5')
        nombres = [d[0] for d in cursor.description]
        escribir("  COLUMNAS: " + " | ".join(nombres))
        filas = cursor.fetchall()
        if not filas:
            escribir("  Sin registros.")
        for fila in filas:
            escribir("  " + " | ".join("" if v is None else str(v) for v in fila))

    titulo("7. RELACIONES DECLARADAS")
    total_relaciones = 0
    for tabla in tablas:
        for clave in foraneas(conexion, tabla):
            total_relaciones += 1
            escribir(f"{tabla}: {clave}")
    if total_relaciones == 0:
        escribir("No hay claves foráneas declaradas.")

    titulo("8. RESULTADO")
    faltantes = [t for t in TABLAS_PRIORITARIAS if t not in tablas]
    escribir(
        f"Tablas prioritarias existentes: "
        f"{len(TABLAS_PRIORITARIAS) - len(faltantes)} de {len(TABLAS_PRIORITARIAS)}"
    )
    if faltantes:
        escribir("Faltantes:")
        for tabla in faltantes:
            escribir(f"- {tabla}")
    escribir()
    escribir("Auditoría de solo lectura: no modifica archivos ni registros.")

    conexion.close()

except sqlite3.Error as error:
    titulo("ERROR SQLITE")
    escribir(repr(error))

SALIDA.write_text("\n".join(contenido), encoding="utf-8")
print("\n".join(contenido))
print(f"\nINFORME CREADO EN: {SALIDA}")
input("\nPresione ENTER para cerrar...")
