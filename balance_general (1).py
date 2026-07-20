"""
BME-ERP - Balance General
Archivo: balance_general.py

Funciones:
- Calcula Activos, Pasivos y Patrimonio a una fecha de corte.
- Incluye automáticamente el resultado acumulado del período.
- Agrupa por clase, grupo y cuenta.
- Permite filtrar por nivel del PUC y módulo.
- Valida la ecuación: Activo = Pasivo + Patrimonio.
- Exporta el reporte a CSV.
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
            SELECT DISTINCT nivel
            FROM plan_cuentas
            ORDER BY nivel
        """)

        niveles = ["TODOS"] + [
            str(fila["nivel"]) for fila in cursor.fetchall()
        ]
        combo_nivel["values"] = niveles
        combo_nivel.set("TODOS")

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

    finally:
        conexion.close()


def validar_filtros():
    fecha_corte = entrada_fecha.get().strip()

    if not fecha_valida(fecha_corte):
        raise ValueError(
            "La fecha de corte debe tener formato AAAA-MM-DD."
        )

    nivel = combo_nivel.get().strip()
    modulo = combo_modulo.get().strip()

    return fecha_corte, nivel, modulo


# ============================================================
# CÁLCULOS
# ============================================================

def obtener_saldos_balance(fecha_corte, modulo):
    condiciones = [
        "c.estado='CONTABILIZADO'",
        "(pc.codigo LIKE '1%' OR pc.codigo LIKE '2%' OR pc.codigo LIKE '3%')"
    ]
    parametros = []

    if fecha_corte:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(fecha_corte)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(f"""
            SELECT
                pc.id,
                pc.codigo,
                pc.nombre,
                pc.nivel,
                pc.naturaleza,
                pc.tipo_cuenta,
                SUM(d.debito) AS debitos,
                SUM(d.credito) AS creditos,
                COUNT(*) AS movimientos
            FROM detalle_comprobante d
            INNER JOIN comprobantes c
                ON c.id=d.comprobante_id
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY
                pc.id,
                pc.codigo,
                pc.nombre,
                pc.nivel,
                pc.naturaleza,
                pc.tipo_cuenta
            ORDER BY pc.codigo
        """, parametros)

        registros = []

        for fila in cursor.fetchall():
            codigo = str(fila["codigo"])
            debitos = float(fila["debitos"] or 0)
            creditos = float(fila["creditos"] or 0)

            if codigo.startswith("1"):
                valor = debitos - creditos
                clase = "ACTIVO"
            elif codigo.startswith("2"):
                valor = creditos - debitos
                clase = "PASIVO"
            elif codigo.startswith("3"):
                valor = creditos - debitos
                clase = "PATRIMONIO"
            else:
                continue

            registros.append({
                "id": int(fila["id"]),
                "codigo": codigo,
                "nombre": fila["nombre"],
                "nivel": int(fila["nivel"]),
                "naturaleza": fila["naturaleza"],
                "tipo_cuenta": fila["tipo_cuenta"],
                "clase": clase,
                "debitos": debitos,
                "creditos": creditos,
                "valor": valor,
                "movimientos": int(fila["movimientos"] or 0)
            })

        return registros

    finally:
        conexion.close()


def obtener_resultado_acumulado(fecha_corte, modulo):
    condiciones = [
        "c.estado='CONTABILIZADO'",
        "(pc.codigo LIKE '4%' OR pc.codigo LIKE '5%' OR pc.codigo LIKE '6%')"
    ]
    parametros = []

    if fecha_corte:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(fecha_corte)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute(f"""
            SELECT
                pc.codigo,
                SUM(d.debito) AS debitos,
                SUM(d.credito) AS creditos
            FROM detalle_comprobante d
            INNER JOIN comprobantes c
                ON c.id=d.comprobante_id
            INNER JOIN plan_cuentas pc
                ON pc.id=d.cuenta_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY pc.codigo
        """, parametros)

        resultado = 0.0

        for fila in cursor.fetchall():
            codigo = str(fila["codigo"])
            debitos = float(fila["debitos"] or 0)
            creditos = float(fila["creditos"] or 0)

            if codigo.startswith("4"):
                resultado += creditos - debitos
            elif codigo.startswith("5") or codigo.startswith("6"):
                resultado -= debitos - creditos

        return resultado

    finally:
        conexion.close()


def clasificar_corriente(codigo, clase):
    """
    Clasificación inicial basada en el PUC.
    Puede refinarse posteriormente desde parámetros contables.
    """
    codigo = str(codigo)

    if clase == "ACTIVO":
        if codigo.startswith(("11", "13", "14")):
            return "CORRIENTE"
        return "NO CORRIENTE"

    if clase == "PASIVO":
        if codigo.startswith(("21", "22", "23", "24", "25", "26")):
            return "CORRIENTE"
        return "NO CORRIENTE"

    return "PATRIMONIO"


# ============================================================
# CONSULTA PRINCIPAL
# ============================================================

datos_actuales = []
resumen_actual = {}


def consultar_balance():
    try:
        fecha_corte, nivel, modulo = validar_filtros()

        registros = obtener_saldos_balance(
            fecha_corte,
            modulo
        )

        resultado_periodo = obtener_resultado_acumulado(
            fecha_corte,
            modulo
        )

        if nivel and nivel != "TODOS":
            registros = [
                fila for fila in registros
                if fila["nivel"] == int(nivel)
            ]

        incluir_ceros = variable_ceros.get()

        filtrados = []

        for fila in registros:
            if not incluir_ceros and abs(fila["valor"]) <= 0.005:
                continue

            fila["clasificacion"] = clasificar_corriente(
                fila["codigo"],
                fila["clase"]
            )
            filtrados.append(fila)

        total_activo_corriente = sum(
            fila["valor"]
            for fila in filtrados
            if fila["clase"] == "ACTIVO"
            and fila["clasificacion"] == "CORRIENTE"
        )

        total_activo_no_corriente = sum(
            fila["valor"]
            for fila in filtrados
            if fila["clase"] == "ACTIVO"
            and fila["clasificacion"] == "NO CORRIENTE"
        )

        total_pasivo_corriente = sum(
            fila["valor"]
            for fila in filtrados
            if fila["clase"] == "PASIVO"
            and fila["clasificacion"] == "CORRIENTE"
        )

        total_pasivo_no_corriente = sum(
            fila["valor"]
            for fila in filtrados
            if fila["clase"] == "PASIVO"
            and fila["clasificacion"] == "NO CORRIENTE"
        )

        patrimonio_contable = sum(
            fila["valor"]
            for fila in filtrados
            if fila["clase"] == "PATRIMONIO"
        )

        total_activo = (
            total_activo_corriente
            + total_activo_no_corriente
        )

        total_pasivo = (
            total_pasivo_corriente
            + total_pasivo_no_corriente
        )

        total_patrimonio = (
            patrimonio_contable
            + resultado_periodo
        )

        total_pasivo_patrimonio = (
            total_pasivo
            + total_patrimonio
        )

        diferencia = total_activo - total_pasivo_patrimonio

        tabla.delete(*tabla.get_children())

        for fila in filtrados:
            tabla.insert(
                "",
                "end",
                iid=str(fila["id"]),
                values=(
                    fila["codigo"],
                    fila["nombre"],
                    fila["nivel"],
                    fila["clase"],
                    fila["clasificacion"],
                    fila["naturaleza"],
                    moneda(fila["debitos"]),
                    moneda(fila["creditos"]),
                    moneda(fila["valor"]),
                    fila["movimientos"]
                )
            )

        lbl_activo_corriente.config(
            text=moneda(total_activo_corriente)
        )
        lbl_activo_no_corriente.config(
            text=moneda(total_activo_no_corriente)
        )
        lbl_total_activo.config(
            text=moneda(total_activo)
        )
        lbl_pasivo_corriente.config(
            text=moneda(total_pasivo_corriente)
        )
        lbl_pasivo_no_corriente.config(
            text=moneda(total_pasivo_no_corriente)
        )
        lbl_total_pasivo.config(
            text=moneda(total_pasivo)
        )
        lbl_patrimonio_contable.config(
            text=moneda(patrimonio_contable)
        )
        lbl_resultado_periodo.config(
            text=moneda(resultado_periodo)
        )
        lbl_total_patrimonio.config(
            text=moneda(total_patrimonio)
        )
        lbl_pasivo_patrimonio.config(
            text=moneda(total_pasivo_patrimonio)
        )
        lbl_diferencia.config(
            text=moneda(diferencia)
        )

        if abs(diferencia) <= 0.01:
            lbl_estado.config(
                text="ECUACIÓN CONTABLE CUADRADA",
                fg=COLOR_VERDE
            )
            lbl_diferencia.config(fg=COLOR_VERDE)
        else:
            lbl_estado.config(
                text="DIFERENCIA EN ECUACIÓN CONTABLE",
                fg=COLOR_ROJO
            )
            lbl_diferencia.config(fg=COLOR_ROJO)

        capital_trabajo = (
            total_activo_corriente
            - total_pasivo_corriente
        )

        razon_corriente = (
            total_activo_corriente / total_pasivo_corriente
            if total_pasivo_corriente
            else 0
        )

        endeudamiento = (
            total_pasivo / total_activo * 100
            if total_activo
            else 0
        )

        lbl_capital_trabajo.config(
            text=moneda(capital_trabajo)
        )
        lbl_razon_corriente.config(
            text=f"{razon_corriente:,.2f}"
        )
        lbl_endeudamiento.config(
            text=f"{endeudamiento:,.2f}%"
        )

        datos_actuales.clear()
        datos_actuales.extend(filtrados)

        resumen_actual.clear()
        resumen_actual.update({
            "fecha_corte": fecha_corte,
            "activo_corriente": total_activo_corriente,
            "activo_no_corriente": total_activo_no_corriente,
            "total_activo": total_activo,
            "pasivo_corriente": total_pasivo_corriente,
            "pasivo_no_corriente": total_pasivo_no_corriente,
            "total_pasivo": total_pasivo,
            "patrimonio_contable": patrimonio_contable,
            "resultado_periodo": resultado_periodo,
            "total_patrimonio": total_patrimonio,
            "pasivo_patrimonio": total_pasivo_patrimonio,
            "diferencia": diferencia,
            "capital_trabajo": capital_trabajo,
            "razon_corriente": razon_corriente,
            "endeudamiento": endeudamiento
        })

    except Exception as error:
        messagebox.showerror(
            "Balance General",
            str(error)
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
        title="Guardar Balance General",
        defaultextension=".csv",
        initialfile="balance_general.csv",
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

            escritor.writerow(["BALANCE GENERAL"])
            escritor.writerow([
                "Fecha de corte",
                resumen_actual.get("fecha_corte", "")
            ])
            escritor.writerow([])

            escritor.writerow([
                "Cuenta",
                "Nombre",
                "Nivel",
                "Clase",
                "Clasificación",
                "Naturaleza",
                "Débitos",
                "Créditos",
                "Saldo",
                "Movimientos"
            ])

            for fila in datos_actuales:
                escritor.writerow([
                    fila["codigo"],
                    fila["nombre"],
                    fila["nivel"],
                    fila["clase"],
                    fila["clasificacion"],
                    fila["naturaleza"],
                    fila["debitos"],
                    fila["creditos"],
                    fila["valor"],
                    fila["movimientos"]
                ])

            escritor.writerow([])
            escritor.writerow([
                "Activo corriente",
                resumen_actual["activo_corriente"]
            ])
            escritor.writerow([
                "Activo no corriente",
                resumen_actual["activo_no_corriente"]
            ])
            escritor.writerow([
                "Total activo",
                resumen_actual["total_activo"]
            ])
            escritor.writerow([
                "Pasivo corriente",
                resumen_actual["pasivo_corriente"]
            ])
            escritor.writerow([
                "Pasivo no corriente",
                resumen_actual["pasivo_no_corriente"]
            ])
            escritor.writerow([
                "Total pasivo",
                resumen_actual["total_pasivo"]
            ])
            escritor.writerow([
                "Patrimonio contable",
                resumen_actual["patrimonio_contable"]
            ])
            escritor.writerow([
                "Resultado del período",
                resumen_actual["resultado_periodo"]
            ])
            escritor.writerow([
                "Total patrimonio",
                resumen_actual["total_patrimonio"]
            ])
            escritor.writerow([
                "Pasivo + Patrimonio",
                resumen_actual["pasivo_patrimonio"]
            ])
            escritor.writerow([
                "Diferencia",
                resumen_actual["diferencia"]
            ])
            escritor.writerow([
                "Capital de trabajo",
                resumen_actual["capital_trabajo"]
            ])
            escritor.writerow([
                "Razón corriente",
                resumen_actual["razon_corriente"]
            ])
            escritor.writerow([
                "Endeudamiento %",
                resumen_actual["endeudamiento"]
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
    entrada_fecha.delete(0, tk.END)
    combo_nivel.set("TODOS")
    combo_modulo.set("TODOS")
    variable_ceros.set(False)
    consultar_balance()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Balance General")
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
    text="BALANCE GENERAL",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Activos, pasivos, patrimonio y ecuación contable",
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

etiqueta_filtro("Fecha de corte", 0)
entrada_fecha = ttk.Entry(filtros, width=15)
entrada_fecha.grid(row=1, column=0, padx=(0, 10))

etiqueta_filtro("Nivel PUC", 1)
combo_nivel = ttk.Combobox(
    filtros,
    state="readonly",
    width=12
)
combo_nivel.grid(row=1, column=1, padx=(0, 10))

etiqueta_filtro("Módulo", 2)
combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=24
)
combo_modulo.grid(row=1, column=2, padx=(0, 10))

variable_ceros = tk.BooleanVar(value=False)

tk.Checkbutton(
    filtros,
    text="Incluir cuentas en cero",
    variable=variable_ceros,
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    activebackground=COLOR_TARJETA,
    font=("Segoe UI", 8)
).grid(row=1, column=3, padx=8)

tk.Button(
    filtros,
    text="Consultar",
    command=consultar_balance,
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

# Estado
panel_estado = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_estado.pack(fill="x", pady=(0, 12))

estado = tk.Frame(panel_estado, bg=COLOR_TARJETA)
estado.pack(fill="x", padx=16, pady=12)

lbl_estado = tk.Label(
    estado,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 11, "bold")
)
lbl_estado.pack(side="left")

tk.Label(
    estado,
    text="Diferencia:",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 9, "bold")
).pack(side="right")

lbl_diferencia = tk.Label(
    estado,
    text="$0.00",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 11, "bold")
)
lbl_diferencia.pack(side="right", padx=(6, 18))

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

lbl_total_activo = crear_tarjeta(0, "TOTAL ACTIVO")
lbl_total_pasivo = crear_tarjeta(1, "TOTAL PASIVO")
lbl_total_patrimonio = crear_tarjeta(2, "TOTAL PATRIMONIO")
lbl_pasivo_patrimonio = crear_tarjeta(3, "PASIVO + PATRIMONIO")
lbl_capital_trabajo = crear_tarjeta(4, "CAPITAL DE TRABAJO")
lbl_razon_corriente = crear_tarjeta(5, "RAZÓN CORRIENTE")

# Indicadores secundarios
secundario = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
secundario.pack(fill="x", pady=(0, 12))

bloques = tk.Frame(secundario, bg=COLOR_TARJETA)
bloques.pack(fill="x", padx=15, pady=12)

for columna in range(8):
    bloques.columnconfigure(columna, weight=1)

def crear_bloque(columna, titulo, texto_inicial="$0.00"):
    marco = tk.Frame(bloques, bg=COLOR_TARJETA)
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
        text=texto_inicial,
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 10, "bold")
    )
    valor.pack(anchor="w", pady=(2, 0))
    return valor

lbl_activo_corriente = crear_bloque(
    0, "ACTIVO CORRIENTE"
)
lbl_activo_no_corriente = crear_bloque(
    1, "ACTIVO NO CORRIENTE"
)
lbl_pasivo_corriente = crear_bloque(
    2, "PASIVO CORRIENTE"
)
lbl_pasivo_no_corriente = crear_bloque(
    3, "PASIVO NO CORRIENTE"
)
lbl_patrimonio_contable = crear_bloque(
    4, "PATRIMONIO CONTABLE"
)
lbl_resultado_periodo = crear_bloque(
    5, "RESULTADO DEL PERÍODO"
)
lbl_endeudamiento = crear_bloque(
    6, "ENDEUDAMIENTO", "0.00%"
)
crear_bloque(
    7, "ECUACIÓN", "A = P + PT"
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
    text="Detalle de cuentas de balance",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(12, 5))

columnas = (
    "Cuenta",
    "Nombre",
    "Nivel",
    "Clase",
    "Clasificación",
    "Naturaleza",
    "Débitos",
    "Créditos",
    "Saldo",
    "Movimientos"
)

tabla = ttk.Treeview(
    panel_tabla,
    columns=columnas,
    show="headings"
)

anchos = {
    "Cuenta": 100,
    "Nombre": 330,
    "Nivel": 60,
    "Clase": 110,
    "Clasificación": 130,
    "Naturaleza": 100,
    "Débitos": 135,
    "Créditos": 135,
    "Saldo": 135,
    "Movimientos": 100
}

for columna in columnas:
    tabla.heading(columna, text=columna)
    tabla.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in (
            "Débitos", "Créditos", "Saldo", "Movimientos"
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
consultar_balance()

ventana.mainloop()
