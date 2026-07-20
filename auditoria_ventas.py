import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "erp_cafe.db"
VENTAS_PATH = BASE_DIR / "ventas_integradas.py"

TABLAS_REQUERIDAS = [
    "ventas_integradas",
    "detalle_ventas_integradas",
    "clientes",
    "bancos",
    "movimientos_bancos",
    "cuentas_cobrar_v1",
    "almacen_pergamino",
    "kardex",
    "comprobantes",
]


def imprimir_titulo(texto):
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def verificar_archivos():
    imprimir_titulo("1. VERIFICACIÓN DE ARCHIVOS")

    for ruta in [DB_PATH, VENTAS_PATH]:
        if ruta.exists():
            tamaño = ruta.stat().st_size
            print(f"[OK] {ruta.name} existe — {tamaño:,} bytes")
        else:
            print(f"[ERROR] No existe: {ruta}")


def obtener_tablas(cursor):
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)
    return [fila[0] for fila in cursor.fetchall()]


def mostrar_estructura(cursor, tabla):
    print(f"\nTABLA: {tabla}")
    print("-" * 80)

    cursor.execute(f"PRAGMA table_info('{tabla}')")
    columnas = cursor.fetchall()

    if not columnas:
        print("Sin columnas o tabla inexistente.")
        return

    for columna in columnas:
        cid, nombre, tipo, obligatorio, valor_defecto, pk = columna
        print(
            f"{nombre:30} "
            f"Tipo: {tipo or 'SIN TIPO':15} "
            f"Obligatorio: {'SÍ' if obligatorio else 'NO':3} "
            f"PK: {'SÍ' if pk else 'NO'}"
        )

    cursor.execute(f"SELECT COUNT(*) FROM '{tabla}'")
    cantidad = cursor.fetchone()[0]
    print(f"Registros actuales: {cantidad}")


def revisar_claves_foraneas(cursor, tabla):
    cursor.execute(f"PRAGMA foreign_key_list('{tabla}')")
    relaciones = cursor.fetchall()

    if relaciones:
        print("\nRelaciones declaradas:")
        for relacion in relaciones:
            print(
                f"  {relacion[3]} -> "
                f"{relacion[2]}.{relacion[4]}"
            )
    else:
        print("\nNo tiene claves foráneas declaradas.")


def revisar_codigo_ventas():
    imprimir_titulo("4. REVISIÓN PRELIMINAR DEL CÓDIGO")

    if not VENTAS_PATH.exists():
        print("[ERROR] No se encontró ventas_integradas.py")
        return

    contenido = VENTAS_PATH.read_text(
        encoding="utf-8",
        errors="replace"
    )

    verificaciones = {
        "Conexión SQLite": "sqlite3.connect" in contenido,
        "Uso de transacciones": (
            "commit()" in contenido and
            ("rollback()" in contenido or "with sqlite3.connect" in contenido)
        ),
        "Inserción de venta": "INSERT INTO ventas_integradas" in contenido,
        "Inserción de detalle": "detalle_ventas_integradas" in contenido,
        "Actualización de inventario": (
            "almacen_pergamino" in contenido or
            "inventario" in contenido.lower()
        ),
        "Registro de Kardex": "kardex" in contenido.lower(),
        "Manejo de bancos": "movimientos_bancos" in contenido,
        "Manejo de cartera": (
            "cuentas_cobrar" in contenido.lower() or
            "cxc" in contenido.lower()
        ),
        "Integración contable": (
            "motor_contable" in contenido or
            "comprobantes" in contenido.lower()
        ),
        "Proceso de anulación": "anul" in contenido.lower(),
    }

    for nombre, resultado in verificaciones.items():
        estado = "[OK]" if resultado else "[REVISAR]"
        print(f"{estado:10} {nombre}")


def main():
    verificar_archivos()

    if not DB_PATH.exists():
        print("\nNo es posible continuar sin erp_cafe.db.")
        return

    conexion = sqlite3.connect(DB_PATH)

    try:
        cursor = conexion.cursor()

        imprimir_titulo("2. INVENTARIO DE TABLAS")
        tablas = obtener_tablas(cursor)

        print(f"Total de tablas encontradas: {len(tablas)}")

        for tabla in TABLAS_REQUERIDAS:
            estado = "[OK]" if tabla in tablas else "[FALTA]"
            print(f"{estado:10} {tabla}")

        imprimir_titulo("3. ESTRUCTURA DE TABLAS DE VENTAS")

        for tabla in [
            "ventas_integradas",
            "detalle_ventas_integradas",
        ]:
            if tabla in tablas:
                mostrar_estructura(cursor, tabla)
                revisar_claves_foraneas(cursor, tabla)
            else:
                print(f"\n[ERROR] No existe la tabla {tabla}")

        revisar_codigo_ventas()

        imprimir_titulo("5. RESULTADO")
        print("Auditoría terminada.")
        print("No se realizó ninguna modificación en la base de datos.")

    except sqlite3.Error as error:
        print(f"\n[ERROR SQLite] {error}")

    finally:
        conexion.close()


if __name__ == "__main__":
    main()