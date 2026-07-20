"""
BME-ERP - Ventas integradas con Contabilidad Automática
Archivo: ventas_contabilidad.py

Versión de prueba segura:
- No reemplaza ventas.py.
- Registra venta, descuenta inventario y actualiza kardex.
- Permite venta de contado o a crédito.
- Crea cuenta por cobrar cuando corresponde.
- Genera comprobante automático mediante motor_contable.py.
- Si la contabilización falla, revierte la operación comercial.
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

try:
    from motor_contable import contabilizar_evento, ErrorContable
except ImportError as error:
    raise SystemExit(
        "No se pudo importar motor_contable.py.\n"
        "Verifique que esté en C:\\Users\\jrive\\visual.\n\n"
        f"Detalle: {error}"
    )

# ============================================================
# CONFIGURACIÓN
# ============================================================

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
        raise FileNotFoundError(
            f"No se encontró la base de datos:\n{RUTA_DB}"
        )

    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.execute("PRAGMA busy_timeout = 5000")
    return conexion


def columnas_tabla(cursor, tabla):
    cursor.execute(f"PRAGMA table_info({tabla})")
    return {fila["name"] for fila in cursor.fetchall()}


def agregar_columna_si_falta(cursor, tabla, columna, definicion):
    columnas = columnas_tabla(cursor, tabla)

    if columna not in columnas:
        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


def preparar_estructura():
    """
    Amplía la tabla ventas sin eliminar datos existentes.
    Las columnas nuevas permiten controlar IVA, forma de pago
    y comprobante contable.
    """
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        agregar_columna_si_falta(
            cursor, "ventas", "forma_pago", "TEXT DEFAULT 'CONTADO'"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "subtotal", "REAL DEFAULT 0"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "iva_porcentaje", "REAL DEFAULT 0"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "iva", "REAL DEFAULT 0"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "cliente_documento", "TEXT DEFAULT ''"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "factura", "TEXT DEFAULT ''"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "comprobante_id", "INTEGER"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "comprobante_numero", "TEXT DEFAULT ''"
        )
        agregar_columna_si_falta(
            cursor, "ventas", "estado_contable", "TEXT DEFAULT 'PENDIENTE'"
        )

        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# UTILIDADES
# ============================================================

def numero(texto, nombre, permitir_cero=False):
    texto = str(texto).strip().replace(",", ".")

    try:
        valor = float(texto)
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


def generar_numero_factura(venta_id):
    return f"V-{int(venta_id):06d}"


# ============================================================
# CARGA DE DATOS
# ============================================================

def cargar_clientes():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                id,
                nombre,
                COALESCE(nit, '') AS documento,
                COALESCE(telefono, '') AS telefono,
                COALESCE(correo, '') AS correo,
                COALESCE(ciudad, '') AS ciudad
            FROM clientes
            WHERE UPPER(COALESCE(estado, 'ACTIVO')) <> 'INACTIVO'
            ORDER BY nombre
        """)

        registros = [dict(fila) for fila in cursor.fetchall()]
        mapa_clientes.clear()

        opciones = []

        for registro in registros:
            texto = registro["nombre"]

            if registro["documento"]:
                texto += f" - {registro['documento']}"

            opciones.append(texto)
            mapa_clientes[texto] = registro

        combo_cliente["values"] = opciones

    except sqlite3.Error:
        combo_cliente["values"] = []

    finally:
        conexion.close()


def seleccionar_cliente(evento=None):
    datos = mapa_clientes.get(combo_cliente.get())

    if not datos:
        return

    entrada_cliente.delete(0, tk.END)
    entrada_cliente.insert(0, datos["nombre"])

    entrada_documento.delete(0, tk.END)
    entrada_documento.insert(0, datos["documento"])


def cargar_productos():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT DISTINCT producto
            FROM inventario
            WHERE COALESCE(cantidad, 0) > 0
            ORDER BY producto
        """)

        productos = [fila["producto"] for fila in cursor.fetchall()]
        combo_producto["values"] = productos

    finally:
        conexion.close()


def cargar_presentaciones(evento=None):
    producto = combo_producto.get().strip()
    combo_presentacion.set("")

    if not producto:
        combo_presentacion["values"] = []
        return

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT DISTINCT presentacion
            FROM inventario
            WHERE producto=?
              AND COALESCE(cantidad, 0) > 0
            ORDER BY presentacion
        """, (producto,))

        presentaciones = [
            fila["presentacion"]
            for fila in cursor.fetchall()
        ]

        combo_presentacion["values"] = presentaciones

    finally:
        conexion.close()


def mostrar_existencia(evento=None):
    producto = combo_producto.get().strip()
    presentacion = combo_presentacion.get().strip()

    if not producto or not presentacion:
        lbl_existencia.config(text="Existencia: —")
        return

    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                COALESCE(cantidad, 0) AS cantidad,
                COALESCE(costo_unitario, costo, 0) AS costo
            FROM inventario
            WHERE producto=? AND presentacion=?
            ORDER BY id
            LIMIT 1
        """, (producto, presentacion))

        fila = cursor.fetchone()

        if not fila:
            lbl_existencia.config(text="Existencia: 0")
            return

        lbl_existencia.config(
            text=(
                f"Existencia: {float(fila['cantidad']):,.2f} | "
                f"Costo unitario: {moneda(fila['costo'])}"
            )
        )

    finally:
        conexion.close()


# ============================================================
# CÁLCULOS
# ============================================================

def calcular_valores(mostrar_error=True):
    try:
        cantidad = numero(
            entrada_cantidad.get(),
            "La cantidad"
        )
        precio = numero(
            entrada_precio.get(),
            "El precio unitario"
        )
        porcentaje_iva = numero(
            combo_iva.get() or "0",
            "El IVA",
            permitir_cero=True
        )

        subtotal = round(cantidad * precio, 2)
        iva = round(subtotal * porcentaje_iva / 100, 2)
        total = round(subtotal + iva, 2)

        lbl_subtotal_valor.config(text=moneda(subtotal))
        lbl_iva_valor.config(text=moneda(iva))
        lbl_total_valor.config(text=moneda(total))

        return {
            "cantidad": cantidad,
            "precio": precio,
            "iva_porcentaje": porcentaje_iva,
            "subtotal": subtotal,
            "iva": iva,
            "total": total
        }

    except ValueError as error:
        if mostrar_error:
            messagebox.showerror("Datos de venta", str(error))
        return None


def actualizar_calculos(evento=None):
    calcular_valores(mostrar_error=False)


# ============================================================
# VALIDACIÓN
# ============================================================

def obtener_datos_formulario():
    cliente = entrada_cliente.get().strip()
    documento = entrada_documento.get().strip()
    producto = combo_producto.get().strip()
    presentacion = combo_presentacion.get().strip()
    forma_pago = combo_forma_pago.get().strip().upper()
    dias_credito_texto = entrada_dias_credito.get().strip() or "0"

    if not cliente:
        raise ValueError("Debe ingresar o seleccionar un cliente.")

    if not documento:
        raise ValueError(
            "Debe ingresar el documento o NIT del cliente."
        )

    if not producto:
        raise ValueError("Debe seleccionar un producto.")

    if not presentacion:
        raise ValueError("Debe seleccionar una presentación.")

    if forma_pago not in ("CONTADO", "CRÉDITO"):
        raise ValueError("Seleccione CONTADO o CRÉDITO.")

    valores = calcular_valores(mostrar_error=False)

    if not valores:
        raise ValueError(
            "Revise la cantidad, el precio unitario y el IVA."
        )

    try:
        dias_credito = int(dias_credito_texto)
    except ValueError:
        raise ValueError("Los días de crédito deben ser un número entero.")

    if forma_pago == "CRÉDITO" and dias_credito <= 0:
        raise ValueError(
            "En una venta a crédito, los días de crédito deben ser mayores que cero."
        )

    if forma_pago == "CONTADO":
        dias_credito = 0

    return {
        "cliente": cliente,
        "documento": documento,
        "producto": producto,
        "presentacion": presentacion,
        "forma_pago": forma_pago,
        "dias_credito": dias_credito,
        **valores
    }


# ============================================================
# OPERACIÓN COMERCIAL
# ============================================================

def registrar_operacion_comercial(datos):
    """
    Registra venta, inventario, kardex y CxC.
    Devuelve los identificadores necesarios para contabilizar
    o revertir la operación.
    """
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT
                id,
                COALESCE(cantidad, 0) AS cantidad,
                COALESCE(costo_unitario, costo, 0) AS costo_unitario,
                COALESCE(lote, '') AS lote
            FROM inventario
            WHERE producto=? AND presentacion=?
            ORDER BY id
            LIMIT 1
        """, (
            datos["producto"],
            datos["presentacion"]
        ))

        inventario = cursor.fetchone()

        if not inventario:
            raise ValueError(
                "No existe inventario para el producto y presentación seleccionados."
            )

        stock_actual = float(inventario["cantidad"])
        costo_unitario = float(inventario["costo_unitario"])

        if datos["cantidad"] > stock_actual:
            raise ValueError(
                f"Stock insuficiente. Disponible: {stock_actual:,.2f}"
            )

        costo_total = round(
            costo_unitario * datos["cantidad"],
            2
        )
        utilidad = round(
            datos["subtotal"] - costo_total,
            2
        )
        margen = (
            round(utilidad / datos["subtotal"] * 100, 2)
            if datos["subtotal"] > 0
            else 0
        )

        fecha = fecha_actual()

        cursor.execute("""
            INSERT INTO ventas(
                fecha,
                cliente,
                producto,
                presentacion,
                cantidad,
                precio_unitario,
                total,
                costo_unitario,
                utilidad_total,
                margen,
                forma_pago,
                subtotal,
                iva_porcentaje,
                iva,
                cliente_documento,
                factura,
                estado_contable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 'PENDIENTE')
        """, (
            fecha,
            datos["cliente"],
            datos["producto"],
            datos["presentacion"],
            datos["cantidad"],
            datos["precio"],
            datos["total"],
            costo_unitario,
            utilidad,
            margen,
            datos["forma_pago"],
            datos["subtotal"],
            datos["iva_porcentaje"],
            datos["iva"],
            datos["documento"]
        ))

        venta_id = int(cursor.lastrowid)
        factura = generar_numero_factura(venta_id)

        cursor.execute("""
            UPDATE ventas
            SET factura=?
            WHERE id=?
        """, (factura, venta_id))

        nuevo_stock = round(
            stock_actual - datos["cantidad"],
            4
        )

        cursor.execute("""
            UPDATE inventario
            SET cantidad=?
            WHERE id=?
        """, (
            nuevo_stock,
            int(inventario["id"])
        ))

        cursor.execute("""
            INSERT INTO kardex(
                fecha,
                producto,
                presentacion,
                movimiento,
                entrada,
                salida,
                saldo,
                costo_unitario,
                lote,
                origen,
                observaciones
            )
            VALUES (?, ?, ?, 'SALIDA', 0, ?, ?, ?, ?, 'VENTA', ?)
        """, (
            fecha,
            datos["producto"],
            datos["presentacion"],
            datos["cantidad"],
            nuevo_stock,
            costo_unitario,
            inventario["lote"],
            f"{factura} - {datos['cliente']}"
        ))

        kardex_id = int(cursor.lastrowid)
        cuenta_cobrar_id = None

        if datos["forma_pago"] == "CRÉDITO":
            vencimiento = (
                datetime.now() + timedelta(days=datos["dias_credito"])
            ).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO cuentas_cobrar(
                    fecha,
                    cliente,
                    concepto,
                    valor,
                    saldo,
                    vencimiento,
                    estado,
                    venta_id,
                    factura,
                    documento_cliente,
                    dias_mora,
                    fecha_ultimo_pago,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE', ?, ?, ?, 0, '', ?)
            """, (
                fecha,
                datos["cliente"],
                f"Venta a crédito {factura}",
                datos["total"],
                datos["total"],
                vencimiento,
                venta_id,
                factura,
                datos["documento"],
                f"Crédito a {datos['dias_credito']} días"
            ))

            cuenta_cobrar_id = int(cursor.lastrowid)

        conexion.commit()

        return {
            "venta_id": venta_id,
            "factura": factura,
            "fecha": fecha,
            "inventario_id": int(inventario["id"]),
            "stock_anterior": stock_actual,
            "nuevo_stock": nuevo_stock,
            "kardex_id": kardex_id,
            "cuenta_cobrar_id": cuenta_cobrar_id,
            "costo_unitario": costo_unitario,
            "costo_total": costo_total,
            "utilidad": utilidad,
            "margen": margen
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def revertir_operacion_comercial(resultado):
    """
    Compensación usada solamente si motor_contable falla.
    Restaura inventario y elimina los registros recién creados.
    """
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        if resultado.get("cuenta_cobrar_id"):
            cursor.execute("""
                DELETE FROM cuentas_cobrar
                WHERE id=?
            """, (resultado["cuenta_cobrar_id"],))

        cursor.execute("""
            DELETE FROM kardex
            WHERE id=?
        """, (resultado["kardex_id"],))

        cursor.execute("""
            UPDATE inventario
            SET cantidad=?
            WHERE id=?
        """, (
            resultado["stock_anterior"],
            resultado["inventario_id"]
        ))

        cursor.execute("""
            DELETE FROM ventas
            WHERE id=?
        """, (resultado["venta_id"],))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def actualizar_comprobante_venta(
    venta_id,
    comprobante_id,
    comprobante_numero
):
    conexion = conectar()

    try:
        conexion.execute("""
            UPDATE ventas
            SET
                comprobante_id=?,
                comprobante_numero=?,
                estado_contable='CONTABILIZADO'
            WHERE id=?
        """, (
            comprobante_id,
            comprobante_numero,
            venta_id
        ))
        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# GUARDAR VENTA COMPLETA
# ============================================================

def guardar_venta():
    boton_guardar.config(state="disabled")
    resultado = None

    try:
        datos = obtener_datos_formulario()
        resultado = registrar_operacion_comercial(datos)

        evento = (
            "VENTA_CONTADO"
            if datos["forma_pago"] == "CONTADO"
            else "VENTA_CREDITO"
        )

        tercero = {
            "tipo_documento": "NIT",
            "numero_documento": datos["documento"],
            "nombre_razon_social": datos["cliente"],
            "tipo_tercero": "CLIENTE",
            "origen_modulo": "VENTAS"
        }

        comprobante = contabilizar_evento(
            evento=evento,
            valores={
                "total": datos["total"],
                "subtotal_sin_iva": datos["subtotal"],
                "iva": datos["iva"],
                "costo_total": resultado["costo_total"]
            },
            concepto=(
                f"{resultado['factura']} - Venta de "
                f"{datos['producto']} {datos['presentacion']} "
                f"a {datos['cliente']}"
            ),
            modulo_origen="VENTAS",
            tabla_origen="ventas",
            registro_origen_id=resultado["venta_id"],
            tercero=tercero,
            centro_costo="VENTAS",
            fecha=resultado["fecha"],
            documento_referencia=resultado["factura"],
            usuario=USUARIO
        )

        actualizar_comprobante_venta(
            resultado["venta_id"],
            comprobante["comprobante_id"],
            comprobante["consecutivo"] or ""
        )

        messagebox.showinfo(
            "Venta registrada y contabilizada",
            (
                f"Factura: {resultado['factura']}\n"
                f"Forma de pago: {datos['forma_pago']}\n\n"
                f"Subtotal: {moneda(datos['subtotal'])}\n"
                f"IVA: {moneda(datos['iva'])}\n"
                f"Total: {moneda(datos['total'])}\n\n"
                f"Costo: {moneda(resultado['costo_total'])}\n"
                f"Utilidad: {moneda(resultado['utilidad'])}\n"
                f"Margen: {resultado['margen']:.2f}%\n"
                f"Stock restante: {resultado['nuevo_stock']:,.2f}\n\n"
                f"Comprobante contable:\n"
                f"{comprobante['consecutivo']}"
            )
        )

        limpiar_formulario()
        cargar_productos()

    except (ValueError, sqlite3.Error, ErrorContable, Exception) as error:
        mensaje_reversion = ""

        if resultado:
            try:
                revertir_operacion_comercial(resultado)
                mensaje_reversion = (
                    "\n\nLa venta, el kardex, la cuenta por cobrar "
                    "y el inventario fueron revertidos."
                )
            except Exception as error_reversion:
                mensaje_reversion = (
                    "\n\nATENCIÓN: no fue posible completar la reversión."
                    f"\nDetalle: {error_reversion}"
                )

        messagebox.showerror(
            "No fue posible registrar la venta",
            f"{error}{mensaje_reversion}"
        )

    finally:
        boton_guardar.config(state="normal")


# ============================================================
# INTERFAZ
# ============================================================

def cambiar_forma_pago(evento=None):
    if combo_forma_pago.get().upper() == "CRÉDITO":
        entrada_dias_credito.config(state="normal")
        if not entrada_dias_credito.get().strip():
            entrada_dias_credito.insert(0, "30")
    else:
        entrada_dias_credito.delete(0, tk.END)
        entrada_dias_credito.insert(0, "0")
        entrada_dias_credito.config(state="disabled")


def limpiar_formulario():
    combo_cliente.set("")
    entrada_cliente.delete(0, tk.END)
    entrada_documento.delete(0, tk.END)
    combo_producto.set("")
    combo_presentacion.set("")
    combo_presentacion["values"] = []
    entrada_cantidad.delete(0, tk.END)
    entrada_precio.delete(0, tk.END)
    combo_iva.set("0")
    combo_forma_pago.set("CONTADO")
    cambiar_forma_pago()

    lbl_existencia.config(text="Existencia: —")
    lbl_subtotal_valor.config(text="$0")
    lbl_iva_valor.config(text="$0")
    lbl_total_valor.config(text="$0")


preparar_estructura()

ventana = tk.Tk()
ventana.title(
    "BME-ERP - Ventas con Contabilidad Automática"
)
ventana.geometry("860x760")
ventana.minsize(800, 700)
ventana.configure(bg=COLOR_FONDO)

estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "TCombobox",
    padding=5,
    font=("Segoe UI", 10)
)

cabecera = tk.Frame(
    ventana,
    bg=COLOR_AZUL,
    height=92
)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="VENTAS CON CONTABILIDAD AUTOMÁTICA",
    font=("Segoe UI", 19, "bold"),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=30, pady=(17, 0))

tk.Label(
    cabecera,
    text=(
        "Registra venta, inventario, kardex, cartera "
        "y comprobante contable"
    ),
    font=("Segoe UI", 9),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=31, pady=(3, 0))

contenedor = tk.Frame(
    ventana,
    bg=COLOR_FONDO
)
contenedor.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=20
)

tarjeta = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
tarjeta.pack(fill="both", expand=True)

formulario = tk.Frame(
    tarjeta,
    bg=COLOR_TARJETA
)
formulario.pack(
    fill="x",
    padx=28,
    pady=22
)

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
        pady=8
    )


mapa_clientes = {}

etiqueta("Cliente registrado", 0, 0)
combo_cliente = ttk.Combobox(
    formulario,
    state="readonly",
    width=33
)
combo_cliente.grid(
    row=0, column=1, sticky="ew", pady=8, padx=(0, 20)
)
combo_cliente.bind(
    "<<ComboboxSelected>>",
    seleccionar_cliente
)

etiqueta("Nombre cliente", 0, 2)
entrada_cliente = ttk.Entry(
    formulario,
    font=("Segoe UI", 10)
)
entrada_cliente.grid(
    row=0, column=3, sticky="ew", pady=8
)

etiqueta("Documento / NIT", 1, 0)
entrada_documento = ttk.Entry(
    formulario,
    font=("Segoe UI", 10)
)
entrada_documento.grid(
    row=1, column=1, sticky="ew", pady=8, padx=(0, 20)
)

etiqueta("Forma de pago", 1, 2)
combo_forma_pago = ttk.Combobox(
    formulario,
    values=["CONTADO", "CRÉDITO"],
    state="readonly"
)
combo_forma_pago.grid(
    row=1, column=3, sticky="ew", pady=8
)
combo_forma_pago.set("CONTADO")
combo_forma_pago.bind(
    "<<ComboboxSelected>>",
    cambiar_forma_pago
)

etiqueta("Producto", 2, 0)
combo_producto = ttk.Combobox(
    formulario,
    state="readonly"
)
combo_producto.grid(
    row=2, column=1, sticky="ew", pady=8, padx=(0, 20)
)
combo_producto.bind(
    "<<ComboboxSelected>>",
    cargar_presentaciones
)

etiqueta("Presentación", 2, 2)
combo_presentacion = ttk.Combobox(
    formulario,
    state="readonly"
)
combo_presentacion.grid(
    row=2, column=3, sticky="ew", pady=8
)
combo_presentacion.bind(
    "<<ComboboxSelected>>",
    mostrar_existencia
)

etiqueta("Cantidad", 3, 0)
entrada_cantidad = ttk.Entry(
    formulario,
    font=("Segoe UI", 10)
)
entrada_cantidad.grid(
    row=3, column=1, sticky="ew", pady=8, padx=(0, 20)
)
entrada_cantidad.bind("<KeyRelease>", actualizar_calculos)

etiqueta("Precio unitario sin IVA", 3, 2)
entrada_precio = ttk.Entry(
    formulario,
    font=("Segoe UI", 10)
)
entrada_precio.grid(
    row=3, column=3, sticky="ew", pady=8
)
entrada_precio.bind("<KeyRelease>", actualizar_calculos)

etiqueta("IVA (%)", 4, 0)
combo_iva = ttk.Combobox(
    formulario,
    values=["0", "5", "19"],
    state="readonly"
)
combo_iva.grid(
    row=4, column=1, sticky="ew", pady=8, padx=(0, 20)
)
combo_iva.set("0")
combo_iva.bind(
    "<<ComboboxSelected>>",
    actualizar_calculos
)

etiqueta("Días de crédito", 4, 2)
entrada_dias_credito = ttk.Entry(
    formulario,
    font=("Segoe UI", 10)
)
entrada_dias_credito.grid(
    row=4, column=3, sticky="ew", pady=8
)
entrada_dias_credito.insert(0, "0")
entrada_dias_credito.config(state="disabled")

lbl_existencia = tk.Label(
    formulario,
    text="Existencia: —",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 9)
)
lbl_existencia.grid(
    row=5,
    column=0,
    columnspan=4,
    sticky="w",
    pady=(8, 2)
)

separador = ttk.Separator(
    tarjeta,
    orient="horizontal"
)
separador.pack(fill="x", padx=28)

resumen = tk.Frame(
    tarjeta,
    bg=COLOR_TARJETA
)
resumen.pack(
    fill="x",
    padx=28,
    pady=20
)

for columna in range(3):
    resumen.columnconfigure(columna, weight=1)

def cuadro_resumen(columna, titulo):
    marco = tk.Frame(
        resumen,
        bg="#F8FAFC",
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=7
    )

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


lbl_subtotal_valor = cuadro_resumen(0, "SUBTOTAL")
lbl_iva_valor = cuadro_resumen(1, "IVA")
lbl_total_valor = cuadro_resumen(2, "TOTAL")

botones = tk.Frame(
    tarjeta,
    bg=COLOR_TARJETA
)
botones.pack(
    fill="x",
    padx=28,
    pady=(5, 25)
)

tk.Button(
    botones,
    text="Calcular",
    command=calcular_valores,
    bg=COLOR_AZUL,
    fg="white",
    activebackground="#0B4B75",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
).pack(
    side="left",
    expand=True,
    fill="x",
    padx=(0, 6),
    ipady=10
)

boton_guardar = tk.Button(
    botones,
    text="Guardar y contabilizar venta",
    command=guardar_venta,
    bg=COLOR_VERDE,
    fg="white",
    activebackground="#11632F",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
)
boton_guardar.pack(
    side="left",
    expand=True,
    fill="x",
    padx=6,
    ipady=10
)

tk.Button(
    botones,
    text="Limpiar",
    command=limpiar_formulario,
    bg="#64748B",
    fg="white",
    activebackground="#475569",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
).pack(
    side="left",
    expand=True,
    fill="x",
    padx=(6, 0),
    ipady=10
)

pie = tk.Label(
    ventana,
    text=(
        f"Base: {RUTA_DB}  |  Usuario: {USUARIO}  |  "
        "Archivo de prueba: ventas_contabilidad.py"
    ),
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
)
pie.pack(pady=(0, 10))

cargar_clientes()
cargar_productos()
cambiar_forma_pago()

ventana.mainloop()
