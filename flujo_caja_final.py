"""
BME-ERP - Flujo de Caja
Archivo: flujo_caja.py

Funciones:
- Consulta movimientos bancarios por rango de fechas.
- Calcula saldo inicial, ingresos, egresos y saldo final.
- Permite filtrar por banco, tipo de movimiento y texto.
- Presenta resumen por banco y detalle cronológico.
- Exporta resultados a CSV.
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
COLOR_ROJO = "#B42318"
COLOR_TEXTO = "#1F2937"
COLOR_SUAVE = "#64748B"
COLOR_BORDE = "#D7E0E8"

datos_detalle = []
datos_resumen = []


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
        return f"${float(valor or 0):,.2f}"
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


def tipo_flujo(tipo):
    texto = str(tipo or "").upper()

    if "TRANSFERENCIA" in texto:
        return "TRANSFERENCIA INTERNA"

    palabras_ingreso = (
        "INGRESO",
        "RECAUDO",
        "CONSIGNACION",
        "CONSIGNACIÓN",
        "VENTA",
        "ABONO CLIENTE"
    )

    palabras_egreso = (
        "EGRESO",
        "PAGO",
        "RETIRO",
        "COMPRA",
        "GASTO"
    )

    if any(palabra in texto for palabra in palabras_ingreso):
        return "INGRESO"

    if any(palabra in texto for palabra in palabras_egreso):
        return "EGRESO"

    return "OTRO"


# ============================================================
# FILTROS
# ============================================================

mapa_bancos = {}


def cargar_filtros():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id, banco, numero_cuenta
            FROM bancos
            ORDER BY banco, numero_cuenta
        """)

        opciones = ["TODOS"]
        mapa_bancos.clear()

        for fila in cursor.fetchall():
            texto = (
                f"{fila['id']} - {fila['banco']} - "
                f"{fila['numero_cuenta']}"
            )
            opciones.append(texto)
            mapa_bancos[texto] = int(fila["id"])

        combo_banco["values"] = opciones
        combo_banco.set("TODOS")

        cursor.execute("""
            SELECT DISTINCT tipo
            FROM movimientos_bancos
            WHERE COALESCE(tipo, '') <> ''
            ORDER BY tipo
        """)

        tipos = ["TODOS"] + [
            fila["tipo"] for fila in cursor.fetchall()
        ]
        combo_tipo["values"] = tipos
        combo_tipo.set("TODOS")

    finally:
        conexion.close()


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

    if desde and hasta:
        fecha_desde = datetime.strptime(desde, "%Y-%m-%d")
        fecha_hasta = datetime.strptime(hasta, "%Y-%m-%d")

        if fecha_desde > fecha_hasta:
            raise ValueError(
                "La fecha inicial no puede ser mayor que la fecha final."
            )

    return desde, hasta


def banco_seleccionado():
    texto = combo_banco.get().strip()

    if not texto or texto == "TODOS":
        return None

    return mapa_bancos.get(texto)


# ============================================================
# CONSULTAS
# ============================================================

def saldo_inicial_banco(cursor, banco_id, fecha_desde):
    if not fecha_desde:
        cursor.execute("""
            SELECT
                COALESCE(MIN(saldo_anterior), 0) AS saldo
            FROM movimientos_bancos
            WHERE banco_id=?
        """, (banco_id,))
        fila = cursor.fetchone()
        return float(fila["saldo"] or 0)

    cursor.execute("""
        SELECT saldo_nuevo
        FROM movimientos_bancos
        WHERE banco_id=?
          AND date(fecha) < date(?)
        ORDER BY fecha DESC, id DESC
        LIMIT 1
    """, (banco_id, fecha_desde))

    fila = cursor.fetchone()

    if fila:
        return float(fila["saldo_nuevo"] or 0)

    cursor.execute("""
        SELECT COALESCE(MIN(saldo_anterior), 0) AS saldo
        FROM movimientos_bancos
        WHERE banco_id=?
    """, (banco_id,))

    fila = cursor.fetchone()
    return float(fila["saldo"] or 0)


def consultar_flujo():
    try:
        desde, hasta = validar_fechas()
        banco_id = banco_seleccionado()
        tipo = combo_tipo.get().strip()
        buscar = entrada_buscar.get().strip()

        condiciones = ["1=1"]
        parametros = []

        if desde:
            condiciones.append("date(m.fecha) >= date(?)")
            parametros.append(desde)

        if hasta:
            condiciones.append("date(m.fecha) <= date(?)")
            parametros.append(hasta)

        if banco_id:
            condiciones.append("m.banco_id=?")
            parametros.append(banco_id)

        if tipo and tipo != "TODOS":
            condiciones.append("m.tipo=?")
            parametros.append(tipo)

        if buscar:
            condiciones.append("""
                (
                    m.concepto LIKE ?
                    OR m.tipo LIKE ?
                    OR COALESCE(m.autorizado_por, '') LIKE ?
                    OR b.banco LIKE ?
                )
            """)
            patron = f"%{buscar}%"
            parametros.extend([patron, patron, patron, patron])

        conexion = conectar()

        try:
            cursor = conexion.cursor()

            cursor.execute(f"""
                SELECT
                    m.id,
                    m.fecha,
                    m.banco_id,
                    b.banco,
                    b.numero_cuenta,
                    m.tipo,
                    m.concepto,
                    m.valor,
                    m.saldo_anterior,
                    m.saldo_nuevo,
                    COALESCE(m.autorizado_por, '') AS autorizado_por
                FROM movimientos_bancos m
                INNER JOIN bancos b
                    ON b.id=m.banco_id
                WHERE {' AND '.join(condiciones)}
                ORDER BY m.fecha, m.id
            """, parametros)

            movimientos = [dict(fila) for fila in cursor.fetchall()]

            cursor.execute("""
                SELECT id, banco, numero_cuenta, saldo
                FROM bancos
                ORDER BY banco, numero_cuenta
            """)

            bancos = [dict(fila) for fila in cursor.fetchall()]

            if banco_id:
                bancos = [
                    banco for banco in bancos
                    if int(banco["id"]) == banco_id
                ]

            resumen = []

            for banco in bancos:
                movimientos_banco = [
                    mov for mov in movimientos
                    if int(mov["banco_id"]) == int(banco["id"])
                ]

                saldo_inicial = saldo_inicial_banco(
                    cursor,
                    int(banco["id"]),
                    desde
                )

                ingresos = 0.0
                egresos = 0.0
                otros = 0.0

                for mov in movimientos_banco:
                    valor = float(mov["valor"] or 0)
                    flujo = tipo_flujo(mov["tipo"])

                    if flujo == "INGRESO":
                        ingresos += valor
                    elif flujo == "EGRESO":
                        egresos += valor
                    elif flujo == "TRANSFERENCIA INTERNA":
                        pass
                    else:
                        cambio = (
                            float(mov["saldo_nuevo"] or 0)
                            - float(mov["saldo_anterior"] or 0)
                        )

                        if cambio >= 0:
                            ingresos += abs(cambio)
                        else:
                            egresos += abs(cambio)

                        otros += 1

                saldo_final = saldo_inicial + ingresos - egresos

                resumen.append({
                    "banco_id": int(banco["id"]),
                    "banco": banco["banco"],
                    "numero_cuenta": banco["numero_cuenta"],
                    "saldo_inicial": saldo_inicial,
                    "ingresos": ingresos,
                    "egresos": egresos,
                    "saldo_final": saldo_final,
                    "movimientos": len(movimientos_banco),
                    "clasificaciones_automaticas": otros
                })

        finally:
            conexion.close()

        cargar_tabla_detalle(movimientos)
        cargar_tabla_resumen(resumen)
        actualizar_totales(resumen, movimientos)

        datos_detalle.clear()
        datos_detalle.extend(movimientos)

        datos_resumen.clear()
        datos_resumen.extend(resumen)

    except Exception as error:
        messagebox.showerror(
            "Flujo de Caja",
            str(error)
        )


def cargar_tabla_detalle(movimientos):
    tabla_detalle.delete(*tabla_detalle.get_children())

    for fila in movimientos:
        flujo = tipo_flujo(fila["tipo"])
        valor = float(fila["valor"] or 0)

        ingreso = valor if flujo == "INGRESO" else 0
        egreso = valor if flujo == "EGRESO" else 0

        if flujo == "OTRO":
            diferencia = (
                float(fila["saldo_nuevo"] or 0)
                - float(fila["saldo_anterior"] or 0)
            )

            if diferencia >= 0:
                ingreso = abs(diferencia)
            else:
                egreso = abs(diferencia)

        elif flujo == "TRANSFERENCIA INTERNA":
            ingreso = 0
            egreso = 0

        tabla_detalle.insert(
            "",
            "end",
            iid=str(fila["id"]),
            values=(
                fila["fecha"],
                fila["banco"],
                fila["numero_cuenta"],
                fila["tipo"],
                flujo,
                fila["concepto"],
                moneda(ingreso),
                moneda(egreso),
                moneda(fila["saldo_anterior"]),
                moneda(fila["saldo_nuevo"]),
                fila["autorizado_por"]
            )
        )


def cargar_tabla_resumen(resumen):
    tabla_resumen.delete(*tabla_resumen.get_children())

    for fila in resumen:
        tabla_resumen.insert(
            "",
            "end",
            iid=str(fila["banco_id"]),
            values=(
                fila["banco"],
                fila["numero_cuenta"],
                moneda(fila["saldo_inicial"]),
                moneda(fila["ingresos"]),
                moneda(fila["egresos"]),
                moneda(fila["saldo_final"]),
                fila["movimientos"]
            )
        )


def actualizar_totales(resumen, movimientos):
    saldo_inicial = sum(
        fila["saldo_inicial"] for fila in resumen
    )
    ingresos = sum(
        fila["ingresos"] for fila in resumen
    )
    egresos = sum(
        fila["egresos"] for fila in resumen
    )
    saldo_final = sum(
        fila["saldo_final"] for fila in resumen
    )

    flujo_neto = ingresos - egresos

    lbl_saldo_inicial.config(text=moneda(saldo_inicial))
    lbl_ingresos.config(text=moneda(ingresos))
    lbl_egresos.config(text=moneda(egresos))
    lbl_flujo_neto.config(text=moneda(flujo_neto))
    lbl_saldo_final.config(text=moneda(saldo_final))
    lbl_efectivo_disponible.config(text=moneda(saldo_final))
    lbl_movimientos.config(text=str(len(movimientos)))

    if flujo_neto >= 0:
        lbl_estado.config(
            text="FLUJO NETO POSITIVO",
            fg=COLOR_VERDE
        )
    else:
        lbl_estado.config(
            text="FLUJO NETO NEGATIVO",
            fg=COLOR_ROJO
        )


# ============================================================
# EXPORTACIÓN
# ============================================================

def exportar_csv():
    if not datos_detalle:
        messagebox.showwarning(
            "Exportar",
            "No hay movimientos para exportar."
        )
        return

    ruta = filedialog.asksaveasfilename(
        title="Guardar Flujo de Caja",
        defaultextension=".csv",
        initialfile="flujo_caja.csv",
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

            escritor.writerow(["FLUJO DE CAJA"])
            escritor.writerow([
                "Desde",
                entrada_desde.get().strip(),
                "Hasta",
                entrada_hasta.get().strip()
            ])
            escritor.writerow([])

            escritor.writerow(["RESUMEN POR BANCO"])
            escritor.writerow([
                "Banco",
                "Cuenta",
                "Saldo inicial",
                "Ingresos",
                "Egresos",
                "Saldo final",
                "Movimientos"
            ])

            for fila in datos_resumen:
                escritor.writerow([
                    fila["banco"],
                    fila["numero_cuenta"],
                    fila["saldo_inicial"],
                    fila["ingresos"],
                    fila["egresos"],
                    fila["saldo_final"],
                    fila["movimientos"]
                ])

            escritor.writerow([])
            escritor.writerow(["DETALLE DE MOVIMIENTOS"])
            escritor.writerow([
                "Fecha",
                "Banco",
                "Cuenta",
                "Tipo",
                "Clasificación",
                "Concepto",
                "Ingreso",
                "Egreso",
                "Saldo anterior",
                "Saldo nuevo",
                "Autorizado por"
            ])

            for fila in datos_detalle:
                flujo = tipo_flujo(fila["tipo"])
                valor = float(fila["valor"] or 0)

                ingreso = valor if flujo == "INGRESO" else 0
                egreso = valor if flujo == "EGRESO" else 0

                if flujo == "OTRO":
                    cambio = (
                        float(fila["saldo_nuevo"] or 0)
                        - float(fila["saldo_anterior"] or 0)
                    )
                    if cambio >= 0:
                        ingreso = abs(cambio)
                    else:
                        egreso = abs(cambio)

                elif flujo == "TRANSFERENCIA INTERNA":
                    ingreso = 0
                    egreso = 0

                escritor.writerow([
                    fila["fecha"],
                    fila["banco"],
                    fila["numero_cuenta"],
                    fila["tipo"],
                    flujo,
                    fila["concepto"],
                    ingreso,
                    egreso,
                    fila["saldo_anterior"],
                    fila["saldo_nuevo"],
                    fila["autorizado_por"]
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
    combo_banco.set("TODOS")
    combo_tipo.set("TODOS")
    entrada_buscar.delete(0, tk.END)
    consultar_flujo()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Flujo de Caja")
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

cabecera = tk.Frame(
    ventana,
    bg=COLOR_AZUL,
    height=88
)
cabecera.pack(fill="x")
cabecera.pack_propagate(False)

tk.Label(
    cabecera,
    text="FLUJO DE CAJA",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Ingresos, egresos y saldos por banco",
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

etiqueta_filtro("Banco", 2)
combo_banco = ttk.Combobox(
    filtros,
    state="readonly",
    width=35
)
combo_banco.grid(row=1, column=2, padx=(0, 10))

etiqueta_filtro("Tipo movimiento", 3)
combo_tipo = ttk.Combobox(
    filtros,
    state="readonly",
    width=22
)
combo_tipo.grid(row=1, column=3, padx=(0, 10))

etiqueta_filtro("Buscar", 4)
entrada_buscar = ttk.Entry(filtros, width=24)
entrada_buscar.grid(row=1, column=4, padx=(0, 10))

tk.Button(
    filtros,
    text="Consultar",
    command=consultar_flujo,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=18,
    pady=7
).grid(row=1, column=5, padx=4)

tk.Button(
    filtros,
    text="Limpiar",
    command=limpiar_filtros,
    bg="#64748B",
    fg="white",
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
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=18,
    pady=7
).grid(row=1, column=7, padx=4)

panel_estado = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_estado.pack(fill="x", pady=(0, 12))

lbl_estado = tk.Label(
    panel_estado,
    text="—",
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 11, "bold")
)
lbl_estado.pack(anchor="w", padx=16, pady=12)

resumen = tk.Frame(contenedor, bg=COLOR_FONDO)
resumen.pack(fill="x", pady=(0, 12))

for columna in range(7):
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

lbl_saldo_inicial = crear_tarjeta(0, "SALDO INICIAL")
lbl_ingresos = crear_tarjeta(1, "INGRESOS")
lbl_egresos = crear_tarjeta(2, "EGRESOS")
lbl_flujo_neto = crear_tarjeta(3, "FLUJO NETO")
lbl_saldo_final = crear_tarjeta(4, "SALDO FINAL")
lbl_efectivo_disponible = crear_tarjeta(5, "EFECTIVO DISPONIBLE")
lbl_movimientos = crear_tarjeta(6, "MOVIMIENTOS")

panel_resumen = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_resumen.pack(fill="both", expand=True, pady=(0, 12))

tk.Label(
    panel_resumen,
    text="Resumen por banco",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(10, 5))

columnas_resumen = (
    "Banco",
    "Cuenta",
    "Saldo inicial",
    "Ingresos",
    "Egresos",
    "Saldo final",
    "Movimientos"
)

tabla_resumen = ttk.Treeview(
    panel_resumen,
    columns=columnas_resumen,
    show="headings",
    height=6
)

anchos_resumen = {
    "Banco": 220,
    "Cuenta": 180,
    "Saldo inicial": 140,
    "Ingresos": 140,
    "Egresos": 140,
    "Saldo final": 140,
    "Movimientos": 100
}

for columna in columnas_resumen:
    tabla_resumen.heading(columna, text=columna)
    tabla_resumen.column(
        columna,
        width=anchos_resumen[columna],
        anchor="e" if columna in (
            "Saldo inicial",
            "Ingresos",
            "Egresos",
            "Saldo final",
            "Movimientos"
        ) else "w"
    )

tabla_resumen.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 10)
)

panel_detalle = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_detalle.pack(fill="both", expand=True)

tk.Label(
    panel_detalle,
    text=(
        "Las transferencias internas no afectan el flujo neto consolidado; "
        "solo redistribuyen efectivo entre bancos."
    ),
    bg=COLOR_TARJETA,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(anchor="w", padx=14, pady=(8, 0))

tk.Label(
    panel_detalle,
    text="Detalle de movimientos",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(10, 5))

columnas_detalle = (
    "Fecha",
    "Banco",
    "Cuenta",
    "Tipo",
    "Clasificación",
    "Concepto",
    "Ingreso",
    "Egreso",
    "Saldo anterior",
    "Saldo nuevo",
    "Autorizado por"
)

tabla_detalle = ttk.Treeview(
    panel_detalle,
    columns=columnas_detalle,
    show="headings",
    height=9
)

anchos_detalle = {
    "Fecha": 135,
    "Banco": 160,
    "Cuenta": 130,
    "Tipo": 140,
    "Clasificación": 155,
    "Concepto": 300,
    "Ingreso": 120,
    "Egreso": 120,
    "Saldo anterior": 130,
    "Saldo nuevo": 130,
    "Autorizado por": 130
}

for columna in columnas_detalle:
    tabla_detalle.heading(columna, text=columna)
    tabla_detalle.column(
        columna,
        width=anchos_detalle[columna],
        anchor="e" if columna in (
            "Ingreso",
            "Egreso",
            "Saldo anterior",
            "Saldo nuevo"
        ) else "w"
    )

scroll_y = ttk.Scrollbar(
    panel_detalle,
    orient="vertical",
    command=tabla_detalle.yview
)

scroll_x = ttk.Scrollbar(
    panel_detalle,
    orient="horizontal",
    command=tabla_detalle.xview
)

tabla_detalle.configure(
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)

tabla_detalle.pack(
    fill="both",
    expand=True,
    padx=(14, 0),
    pady=(0, 0)
)

scroll_y.place(
    relx=1.0,
    rely=0.08,
    relheight=0.82,
    anchor="ne"
)

scroll_x.pack(
    fill="x",
    padx=14,
    pady=(0, 10)
)

tk.Label(
    ventana,
    text=f"Base: {RUTA_DB}",
    bg=COLOR_FONDO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(pady=(0, 8))

cargar_filtros()
consultar_flujo()

ventana.mainloop()
