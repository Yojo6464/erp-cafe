"""
BME-ERP - Compras con Contabilidad Automática
Archivo: compras_contabilidad.py

Funciones:
- Registra compras de contado y a crédito.
- Actualiza inventario con costo promedio ponderado.
- Registra entrada en kardex.
- Crea cuenta por pagar en compras a crédito.
- Descuenta el banco en compras de contado.
- Genera comprobante contable automático.
- Revierte la operación comercial si falla la contabilidad.
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

from motor_contable import contabilizar_evento, ErrorContable

# BME-PROTECCION-PERIODOS - IMPORT
from proteccion_periodos import validar_periodo_abierto

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")
USUARIO = (
    os.environ.get("ERP_USUARIO", "").strip()
    or os.environ.get("USERNAME", "SISTEMA")
)

COLOR_FONDO = "#EEF3F8"
COLOR_TARJETA = "#FFFFFF"
COLOR_AZUL = "#0F5C8E"
COLOR_VERDE = "#15803D"
COLOR_ROJO = "#B42318"
COLOR_TEXTO = "#1F2937"
COLOR_SUAVE = "#64748B"
COLOR_BORDE = "#D7E0E8"


# ============================================================
# BASE DE DATOS
# ============================================================

def conectar():
    if not RUTA_DB.exists():
        raise FileNotFoundError(f"No se encontró la base:\n{RUTA_DB}")

    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def columnas_tabla(cursor, tabla):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return {fila["name"] for fila in cursor.fetchall()}


def agregar_columna(cursor, tabla, nombre, definicion):
    if nombre not in columnas_tabla(cursor, tabla):
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"
        )


def preparar_estructura():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        agregar_columna(
            cursor, "compras", "producto", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "compras", "presentacion", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "compras", "cantidad", "REAL DEFAULT 0"
        )
        agregar_columna(
            cursor, "compras", "costo_unitario", "REAL DEFAULT 0"
        )
        agregar_columna(
            cursor, "compras", "iva_porcentaje", "REAL DEFAULT 0"
        )
        agregar_columna(
            cursor, "compras", "proveedor_documento", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "compras", "banco_id", "INTEGER"
        )
        agregar_columna(
            cursor, "compras", "comprobante_id", "INTEGER"
        )
        agregar_columna(
            cursor, "compras", "comprobante_numero", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "compras", "estado_contable", "TEXT DEFAULT 'PENDIENTE'"
        )

        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# UTILIDADES
# ============================================================

def numero(texto, nombre, permitir_cero=False):
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{nombre} debe ser un número válido.")

    if permitir_cero:
        if valor < 0:
            raise ValueError(f"{nombre} no puede ser negativo.")
    elif valor <= 0:
        raise ValueError(f"{nombre} debe ser mayor que cero.")

    return valor


def moneda(valor):
    return f"${float(valor):,.0f}"


def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# CARGA DE DATOS
# ============================================================

mapa_proveedores = {}
mapa_bancos = {}


def cargar_proveedores():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, nombre,
                   COALESCE(telefono, '') AS telefono,
                   COALESCE(ciudad, '') AS ciudad,
                   COALESCE(correo, '') AS correo
            FROM proveedores
            ORDER BY nombre
        """)

        mapa_proveedores.clear()
        opciones = []

        for fila in cursor.fetchall():
            texto = fila["nombre"]
            opciones.append(texto)
            mapa_proveedores[texto] = dict(fila)

        combo_proveedor["values"] = opciones

    finally:
        conexion.close()


def cargar_bancos():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id, banco, numero_cuenta, saldo
            FROM bancos
            WHERE UPPER(estado)='ACTIVA'
            ORDER BY banco
        """)

        mapa_bancos.clear()
        opciones = []

        for fila in cursor.fetchall():
            texto = (
                f"{fila['id']} - {fila['banco']} - "
                f"{fila['numero_cuenta']} - {moneda(fila['saldo'])}"
            )
            opciones.append(texto)
            mapa_bancos[texto] = dict(fila)

        combo_banco["values"] = opciones

    finally:
        conexion.close()


# ============================================================
# CÁLCULOS
# ============================================================

def calcular(mostrar_error=True):
    try:
        cantidad = numero(entrada_cantidad.get(), "La cantidad")
        costo_unitario = numero(
            entrada_costo_unitario.get(),
            "El costo unitario"
        )
        iva_porcentaje = numero(
            combo_iva.get() or "0",
            "El IVA",
            permitir_cero=True
        )

        subtotal = round(cantidad * costo_unitario, 2)
        iva = round(subtotal * iva_porcentaje / 100, 2)
        total = round(subtotal + iva, 2)

        lbl_subtotal.config(text=moneda(subtotal))
        lbl_iva.config(text=moneda(iva))
        lbl_total.config(text=moneda(total))

        return {
            "cantidad": cantidad,
            "costo_unitario": costo_unitario,
            "iva_porcentaje": iva_porcentaje,
            "subtotal": subtotal,
            "iva": iva,
            "total": total
        }

    except ValueError as error:
        if mostrar_error:
            messagebox.showerror("Compra", str(error))
        return None


def actualizar_calculo(evento=None):
    calcular(False)


def cambiar_forma_pago(evento=None):
    credito = combo_forma_pago.get().upper() == "CRÉDITO"

    if credito:
        entrada_dias.config(state="normal")
        if not entrada_dias.get().strip():
            entrada_dias.insert(0, "30")
        combo_banco.set("")
        combo_banco.config(state="disabled")
    else:
        entrada_dias.config(state="normal")
        entrada_dias.delete(0, tk.END)
        entrada_dias.insert(0, "0")
        entrada_dias.config(state="disabled")
        combo_banco.config(state="readonly")


# ============================================================
# VALIDACIÓN
# ============================================================

def obtener_datos():
    proveedor = combo_proveedor.get().strip()
    documento = entrada_documento.get().strip()
    producto = entrada_producto.get().strip()
    presentacion = entrada_presentacion.get().strip()
    lote = entrada_lote.get().strip()
    factura = entrada_factura.get().strip()
    forma_pago = combo_forma_pago.get().strip().upper()
    observaciones = entrada_observaciones.get().strip()

    if not proveedor:
        raise ValueError("Seleccione un proveedor.")

    if not documento:
        raise ValueError("Ingrese el NIT o documento del proveedor.")

    if not producto:
        raise ValueError("Ingrese el producto comprado.")

    if not presentacion:
        raise ValueError("Ingrese la presentación.")

    if not factura:
        raise ValueError("Ingrese la factura del proveedor.")

    if forma_pago not in ("CONTADO", "CRÉDITO"):
        raise ValueError("Seleccione CONTADO o CRÉDITO.")

    valores = calcular(False)

    if not valores:
        raise ValueError("Revise cantidad, costo e IVA.")

    try:
        dias = int(entrada_dias.get().strip() or "0")
    except ValueError:
        raise ValueError("Los días de crédito deben ser enteros.")

    banco = None

    if forma_pago == "CONTADO":
        banco = mapa_bancos.get(combo_banco.get())

        if not banco:
            raise ValueError(
                "Seleccione el banco para pagar la compra."
            )

        if float(banco["saldo"]) < valores["total"]:
            raise ValueError(
                "El banco seleccionado no tiene saldo suficiente."
            )

        dias = 0

    elif dias <= 0:
        raise ValueError(
            "En compra a crédito, los días deben ser mayores que cero."
        )

    return {
        "proveedor": proveedor,
        "documento": documento,
        "producto": producto,
        "presentacion": presentacion,
        "lote": lote,
        "factura": factura,
        "forma_pago": forma_pago,
        "dias_credito": dias,
        "banco": banco,
        "observaciones": observaciones,
        **valores
    }


# ============================================================
# REGISTRO COMERCIAL
# ============================================================

def registrar_compra(datos):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        fecha = fecha_actual()

        vencimiento = ""
        if datos["forma_pago"] == "CRÉDITO":
            vencimiento = (
                datetime.now()
                + timedelta(days=datos["dias_credito"])
            ).strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO compras(
                fecha, proveedor, tipo_compra, descripcion,
                valor, forma_pago, dias_credito, factura,
                subtotal, iva, total, estado,
                observaciones, vencimiento,
                producto, presentacion, cantidad,
                costo_unitario, iva_porcentaje,
                proveedor_documento, banco_id,
                estado_contable
            )
            VALUES (
                ?, ?, 'INVENTARIO', ?, ?, ?, ?, ?,
                ?, ?, ?, 'RECIBIDA', ?, ?,
                ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE'
            )
        """, (
            fecha,
            datos["proveedor"],
            f"{datos['producto']} {datos['presentacion']}",
            datos["total"],
            datos["forma_pago"],
            datos["dias_credito"],
            datos["factura"],
            datos["subtotal"],
            datos["iva"],
            datos["total"],
            datos["observaciones"],
            vencimiento,
            datos["producto"],
            datos["presentacion"],
            datos["cantidad"],
            datos["costo_unitario"],
            datos["iva_porcentaje"],
            datos["documento"],
            datos["banco"]["id"] if datos["banco"] else None
        ))

        compra_id = int(cursor.lastrowid)

        cursor.execute("""
            SELECT id, cantidad,
                   COALESCE(costo_unitario, costo, 0) AS costo_actual
            FROM inventario
            WHERE producto=? AND presentacion=?
            ORDER BY id
            LIMIT 1
        """, (
            datos["producto"],
            datos["presentacion"]
        ))

        inventario = cursor.fetchone()

        if inventario:
            cantidad_anterior = float(inventario["cantidad"] or 0)
            costo_anterior = float(inventario["costo_actual"] or 0)
            nueva_cantidad = cantidad_anterior + datos["cantidad"]

            nuevo_costo = (
                (
                    cantidad_anterior * costo_anterior
                    + datos["cantidad"] * datos["costo_unitario"]
                ) / nueva_cantidad
                if nueva_cantidad > 0
                else datos["costo_unitario"]
            )

            cursor.execute("""
                UPDATE inventario
                SET cantidad=?,
                    costo_unitario=?,
                    costo=?,
                    lote=?,
                    fecha_ingreso=?
                WHERE id=?
            """, (
                nueva_cantidad,
                nuevo_costo,
                nuevo_costo,
                datos["lote"],
                fecha,
                inventario["id"]
            ))

            inventario_id = int(inventario["id"])

        else:
            cantidad_anterior = 0
            costo_anterior = 0
            nueva_cantidad = datos["cantidad"]
            nuevo_costo = datos["costo_unitario"]

            cursor.execute("""
                INSERT INTO inventario(
                    producto, presentacion, cantidad, lote,
                    costo_unitario, fecha_ingreso,
                    costo, fecha
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["producto"],
                datos["presentacion"],
                nueva_cantidad,
                datos["lote"],
                nuevo_costo,
                fecha,
                nuevo_costo,
                fecha
            ))

            inventario_id = int(cursor.lastrowid)

        cursor.execute("""
            INSERT INTO kardex(
                fecha, producto, presentacion, movimiento,
                entrada, salida, saldo, costo_unitario,
                lote, origen, observaciones
            )
            VALUES (?, ?, ?, 'ENTRADA', ?, 0, ?, ?, ?, 'COMPRA', ?)
        """, (
            fecha,
            datos["producto"],
            datos["presentacion"],
            datos["cantidad"],
            nueva_cantidad,
            datos["costo_unitario"],
            datos["lote"],
            f"Compra #{compra_id} - Factura {datos['factura']}"
        ))

        kardex_id = int(cursor.lastrowid)
        cuenta_pagar_id = None
        movimiento_banco_id = None
        saldo_banco_anterior = None

        if datos["forma_pago"] == "CRÉDITO":
            cursor.execute("""
                INSERT INTO cuentas_pagar(
                    proveedor, valor, saldo,
                    fecha, vencimiento, estado
                )
                VALUES (?, ?, ?, ?, ?, 'PENDIENTE')
            """, (
                datos["proveedor"],
                datos["total"],
                datos["total"],
                fecha,
                vencimiento
            ))

            cuenta_pagar_id = int(cursor.lastrowid)

        else:
            banco_id = int(datos["banco"]["id"])

            cursor.execute("""
                SELECT saldo
                FROM bancos
                WHERE id=? AND UPPER(estado)='ACTIVA'
            """, (banco_id,))

            fila_banco = cursor.fetchone()

            if not fila_banco:
                raise ValueError("El banco ya no está disponible.")

            saldo_banco_anterior = float(fila_banco["saldo"])

            if saldo_banco_anterior < datos["total"]:
                raise ValueError("Saldo bancario insuficiente.")

            nuevo_saldo = saldo_banco_anterior - datos["total"]

            cursor.execute("""
                UPDATE bancos
                SET saldo=?
                WHERE id=?
            """, (nuevo_saldo, banco_id))

            cursor.execute("""
                INSERT INTO movimientos_bancos(
                    fecha, banco_id, tipo, concepto,
                    valor, saldo_anterior, saldo_nuevo,
                    autorizado_por
                )
                VALUES (?, ?, 'COMPRA CONTADO', ?, ?, ?, ?, ?)
            """, (
                fecha,
                banco_id,
                f"Compra #{compra_id} - {datos['proveedor']}",
                datos["total"],
                saldo_banco_anterior,
                nuevo_saldo,
                USUARIO
            ))

            movimiento_banco_id = int(cursor.lastrowid)

        conexion.commit()

        return {
            "compra_id": compra_id,
            "fecha": fecha,
            "inventario_id": inventario_id,
            "cantidad_anterior": cantidad_anterior,
            "costo_anterior": costo_anterior,
            "kardex_id": kardex_id,
            "cuenta_pagar_id": cuenta_pagar_id,
            "movimiento_banco_id": movimiento_banco_id,
            "saldo_banco_anterior": saldo_banco_anterior,
            "banco_id": datos["banco"]["id"] if datos["banco"] else None
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def revertir_compra(resultado):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        if resultado["movimiento_banco_id"]:
            cursor.execute(
                "DELETE FROM movimientos_bancos WHERE id=?",
                (resultado["movimiento_banco_id"],)
            )
            cursor.execute(
                "UPDATE bancos SET saldo=? WHERE id=?",
                (
                    resultado["saldo_banco_anterior"],
                    resultado["banco_id"]
                )
            )

        if resultado["cuenta_pagar_id"]:
            cursor.execute(
                "DELETE FROM cuentas_pagar WHERE id=?",
                (resultado["cuenta_pagar_id"],)
            )

        cursor.execute(
            "DELETE FROM kardex WHERE id=?",
            (resultado["kardex_id"],)
        )

        if resultado["cantidad_anterior"] == 0:
            cursor.execute(
                "DELETE FROM inventario WHERE id=?",
                (resultado["inventario_id"],)
            )
        else:
            cursor.execute("""
                UPDATE inventario
                SET cantidad=?, costo_unitario=?, costo=?
                WHERE id=?
            """, (
                resultado["cantidad_anterior"],
                resultado["costo_anterior"],
                resultado["costo_anterior"],
                resultado["inventario_id"]
            ))

        cursor.execute(
            "DELETE FROM compras WHERE id=?",
            (resultado["compra_id"],)
        )

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def actualizar_comprobante(compra_id, comprobante):
    conexion = conectar()

    try:
        conexion.execute("""
            UPDATE compras
            SET comprobante_id=?,
                comprobante_numero=?,
                estado_contable='CONTABILIZADO'
            WHERE id=?
        """, (
            comprobante["comprobante_id"],
            comprobante["consecutivo"],
            compra_id
        ))
        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# GUARDAR Y CONTABILIZAR
# ============================================================

def guardar_compra():
    boton_guardar.config(state="disabled")
    resultado = None

    try:
        datos = obtener_datos()
        # BME-PROTECCION-PERIODOS - COMPRAS
        validar_periodo_abierto(
            datetime.now().strftime("%Y-%m-%d")
        )
        resultado = registrar_compra(datos)

        evento = (
            "COMPRA_CONTADO"
            if datos["forma_pago"] == "CONTADO"
            else "COMPRA_CREDITO"
        )

        comprobante = contabilizar_evento(
            evento=evento,
            valores={
                "subtotal": datos["subtotal"],
                "iva": datos["iva"],
                "total": datos["total"]
            },
            concepto=(
                f"Compra factura {datos['factura']} - "
                f"{datos['producto']} {datos['presentacion']} "
                f"a {datos['proveedor']}"
            ),
            modulo_origen="COMPRAS",
            tabla_origen="compras",
            registro_origen_id=resultado["compra_id"],
            tercero={
                "tipo_documento": "NIT",
                "numero_documento": datos["documento"],
                "nombre_razon_social": datos["proveedor"],
                "tipo_tercero": "PROVEEDOR",
                "origen_modulo": "COMPRAS"
            },
            centro_costo="PROD",
            fecha=resultado["fecha"],
            documento_referencia=datos["factura"],
            usuario=USUARIO
        )

        actualizar_comprobante(resultado["compra_id"], comprobante)

        messagebox.showinfo(
            "Compra contabilizada",
            (
                f"Compra No. {resultado['compra_id']}\n"
                f"Factura: {datos['factura']}\n"
                f"Forma de pago: {datos['forma_pago']}\n\n"
                f"Subtotal: {moneda(datos['subtotal'])}\n"
                f"IVA: {moneda(datos['iva'])}\n"
                f"Total: {moneda(datos['total'])}\n\n"
                f"Comprobante:\n{comprobante['consecutivo']}"
            )
        )

        limpiar()
        cargar_bancos()

    except Exception as error:
        mensaje = ""

        if resultado:
            try:
                revertir_compra(resultado)
                mensaje = (
                    "\n\nLa compra, inventario, kardex, "
                    "CxP y banco fueron revertidos."
                )
            except Exception as error_reversion:
                mensaje = (
                    "\n\nATENCIÓN: falló la reversión.\n"
                    f"{error_reversion}"
                )

        messagebox.showerror(
            "No fue posible registrar la compra",
            f"{error}{mensaje}"
        )

    finally:
        boton_guardar.config(state="normal")


def limpiar():
    combo_proveedor.set("")
    entrada_documento.delete(0, tk.END)
    entrada_producto.delete(0, tk.END)
    entrada_presentacion.delete(0, tk.END)
    entrada_lote.delete(0, tk.END)
    entrada_factura.delete(0, tk.END)
    entrada_cantidad.delete(0, tk.END)
    entrada_costo_unitario.delete(0, tk.END)
    combo_iva.set("0")
    combo_forma_pago.set("CRÉDITO")
    entrada_observaciones.delete(0, tk.END)
    lbl_subtotal.config(text="$0")
    lbl_iva.config(text="$0")
    lbl_total.config(text="$0")
    cambiar_forma_pago()


# ============================================================
# INTERFAZ
# ============================================================

preparar_estructura()

ventana = tk.Tk()
ventana.title("BME-ERP - Compras con Contabilidad Automática")
ventana.geometry("930x800")
ventana.minsize(850, 720)
ventana.configure(bg=COLOR_FONDO)

estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

cabecera = tk.Frame(ventana, bg=COLOR_AZUL, height=92)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="COMPRAS CON CONTABILIDAD AUTOMÁTICA",
    font=("Segoe UI", 19, "bold"),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=30, pady=(17, 0))

tk.Label(
    cabecera,
    text="Compra, inventario, kardex, proveedores y comprobante",
    font=("Segoe UI", 9),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=31, pady=(3, 0))

contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
contenedor.pack(fill="both", expand=True, padx=25, pady=20)

tarjeta = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
tarjeta.pack(fill="both", expand=True)

formulario = tk.Frame(tarjeta, bg=COLOR_TARJETA)
formulario.pack(fill="x", padx=28, pady=22)

formulario.columnconfigure(1, weight=1)
formulario.columnconfigure(3, weight=1)

def etiqueta(texto, fila, columna):
    tk.Label(
        formulario,
        text=texto,
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 9, "bold")
    ).grid(
        row=fila,
        column=columna,
        sticky="w",
        padx=(0, 10),
        pady=7
    )

etiqueta("Proveedor", 0, 0)
combo_proveedor = ttk.Combobox(
    formulario, state="readonly", width=30
)
combo_proveedor.grid(
    row=0, column=1, sticky="ew", padx=(0, 20), pady=7
)

etiqueta("NIT / Documento", 0, 2)
entrada_documento = ttk.Entry(formulario)
entrada_documento.grid(row=0, column=3, sticky="ew", pady=7)

etiqueta("Producto", 1, 0)
entrada_producto = ttk.Entry(formulario)
entrada_producto.grid(
    row=1, column=1, sticky="ew", padx=(0, 20), pady=7
)

etiqueta("Presentación", 1, 2)
entrada_presentacion = ttk.Entry(formulario)
entrada_presentacion.grid(row=1, column=3, sticky="ew", pady=7)

etiqueta("Lote", 2, 0)
entrada_lote = ttk.Entry(formulario)
entrada_lote.grid(
    row=2, column=1, sticky="ew", padx=(0, 20), pady=7
)

etiqueta("Factura proveedor", 2, 2)
entrada_factura = ttk.Entry(formulario)
entrada_factura.grid(row=2, column=3, sticky="ew", pady=7)

etiqueta("Cantidad", 3, 0)
entrada_cantidad = ttk.Entry(formulario)
entrada_cantidad.grid(
    row=3, column=1, sticky="ew", padx=(0, 20), pady=7
)
entrada_cantidad.bind("<KeyRelease>", actualizar_calculo)

etiqueta("Costo unitario sin IVA", 3, 2)
entrada_costo_unitario = ttk.Entry(formulario)
entrada_costo_unitario.grid(row=3, column=3, sticky="ew", pady=7)
entrada_costo_unitario.bind("<KeyRelease>", actualizar_calculo)

etiqueta("IVA (%)", 4, 0)
combo_iva = ttk.Combobox(
    formulario,
    values=["0", "5", "19"],
    state="readonly"
)
combo_iva.grid(
    row=4, column=1, sticky="ew", padx=(0, 20), pady=7
)
combo_iva.set("0")
combo_iva.bind("<<ComboboxSelected>>", actualizar_calculo)

etiqueta("Forma de pago", 4, 2)
combo_forma_pago = ttk.Combobox(
    formulario,
    values=["CONTADO", "CRÉDITO"],
    state="readonly"
)
combo_forma_pago.grid(row=4, column=3, sticky="ew", pady=7)
combo_forma_pago.set("CRÉDITO")
combo_forma_pago.bind(
    "<<ComboboxSelected>>", cambiar_forma_pago
)

etiqueta("Días de crédito", 5, 0)
entrada_dias = ttk.Entry(formulario)
entrada_dias.grid(
    row=5, column=1, sticky="ew", padx=(0, 20), pady=7
)
entrada_dias.insert(0, "30")

etiqueta("Banco para pago", 5, 2)
combo_banco = ttk.Combobox(formulario, state="disabled")
combo_banco.grid(row=5, column=3, sticky="ew", pady=7)

etiqueta("Observaciones", 6, 0)
entrada_observaciones = ttk.Entry(formulario)
entrada_observaciones.grid(
    row=6, column=1, columnspan=3, sticky="ew", pady=7
)

ttk.Separator(tarjeta, orient="horizontal").pack(
    fill="x", padx=28
)

resumen = tk.Frame(tarjeta, bg=COLOR_TARJETA)
resumen.pack(fill="x", padx=28, pady=20)

for columna in range(3):
    resumen.columnconfigure(columna, weight=1)

def tarjeta_valor(columna, titulo):
    marco = tk.Frame(
        resumen,
        bg="#F8FAFC",
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(row=0, column=columna, sticky="ew", padx=7)

    tk.Label(
        marco,
        text=titulo,
        bg="#F8FAFC",
        fg=COLOR_SUAVE,
        font=("Segoe UI", 9, "bold")
    ).pack(pady=(12, 2))

    valor = tk.Label(
        marco,
        text="$0",
        bg="#F8FAFC",
        fg=COLOR_TEXTO,
        font=("Segoe UI", 16, "bold")
    )
    valor.pack(pady=(0, 12))
    return valor

lbl_subtotal = tarjeta_valor(0, "SUBTOTAL")
lbl_iva = tarjeta_valor(1, "IVA")
lbl_total = tarjeta_valor(2, "TOTAL")

botones = tk.Frame(tarjeta, bg=COLOR_TARJETA)
botones.pack(fill="x", padx=28, pady=(5, 25))

tk.Button(
    botones,
    text="Calcular",
    command=calcular,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
).pack(
    side="left", expand=True, fill="x", padx=(0, 6), ipady=10
)

boton_guardar = tk.Button(
    botones,
    text="Guardar y contabilizar compra",
    command=guardar_compra,
    bg=COLOR_VERDE,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
)
boton_guardar.pack(
    side="left", expand=True, fill="x", padx=6, ipady=10
)

tk.Button(
    botones,
    text="Limpiar",
    command=limpiar,
    bg="#64748B",
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
).pack(
    side="left", expand=True, fill="x", padx=(6, 0), ipady=10
)

tk.Label(
    ventana,
    text=(
        f"Base: {RUTA_DB} | Usuario: {USUARIO} | "
        "Archivo de prueba: compras_contabilidad.py"
    ),
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 10))

cargar_proveedores()
cargar_bancos()
cambiar_forma_pago()

ventana.mainloop()
