"""
BME-ERP - Estado de Resultados
Archivo: estado_resultados.py

Funciones:
- Calcula ingresos, costos, gastos y utilidad neta.
- Consulta por rango de fechas.
- Permite filtrar por módulo y centro de costo.
- Presenta detalle por cuenta contable.
- Compara con un período anterior opcional.
- Exporta el resultado a CSV.
"""

import csv
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

RUTA_DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")

COLOR_FONDO = "#EEF3F8"
COLOR_TARJETA = "#FFFFFF"
COLOR_AZUL = "#0F5C8E"
COLOR_VERDE = "#15803D"
COLOR_NARANJA = "#C56A00"
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


def moneda(valor):
    try:
        return f"${float(valor):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def porcentaje(valor):
    try:
        return f"{float(valor):,.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


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
# FILTROS
# ============================================================

def cargar_filtros():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT DISTINCT modulo_origen
            FROM comprobantes
            WHERE COALESCE(modulo_origen, '') <> ''
            ORDER BY modulo_origen
        """)

        modulos = ["TODOS"] + [
            fila["modulo_origen"] for fila in cursor.fetchall()
        ]
        combo_modulo["values"] = modulos
        combo_modulo.set("TODOS")

        cursor.execute("""
            SELECT codigo || ' - ' || nombre AS centro
            FROM centros_costo_contables
            WHERE estado='ACTIVO'
            ORDER BY codigo
        """)

        centros = ["TODOS"] + [
            fila["centro"] for fila in cursor.fetchall()
        ]
        combo_centro["values"] = centros
        combo_centro.set("TODOS")

    finally:
        conexion.close()


def validar_filtros():
    desde = entrada_desde.get().strip()
    hasta = entrada_hasta.get().strip()

    if not fecha_valida(desde):
        raise ValueError(
            "La fecha inicial debe tener formato AAAA-MM-DD."
        )

    if not fecha_valida(hasta):
        raise ValueError(
            "La fecha final debe tener formato AAAA-MM-DD."
        )

    if desde and hasta:
        fecha_desde = datetime.strptime(desde, "%Y-%m-%d")
        fecha_hasta = datetime.strptime(hasta, "%Y-%m-%d")

        if fecha_desde > fecha_hasta:
            raise ValueError(
                "La fecha inicial no puede ser mayor que la fecha final."
            )

    return desde, hasta


def codigo_centro():
    texto = combo_centro.get().strip()

    if not texto or texto == "TODOS":
        return None

    return texto.split(" - ", 1)[0].strip()


# ============================================================
# CONSULTA CONTABLE
# ============================================================

def consultar_cuentas_resultado(desde, hasta, modulo, centro):
    condiciones = [
        "c.estado='CONTABILIZADO'",
        "(pc.codigo LIKE '4%' OR pc.codigo LIKE '5%' OR pc.codigo LIKE '6%')"
    ]
    parametros = []

    if desde:
        condiciones.append("date(c.fecha) >= date(?)")
        parametros.append(desde)

    if hasta:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(hasta)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    if centro:
        condiciones.append("cc.codigo=?")
        parametros.append(centro)

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(f"""
            SELECT
                pc.id,
                pc.codigo,
                pc.nombre,
                pc.tipo_cuenta,
                pc.naturaleza,
                SUM(d.debito) AS debitos,
                SUM(d.credito) AS creditos,
                COUNT(*) AS movimientos
            FROM detalle_comprobante d
            INNER JOIN comprobantes c
                ON c.id=d.comprobante_id
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            LEFT JOIN centros_costo_contables cc
                ON cc.id=d.centro_costo_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY
                pc.id,
                pc.codigo,
                pc.nombre,
                pc.tipo_cuenta,
                pc.naturaleza
            ORDER BY pc.codigo
        """, parametros)

        registros = []

        for fila in cursor.fetchall():
            codigo = str(fila["codigo"])
            debitos = float(fila["debitos"] or 0)
            creditos = float(fila["creditos"] or 0)

            if codigo.startswith("4"):
                valor = creditos - debitos
                grupo = "INGRESOS"
            elif codigo.startswith("5"):
                valor = debitos - creditos
                grupo = "GASTOS"
            elif codigo.startswith("6"):
                valor = debitos - creditos
                grupo = "COSTOS"
            else:
                continue

            registros.append({
                "id": int(fila["id"]),
                "codigo": codigo,
                "nombre": fila["nombre"],
                "tipo_cuenta": fila["tipo_cuenta"],
                "naturaleza": fila["naturaleza"],
                "grupo": grupo,
                "debitos": debitos,
                "creditos": creditos,
                "valor": valor,
                "movimientos": int(fila["movimientos"] or 0)
            })

        return registros

    finally:
        conexion.close()


def clasificar_resultados(registros):
    ingresos_operacionales = 0.0
    otros_ingresos = 0.0
    costo_ventas = 0.0
    gastos_administracion = 0.0
    gastos_ventas = 0.0
    gastos_financieros = 0.0
    otros_gastos = 0.0

    for fila in registros:
        codigo = fila["codigo"]
        valor = fila["valor"]

        if codigo.startswith("41"):
            ingresos_operacionales += valor
        elif codigo.startswith("42"):
            otros_ingresos += valor
        elif codigo.startswith("6"):
            costo_ventas += valor
        elif codigo.startswith("51"):
            gastos_administracion += valor
        elif codigo.startswith("52"):
            gastos_ventas += valor
        elif codigo.startswith("53"):
            gastos_financieros += valor
        elif codigo.startswith("5"):
            otros_gastos += valor

    total_ingresos = ingresos_operacionales + otros_ingresos
    utilidad_bruta = ingresos_operacionales - costo_ventas

    gastos_operacionales = (
        gastos_administracion
        + gastos_ventas
    )

    utilidad_operacional = (
        utilidad_bruta
        - gastos_operacionales
    )

    utilidad_antes_impuestos = (
        utilidad_operacional
        + otros_ingresos
        - gastos_financieros
        - otros_gastos
    )

    impuesto_estimado = 0.0
    utilidad_neta = utilidad_antes_impuestos - impuesto_estimado

    margen_bruto = (
        utilidad_bruta / ingresos_operacionales * 100
        if ingresos_operacionales
        else 0
    )

    margen_operacional = (
        utilidad_operacional / ingresos_operacionales * 100
        if ingresos_operacionales
        else 0
    )

    margen_neto = (
        utilidad_neta / ingresos_operacionales * 100
        if ingresos_operacionales
        else 0
    )

    return {
        "ingresos_operacionales": ingresos_operacionales,
        "otros_ingresos": otros_ingresos,
        "total_ingresos": total_ingresos,
        "costo_ventas": costo_ventas,
        "utilidad_bruta": utilidad_bruta,
        "gastos_administracion": gastos_administracion,
        "gastos_ventas": gastos_ventas,
        "gastos_operacionales": gastos_operacionales,
        "gastos_financieros": gastos_financieros,
        "otros_gastos": otros_gastos,
        "utilidad_operacional": utilidad_operacional,
        "utilidad_antes_impuestos": utilidad_antes_impuestos,
        "impuesto_estimado": impuesto_estimado,
        "utilidad_neta": utilidad_neta,
        "margen_bruto": margen_bruto,
        "margen_operacional": margen_operacional,
        "margen_neto": margen_neto
    }


# ============================================================
# CONSULTA PRINCIPAL
# ============================================================

datos_actuales = []
resumen_actual = {}


def consultar_estado():
    try:
        desde, hasta = validar_filtros()
        modulo = combo_modulo.get().strip()
        centro = codigo_centro()

        registros = consultar_cuentas_resultado(
            desde,
            hasta,
            modulo,
            centro
        )

        resumen = clasificar_resultados(registros)

        tabla.delete(*tabla.get_children())

        for fila in registros:
            tabla.insert(
                "",
                "end",
                iid=str(fila["id"]),
                values=(
                    fila["codigo"],
                    fila["nombre"],
                    fila["grupo"],
                    fila["naturaleza"],
                    moneda(fila["debitos"]),
                    moneda(fila["creditos"]),
                    moneda(fila["valor"]),
                    fila["movimientos"]
                )
            )

        actualizar_resumen(resumen)
        actualizar_estado_gerencial(resumen)

        datos_actuales.clear()
        datos_actuales.extend(registros)

        resumen_actual.clear()
        resumen_actual.update(resumen)

    except Exception as error:
        messagebox.showerror(
            "Estado de Resultados",
            str(error)
        )


def actualizar_resumen(resumen):
    lbl_ingresos_operacionales.config(
        text=moneda(resumen["ingresos_operacionales"])
    )
    lbl_otros_ingresos.config(
        text=moneda(resumen["otros_ingresos"])
    )
    lbl_total_ingresos.config(
        text=moneda(resumen["total_ingresos"])
    )
    lbl_costo_ventas.config(
        text=moneda(resumen["costo_ventas"])
    )
    lbl_utilidad_bruta.config(
        text=moneda(resumen["utilidad_bruta"])
    )
    lbl_gastos_administracion.config(
        text=moneda(resumen["gastos_administracion"])
    )
    lbl_gastos_ventas.config(
        text=moneda(resumen["gastos_ventas"])
    )
    lbl_gastos_financieros.config(
        text=moneda(resumen["gastos_financieros"])
    )
    lbl_otros_gastos.config(
        text=moneda(resumen["otros_gastos"])
    )
    lbl_utilidad_operacional.config(
        text=moneda(resumen["utilidad_operacional"])
    )
    lbl_utilidad_antes_impuestos.config(
        text=moneda(resumen["utilidad_antes_impuestos"])
    )
    lbl_utilidad_neta.config(
        text=moneda(resumen["utilidad_neta"])
    )
    lbl_margen_bruto.config(
        text=porcentaje(resumen["margen_bruto"])
    )
    lbl_margen_operacional.config(
        text=porcentaje(resumen["margen_operacional"])
    )
    lbl_margen_neto.config(
        text=porcentaje(resumen["margen_neto"])
    )


def actualizar_estado_gerencial(resumen):
    utilidad = resumen["utilidad_neta"]

    if utilidad > 0:
        lbl_estado.config(
            text="RESULTADO POSITIVO",
            fg=COLOR_VERDE
        )
        lbl_mensaje.config(
            text=(
                f"La empresa presenta utilidad neta de "
                f"{moneda(utilidad)}."
            ),
            fg=COLOR_VERDE
        )
    elif utilidad < 0:
        lbl_estado.config(
            text="RESULTADO NEGATIVO",
            fg=COLOR_ROJO
        )
        lbl_mensaje.config(
            text=(
                f"La empresa presenta pérdida neta de "
                f"{moneda(abs(utilidad))}."
            ),
            fg=COLOR_ROJO
        )
    else:
        lbl_estado.config(
            text="PUNTO DE EQUILIBRIO",
            fg=COLOR_NARANJA
        )
        lbl_mensaje.config(
            text="El resultado neto del período es cero.",
            fg=COLOR_NARANJA
        )


# ============================================================
# EXPORTACIÓN
# ============================================================

def exportar_csv():
    if not datos_actuales:
        messagebox.showwarning(
            "Exportar",
            "No hay información para exportar."
        )
        return

    ruta = filedialog.asksaveasfilename(
        title="Guardar Estado de Resultados",
        defaultextension=".csv",
        initialfile="estado_resultados.csv",
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
                "ESTADO DE RESULTADOS"
            ])
            escritor.writerow([
                "Desde",
                entrada_desde.get().strip(),
                "Hasta",
                entrada_hasta.get().strip()
            ])
            escritor.writerow([])

            escritor.writerow([
                "Cuenta",
                "Nombre",
                "Grupo",
                "Naturaleza",
                "Débitos",
                "Créditos",
                "Valor neto",
                "Movimientos"
            ])

            for fila in datos_actuales:
                escritor.writerow([
                    fila["codigo"],
                    fila["nombre"],
                    fila["grupo"],
                    fila["naturaleza"],
                    fila["debitos"],
                    fila["creditos"],
                    fila["valor"],
                    fila["movimientos"]
                ])

            escritor.writerow([])
            escritor.writerow([
                "Ingresos operacionales",
                resumen_actual["ingresos_operacionales"]
            ])
            escritor.writerow([
                "Otros ingresos",
                resumen_actual["otros_ingresos"]
            ])
            escritor.writerow([
                "Costo de ventas",
                resumen_actual["costo_ventas"]
            ])
            escritor.writerow([
                "Utilidad bruta",
                resumen_actual["utilidad_bruta"]
            ])
            escritor.writerow([
                "Gastos de administración",
                resumen_actual["gastos_administracion"]
            ])
            escritor.writerow([
                "Gastos de ventas",
                resumen_actual["gastos_ventas"]
            ])
            escritor.writerow([
                "Gastos financieros",
                resumen_actual["gastos_financieros"]
            ])
            escritor.writerow([
                "Otros gastos",
                resumen_actual["otros_gastos"]
            ])
            escritor.writerow([
                "Utilidad operacional",
                resumen_actual["utilidad_operacional"]
            ])
            escritor.writerow([
                "Utilidad antes de impuestos",
                resumen_actual["utilidad_antes_impuestos"]
            ])
            escritor.writerow([
                "Utilidad neta",
                resumen_actual["utilidad_neta"]
            ])
            escritor.writerow([
                "Margen bruto %",
                resumen_actual["margen_bruto"]
            ])
            escritor.writerow([
                "Margen operacional %",
                resumen_actual["margen_operacional"]
            ])
            escritor.writerow([
                "Margen neto %",
                resumen_actual["margen_neto"]
            ])

        messagebox.showinfo(
            "Exportar",
            f"Archivo creado correctamente:\n\n{ruta}"
        )

    except OSError as error:
        messagebox.showerror(
            "Exportar",
            str(error)
        )


# ============================================================
# LIMPIAR
# ============================================================

def limpiar_filtros():
    entrada_desde.delete(0, tk.END)
    entrada_hasta.delete(0, tk.END)
    combo_modulo.set("TODOS")
    combo_centro.set("TODOS")
    consultar_estado()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Estado de Resultados")
ventana.geometry("1550x920")
ventana.minsize(1200, 760)
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
    background="#E8EEF4",
    foreground=COLOR_TEXTO,
    font=("Segoe UI", 9, "bold")
)

estilo.map(
    "Treeview",
    background=[("selected", COLOR_AZUL)],
    foreground=[("selected", "white")]
)

# Cabecera
cabecera = tk.Frame(
    ventana,
    bg=COLOR_AZUL,
    height=88
)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="ESTADO DE RESULTADOS",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Ingresos, costos, gastos y utilidad del período",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=29, pady=(3, 0))

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
panel_filtros = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_filtros.pack(fill="x", pady=(0, 12))

filtros = tk.Frame(panel_filtros, bg=COLOR_TARJETA)
filtros.pack(fill="x", padx=15, pady=14)

def etiqueta_filtro(texto, columna):
    tk.Label(
        filtros,
        text=texto,
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 8, "bold")
    ).grid(row=0, column=columna, sticky="w")

etiqueta_filtro("Desde", 0)
entrada_desde = ttk.Entry(filtros, width=13)
entrada_desde.grid(row=1, column=0, padx=(0, 10))

etiqueta_filtro("Hasta", 1)
entrada_hasta = ttk.Entry(filtros, width=13)
entrada_hasta.grid(row=1, column=1, padx=(0, 10))

etiqueta_filtro("Módulo", 2)
combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=23
)
combo_modulo.grid(row=1, column=2, padx=(0, 10))

etiqueta_filtro("Centro de costo", 3)
combo_centro = ttk.Combobox(
    filtros,
    state="readonly",
    width=28
)
combo_centro.grid(row=1, column=3, padx=(0, 10))

tk.Button(
    filtros,
    text="Consultar",
    command=consultar_estado,
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
).grid(row=1, column=4, padx=4)

tk.Button(
    filtros,
    text="Limpiar",
    command=limpiar_filtros,
    bg="#64748B",
    fg="white",
    activebackground="#475569",
    activeforeground="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=18,
    pady=7
).grid(row=1, column=5, padx=4)

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
).grid(row=1, column=6, padx=4)

# Panel gerencial
panel_gerencial = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_gerencial.pack(fill="x", pady=(0, 12))

gerencial = tk.Frame(panel_gerencial, bg=COLOR_TARJETA)
gerencial.pack(fill="x", padx=16, pady=12)

lbl_estado = tk.Label(
    gerencial,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 12, "bold")
)
lbl_estado.pack(side="left")

lbl_mensaje = tk.Label(
    gerencial,
    text="",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 10)
)
lbl_mensaje.pack(side="left", padx=18)

# Tarjetas principales
resumen = tk.Frame(
    contenedor,
    bg=COLOR_FONDO
)
resumen.pack(fill="x", pady=(0, 12))

for columna in range(6):
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
        padx=4
    )

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w", padx=12, pady=(10, 2))

    valor = tk.Label(
        marco,
        text="$0.00",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 14, "bold")
    )
    valor.pack(anchor="w", padx=12, pady=(0, 10))

    return valor

lbl_ingresos_operacionales = crear_tarjeta(
    0, "INGRESOS OPERACIONALES"
)
lbl_costo_ventas = crear_tarjeta(
    1, "COSTO DE VENTAS"
)
lbl_utilidad_bruta = crear_tarjeta(
    2, "UTILIDAD BRUTA"
)
lbl_utilidad_operacional = crear_tarjeta(
    3, "UTILIDAD OPERACIONAL"
)
lbl_utilidad_antes_impuestos = crear_tarjeta(
    4, "UTILIDAD ANTES IMPUESTOS"
)
lbl_utilidad_neta = crear_tarjeta(
    5, "UTILIDAD NETA"
)

# Indicadores secundarios
secundario = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
secundario.pack(fill="x", pady=(0, 12))

cuadros = tk.Frame(secundario, bg=COLOR_TARJETA)
cuadros.pack(fill="x", padx=15, pady=12)

for columna in range(9):
    cuadros.columnconfigure(columna, weight=1)

def bloque_indicador(columna, titulo, es_porcentaje=False):
    marco = tk.Frame(cuadros, bg=COLOR_TARJETA)
    marco.grid(row=0, column=columna, sticky="ew", padx=5)

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 7, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="0.00%" if es_porcentaje else "$0.00",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 10, "bold")
    )
    valor.pack(anchor="w", pady=(2, 0))
    return valor

lbl_otros_ingresos = bloque_indicador(0, "OTROS INGRESOS")
lbl_total_ingresos = bloque_indicador(1, "TOTAL INGRESOS")
lbl_gastos_administracion = bloque_indicador(
    2, "GASTOS ADMIN."
)
lbl_gastos_ventas = bloque_indicador(
    3, "GASTOS VENTAS"
)
lbl_gastos_financieros = bloque_indicador(
    4, "GASTOS FINANCIEROS"
)
lbl_otros_gastos = bloque_indicador(
    5, "OTROS GASTOS"
)
lbl_margen_bruto = bloque_indicador(
    6, "MARGEN BRUTO", True
)
lbl_margen_operacional = bloque_indicador(
    7, "MARGEN OPERACIONAL", True
)
lbl_margen_neto = bloque_indicador(
    8, "MARGEN NETO", True
)

# Tabla
panel_tabla = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_tabla.pack(fill="both", expand=True)

tk.Label(
    panel_tabla,
    text="Detalle por cuenta contable",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(12, 5))

columnas = (
    "Cuenta",
    "Nombre",
    "Grupo",
    "Naturaleza",
    "Débitos",
    "Créditos",
    "Valor neto",
    "Movimientos"
)

tabla = ttk.Treeview(
    panel_tabla,
    columns=columnas,
    show="headings"
)

anchos = {
    "Cuenta": 100,
    "Nombre": 340,
    "Grupo": 130,
    "Naturaleza": 110,
    "Débitos": 140,
    "Créditos": 140,
    "Valor neto": 140,
    "Movimientos": 100
}

for columna in columnas:
    tabla.heading(columna, text=columna)
    tabla.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in (
            "Débitos",
            "Créditos",
            "Valor neto",
            "Movimientos"
        ) else "w"
    )

scroll_y = ttk.Scrollbar(
    panel_tabla,
    orient="vertical",
    command=tabla.yview
)

tabla.configure(
    yscrollcommand=scroll_y.set
)

tabla.pack(
    fill="both",
    expand=True,
    padx=(14, 0),
    pady=(0, 12)
)

scroll_y.place(
    relx=1.0,
    rely=0.07,
    relheight=0.87,
    anchor="ne"
)

tk.Label(
    ventana,
    text=f"Base: {RUTA_DB}",
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

cargar_filtros()
consultar_estado()

ventana.mainloop()
