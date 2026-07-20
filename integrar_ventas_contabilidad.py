from pathlib import Path
from datetime import datetime
import re
import shutil
import sys


BASE_DIR = Path(__file__).resolve().parent
MOTOR = BASE_DIR / "motor_contable.py"
VENTAS = BASE_DIR / "ventas_integradas.py"
RESPALDOS = BASE_DIR / "respaldos"


def detener(mensaje):
    print(f"\n[ERROR] {mensaje}")
    sys.exit(1)


def reemplazar_unico(texto, anterior, nuevo, descripcion):
    cantidad = texto.count(anterior)

    if cantidad != 1:
        detener(
            f"No se pudo aplicar '{descripcion}'. "
            f"Coincidencias encontradas: {cantidad}"
        )

    return texto.replace(anterior, nuevo, 1)


def respaldar():
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = RESPALDOS / f"integracion_ventas_contabilidad_{fecha}"
    carpeta.mkdir(parents=True, exist_ok=False)

    shutil.copy2(MOTOR, carpeta / MOTOR.name)
    shutil.copy2(VENTAS, carpeta / VENTAS.name)

    print(f"[OK] Respaldo creado en:\n{carpeta}")
    return carpeta


def actualizar_motor(texto):
    # --------------------------------------------------------
    # 1. Ruta portátil
    # --------------------------------------------------------
    patron_ruta = re.compile(
        r'RUTA_DB\s*=\s*Path\('
        r'r?["\']C:\\Users\\jrive\\visual\\erp_cafe\.db["\']'
        r'\)'
    )

    texto, cantidad = patron_ruta.subn(
        'BASE_DIR = Path(__file__).resolve().parent\n'
        'RUTA_DB = BASE_DIR / "erp_cafe.db"',
        texto,
        count=1
    )

    if cantidad == 1:
        print("[OK] Ruta portátil configurada en motor_contable.py")
    elif 'RUTA_DB = BASE_DIR / "erp_cafe.db"' in texto:
        print("[OK] El motor ya utilizaba una ruta portátil")
    else:
        detener("No se encontró la ruta fija del motor contable.")

    # --------------------------------------------------------
    # 2. Permitir conexión externa
    # --------------------------------------------------------
    if "conexion_externa=None" not in texto:
        texto = reemplazar_unico(
            texto,
            """    tipo_comprobante_codigo=None,
    ruta_db=RUTA_DB
):""",
            """    tipo_comprobante_codigo=None,
    ruta_db=RUTA_DB,
    conexion_externa=None
):""",
            "agregar conexion_externa a contabilizar_evento"
        )
        print("[OK] Parámetro conexion_externa agregado")
    else:
        print("[OK] El motor ya admite conexión externa")

    # --------------------------------------------------------
    # 3. Control transaccional
    # --------------------------------------------------------
    patron_inicio = re.compile(
        r'''    # BME-PROTECCION-PERIODOS - MOTOR\s+
    validar_periodo_abierto\(\s+
        fecha,\s+
        empresa_codigo=empresa_codigo,\s+
        ruta_db=ruta_db\s+
    \)\s+

    conexion = None\s+

    try:\s+
        conexion = conectar\(ruta_db\)\s+
        cursor = conexion\.cursor\(\)\s+
        cursor\.execute\("BEGIN IMMEDIATE"\)''',
        re.VERBOSE
    )

    bloque_nuevo = '''    # La contabilización puede ejecutarse de dos formas:
    # 1. Con conexión propia.
    # 2. Dentro de la transacción del módulo que origina el movimiento.
    conexion = None
    conexion_propia = conexion_externa is None
    row_factory_anterior = None

    try:
        if conexion_propia:
            validar_periodo_abierto(
                fecha,
                empresa_codigo=empresa_codigo,
                ruta_db=ruta_db
            )

            conexion = conectar(ruta_db)
            cursor = conexion.cursor()
            cursor.execute("BEGIN IMMEDIATE")
        else:
            conexion = conexion_externa
            row_factory_anterior = conexion.row_factory
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()'''

    texto, cantidad = patron_inicio.subn(
        bloque_nuevo,
        texto,
        count=1
    )

    if cantidad == 1:
        print("[OK] Inicio transaccional del motor actualizado")
    elif "conexion_propia = conexion_externa is None" in texto:
        print("[OK] El control transaccional ya estaba actualizado")
    else:
        detener(
            "No se pudo localizar el inicio transaccional "
            "de contabilizar_evento."
        )

    # Trabajamos solamente dentro de contabilizar_evento.
    inicio = texto.find("def contabilizar_evento(")
    final = texto.find(
        "# ============================================================\n"
        "# CONSULTA DE COMPROBANTE",
        inicio
    )

    if inicio == -1 or final == -1:
        detener("No se pudo aislar la función contabilizar_evento.")

    antes = texto[:inicio]
    funcion = texto[inicio:final]
    despues = texto[final:]

    # --------------------------------------------------------
    # 4. Commit solamente cuando el motor abrió la conexión
    # --------------------------------------------------------
    if "if conexion_propia:\n            conexion.commit()" not in funcion:
        funcion = reemplazar_unico(
            funcion,
            "        conexion.commit()",
            """        if conexion_propia:
            conexion.commit()""",
            "commit condicional"
        )
        print("[OK] Commit condicional configurado")

    # --------------------------------------------------------
    # 5. Rollback y cierre condicional
    # --------------------------------------------------------
    bloque_anterior = '''    except Exception:
        if conexion:
            conexion.rollback()
        raise

    finally:
        if conexion:
            conexion.close()
'''

    bloque_nuevo = '''    except Exception:
        if conexion and conexion_propia:
            conexion.rollback()
        raise

    finally:
        if (
            conexion
            and not conexion_propia
            and row_factory_anterior is not None
        ):
            conexion.row_factory = row_factory_anterior

        if conexion and conexion_propia:
            conexion.close()
'''

    if bloque_anterior in funcion:
        funcion = funcion.replace(
            bloque_anterior,
            bloque_nuevo,
            1
        )
        print("[OK] Rollback y cierre condicional configurados")
    elif "and conexion_propia" in funcion:
        print("[OK] Rollback condicional ya configurado")
    else:
        detener("No se encontró el bloque final de transacción del motor.")

    return antes + funcion + despues


def actualizar_ventas(texto):
    # --------------------------------------------------------
    # 1. Importar motor contable
    # --------------------------------------------------------
    importacion = (
        "from motor_contable import contabilizar_evento"
    )

    if importacion not in texto:
        texto = reemplazar_unico(
            texto,
            "from proteccion_periodos import validar_periodo_abierto",
            """from proteccion_periodos import validar_periodo_abierto
from motor_contable import contabilizar_evento""",
            "importar motor contable"
        )
        print("[OK] Motor contable importado en Ventas")
    else:
        print("[OK] Ventas ya importaba el motor contable")

    inicio = texto.find("def guardar_venta():")
    final = texto.find(
        "# ============================================================\n"
        "# HISTORIAL Y ANULACIÓN",
        inicio
    )

    # Compatibilidad con archivos que muestran caracteres alterados.
    if final == -1:
        final = texto.find(
            "# ============================================================\n"
            "# HISTORIAL Y ANULACI",
            inicio
        )

    if inicio == -1 or final == -1:
        detener("No se pudo aislar guardar_venta().")

    antes = texto[:inicio]
    funcion = texto[inicio:final]
    despues = texto[final:]

    # --------------------------------------------------------
    # 2. Insertar contabilización antes de auditoría y commit
    # --------------------------------------------------------
    marca = '''        registrar_auditoria(
            conexion,
            "REGISTRAR VENTA",'''

    bloque = '''        evento_contable = (
            "VENTA_CONTADO"
            if forma_pago == "CONTADO"
            else "VENTA_CREDITO"
        )

        documento_cliente_contable = (
            cliente[0]
            or f"CLIENTE-{cliente_id}"
        )

        resultado_contable = contabilizar_evento(
            evento=evento_contable,
            valores={
                "total": total,
                "subtotal_sin_iva": base,
                "subtotal": base,
                "descuento": descuento,
                "iva": iva,
                "costo_total": costo_total_venta,
                "utilidad": utilidad_total
            },
            concepto=(
                f"Venta {lbl_numero.cget('text')} "
                f"a {cliente[1]}"
            ),
            modulo_origen="VENTAS",
            tabla_origen="ventas_integradas",
            registro_origen_id=venta_id,
            tercero={
                "tipo_documento": "NIT",
                "numero_documento": documento_cliente_contable,
                "nombre_razon_social": cliente[1],
                "tipo_tercero": "CLIENTE"
            },
            fecha=fecha_venta,
            documento_referencia=(
                entry_factura.get().strip()
                or lbl_numero.cget("text")
            ),
            usuario=os.environ.get(
                "ERP_USUARIO",
                "usuario_local"
            ),
            ruta_db=RUTA_DB,
            conexion_externa=conexion
        )

        registrar_auditoria(
            conexion,
            "REGISTRAR VENTA",'''

    if "resultado_contable = contabilizar_evento(" not in funcion:
        funcion = reemplazar_unico(
            funcion,
            marca,
            bloque,
            "integrar guardar_venta con contabilidad"
        )
        print("[OK] Contabilización integrada en guardar_venta")
    else:
        print("[OK] guardar_venta ya estaba integrado")

    # --------------------------------------------------------
    # 3. Mostrar comprobante generado
    # --------------------------------------------------------
    texto_actual = '''                f"Venta guardada correctamente.\\n\\n"
                f"Total: {moneda(total)}\\n"'''

    texto_nuevo = '''                f"Venta guardada correctamente.\\n\\n"
                f"Comprobante contable: "
                f"{resultado_contable['consecutivo']}\\n"
                f"Total: {moneda(total)}\\n"'''

    if "Comprobante contable:" not in funcion:
        if texto_actual not in funcion:
            detener(
                "No se encontró el mensaje final de venta "
                "para agregar el comprobante."
            )

        funcion = funcion.replace(
            texto_actual,
            texto_nuevo,
            1
        )
        print("[OK] Comprobante agregado al mensaje final")

    return antes + funcion + despues


def main():
    print("=" * 70)
    print("INTEGRACIÓN TRANSACCIONAL VENTAS - CONTABILIDAD")
    print("=" * 70)

    if not MOTOR.exists():
        detener(f"No existe {MOTOR.name}")

    if not VENTAS.exists():
        detener(f"No existe {VENTAS.name}")

    respaldar()

    motor_texto = MOTOR.read_text(
        encoding="utf-8",
        errors="strict"
    )
    ventas_texto = VENTAS.read_text(
        encoding="utf-8",
        errors="strict"
    )

    motor_nuevo = actualizar_motor(motor_texto)
    ventas_nuevo = actualizar_ventas(ventas_texto)

    MOTOR.write_text(
        motor_nuevo,
        encoding="utf-8",
        newline="\n"
    )
    VENTAS.write_text(
        ventas_nuevo,
        encoding="utf-8",
        newline="\n"
    )

    print("\n" + "=" * 70)
    print("[OK] INTEGRACIÓN APLICADA")
    print("=" * 70)
    print("Archivos modificados:")
    print(f"- {MOTOR.name}")
    print(f"- {VENTAS.name}")
    print("\nAhora ejecute:")
    print("python -m py_compile motor_contable.py")
    print("python -m py_compile ventas_integradas.py")


if __name__ == "__main__":
    main()