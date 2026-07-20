"""
BME-ERP - Instalador robusto V3 del bloqueo de períodos
Archivo: instalar_bloqueo_periodos_v3.py

Corrección V3:
- No intenta copiar proteccion_periodos.py sobre sí mismo.
- Identifica el archivo procesado.
- Crea respaldo.
- Valida antes de reemplazar.
- Revierte automáticamente si falla.
"""

from __future__ import annotations

import os
import py_compile
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

CARPETA_ERP = Path(r"C:\Users\jrive\visual")
ARCHIVO_PROTECCION = CARPETA_ERP / "proteccion_periodos.py"
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

    temporal.unlink(missing_ok=True)

    raise ErrorInstalacion(
        f"No fue posible reemplazar:\n{ruta}\n\n"
        "Cierre todas las ventanas del ERP y VS Code."
    ) from ultimo_error


def copiar_respaldo(origen: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origen, destino)


def insertar_import(contenido: str) -> str:
    if "from proteccion_periodos import validar_periodo_abierto" in contenido:
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

    coincidencia = re.search(
        patron,
        contenido,
        flags=re.MULTILINE
    )

    if not coincidencia:
        raise ErrorInstalacion(
            f"No se encontró el punto de integración en {descripcion}."
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
        "motor_contable.py"
    )


def parche_operacion(
    contenido: str,
    linea_datos: str,
    etiqueta: str
) -> str:
    contenido = insertar_import(contenido)

    bloque = (
        "\n"
        f"        {MARCA} - {etiqueta}\n"
        "        validar_periodo_abierto(\n"
        "            datetime.now().strftime(\"%Y-%m-%d\")\n"
        "        )"
    )

    patron = rf'(\n    try:\n        {re.escape(linea_datos)})'

    return insertar_despues(
        contenido,
        patron,
        bloque,
        etiqueta
    )


def parche_ventas(contenido: str) -> str:
    return parche_operacion(
        contenido,
        "datos = obtener_datos_formulario()",
        "VENTAS"
    )


def parche_compras(contenido: str) -> str:
    return parche_operacion(
        contenido,
        "datos = obtener_datos()",
        "COMPRAS"
    )


def parche_cxc(contenido: str) -> str:
    return parche_operacion(
        contenido,
        "datos = obtener_datos_recaudo()",
        "RECAUDOS-CXC"
    )


def parche_cxp(contenido: str) -> str:
    return parche_operacion(
        contenido,
        "datos = obtener_datos_pago()",
        "PAGOS-CXP"
    )


OBJETIVOS = [
    ("motor_contable.py", parche_motor),
    ("ventas_contabilidad.py", parche_ventas),
    ("compras_contabilidad.py", parche_compras),
    ("pagos_cxc_contabilidad.py", parche_cxc),
    ("pagos_cxp_contabilidad.py", parche_cxp),
]


def main() -> int:
    print("=" * 72)
    print("BME-ERP - INSTALACIÓN ROBUSTA V3 DEL BLOQUEO DE PERÍODOS")
    print("=" * 72)

    if not CARPETA_ERP.exists():
        print(f"ERROR: no existe la carpeta:\n{CARPETA_ERP}")
        return 1

    if not ARCHIVO_PROTECCION.exists():
        print(
            "ERROR: falta proteccion_periodos.py en:\n"
            f"{ARCHIVO_PROTECCION}"
        )
        return 1

    # Validar primero el archivo central.
    py_compile.compile(
        str(ARCHIVO_PROTECCION),
        doraise=True
    )

    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    respaldo = (
        CARPETA_ERP
        / "backups"
        / f"antes_bloqueo_periodos_v3_{marca_tiempo}"
    )
    respaldo.mkdir(parents=True, exist_ok=True)

    originales: dict[Path, bytes] = {}
    resultados = []

    try:
        print("\nProtección central:")
        print("  OK  proteccion_periodos.py ya está en destino")

        print("\nVerificando archivos obligatorios...")
        for nombre, _ in OBJETIVOS:
            ruta = CARPETA_ERP / nombre

            if not ruta.exists():
                raise ErrorInstalacion(
                    f"Falta el archivo obligatorio:\n{ruta}"
                )

            print(f"  OK  {nombre}")

        print("\nIntegrando módulos...")

        for nombre, funcion_parche in OBJETIVOS:
            ruta = CARPETA_ERP / nombre
            print(f"  Procesando: {nombre}")

            originales[ruta] = ruta.read_bytes()
            copiar_respaldo(
                ruta,
                respaldo / ruta.name
            )

            contenido = leer(ruta)

            if MARCA in contenido:
                resultados.append((nombre, "YA PROTEGIDO"))
                print("    Ya estaba protegido")
                continue

            nuevo = funcion_parche(contenido)

            # Validación sintáctica previa.
            compile(nuevo, str(ruta), "exec")

            escribir_seguro(ruta, nuevo)

            # Validación sintáctica posterior.
            py_compile.compile(
                str(ruta),
                doraise=True
            )

            resultados.append((nombre, "PROTEGIDO"))
            print("    Integración correcta")

        print("\nCompilación final...")

        archivos = [ARCHIVO_PROTECCION] + [
            CARPETA_ERP / nombre
            for nombre, _ in OBJETIVOS
        ]

        for ruta in archivos:
            py_compile.compile(
                str(ruta),
                doraise=True
            )
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
                temporal = ruta.with_suffix(
                    ruta.suffix + ".restore_tmp"
                )
                temporal.write_bytes(datos)
                os.replace(temporal, ruta)
            except Exception as restore_error:
                print(
                    f"ADVERTENCIA: no se pudo restaurar "
                    f"{ruta.name}: {restore_error}"
                )

        print(f"\nRespaldo conservado en:\n{respaldo}")
        return 1


if __name__ == "__main__":
    salida = main()
    input("\nPresione ENTER para cerrar...")
    raise SystemExit(salida)
