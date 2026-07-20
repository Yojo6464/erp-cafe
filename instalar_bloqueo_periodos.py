"""
BME-ERP - Instalador robusto del bloqueo de períodos
Archivo: instalar_bloqueo_periodos.py

Características:
- Informa exactamente qué archivo está procesando.
- Reintenta cuando Windows reporta un archivo ocupado.
- Usa copias temporales y reemplazo seguro.
- Crea respaldo.
- Revierte automáticamente ante cualquier error.
"""

from __future__ import annotations

import os
import py_compile
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

CARPETA_ERP = Path(r"C:\Users\jrive\visual")
ARCHIVO_PROTECCION = Path(__file__).with_name("proteccion_periodos.py")
MARCA = "# BME-PROTECCION-PERIODOS"
INTENTOS = 5
ESPERA_SEGUNDOS = 2


class ErrorInstalacion(Exception):
    pass


def leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def escribir_seguro(ruta: Path, contenido: str) -> None:
    temporal = ruta.with_suffix(ruta.suffix + ".bme_tmp")
    temporal.write_text(contenido, encoding="utf-8")

    ultimo_error = None

    for intento in range(1, INTENTOS + 1):
        try:
            os.replace(temporal, ruta)
            return
        except PermissionError as error:
            ultimo_error = error
            print(
                f"  Archivo ocupado: {ruta.name} "
                f"(intento {intento}/{INTENTOS})"
            )
            time.sleep(ESPERA_SEGUNDOS)

    if temporal.exists():
        temporal.unlink(missing_ok=True)

    raise ErrorInstalacion(
        f"No fue posible reemplazar el archivo:\n{ruta}\n\n"
        "Está siendo utilizado por otro proceso. Cierre todas las "
        "ventanas del ERP, Python y VS Code, y ejecute nuevamente."
    ) from ultimo_error


def copiar_seguro(origen: Path, destino: Path) -> None:
    ultimo_error = None

    for intento in range(1, INTENTOS + 1):
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origen, destino)
            return
        except PermissionError as error:
            ultimo_error = error
            print(
                f"  Archivo ocupado: {destino.name} "
                f"(intento {intento}/{INTENTOS})"
            )
            time.sleep(ESPERA_SEGUNDOS)

    raise ErrorInstalacion(
        f"No fue posible copiar:\n{origen}\n\na:\n{destino}\n\n"
        "Cierre todas las ventanas del ERP, Python y VS Code."
    ) from ultimo_error


def insertar_import(contenido: str) -> str:
    if "from proteccion_periodos import" in contenido:
        return contenido

    lineas = contenido.splitlines()
    indice = 0

    for i, linea in enumerate(lineas):
        if linea.startswith("import ") or linea.startswith("from "):
            indice = i + 1

    lineas[indice:indice] = [
        "",
        f"{MARCA} - IMPORT",
        "from proteccion_periodos import validar_periodo_abierto",
    ]
    return "\n".join(lineas) + "\n"


def insertar_despues(
    contenido: str,
    patron: str,
    bloque: str,
    descripcion: str
) -> str:
    if bloque.strip() in contenido:
        return contenido

    coincidencia = re.search(patron, contenido, flags=re.MULTILINE)

    if not coincidencia:
        raise ErrorInstalacion(
            f"No se encontró el punto de integración: {descripcion}"
        )

    fin = coincidencia.end()
    return contenido[:fin] + bloque + contenido[fin:]


def parche_motor(contenido: str) -> str:
    contenido = insertar_import(contenido)

    bloque = (
        "\n\n"
        f"    {MARCA} - MOTOR\n"
        "    validar_periodo_abierto(\n"
        "        fecha,\n"
        "        empresa_codigo=empresa_codigo,\n"
        "        ruta_db=ruta_db\n"
        "    )"
    )

    patron = (
        r'(\n    fecha = fecha or datetime\.now\(\)\.strftime'
        r'\("%Y-%m-%d %H:%M:%S"\)\n'
        r'    datetime\.strptime\(fecha\[:10\], "%Y-%m-%d"\))'
    )

    return insertar_despues(
        contenido,
        patron,
        bloque,
        "motor_contable.py / fecha normalizada"
    )


def parche_funcion_actual(
    contenido: str,
    linea_datos: str,
    descripcion: str
) -> str:
    contenido = insertar_import(contenido)

    bloque = (
        "\n"
        f"        {MARCA} - {descripcion.upper()}\n"
        "        validar_periodo_abierto(\n"
        "            datetime.now().strftime(\"%Y-%m-%d\")\n"
        "        )"
    )

    patron = rf'(\n    try:\n        {re.escape(linea_datos)})'

    return insertar_despues(
        contenido,
        patron,
        bloque,
        descripcion
    )


def parche_ventas(contenido: str) -> str:
    return parche_funcion_actual(
        contenido,
        "datos = obtener_datos_formulario()",
        "ventas"
    )


def parche_compras(contenido: str) -> str:
    return parche_funcion_actual(
        contenido,
        "datos = obtener_datos()",
        "compras"
    )


def parche_pago_cxc(contenido: str) -> str:
    return parche_funcion_actual(
        contenido,
        "datos = obtener_datos_recaudo()",
        "recaudos-cxc"
    )


def parche_pago_cxp(contenido: str) -> str:
    return parche_funcion_actual(
        contenido,
        "datos = obtener_datos_pago()",
        "pagos-cxp"
    )


OBJETIVOS = [
    ("motor_contable.py", parche_motor, True),
    ("ventas_contabilidad.py", parche_ventas, True),
    ("compras_contabilidad.py", parche_compras, True),
    ("pagos_cxc_contabilidad.py", parche_pago_cxc, True),
    ("pagos_cxp_contabilidad.py", parche_pago_cxp, True),
]


def main() -> int:
    print("=" * 72)
    print("BME-ERP - INSTALACIÓN ROBUSTA DEL BLOQUEO DE PERÍODOS")
    print("=" * 72)

    if not CARPETA_ERP.exists():
        print(f"ERROR: no existe la carpeta:\n{CARPETA_ERP}")
        return 1

    if not ARCHIVO_PROTECCION.exists():
        print(
            "ERROR: proteccion_periodos.py debe estar "
            "junto al instalador."
        )
        return 1

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    respaldo = (
        CARPETA_ERP
        / "backups"
        / f"antes_bloqueo_periodos_{marca_tiempo}"
    )
    respaldo.mkdir(parents=True, exist_ok=True)

    originales: dict[Path, bytes] = {}
    creados: list[Path] = []
    resultados = []

    try:
        print("\nVerificando archivos obligatorios...")
        for nombre, _, obligatorio in OBJETIVOS:
            ruta = CARPETA_ERP / nombre
            if obligatorio and not ruta.exists():
                raise ErrorInstalacion(
                    f"Falta el archivo obligatorio:\n{ruta}"
                )
            print(f"  OK  {nombre}")

        print("\nInstalando protección central...")
        destino_proteccion = CARPETA_ERP / "proteccion_periodos.py"

        if destino_proteccion.exists():
            originales[destino_proteccion] = destino_proteccion.read_bytes()
            copiar_seguro(
                destino_proteccion,
                respaldo / destino_proteccion.name
            )
        else:
            creados.append(destino_proteccion)

        copiar_seguro(ARCHIVO_PROTECCION, destino_proteccion)
        print("  OK  proteccion_periodos.py")

        print("\nIntegrando módulos...")
        for nombre, funcion_parche, obligatorio in OBJETIVOS:
            ruta = CARPETA_ERP / nombre

            if not ruta.exists():
                resultados.append((nombre, "OMITIDO"))
                continue

            print(f"  Procesando: {nombre}")
            originales[ruta] = ruta.read_bytes()
            copiar_seguro(ruta, respaldo / ruta.name)

            contenido = leer(ruta)

            if MARCA in contenido:
                resultados.append((nombre, "YA PROTEGIDO"))
                print("    Ya estaba protegido")
                continue

            nuevo = funcion_parche(contenido)

            # Validate before replacing the user's file.
            compile(nuevo, str(ruta), "exec")
            escribir_seguro(ruta, nuevo)

            resultados.append((nombre, "PROTEGIDO"))
            print("    Integración correcta")

        print("\nCompilación final...")
        archivos_compilar = [
            CARPETA_ERP / "proteccion_periodos.py"
        ] + [
            CARPETA_ERP / nombre
            for nombre, _, _ in OBJETIVOS
            if (CARPETA_ERP / nombre).exists()
        ]

        for ruta in archivos_compilar:
            py_compile.compile(str(ruta), doraise=True)
            print(f"  OK  {ruta.name}")

        print("\n" + "=" * 72)
        print("INSTALACIÓN COMPLETADA")
        print("=" * 72)
        print(f"Respaldo:\n{respaldo}\n")

        for nombre, estado in resultados:
            print(f"{estado:<20} {nombre}")

        print("=" * 72)
        return 0

    except Exception as error:
        print("\n" + "=" * 72)
        print("ERROR - REVERSIÓN AUTOMÁTICA")
        print("=" * 72)
        print(error)

        for ruta, datos in originales.items():
            try:
                temporal = ruta.with_suffix(ruta.suffix + ".restore_tmp")
                temporal.write_bytes(datos)
                os.replace(temporal, ruta)
            except Exception as restore_error:
                print(
                    f"ADVERTENCIA: no se pudo restaurar "
                    f"{ruta.name}: {restore_error}"
                )

        for ruta in creados:
            try:
                ruta.unlink(missing_ok=True)
            except Exception:
                pass

        print(f"\nRespaldo conservado en:\n{respaldo}")
        return 1


if __name__ == "__main__":
    codigo_salida = main()
    input("\nPresione ENTER para cerrar...")
    raise SystemExit(codigo_salida)
