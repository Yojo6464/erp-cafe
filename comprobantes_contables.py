"""
BME-ERP - Visor de Comprobantes Contables
Archivo: comprobantes_contables.py

Funciones:
- Lista comprobantes contables.
- Filtra por fechas, tipo, estado, módulo y texto.
- Muestra encabezado y detalle.
- Verifica que el comprobante esté cuadrado.
- Permite exportar el comprobante seleccionado a CSV.
- No modifica comprobantes ni saldos.
"""

import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# ============================================================
# CONFIGURACIÓN
# ============================================================

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")

COLOR_FONDO = "#EEF3F8"
COLOR_SIDEBAR = "#153B5B"
COLOR_SIDEBAR_ACTIVO = "#1F567D"
COLOR_SUPERIOR = "#FFFFFF"
COLOR_TARJETA = "#FFFFFF"
COLOR_TEXTO = "#1F2937"
COLOR_SUAVE = "#64748B"
COLOR_AZUL = "#0F5C8E"
COLOR_VERDE = "#15803D"
COLOR_NARANJA = "#C56A00"
COLOR_ROJO = "#B42318"
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


def moneda(valor):
    try:
        return f"${float(valor):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def fecha_valida(texto):
    texto = texto.strip()

    if not texto:
        return True

    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ============================================================
# CARGA DE FILTROS
# ============================================================

def cargar_filtros():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT DISTINCT codigo
            FROM tipos_comprobante
            WHERE estado='ACTIVO'
            ORDER BY codigo
        """)
        tipos = ["TODOS"] + [fila["codigo"] for fila in cursor.fetchall()]
        combo_tipo["values"] = tipos
        combo_tipo.set("TODOS")

        cursor.execute("""
            SELECT DISTINCT modulo_origen
            FROM comprobantes
            WHERE COALESCE(modulo_origen, '') <> ''
            ORDER BY modulo_origen
        """)
        modulos = ["TODOS"] + [
            fila["modulo_origen"]
            for fila in cursor.fetchall()
        ]
        combo_modulo["values"] = modulos
        combo_modulo.set("TODOS")

        combo_estado["values"] = [
            "TODOS",
            "BORRADOR",
            "CONTABILIZADO",
            "ANULADO",
            "REVERTIDO"
        ]
        combo_estado.set("TODOS")

    finally:
        conexion.close()


# ============================================================
# CONSULTA PRINCIPAL
# ============================================================

def construir_filtros():
    condiciones = ["1=1"]
    parametros = []

    fecha_desde = entrada_desde.get().strip()
    fecha_hasta = entrada_hasta.get().strip()
    tipo = combo_tipo.get().strip()
    estado = combo_estado.get().strip()
    modulo = combo_modulo.get().strip()
    texto = entrada_buscar.get().strip()

    if not fecha_valida(fecha_desde):
        raise ValueError(
            "La fecha inicial debe tener formato AAAA-MM-DD."
        )

    if not fecha_valida(fecha_hasta):
        raise ValueError(
            "La fecha final debe tener formato AAAA-MM-DD."
        )

    if fecha_desde:
        condiciones.append("date(c.fecha) >= date(?)")
        parametros.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(fecha_hasta)

    if tipo and tipo != "TODOS":
        condiciones.append("tc.codigo = ?")
        parametros.append(tipo)

    if estado and estado != "TODOS":
        condiciones.append("c.estado = ?")
        parametros.append(estado)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen = ?")
        parametros.append(modulo)

    if texto:
        condiciones.append("""
            (
                c.consecutivo LIKE ?
                OR c.concepto LIKE ?
                OR c.documento_referencia LIKE ?
                OR COALESCE(t.nombre_razon_social, '') LIKE ?
            )
        """)
        patron = f"%{texto}%"
        parametros.extend([patron, patron, patron, patron])

    return " AND ".join(condiciones), parametros


def cargar_comprobantes():
    try:
        condicion, parametros = construir_filtros()

        conexion = conectar()

        try:
            cursor = conexion.cursor()
            cursor.execute(f"""
                SELECT
                    c.id,
                    c.fecha,
                    c.consecutivo,
                    tc.codigo AS tipo,
                    c.concepto,
                    COALESCE(t.nombre_razon_social, '') AS tercero,
                    c.modulo_origen,
                    c.estado,
                    c.total_debito,
                    c.total_credito
                FROM comprobantes c
                INNER JOIN tipos_comprobante tc
                    ON tc.id=c.tipo_comprobante_id
                LEFT JOIN terceros_contables t
                    ON t.id=c.tercero_id
                WHERE {condicion}
                ORDER BY c.fecha DESC, c.id DESC
            """, parametros)

            registros = cursor.fetchall()

        finally:
            conexion.close()

        tabla_comprobantes.delete(
            *tabla_comprobantes.get_children()
        )

        total_debito = 0.0
        total_credito = 0.0

        for fila in registros:
            total_debito += float(fila["total_debito"] or 0)
            total_credito += float(fila["total_credito"] or 0)

            tabla_comprobantes.insert(
                "",
                "end",
                iid=str(fila["id"]),
                values=(
                    fila["fecha"],
                    fila["consecutivo"],
                    fila["tipo"],
                    fila["concepto"],
                    fila["tercero"],
                    fila["modulo_origen"],
                    fila["estado"],
                    moneda(fila["total_debito"]),
                    moneda(fila["total_credito"])
                )
            )

        lbl_cantidad.config(text=str(len(registros)))
        lbl_debitos.config(text=moneda(total_debito))
        lbl_creditos.config(text=moneda(total_credito))

        diferencia = round(total_debito - total_credito, 2)
        lbl_diferencia.config(text=moneda(diferencia))

        if abs(diferencia) <= 0.01:
            lbl_diferencia.config(fg=COLOR_VERDE)
        else:
            lbl_diferencia.config(fg=COLOR_ROJO)

        limpiar_detalle()

    except Exception as error:
        messagebox.showerror(
            "Comprobantes contables",
            str(error)
        )


# ============================================================
# DETALLE
# ============================================================

def limpiar_detalle():
    for item in tabla_detalle.get_children():
        tabla_detalle.delete(item)

    lbl_comp_numero.config(text="Sin selección")
    lbl_comp_fecha.config(text="—")
    lbl_comp_tipo.config(text="—")
    lbl_comp_tercero.config(text="—")
    lbl_comp_documento.config(text="—")
    lbl_comp_modulo.config(text="—")
    lbl_comp_estado.config(text="—")
    lbl_comp_concepto.config(text="—")
    lbl_total_debito_detalle.config(text="$0.00")
    lbl_total_credito_detalle.config(text="$0.00")
    lbl_balance_detalle.config(text="—", fg=COLOR_SUAVE)


def obtener_comprobante_seleccionado():
    seleccion = tabla_comprobantes.selection()

    if not seleccion:
        return None

    return int(seleccion[0])


def cargar_detalle(evento=None):
    comprobante_id = obtener_comprobante_seleccionado()

    if comprobante_id is None:
        return

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                c.id,
                c.fecha,
                c.consecutivo,
                c.concepto,
                c.documento_referencia,
                c.modulo_origen,
                c.tabla_origen,
                c.registro_origen_id,
                c.estado,
                c.total_debito,
                c.total_credito,
                c.usuario,
                tc.codigo AS tipo_codigo,
                tc.nombre AS tipo_nombre,
                COALESCE(t.nombre_razon_social, '') AS tercero
            FROM comprobantes c
            INNER JOIN tipos_comprobante tc
                ON tc.id=c.tipo_comprobante_id
            LEFT JOIN terceros_contables t
                ON t.id=c.tercero_id
            WHERE c.id=?
        """, (comprobante_id,))

        encabezado = cursor.fetchone()

        if not encabezado:
            limpiar_detalle()
            return

        cursor.execute("""
            SELECT
                d.secuencia,
                pc.codigo AS cuenta_codigo,
                pc.nombre AS cuenta_nombre,
                d.descripcion,
                COALESCE(t.nombre_razon_social, '') AS tercero,
                COALESCE(cc.codigo, '') AS centro_codigo,
                COALESCE(cc.nombre, '') AS centro_nombre,
                d.documento_referencia,
                d.debito,
                d.credito
            FROM detalle_comprobante d
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            LEFT JOIN terceros_contables t
                ON t.id=d.tercero_id
            LEFT JOIN centros_costo_contables cc
                ON cc.id=d.centro_costo_id
            WHERE d.comprobante_id=?
            ORDER BY d.secuencia
        """, (comprobante_id,))

        detalle = cursor.fetchall()

    finally:
        conexion.close()

    lbl_comp_numero.config(text=encabezado["consecutivo"])
    lbl_comp_fecha.config(text=encabezado["fecha"])
    lbl_comp_tipo.config(
        text=f"{encabezado['tipo_codigo']} - {encabezado['tipo_nombre']}"
    )
    lbl_comp_tercero.config(
        text=encabezado["tercero"] or "Sin tercero"
    )
    lbl_comp_documento.config(
        text=encabezado["documento_referencia"] or "—"
    )
    lbl_comp_modulo.config(
        text=(
            f"{encabezado['modulo_origen']} / "
            f"{encabezado['tabla_origen']} "
            f"#{encabezado['registro_origen_id']}"
        )
    )
    lbl_comp_estado.config(text=encabezado["estado"])
    lbl_comp_concepto.config(text=encabezado["concepto"])

    tabla_detalle.delete(*tabla_detalle.get_children())

    total_debito = 0.0
    total_credito = 0.0

    for fila in detalle:
        total_debito += float(fila["debito"] or 0)
        total_credito += float(fila["credito"] or 0)

        centro = fila["centro_codigo"]

        if fila["centro_nombre"]:
            centro += f" - {fila['centro_nombre']}"

        tabla_detalle.insert(
            "",
            "end",
            values=(
                fila["secuencia"],
                fila["cuenta_codigo"],
                fila["cuenta_nombre"],
                fila["descripcion"],
                fila["tercero"],
                centro,
                moneda(fila["debito"]),
                moneda(fila["credito"])
            )
        )

    lbl_total_debito_detalle.config(text=moneda(total_debito))
    lbl_total_credito_detalle.config(text=moneda(total_credito))

    diferencia = round(total_debito - total_credito, 2)

    if abs(diferencia) <= 0.01:
        lbl_balance_detalle.config(
            text="COMPROBANTE CUADRADO",
            fg=COLOR_VERDE
        )
    else:
        lbl_balance_detalle.config(
            text=f"DESCUADRE: {moneda(diferencia)}",
            fg=COLOR_ROJO
        )


# ============================================================
# EXPORTACIÓN
# ============================================================

def exportar_csv():
    comprobante_id = obtener_comprobante_seleccionado()

    if comprobante_id is None:
        messagebox.showwarning(
            "Exportar comprobante",
            "Seleccione un comprobante."
        )
        return

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT consecutivo
            FROM comprobantes
            WHERE id=?
        """, (comprobante_id,))

        fila = cursor.fetchone()

        if not fila:
            return

        consecutivo = fila["consecutivo"]

        cursor.execute("""
            SELECT
                c.consecutivo,
                c.fecha,
                c.concepto,
                pc.codigo AS cuenta,
                pc.nombre AS nombre_cuenta,
                d.descripcion,
                COALESCE(t.nombre_razon_social, '') AS tercero,
                COALESCE(cc.codigo, '') AS centro_costo,
                d.debito,
                d.credito
            FROM detalle_comprobante d
            INNER JOIN comprobantes c
                ON c.id=d.comprobante_id
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            LEFT JOIN terceros_contables t
                ON t.id=d.tercero_id
            LEFT JOIN centros_costo_contables cc
                ON cc.id=d.centro_costo_id
            WHERE d.comprobante_id=?
            ORDER BY d.secuencia
        """, (comprobante_id,))

        registros = cursor.fetchall()

    finally:
        conexion.close()

    ruta = filedialog.asksaveasfilename(
        title="Guardar comprobante en CSV",
        defaultextension=".csv",
        initialfile=f"{consecutivo}.csv",
        filetypes=[
            ("Archivo CSV", "*.csv"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not ruta:
        return

    try:
        with open(
            ruta,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow([
                "Comprobante",
                "Fecha",
                "Concepto",
                "Cuenta",
                "Nombre cuenta",
                "Descripción",
                "Tercero",
                "Centro de costo",
                "Débito",
                "Crédito"
            ])

            for fila in registros:
                escritor.writerow([
                    fila["consecutivo"],
                    fila["fecha"],
                    fila["concepto"],
                    fila["cuenta"],
                    fila["nombre_cuenta"],
                    fila["descripcion"],
                    fila["tercero"],
                    fila["centro_costo"],
                    fila["debito"],
                    fila["credito"]
                ])

        messagebox.showinfo(
            "Exportar comprobante",
            f"Archivo creado correctamente:\n\n{ruta}"
        )

    except OSError as error:
        messagebox.showerror(
            "Exportar comprobante",
            str(error)
        )


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Comprobantes Contables")
ventana.geometry("1500x900")
ventana.minsize(1200, 760)
ventana.configure(bg=COLOR_FONDO)

estilo = ttk.Style()

try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Treeview",
    background="white",
    foreground=COLOR_TEXTO,
    rowheight=27,
    fieldbackground="white",
    font=("Segoe UI", 9)
)

estilo.configure(
    "Treeview.Heading",
    background="#E8EEF4",
    foreground=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold"),
    relief="flat"
)

estilo.map(
    "Treeview",
    background=[("selected", COLOR_AZUL)],
    foreground=[("selected", "white")]
)

# Barra superior
barra_superior = tk.Frame(
    ventana,
    bg=COLOR_SUPERIOR,
    height=72,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
barra_superior.pack(fill="x")
barra_superior.pack_propagate(False)

tk.Label(
    barra_superior,
    text="COMPROBANTES CONTABLES",
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 20, "bold")
).pack(side="left", padx=25)

tk.Label(
    barra_superior,
    text=f"Base: {RUTA_DB}",
    bg=COLOR_SUPERIOR,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(side="right", padx=25)

# Contenedor
contenedor = tk.Frame(
    ventana,
    bg=COLOR_FONDO
)
contenedor.pack(
    fill="both",
    expand=True,
    padx=18,
    pady=18
)

# Filtros
marco_filtros = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
marco_filtros.pack(fill="x", pady=(0, 12))

filtros = tk.Frame(
    marco_filtros,
    bg=COLOR_TARJETA
)
filtros.pack(fill="x", padx=18, pady=14)

for columna in range(14):
    filtros.columnconfigure(columna, weight=0)

tk.Label(
    filtros,
    text="Desde",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=0, sticky="w")

entrada_desde = ttk.Entry(filtros, width=12)
entrada_desde.grid(row=1, column=0, padx=(0, 8))

tk.Label(
    filtros,
    text="Hasta",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=1, sticky="w")

entrada_hasta = ttk.Entry(filtros, width=12)
entrada_hasta.grid(row=1, column=1, padx=(0, 8))

tk.Label(
    filtros,
    text="Tipo",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=2, sticky="w")

combo_tipo = ttk.Combobox(
    filtros,
    state="readonly",
    width=11
)
combo_tipo.grid(row=1, column=2, padx=(0, 8))

tk.Label(
    filtros,
    text="Estado",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=3, sticky="w")

combo_estado = ttk.Combobox(
    filtros,
    state="readonly",
    width=15
)
combo_estado.grid(row=1, column=3, padx=(0, 8))

tk.Label(
    filtros,
    text="Módulo",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=4, sticky="w")

combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=16
)
combo_modulo.grid(row=1, column=4, padx=(0, 8))

tk.Label(
    filtros,
    text="Buscar",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 8, "bold")
).grid(row=0, column=5, sticky="w")

entrada_buscar = ttk.Entry(filtros, width=28)
entrada_buscar.grid(row=1, column=5, padx=(0, 10))

tk.Button(
    filtros,
    text="Consultar",
    command=cargar_comprobantes,
    bg=COLOR_AZUL,
    fg="white",
    activebackground="#0B4B75",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=18,
    pady=7
).grid(row=1, column=6, padx=4)

tk.Button(
    filtros,
    text="Exportar CSV",
    command=exportar_csv,
    bg=COLOR_VERDE,
    fg="white",
    activebackground="#11632F",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=18,
    pady=7
).grid(row=1, column=7, padx=4)

# Tarjetas de resumen
resumen = tk.Frame(
    contenedor,
    bg=COLOR_FONDO
)
resumen.pack(fill="x", pady=(0, 12))

for columna in range(4):
    resumen.columnconfigure(columna, weight=1)

def crear_tarjeta(columna, titulo):
    marco = tk.Frame(
        resumen,
        bg=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=6
    )

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w", padx=14, pady=(10, 2))

    valor = tk.Label(
        marco,
        text="0",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 16, "bold")
    )
    valor.pack(anchor="w", padx=14, pady=(0, 10))

    return valor

lbl_cantidad = crear_tarjeta(0, "COMPROBANTES")
lbl_debitos = crear_tarjeta(1, "TOTAL DÉBITOS")
lbl_creditos = crear_tarjeta(2, "TOTAL CRÉDITOS")
lbl_diferencia = crear_tarjeta(3, "DIFERENCIA")

# Panel superior: lista
panel_lista = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_lista.pack(fill="both", expand=True, pady=(0, 12))

tk.Label(
    panel_lista,
    text="Listado de comprobantes",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=15, pady=(12, 5))

columnas = (
    "Fecha",
    "Consecutivo",
    "Tipo",
    "Concepto",
    "Tercero",
    "Módulo",
    "Estado",
    "Débito",
    "Crédito"
)

tabla_comprobantes = ttk.Treeview(
    panel_lista,
    columns=columnas,
    show="headings",
    height=9
)

anchos = {
    "Fecha": 140,
    "Consecutivo": 140,
    "Tipo": 70,
    "Concepto": 360,
    "Tercero": 200,
    "Módulo": 110,
    "Estado": 115,
    "Débito": 130,
    "Crédito": 130
}

for columna in columnas:
    tabla_comprobantes.heading(columna, text=columna)
    tabla_comprobantes.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in ("Débito", "Crédito") else "w"
    )

scroll_y = ttk.Scrollbar(
    panel_lista,
    orient="vertical",
    command=tabla_comprobantes.yview
)
scroll_x = ttk.Scrollbar(
    panel_lista,
    orient="horizontal",
    command=tabla_comprobantes.xview
)

tabla_comprobantes.configure(
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)

tabla_comprobantes.pack(
    fill="both",
    expand=True,
    padx=(15, 0),
    pady=(0, 0)
)
scroll_y.place(relx=1.0, rely=0.09, relheight=0.78, anchor="ne")
scroll_x.pack(fill="x", padx=15, pady=(0, 10))

tabla_comprobantes.bind(
    "<<TreeviewSelect>>",
    cargar_detalle
)

# Panel detalle
panel_detalle = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_detalle.pack(fill="both", expand=True)

encabezado = tk.Frame(
    panel_detalle,
    bg=COLOR_TARJETA
)
encabezado.pack(fill="x", padx=15, pady=12)

def dato_encabezado(titulo, fila, columna, ancho=25):
    marco = tk.Frame(encabezado, bg=COLOR_TARJETA)
    marco.grid(
        row=fila,
        column=columna,
        sticky="ew",
        padx=8,
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
        anchor="w",
        justify="left",
        wraplength=350
    )
    valor.pack(anchor="w")
    return valor

for columna in range(4):
    encabezado.columnconfigure(columna, weight=1)

lbl_comp_numero = dato_encabezado("COMPROBANTE", 0, 0)
lbl_comp_fecha = dato_encabezado("FECHA", 0, 1)
lbl_comp_tipo = dato_encabezado("TIPO", 0, 2)
lbl_comp_estado = dato_encabezado("ESTADO", 0, 3)
lbl_comp_tercero = dato_encabezado("TERCERO", 1, 0)
lbl_comp_documento = dato_encabezado("DOCUMENTO", 1, 1)
lbl_comp_modulo = dato_encabezado("ORIGEN", 1, 2)
lbl_comp_concepto = dato_encabezado("CONCEPTO", 1, 3)

columnas_detalle = (
    "Sec.",
    "Cuenta",
    "Nombre cuenta",
    "Descripción",
    "Tercero",
    "Centro costo",
    "Débito",
    "Crédito"
)

tabla_detalle = ttk.Treeview(
    panel_detalle,
    columns=columnas_detalle,
    show="headings",
    height=8
)

anchos_detalle = {
    "Sec.": 55,
    "Cuenta": 90,
    "Nombre cuenta": 240,
    "Descripción": 280,
    "Tercero": 180,
    "Centro costo": 150,
    "Débito": 130,
    "Crédito": 130
}

for columna in columnas_detalle:
    tabla_detalle.heading(columna, text=columna)
    tabla_detalle.column(
        columna,
        width=anchos_detalle[columna],
        anchor="e" if columna in ("Débito", "Crédito") else "w"
    )

tabla_detalle.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=(0, 8)
)

totales = tk.Frame(
    panel_detalle,
    bg=COLOR_TARJETA
)
totales.pack(fill="x", padx=15, pady=(0, 12))

tk.Label(
    totales,
    text="Débitos:",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 9, "bold")
).pack(side="left")

lbl_total_debito_detalle = tk.Label(
    totales,
    text="$0.00",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 10, "bold")
)
lbl_total_debito_detalle.pack(side="left", padx=(5, 25))

tk.Label(
    totales,
    text="Créditos:",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 9, "bold")
).pack(side="left")

lbl_total_credito_detalle = tk.Label(
    totales,
    text="$0.00",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 10, "bold")
)
lbl_total_credito_detalle.pack(side="left", padx=(5, 25))

lbl_balance_detalle = tk.Label(
    totales,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 10, "bold")
)
lbl_balance_detalle.pack(side="right")

# Inicio
cargar_filtros()
cargar_comprobantes()

ventana.mainloop()
