"""
BME-ERP - Prueba del Sprint de Bloqueo de Períodos
Archivo: probar_bloqueo_periodos.py
No modifica información.
"""

import py_compile
from datetime import datetime
from pathlib import Path

from proteccion_periodos import (
    ErrorPeriodoContable,
    consultar_periodo,
    validar_periodo_abierto,
)

CARPETA = Path(r"C:\Users\jrive\visual")

ARCHIVOS = [
    "proteccion_periodos.py",
    "motor_contable.py",
    "ventas_contabilidad.py",
    "compras_contabilidad.py",
    "pagos_cxc_contabilidad.py",
    "pagos_cxp_contabilidad.py",
]


def main():
    print("=" * 72)
    print("BME-ERP - PRUEBA DEL BLOQUEO DE PERÍODOS")
    print("=" * 72)

    print("\n1. Verificación de archivos y sintaxis")
    for nombre in ARCHIVOS:
        ruta = CARPETA / nombre
        if not ruta.exists():
            print(f"  FALTA  {nombre}")
            continue

        py_compile.compile(str(ruta), doraise=True)
        contenido = ruta.read_text(encoding="utf-8")
        protegido = (
            "proteccion_periodos.py" in nombre
            or "# BME-PROTECCION-PERIODOS" in contenido
        )
        print(
            f"  {'OK' if protegido else 'SIN MARCA':<10} {nombre}"
        )

    print("\n2. Estado de los períodos de 2026")
    for mes in range(1, 13):
        fecha = f"2026-{mes:02d}-15"
        try:
            periodo = consultar_periodo(fecha)
            estado = periodo["estado"]
            print(f"  {fecha}  {estado}")
        except ErrorPeriodoContable as error:
            print(f"  {fecha}  ERROR: {error}")

    print("\n3. Prueba de la fecha actual")
    hoy = datetime.now().strftime("%Y-%m-%d")
    try:
        periodo = validar_periodo_abierto(hoy)
        print(
            f"  {hoy}: permitido "
            f"({periodo['anio']}-{int(periodo['mes']):02d})"
        )
    except ErrorPeriodoContable as error:
        print(f"  {hoy}: bloqueado")
        print(error)

    print("\nLa prueba no registró ni modificó información.")
    print("=" * 72)


if __name__ == "__main__":
    main()
    input("\nPresione ENTER para cerrar...")
