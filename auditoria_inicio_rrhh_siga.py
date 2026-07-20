"""
SIGA ERP - Auditoría inicial del módulo de Recursos Humanos
Archivo: auditoria_inicio_rrhh_siga.py

Este script NO modifica la base de datos.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RUTA_DB = BASE_DIR / "erp_cafe.db"

TABLAS = [
    "empleados",
    "nomina",
    "prestaciones",
    "usuarios_erp",
    "centros_costos",
    "centros_costo_contables",
    "empresas_contables",
    "auditoria_erp",
]

PATRONES = [
    "*emplead*.py",
    "*rrhh*.py",
    "*recursos_humanos*.py",
    "*nomina*.py",
    "*prestacion*.py",
    "*vacacion*.py",
    "*incapacidad*.py",
    "*contrato*.py",
    "*sst*.py",
]


def titulo(texto):
    print("\n" + "=" * 88)
    print(texto)
    print("=" * 88)


def existe_tabla(con, tabla):
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (tabla,),
    ).fetchone() is not None


def main():
    print("AUDITORÍA DE INICIO — RECURSOS HUMANOS SIGA ERP")
    print("Fecha y hora :", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Carpeta      :", BASE_DIR)
    print("Base de datos:", RUTA_DB)

    titulo("1. VALIDACIÓN")
    print("Existe carpeta:", "SÍ" if BASE_DIR.exists() else "NO")
    print("Existe base   :", "SÍ" if RUTA_DB.exists() else "NO")

    titulo("2. ARCHIVOS RELACIONADOS")
    archivos = {}
    for patron in PATRONES:
        for ruta in BASE_DIR.glob(patron):
            archivos[ruta.name.lower()] = ruta

    if archivos:
        for ruta in sorted(archivos.values(), key=lambda p: p.name.lower()):
            fecha = datetime.fromtimestamp(ruta.stat().st_mtime)
            print(
                f"- {ruta.name} | {ruta.stat().st_size:,} bytes | "
                f"{fecha:%Y-%m-%d %H:%M:%S}"
            )
    else:
        print("No se encontraron archivos relacionados.")

    if not RUTA_DB.exists():
        raise FileNotFoundError(f"No se encontró la base de datos: {RUTA_DB}")

    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row

    titulo("3. TABLAS OBJETIVO")
    for tabla in TABLAS:
        if existe_tabla(con, tabla):
            total = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            print(f"- {tabla}: EXISTE | registros={total}")
        else:
            print(f"- {tabla}: NO EXISTE")

    for tabla in TABLAS:
        if not existe_tabla(con, tabla):
            continue

        titulo(f"4. ESTRUCTURA: {tabla}")
        for col in con.execute(f"PRAGMA table_info({tabla})"):
            print(
                f"{col['cid']:>2} | {col['name']:<30} | "
                f"{col['type']:<15} | NOT NULL={col['notnull']} | "
                f"PK={col['pk']} | DEFAULT={col['dflt_value']}"
            )

        print("\nÍndices:")
        indices = con.execute(f"PRAGMA index_list({tabla})").fetchall()
        if indices:
            for fila in indices:
                print(tuple(fila))
        else:
            print("Sin índices adicionales.")

        print("\nRelaciones:")
        relaciones = con.execute(f"PRAGMA foreign_key_list({tabla})").fetchall()
        if relaciones:
            for fila in relaciones:
                print(tuple(fila))
        else:
            print("Sin claves foráneas.")

        print("\nMuestra:")
        filas = con.execute(f"SELECT * FROM {tabla} LIMIT 5").fetchall()
        if not filas:
            print("Sin registros.")
        else:
            print(" | ".join(filas[0].keys()))
            for fila in filas:
                valores = []
                for nombre in fila.keys():
                    texto = "" if fila[nombre] is None else str(fila[nombre])
                    valores.append(texto[:35])
                print(" | ".join(valores))

    con.close()

    titulo("AUDITORÍA FINALIZADA")
    print("El diagnóstico no modificó la base de datos. dshajkdnasjkdansjkdnjks")
    print("Copia toda la salida y envíala para preparar RR. HH. v1.")


if __name__ == "__main__":
    main()
