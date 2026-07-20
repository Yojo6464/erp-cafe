"""
BME-ERP - Pagos de Cuentas por Pagar con Contabilidad
Archivo: pagos_cxp_contabilidad.py

Funciones:
- Consulta cuentas por pagar pendientes.
- Registra abonos parciales o pagos totales.
- Actualiza saldo y estado de la obligación.
- Disminuye el saldo del banco.
- Registra movimiento bancario.
- Genera comprobante contable automático.
- Revierte toda la operación si falla la contabilidad.
"""

import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from motor_contable import contabilizar_evento

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
            cursor, "pagos_cxp", "banco_id", "INTEGER"
        )
        agregar_columna(
            cursor, "pagos_cxp", "movimiento_banco_id", "INTEGER"
        )
        agregar_columna(
            cursor, "pagos_cxp", "comprobante_id", "INTEGER"
        )
        agregar_columna(
            cursor, "pagos_cxp", "comprobante_numero", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "pagos_cxp", "estado_contable", "TEXT DEFAULT 'PENDIENTE'"
        )
        agregar_columna(
            cursor, "pagos_cxp", "observaciones", "TEXT DEFAULT ''"
        )
        agregar_columna(
            cursor, "pagos_cxp", "usuario", "TEXT DEFAULT ''"
        )

        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# UTILIDADES
# ============================================================

def moneda(valor):
    try:
        return f"${float(valor):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def numero(texto, nombre):
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{nombre} debe ser un número válido.")

    if valor <= 0:
        raise ValueError(f"{nombre} debe ser mayor que cero.")

    return valor


# ============================================================
# CARGA DE DATOS
# ============================================================

mapa_bancos = {}


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

        opciones = []
        mapa_bancos.clear()

        for fila in cursor.fetchall():
            texto = (
                f"{fila['id']} - {fila['banco']} - "
                f"{fila['numero_cuenta']} - Saldo {moneda(fila['saldo'])}"
            )
            opciones.append(texto)
            mapa_bancos[texto] = dict(fila)

        combo_banco["values"] = opciones

        if opciones:
            combo_banco.current(0)

    finally:
        conexion.close()


def cargar_cuentas():
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                id,
                fecha,
                proveedor,
                valor,
                saldo,
                vencimiento,
                estado
            FROM cuentas_pagar
            WHERE COALESCE(saldo, 0) > 0
              AND UPPER(COALESCE(estado, 'PENDIENTE')) <> 'PAGADA'
            ORDER BY vencimiento, id
        """)

        registros = cursor.fetchall()

    finally:
        conexion.close()

    tabla_cuentas.delete(*tabla_cuentas.get_children())

    for fila in registros:
        tabla_cuentas.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["id"],
                fila["fecha"],
                fila["proveedor"],
                moneda(fila["valor"]),
                moneda(fila["saldo"]),
                fila["vencimiento"],
                fila["estado"]
            )
        )

    lbl_cuentas.config(text=str(len(registros)))
    limpiar_seleccion()


def cargar_historial(cuenta_id):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT
                p.id,
                p.fecha,
                p.valor,
                COALESCE(b.banco, '') AS banco,
                COALESCE(p.comprobante_numero, '') AS comprobante,
                COALESCE(p.estado_contable, '') AS estado_contable
            FROM pagos_cxp p
            LEFT JOIN bancos b ON b.id=p.banco_id
            WHERE p.cuenta_id=?
            ORDER BY p.id DESC
        """, (cuenta_id,))

        registros = cursor.fetchall()

    finally:
        conexion.close()

    tabla_historial.delete(*tabla_historial.get_children())

    for fila in registros:
        tabla_historial.insert(
            "",
            "end",
            values=(
                fila["id"],
                fila["fecha"],
                moneda(fila["valor"]),
                fila["banco"],
                fila["comprobante"],
                fila["estado_contable"]
            )
        )


def seleccionar_cuenta(evento=None):
    seleccion = tabla_cuentas.selection()

    if not seleccion:
        return

    datos = tabla_cuentas.item(seleccion[0])["values"]

    cuenta_id = int(datos[0])
    proveedor = str(datos[2])
    saldo_texto = str(datos[4]).replace("$", "").replace(",", "")
    saldo = float(saldo_texto)

    lbl_cuenta_id.config(text=str(cuenta_id))
    lbl_proveedor.config(text=proveedor)
    lbl_saldo.config(text=moneda(saldo))
    lbl_vencimiento.config(text=str(datos[5]))
    lbl_estado.config(text=str(datos[6]))

    entrada_pago.delete(0, tk.END)
    entrada_pago.insert(0, f"{saldo:.2f}")

    cargar_historial(cuenta_id)


def limpiar_seleccion():
    lbl_cuenta_id.config(text="—")
    lbl_proveedor.config(text="—")
    lbl_saldo.config(text="$0")
    lbl_vencimiento.config(text="—")
    lbl_estado.config(text="—")
    entrada_pago.delete(0, tk.END)
    tabla_historial.delete(*tabla_historial.get_children())


# ============================================================
# REGISTRO DEL PAGO
# ============================================================

def obtener_datos_pago():
    seleccion = tabla_cuentas.selection()

    if not seleccion:
        raise ValueError("Seleccione una cuenta por pagar.")

    cuenta_id = int(seleccion[0])
    banco = mapa_bancos.get(combo_banco.get())

    if not banco:
        raise ValueError("Seleccione un banco.")

    valor_pago = numero(
        entrada_pago.get(),
        "El valor del pago"
    )

    if valor_pago > float(banco["saldo"] or 0):
        raise ValueError(
            "El banco seleccionado no tiene saldo suficiente."
        )

    return {
        "cuenta_id": cuenta_id,
        "banco": banco,
        "valor_pago": valor_pago,
        "observaciones": entrada_observaciones.get().strip()
    }


def registrar_pago_db(datos):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT
                id,
                proveedor,
                valor,
                saldo,
                estado,
                vencimiento
            FROM cuentas_pagar
            WHERE id=?
        """, (datos["cuenta_id"],))

        cuenta = cursor.fetchone()

        if not cuenta:
            raise ValueError("La cuenta por pagar ya no existe.")

        saldo_anterior_cxp = float(cuenta["saldo"] or 0)

        if saldo_anterior_cxp <= 0:
            raise ValueError("La cuenta ya está pagada.")

        if datos["valor_pago"] > saldo_anterior_cxp:
            raise ValueError(
                "El pago supera el saldo pendiente."
            )

        cursor.execute("""
            SELECT banco, saldo
            FROM bancos
            WHERE id=? AND UPPER(estado)='ACTIVA'
        """, (int(datos["banco"]["id"]),))

        banco = cursor.fetchone()

        if not banco:
            raise ValueError("El banco seleccionado no está disponible.")

        saldo_banco_anterior = float(banco["saldo"] or 0)

        if datos["valor_pago"] > saldo_banco_anterior:
            raise ValueError("Saldo bancario insuficiente.")

        nuevo_saldo_banco = saldo_banco_anterior - datos["valor_pago"]
        nuevo_saldo_cxp = saldo_anterior_cxp - datos["valor_pago"]

        if nuevo_saldo_cxp <= 0.005:
            nuevo_saldo_cxp = 0
            nuevo_estado = "PAGADA"
        else:
            nuevo_estado = "PENDIENTE"

        fecha = fecha_actual()

        cursor.execute("""
            INSERT INTO pagos_cxp(
                cuenta_id,
                fecha,
                valor,
                banco_id,
                observaciones,
                usuario,
                estado_contable
            )
            VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE')
        """, (
            datos["cuenta_id"],
            fecha,
            datos["valor_pago"],
            int(datos["banco"]["id"]),
            datos["observaciones"],
            USUARIO
        ))

        pago_id = int(cursor.lastrowid)

        cursor.execute("""
            UPDATE cuentas_pagar
            SET
                saldo=?,
                estado=?
            WHERE id=?
        """, (
            nuevo_saldo_cxp,
            nuevo_estado,
            datos["cuenta_id"]
        ))

        cursor.execute("""
            UPDATE bancos
            SET saldo=?
            WHERE id=?
        """, (
            nuevo_saldo_banco,
            int(datos["banco"]["id"])
        ))

        cursor.execute("""
            INSERT INTO movimientos_bancos(
                fecha,
                banco_id,
                tipo,
                concepto,
                valor,
                saldo_anterior,
                saldo_nuevo,
                autorizado_por
            )
            VALUES (?, ?, 'PAGO CXP', ?, ?, ?, ?, ?)
        """, (
            fecha,
            int(datos["banco"]["id"]),
            (
                f"Pago CxP #{datos['cuenta_id']} - "
                f"{cuenta['proveedor']}"
            ),
            datos["valor_pago"],
            saldo_banco_anterior,
            nuevo_saldo_banco,
            USUARIO
        ))

        movimiento_banco_id = int(cursor.lastrowid)

        cursor.execute("""
            UPDATE pagos_cxp
            SET movimiento_banco_id=?
            WHERE id=?
        """, (
            movimiento_banco_id,
            pago_id
        ))

        conexion.commit()

        return {
            "pago_id": pago_id,
            "fecha": fecha,
            "cuenta_id": datos["cuenta_id"],
            "proveedor": cuenta["proveedor"],
            "saldo_anterior_cxp": saldo_anterior_cxp,
            "nuevo_saldo_cxp": nuevo_saldo_cxp,
            "estado_anterior": cuenta["estado"],
            "nuevo_estado": nuevo_estado,
            "banco_id": int(datos["banco"]["id"]),
            "saldo_banco_anterior": saldo_banco_anterior,
            "nuevo_saldo_banco": nuevo_saldo_banco,
            "movimiento_banco_id": movimiento_banco_id,
            "valor_pago": datos["valor_pago"]
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def revertir_pago(resultado):
    conexion = conectar()

    try:
        cursor = conexion.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            DELETE FROM movimientos_bancos
            WHERE id=?
        """, (resultado["movimiento_banco_id"],))

        cursor.execute("""
            UPDATE bancos
            SET saldo=?
            WHERE id=?
        """, (
            resultado["saldo_banco_anterior"],
            resultado["banco_id"]
        ))

        cursor.execute("""
            UPDATE cuentas_pagar
            SET
                saldo=?,
                estado=?
            WHERE id=?
        """, (
            resultado["saldo_anterior_cxp"],
            resultado["estado_anterior"],
            resultado["cuenta_id"]
        ))

        cursor.execute("""
            DELETE FROM pagos_cxp
            WHERE id=?
        """, (resultado["pago_id"],))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


def actualizar_comprobante_pago(pago_id, comprobante):
    conexion = conectar()

    try:
        conexion.execute("""
            UPDATE pagos_cxp
            SET
                comprobante_id=?,
                comprobante_numero=?,
                estado_contable='CONTABILIZADO'
            WHERE id=?
        """, (
            comprobante["comprobante_id"],
            comprobante["consecutivo"],
            pago_id
        ))
        conexion.commit()

    finally:
        conexion.close()


# ============================================================
# GUARDAR Y CONTABILIZAR
# ============================================================

def registrar_pago():
    boton_registrar.config(state="disabled")
    resultado = None

    try:
        datos = obtener_datos_pago()
        # BME-PROTECCION-PERIODOS - PAGOS-CXP
        validar_periodo_abierto(
            datetime.now().strftime("%Y-%m-%d")
        )
        resultado = registrar_pago_db(datos)

        comprobante = contabilizar_evento(
            evento="PAGO_CXP",
            valores={
                "valor": resultado["valor_pago"]
            },
            concepto=(
                f"Pago a proveedor CxP #{resultado['cuenta_id']} - "
                f"{resultado['proveedor']}"
            ),
            modulo_origen="CUENTAS_POR_PAGAR",
            tabla_origen="pagos_cxp",
            registro_origen_id=resultado["pago_id"],
            tercero={
                "tipo_documento": "NIT",
                "numero_documento": f"PROVEEDOR-{resultado['cuenta_id']}",
                "nombre_razon_social": resultado["proveedor"],
                "tipo_tercero": "PROVEEDOR",
                "origen_modulo": "CUENTAS_POR_PAGAR"
            },
            centro_costo=None,
            fecha=resultado["fecha"],
            documento_referencia=f"CXP-{resultado['cuenta_id']}",
            usuario=USUARIO
        )

        actualizar_comprobante_pago(
            resultado["pago_id"],
            comprobante
        )

        messagebox.showinfo(
            "Pago contabilizado",
            (
                f"Pago No. {resultado['pago_id']}\n"
                f"Proveedor: {resultado['proveedor']}\n"
                f"Valor pagado: {moneda(resultado['valor_pago'])}\n\n"
                f"Saldo anterior CxP: "
                f"{moneda(resultado['saldo_anterior_cxp'])}\n"
                f"Nuevo saldo CxP: "
                f"{moneda(resultado['nuevo_saldo_cxp'])}\n"
                f"Estado: {resultado['nuevo_estado']}\n\n"
                f"Nuevo saldo banco: "
                f"{moneda(resultado['nuevo_saldo_banco'])}\n\n"
                f"Comprobante:\n{comprobante['consecutivo']}"
            )
        )

        entrada_observaciones.delete(0, tk.END)
        cargar_cuentas()
        cargar_bancos()

    except Exception as error:
        mensaje = ""

        if resultado:
            try:
                revertir_pago(resultado)
                mensaje = (
                    "\n\nEl pago, la cuenta por pagar y el "
                    "movimiento bancario fueron revertidos."
                )
            except Exception as error_reversion:
                mensaje = (
                    "\n\nATENCIÓN: falló la reversión.\n"
                    f"{error_reversion}"
                )

        messagebox.showerror(
            "No fue posible registrar el pago",
            f"{error}{mensaje}"
        )

    finally:
        boton_registrar.config(state="normal")


# ============================================================
# INTERFAZ
# ============================================================

preparar_estructura()

ventana = tk.Tk()
ventana.title(
    "BME-ERP - Pagos de Cuentas por Pagar"
)
ventana.geometry("1380x850")
ventana.minsize(1100, 720)
ventana.configure(bg=COLOR_FONDO)

estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Treeview",
    rowheight=27,
    font=("Segoe UI", 9),
    background="white",
    fieldbackground="white"
)
estilo.configure(
    "Treeview.Heading",
    font=("Segoe UI", 9, "bold"),
    background="#E8EEF4",
    foreground=COLOR_TEXTO
)
estilo.map(
    "Treeview",
    background=[("selected", COLOR_AZUL)],
    foreground=[("selected", "white")]
)

cabecera = tk.Frame(ventana, bg=COLOR_AZUL, height=88)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="PAGOS DE CUENTAS POR PAGAR",
    font=("Segoe UI", 19, "bold"),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=28, pady=(15, 0))

tk.Label(
    cabecera,
    text="Proveedores, bancos y contabilidad automática",
    font=("Segoe UI", 9),
    bg=COLOR_AZUL,
    fg="white"
).pack(anchor="w", padx=29, pady=(3, 0))

contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
contenedor.pack(fill="both", expand=True, padx=18, pady=18)

resumen = tk.Frame(contenedor, bg=COLOR_FONDO)
resumen.pack(fill="x", pady=(0, 10))

marco_resumen = tk.Frame(
    resumen,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
marco_resumen.pack(side="left", fill="x", expand=True)

tk.Label(
    marco_resumen,
    text="CUENTAS PENDIENTES",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8, "bold")
).pack(anchor="w", padx=14, pady=(10, 2))

lbl_cuentas = tk.Label(
    marco_resumen,
    text="0",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 17, "bold")
)
lbl_cuentas.pack(anchor="w", padx=14, pady=(0, 10))

panel_cuentas = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_cuentas.pack(fill="both", expand=True, pady=(0, 10))

tk.Label(
    panel_cuentas,
    text="Cuentas por pagar pendientes",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(10, 5))

columnas = (
    "ID", "Fecha", "Proveedor", "Valor",
    "Saldo", "Vencimiento", "Estado"
)

tabla_cuentas = ttk.Treeview(
    panel_cuentas,
    columns=columnas,
    show="headings",
    height=9
)

anchos = {
    "ID": 60,
    "Fecha": 130,
    "Proveedor": 260,
    "Valor": 130,
    "Saldo": 130,
    "Vencimiento": 120,
    "Estado": 110
}

for columna in columnas:
    tabla_cuentas.heading(columna, text=columna)
    tabla_cuentas.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in ("Valor", "Saldo") else "w"
    )

tabla_cuentas.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 10)
)
tabla_cuentas.bind(
    "<<TreeviewSelect>>",
    seleccionar_cuenta
)

panel_inferior = tk.Frame(contenedor, bg=COLOR_FONDO)
panel_inferior.pack(fill="both", expand=True)

panel_pago = tk.Frame(
    panel_inferior,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_pago.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 5)
)

panel_historial = tk.Frame(
    panel_inferior,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_historial.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(5, 0)
)

tk.Label(
    panel_pago,
    text="Registrar pago",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=16, pady=(12, 8))

datos = tk.Frame(panel_pago, bg=COLOR_TARJETA)
datos.pack(fill="x", padx=16)

for columna in range(5):
    datos.columnconfigure(columna, weight=1)

def dato(titulo, fila, columna):
    marco = tk.Frame(datos, bg=COLOR_TARJETA)
    marco.grid(
        row=fila,
        column=columna,
        sticky="ew",
        padx=5,
        pady=4
    )

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="—",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 9, "bold"),
        wraplength=170,
        justify="left"
    )
    valor.pack(anchor="w")
    return valor

lbl_cuenta_id = dato("CUENTA ID", 0, 0)
lbl_proveedor = dato("PROVEEDOR", 0, 1)
lbl_saldo = dato("SALDO", 0, 2)
lbl_vencimiento = dato("VENCIMIENTO", 0, 3)
lbl_estado = dato("ESTADO", 0, 4)

formulario = tk.Frame(panel_pago, bg=COLOR_TARJETA)
formulario.pack(fill="x", padx=16, pady=10)
formulario.columnconfigure(1, weight=1)

tk.Label(
    formulario,
    text="Banco",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold")
).grid(row=0, column=0, sticky="w", pady=6)

combo_banco = ttk.Combobox(
    formulario,
    state="readonly",
    width=45
)
combo_banco.grid(
    row=0, column=1, sticky="ew", padx=(10, 0), pady=6
)

tk.Label(
    formulario,
    text="Valor pagado",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold")
).grid(row=1, column=0, sticky="w", pady=6)

entrada_pago = ttk.Entry(formulario)
entrada_pago.grid(
    row=1, column=1, sticky="ew", padx=(10, 0), pady=6
)

tk.Label(
    formulario,
    text="Observaciones",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold")
).grid(row=2, column=0, sticky="w", pady=6)

entrada_observaciones = ttk.Entry(formulario)
entrada_observaciones.grid(
    row=2, column=1, sticky="ew", padx=(10, 0), pady=6
)

boton_registrar = tk.Button(
    panel_pago,
    text="Registrar y contabilizar pago",
    command=registrar_pago,
    bg=COLOR_VERDE,
    fg="white",
    activebackground="#11632F",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 10, "bold"),
    cursor="hand2"
)
boton_registrar.pack(
    fill="x",
    padx=16,
    pady=(6, 14),
    ipady=10
)

tk.Label(
    panel_historial,
    text="Historial de pagos",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=16, pady=(12, 8))

columnas_historial = (
    "ID", "Fecha", "Valor", "Banco", "Comprobante", "Estado"
)

tabla_historial = ttk.Treeview(
    panel_historial,
    columns=columnas_historial,
    show="headings",
    height=8
)

anchos_historial = {
    "ID": 50,
    "Fecha": 130,
    "Valor": 100,
    "Banco": 130,
    "Comprobante": 130,
    "Estado": 110
}

for columna in columnas_historial:
    tabla_historial.heading(columna, text=columna)
    tabla_historial.column(
        columna,
        width=anchos_historial[columna]
    )

tabla_historial.pack(
    fill="both",
    expand=True,
    padx=16,
    pady=(0, 14)
)

tk.Label(
    ventana,
    text=(
        f"Base: {RUTA_DB} | Usuario: {USUARIO} | "
        "Archivo de prueba: pagos_cxp_contabilidad.py"
    ),
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

cargar_bancos()
cargar_cuentas()

ventana.mainloop()
