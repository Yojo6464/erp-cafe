"""
BME-ERP - Balance de Comprobación
Archivo: balance_comprobacion.py

Funciones:
- Consolida movimientos por cuenta contable.
- Calcula saldo inicial, débitos, créditos y saldo final.
- Filtra por rango de fechas, nivel, clase, naturaleza y módulo.
- Valida igualdad de débitos y créditos.
- Permite incluir cuentas sin movimiento.
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


def fecha_valida(texto):
    texto = texto.strip()

    if not texto:
        return True

    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def clase_desde_codigo(codigo):
    mapa = {
        "1": "ACTIVO",
        "2": "PASIVO",
        "3": "PATRIMONIO",
        "4": "INGRESOS",
        "5": "GASTOS",
        "6": "COSTOS",
        "8": "ORDEN DEUDORAS",
        "9": "ORDEN ACREEDORAS"
    }

    return mapa.get(str(codigo)[:1], "OTRA")


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

        combo_clase["values"] = [
            "TODAS",
            "ACTIVO",
            "PASIVO",
            "PATRIMONIO",
            "INGRESOS",
            "GASTOS",
            "COSTOS",
            "ORDEN DEUDORAS",
            "ORDEN ACREEDORAS"
        ]
        combo_clase.set("TODAS")

        combo_naturaleza["values"] = [
            "TODAS",
            "DEBITO",
            "CREDITO"
        ]
        combo_naturaleza.set("TODAS")

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


def construir_condiciones_cuentas():
    condiciones = ["pc.estado='ACTIVA'"]
    parametros = []

    nivel = combo_nivel.get().strip()
    clase = combo_clase.get().strip()
    naturaleza = combo_naturaleza.get().strip()
    buscar = entrada_buscar.get().strip()

    if nivel and nivel != "TODOS":
        condiciones.append("pc.nivel=?")
        parametros.append(int(nivel))

    if naturaleza and naturaleza != "TODAS":
        condiciones.append("pc.naturaleza=?")
        parametros.append(naturaleza)

    if clase and clase != "TODAS":
        primer_digito = {
            "ACTIVO": "1",
            "PASIVO": "2",
            "PATRIMONIO": "3",
            "INGRESOS": "4",
            "GASTOS": "5",
            "COSTOS": "6",
            "ORDEN DEUDORAS": "8",
            "ORDEN ACREEDORAS": "9"
        }.get(clase)

        if primer_digito:
            condiciones.append("pc.codigo LIKE ?")
            parametros.append(f"{primer_digito}%")

    if buscar:
        condiciones.append("""
            (
                pc.codigo LIKE ?
                OR pc.nombre LIKE ?
            )
        """)
        patron = f"%{buscar}%"
        parametros.extend([patron, patron])

    return " AND ".join(condiciones), parametros


def validar_fechas():
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

    return desde, hasta


# ============================================================
# CÁLCULOS CONTABLES
# ============================================================

def obtener_saldo_inicial(
    cursor,
    cuenta_id,
    desde,
    modulo
):
    if not desde:
        return 0.0

    condiciones = [
        "d.cuenta_id=?",
        "c.estado='CONTABILIZADO'",
        "date(c.fecha) < date(?)"
    ]
    parametros = [cuenta_id, desde]

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    cursor.execute(f"""
        SELECT
            IFNULL(SUM(d.debito - d.credito), 0) AS saldo
        FROM detalle_comprobante d
        INNER JOIN comprobantes c
            ON c.id=d.comprobante_id
        WHERE {' AND '.join(condiciones)}
    """, parametros)

    return float(cursor.fetchone()["saldo"] or 0)


def obtener_movimientos_periodo(
    cursor,
    cuenta_id,
    desde,
    hasta,
    modulo
):
    condiciones = [
        "d.cuenta_id=?",
        "c.estado='CONTABILIZADO'"
    ]
    parametros = [cuenta_id]

    if desde:
        condiciones.append("date(c.fecha) >= date(?)")
        parametros.append(desde)

    if hasta:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(hasta)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    cursor.execute(f"""
        SELECT
            IFNULL(SUM(d.debito), 0) AS debitos,
            IFNULL(SUM(d.credito), 0) AS creditos,
            COUNT(*) AS movimientos
        FROM detalle_comprobante d
        INNER JOIN comprobantes c
            ON c.id=d.comprobante_id
        WHERE {' AND '.join(condiciones)}
    """, parametros)

    fila = cursor.fetchone()

    return (
        float(fila["debitos"] or 0),
        float(fila["creditos"] or 0),
        int(fila["movimientos"] or 0)
    )


# ============================================================
# CONSULTA PRINCIPAL
# ============================================================

datos_actuales = []


def consultar_balance():
    try:
        desde, hasta = validar_fechas()
        condicion_cuentas, parametros_cuentas = (
            construir_condiciones_cuentas()
        )

        modulo = combo_modulo.get().strip()
        incluir_sin_movimiento = variable_sin_movimiento.get()

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
                    pc.permite_movimiento
                FROM plan_cuentas pc
                WHERE {condicion_cuentas}
                ORDER BY pc.codigo
            """, parametros_cuentas)

            cuentas = cursor.fetchall()
            resultados = []

            for cuenta in cuentas:
                saldo_inicial = obtener_saldo_inicial(
                    cursor,
                    int(cuenta["id"]),
                    desde,
                    modulo
                )

                debitos, creditos, movimientos = (
                    obtener_movimientos_periodo(
                        cursor,
                        int(cuenta["id"]),
                        desde,
                        hasta,
                        modulo
                    )
                )

                saldo_final = saldo_inicial + debitos - creditos

                if (
                    not incluir_sin_movimiento
                    and abs(saldo_inicial) <= 0.005
                    and abs(debitos) <= 0.005
                    and abs(creditos) <= 0.005
                    and abs(saldo_final) <= 0.005
                ):
                    continue

                resultados.append({
                    "id": int(cuenta["id"]),
                    "codigo": cuenta["codigo"],
                    "nombre": cuenta["nombre"],
                    "nivel": int(cuenta["nivel"]),
                    "clase": clase_desde_codigo(cuenta["codigo"]),
                    "naturaleza": cuenta["naturaleza"],
                    "saldo_inicial": saldo_inicial,
                    "debitos": debitos,
                    "creditos": creditos,
                    "saldo_final": saldo_final,
                    "movimientos": movimientos
                })

        finally:
            conexion.close()

        tabla.delete(*tabla.get_children())

        total_inicial_debito = 0.0
        total_inicial_credito = 0.0
        total_debitos = 0.0
        total_creditos = 0.0
        total_final_debito = 0.0
        total_final_credito = 0.0
        total_movimientos = 0

        for fila in resultados:
            saldo_inicial_debito = max(fila["saldo_inicial"], 0)
            saldo_inicial_credito = max(-fila["saldo_inicial"], 0)
            saldo_final_debito = max(fila["saldo_final"], 0)
            saldo_final_credito = max(-fila["saldo_final"], 0)

            total_inicial_debito += saldo_inicial_debito
            total_inicial_credito += saldo_inicial_credito
            total_debitos += fila["debitos"]
            total_creditos += fila["creditos"]
            total_final_debito += saldo_final_debito
            total_final_credito += saldo_final_credito
            total_movimientos += fila["movimientos"]

            tabla.insert(
                "",
                "end",
                iid=str(fila["id"]),
                values=(
                    fila["codigo"],
                    fila["nombre"],
                    fila["nivel"],
                    fila["clase"],
                    fila["naturaleza"],
                    moneda(saldo_inicial_debito),
                    moneda(saldo_inicial_credito),
                    moneda(fila["debitos"]),
                    moneda(fila["creditos"]),
                    moneda(saldo_final_debito),
                    moneda(saldo_final_credito),
                    fila["movimientos"]
                )
            )

        diferencia_periodo = total_debitos - total_creditos
        diferencia_final = total_final_debito - total_final_credito

        lbl_cuentas.config(text=str(len(resultados)))
        lbl_movimientos.config(text=str(total_movimientos))
        lbl_debitos.config(text=moneda(total_debitos))
        lbl_creditos.config(text=moneda(total_creditos))
        lbl_diferencia.config(text=moneda(diferencia_periodo))

        lbl_inicial_debito.config(
            text=moneda(total_inicial_debito)
        )
        lbl_inicial_credito.config(
            text=moneda(total_inicial_credito)
        )
        lbl_final_debito.config(
            text=moneda(total_final_debito)
        )
        lbl_final_credito.config(
            text=moneda(total_final_credito)
        )

        if abs(diferencia_periodo) <= 0.01:
            lbl_diferencia.config(fg=COLOR_VERDE)
            lbl_estado_balance.config(
                text="BALANCE CUADRADO",
                fg=COLOR_VERDE
            )
        else:
            lbl_diferencia.config(fg=COLOR_ROJO)
            lbl_estado_balance.config(
                text=f"DESCUADRE DEL PERÍODO: {moneda(diferencia_periodo)}",
                fg=COLOR_ROJO
            )

        if abs(diferencia_final) > 0.01:
            lbl_estado_final.config(
                text=f"Saldo final neto: {moneda(diferencia_final)}",
                fg=COLOR_NARANJA
            )
        else:
            lbl_estado_final.config(
                text="Saldos finales balanceados",
                fg=COLOR_VERDE
            )

        datos_actuales.clear()
        datos_actuales.extend(resultados)

    except Exception as error:
        messagebox.showerror(
            "Balance de Comprobación",
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
        title="Guardar Balance de Comprobación",
        defaultextension=".csv",
        initialfile="balance_comprobacion.csv",
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
                "Cuenta",
                "Nombre",
                "Nivel",
                "Clase",
                "Naturaleza",
                "Saldo inicial débito",
                "Saldo inicial crédito",
                "Débitos",
                "Créditos",
                "Saldo final débito",
                "Saldo final crédito",
                "Movimientos"
            ])

            for fila in datos_actuales:
                escritor.writerow([
                    fila["codigo"],
                    fila["nombre"],
                    fila["nivel"],
                    fila["clase"],
                    fila["naturaleza"],
                    max(fila["saldo_inicial"], 0),
                    max(-fila["saldo_inicial"], 0),
                    fila["debitos"],
                    fila["creditos"],
                    max(fila["saldo_final"], 0),
                    max(-fila["saldo_final"], 0),
                    fila["movimientos"]
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
# LIMPIAR FILTROS
# ============================================================

def limpiar_filtros():
    entrada_desde.delete(0, tk.END)
    entrada_hasta.delete(0, tk.END)
    combo_nivel.set("TODOS")
    combo_clase.set("TODAS")
    combo_naturaleza.set("TODAS")
    combo_modulo.set("TODOS")
    entrada_buscar.delete(0, tk.END)
    variable_sin_movimiento.set(False)
    consultar_balance()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Balance de Comprobación")
ventana.geometry("1580x880")
ventana.minsize(1220, 720)
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
    text="BALANCE DE COMPROBACIÓN",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Saldos iniciales, movimientos y saldos finales por cuenta",
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
entrada_desde = ttk.Entry(filtros, width=12)
entrada_desde.grid(row=1, column=0, padx=(0, 8))

etiqueta_filtro("Hasta", 1)
entrada_hasta = ttk.Entry(filtros, width=12)
entrada_hasta.grid(row=1, column=1, padx=(0, 8))

etiqueta_filtro("Nivel", 2)
combo_nivel = ttk.Combobox(
    filtros,
    state="readonly",
    width=10
)
combo_nivel.grid(row=1, column=2, padx=(0, 8))

etiqueta_filtro("Clase", 3)
combo_clase = ttk.Combobox(
    filtros,
    state="readonly",
    width=18
)
combo_clase.grid(row=1, column=3, padx=(0, 8))

etiqueta_filtro("Naturaleza", 4)
combo_naturaleza = ttk.Combobox(
    filtros,
    state="readonly",
    width=13
)
combo_naturaleza.grid(row=1, column=4, padx=(0, 8))

etiqueta_filtro("Módulo", 5)
combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=20
)
combo_modulo.grid(row=1, column=5, padx=(0, 8))

etiqueta_filtro("Buscar cuenta", 6)
entrada_buscar = ttk.Entry(filtros, width=22)
entrada_buscar.grid(row=1, column=6, padx=(0, 10))

variable_sin_movimiento = tk.BooleanVar(value=False)

tk.Checkbutton(
    filtros,
    text="Incluir sin movimiento",
    variable=variable_sin_movimiento,
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    activebackground=COLOR_TARJETA,
    font=("Segoe UI", 8)
).grid(row=1, column=7, padx=5)

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
    padx=16,
    pady=7
).grid(row=1, column=8, padx=4)

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
    padx=16,
    pady=7
).grid(row=1, column=9, padx=4)

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
    padx=16,
    pady=7
).grid(row=1, column=10, padx=4)

# Tarjetas
resumen = tk.Frame(
    contenedor,
    bg=COLOR_FONDO
)
resumen.pack(fill="x", pady=(0, 12))

for columna in range(5):
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
        padx=5
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
        font=("Segoe UI", 15, "bold")
    )
    valor.pack(anchor="w", padx=14, pady=(0, 10))

    return valor

lbl_cuentas = crear_tarjeta(0, "CUENTAS")
lbl_movimientos = crear_tarjeta(1, "MOVIMIENTOS")
lbl_debitos = crear_tarjeta(2, "TOTAL DÉBITOS")
lbl_creditos = crear_tarjeta(3, "TOTAL CRÉDITOS")
lbl_diferencia = crear_tarjeta(4, "DIFERENCIA")

# Totales saldos
panel_saldos = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_saldos.pack(fill="x", pady=(0, 12))

saldos = tk.Frame(panel_saldos, bg=COLOR_TARJETA)
saldos.pack(fill="x", padx=16, pady=12)

def bloque_saldo(titulo, columna):
    marco = tk.Frame(saldos, bg=COLOR_TARJETA)
    marco.grid(row=0, column=columna, sticky="ew", padx=10)
    saldos.columnconfigure(columna, weight=1)

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        marco,
        text="$0.00",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 11, "bold")
    )
    valor.pack(anchor="w", pady=(2, 0))
    return valor

lbl_inicial_debito = bloque_saldo("SALDO INICIAL DÉBITO", 0)
lbl_inicial_credito = bloque_saldo("SALDO INICIAL CRÉDITO", 1)
lbl_final_debito = bloque_saldo("SALDO FINAL DÉBITO", 2)
lbl_final_credito = bloque_saldo("SALDO FINAL CRÉDITO", 3)

lbl_estado_balance = tk.Label(
    saldos,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 10, "bold")
)
lbl_estado_balance.grid(row=0, column=4, padx=15)

lbl_estado_final = tk.Label(
    saldos,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 9, "bold")
)
lbl_estado_final.grid(row=0, column=5, padx=15)

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
    text="Detalle del Balance de Comprobación",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(12, 5))

columnas = (
    "Cuenta",
    "Nombre",
    "Nivel",
    "Clase",
    "Naturaleza",
    "Inicial débito",
    "Inicial crédito",
    "Débitos",
    "Créditos",
    "Final débito",
    "Final crédito",
    "Movimientos"
)

tabla = ttk.Treeview(
    panel_tabla,
    columns=columnas,
    show="headings"
)

anchos = {
    "Cuenta": 95,
    "Nombre": 285,
    "Nivel": 60,
    "Clase": 115,
    "Naturaleza": 90,
    "Inicial débito": 115,
    "Inicial crédito": 115,
    "Débitos": 115,
    "Créditos": 115,
    "Final débito": 115,
    "Final crédito": 115,
    "Movimientos": 95
}

for columna in columnas:
    tabla.heading(columna, text=columna)
    tabla.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in (
            "Inicial débito",
            "Inicial crédito",
            "Débitos",
            "Créditos",
            "Final débito",
            "Final crédito",
            "Movimientos"
        ) else "w"
    )

scroll_y = ttk.Scrollbar(
    panel_tabla,
    orient="vertical",
    command=tabla.yview
)

scroll_x = ttk.Scrollbar(
    panel_tabla,
    orient="horizontal",
    command=tabla.xview
)

tabla.configure(
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)

tabla.pack(
    fill="both",
    expand=True,
    padx=(14, 0),
    pady=(0, 0)
)

scroll_y.place(
    relx=1.0,
    rely=0.07,
    relheight=0.86,
    anchor="ne"
)

scroll_x.pack(
    fill="x",
    padx=14,
    pady=(0, 12)
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
