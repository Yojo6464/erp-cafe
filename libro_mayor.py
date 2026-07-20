"""
BME-ERP - Libro Mayor
Archivo: libro_mayor.py

Funciones:
- Consulta movimientos agrupados por cuenta.
- Filtra por rango de fechas, cuenta, tercero y módulo.
- Calcula saldo inicial, débitos, créditos y saldo final.
- Muestra detalle cronológico de la cuenta seleccionada.
- Exporta resumen y detalle a CSV.
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


def codigo_desde_combo(texto):
    if not texto or texto == "TODAS":
        return None
    return texto.split(" - ", 1)[0].strip()


# ============================================================
# FILTROS
# ============================================================

def cargar_filtros():
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT codigo || ' - ' || nombre AS cuenta
            FROM plan_cuentas
            WHERE permite_movimiento=1
              AND estado='ACTIVA'
            ORDER BY codigo
        """)
        cuentas = ["TODAS"] + [fila["cuenta"] for fila in cursor.fetchall()]
        combo_cuenta["values"] = cuentas
        combo_cuenta.set("TODAS")

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


def construir_condiciones(alias_comprobante="c", alias_detalle="d", alias_cuenta="pc"):
    condiciones = [f"{alias_comprobante}.estado='CONTABILIZADO'"]
    parametros = []

    desde = entrada_desde.get().strip()
    hasta = entrada_hasta.get().strip()
    cuenta = codigo_desde_combo(combo_cuenta.get().strip())
    tercero = entrada_tercero.get().strip()
    modulo = combo_modulo.get().strip()

    if not fecha_valida(desde):
        raise ValueError(
            "La fecha inicial debe tener formato AAAA-MM-DD."
        )

    if not fecha_valida(hasta):
        raise ValueError(
            "La fecha final debe tener formato AAAA-MM-DD."
        )

    if desde:
        condiciones.append(f"date({alias_comprobante}.fecha) >= date(?)")
        parametros.append(desde)

    if hasta:
        condiciones.append(f"date({alias_comprobante}.fecha) <= date(?)")
        parametros.append(hasta)

    if cuenta:
        condiciones.append(f"{alias_cuenta}.codigo=?")
        parametros.append(cuenta)

    if tercero:
        condiciones.append("""
            COALESCE(t.nombre_razon_social, '') LIKE ?
        """)
        parametros.append(f"%{tercero}%")

    if modulo and modulo != "TODOS":
        condiciones.append(f"{alias_comprobante}.modulo_origen=?")
        parametros.append(modulo)

    return " AND ".join(condiciones), parametros


# ============================================================
# CONSULTA RESUMEN
# ============================================================

resumen_actual = []
detalle_actual = []
saldo_inicial_por_cuenta = {}


def calcular_saldo_inicial(cursor, cuenta_id, fecha_desde):
    if not fecha_desde:
        return 0.0

    cursor.execute("""
        SELECT
            IFNULL(SUM(d.debito - d.credito), 0) AS saldo
        FROM detalle_comprobante d
        INNER JOIN comprobantes c
            ON c.id=d.comprobante_id
        WHERE d.cuenta_id=?
          AND c.estado='CONTABILIZADO'
          AND date(c.fecha) < date(?)
    """, (cuenta_id, fecha_desde))

    return float(cursor.fetchone()["saldo"] or 0)


def consultar_mayor():
    try:
        condicion, parametros = construir_condiciones()

        conexion = conectar()

        try:
            cursor = conexion.cursor()

            cursor.execute(f"""
                SELECT
                    pc.id AS cuenta_id,
                    pc.codigo,
                    pc.nombre,
                    pc.naturaleza,
                    SUM(d.debito) AS debitos,
                    SUM(d.credito) AS creditos
                FROM detalle_comprobante d
                INNER JOIN comprobantes c
                    ON c.id=d.comprobante_id
                INNER JOIN plan_cuentas pc
                    ON pc.id=d.cuenta_id
                LEFT JOIN terceros_contables t
                    ON t.id=d.tercero_id
                WHERE {condicion}
                GROUP BY
                    pc.id,
                    pc.codigo,
                    pc.nombre,
                    pc.naturaleza
                ORDER BY pc.codigo
            """, parametros)

            registros = cursor.fetchall()

            fecha_desde = entrada_desde.get().strip()

            resumen = []
            saldo_inicial_por_cuenta.clear()

            for fila in registros:
                saldo_inicial = calcular_saldo_inicial(
                    cursor,
                    int(fila["cuenta_id"]),
                    fecha_desde
                )

                debitos = float(fila["debitos"] or 0)
                creditos = float(fila["creditos"] or 0)

                movimiento = debitos - creditos
                saldo_final = saldo_inicial + movimiento

                saldo_inicial_por_cuenta[int(fila["cuenta_id"])] = saldo_inicial

                resumen.append({
                    "cuenta_id": int(fila["cuenta_id"]),
                    "codigo": fila["codigo"],
                    "nombre": fila["nombre"],
                    "naturaleza": fila["naturaleza"],
                    "saldo_inicial": saldo_inicial,
                    "debitos": debitos,
                    "creditos": creditos,
                    "saldo_final": saldo_final
                })

        finally:
            conexion.close()

        tabla_resumen.delete(*tabla_resumen.get_children())

        total_inicial = 0.0
        total_debitos = 0.0
        total_creditos = 0.0
        total_final = 0.0

        for fila in resumen:
            total_inicial += fila["saldo_inicial"]
            total_debitos += fila["debitos"]
            total_creditos += fila["creditos"]
            total_final += fila["saldo_final"]

            tabla_resumen.insert(
                "",
                "end",
                iid=str(fila["cuenta_id"]),
                values=(
                    fila["codigo"],
                    fila["nombre"],
                    fila["naturaleza"],
                    moneda(fila["saldo_inicial"]),
                    moneda(fila["debitos"]),
                    moneda(fila["creditos"]),
                    moneda(fila["saldo_final"])
                )
            )

        lbl_cuentas.config(text=str(len(resumen)))
        lbl_saldo_inicial.config(text=moneda(total_inicial))
        lbl_debitos.config(text=moneda(total_debitos))
        lbl_creditos.config(text=moneda(total_creditos))
        lbl_saldo_final.config(text=moneda(total_final))

        resumen_actual.clear()
        resumen_actual.extend(resumen)

        limpiar_detalle()

    except Exception as error:
        messagebox.showerror(
            "Libro Mayor",
            str(error)
        )


# ============================================================
# DETALLE DE CUENTA
# ============================================================

def limpiar_detalle():
    tabla_detalle.delete(*tabla_detalle.get_children())
    lbl_cuenta_seleccionada.config(text="Sin selección")
    lbl_detalle_inicial.config(text="$0.00")
    lbl_detalle_debitos.config(text="$0.00")
    lbl_detalle_creditos.config(text="$0.00")
    lbl_detalle_final.config(text="$0.00")
    detalle_actual.clear()


def cargar_detalle(evento=None):
    seleccion = tabla_resumen.selection()

    if not seleccion:
        return

    cuenta_id = int(seleccion[0])

    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT codigo, nombre, naturaleza
            FROM plan_cuentas
            WHERE id=?
        """, (cuenta_id,))

        cuenta = cursor.fetchone()

        condicion, parametros = construir_condiciones()

        condicion += " AND pc.id=?"
        parametros.append(cuenta_id)

        cursor.execute(f"""
            SELECT
                c.fecha,
                c.consecutivo,
                c.documento_referencia,
                c.concepto,
                d.descripcion,
                COALESCE(t.nombre_razon_social, '') AS tercero,
                COALESCE(cc.codigo, '') AS centro_costo,
                c.modulo_origen,
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
            WHERE {condicion}
            ORDER BY c.fecha, c.id, d.secuencia
        """, parametros)

        registros = [dict(fila) for fila in cursor.fetchall()]

    finally:
        conexion.close()

    saldo = saldo_inicial_por_cuenta.get(cuenta_id, 0.0)
    total_debitos = 0.0
    total_creditos = 0.0

    tabla_detalle.delete(*tabla_detalle.get_children())

    for fila in registros:
        debito = float(fila["debito"] or 0)
        credito = float(fila["credito"] or 0)

        total_debitos += debito
        total_creditos += credito
        saldo += debito - credito

        tabla_detalle.insert(
            "",
            "end",
            values=(
                fila["fecha"],
                fila["consecutivo"],
                fila["documento_referencia"],
                fila["concepto"],
                fila["descripcion"],
                fila["tercero"],
                fila["centro_costo"],
                fila["modulo_origen"],
                moneda(debito),
                moneda(credito),
                moneda(saldo)
            )
        )

    lbl_cuenta_seleccionada.config(
        text=f"{cuenta['codigo']} - {cuenta['nombre']}"
    )
    lbl_detalle_inicial.config(
        text=moneda(saldo_inicial_por_cuenta.get(cuenta_id, 0.0))
    )
    lbl_detalle_debitos.config(text=moneda(total_debitos))
    lbl_detalle_creditos.config(text=moneda(total_creditos))
    lbl_detalle_final.config(text=moneda(saldo))

    detalle_actual.clear()
    detalle_actual.extend(registros)


# ============================================================
# EXPORTACIÓN
# ============================================================

def exportar_resumen():
    if not resumen_actual:
        messagebox.showwarning(
            "Exportar",
            "No hay información para exportar."
        )
        return

    ruta = filedialog.asksaveasfilename(
        title="Guardar resumen Libro Mayor",
        defaultextension=".csv",
        initialfile="libro_mayor_resumen.csv",
        filetypes=[
            ("Archivo CSV", "*.csv"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not ruta:
        return

    try:
        with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow([
                "Cuenta",
                "Nombre",
                "Naturaleza",
                "Saldo inicial",
                "Débitos",
                "Créditos",
                "Saldo final"
            ])

            for fila in resumen_actual:
                escritor.writerow([
                    fila["codigo"],
                    fila["nombre"],
                    fila["naturaleza"],
                    fila["saldo_inicial"],
                    fila["debitos"],
                    fila["creditos"],
                    fila["saldo_final"]
                ])

        messagebox.showinfo(
            "Exportar",
            f"Archivo creado correctamente:\n\n{ruta}"
        )

    except OSError as error:
        messagebox.showerror("Exportar", str(error))


def exportar_detalle():
    seleccion = tabla_resumen.selection()

    if not seleccion or not detalle_actual:
        messagebox.showwarning(
            "Exportar",
            "Seleccione una cuenta con movimientos."
        )
        return

    cuenta_texto = lbl_cuenta_seleccionada.cget("text")
    nombre_archivo = (
        cuenta_texto.split(" - ", 1)[0].replace(".", "_")
        + "_mayor.csv"
    )

    ruta = filedialog.asksaveasfilename(
        title="Guardar detalle de cuenta",
        defaultextension=".csv",
        initialfile=nombre_archivo,
        filetypes=[
            ("Archivo CSV", "*.csv"),
            ("Todos los archivos", "*.*")
        ]
    )

    if not ruta:
        return

    try:
        with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.writer(archivo, delimiter=";")
            escritor.writerow([
                "Fecha",
                "Comprobante",
                "Documento",
                "Concepto",
                "Descripción",
                "Tercero",
                "Centro costo",
                "Módulo",
                "Débito",
                "Crédito"
            ])

            for fila in detalle_actual:
                escritor.writerow([
                    fila["fecha"],
                    fila["consecutivo"],
                    fila["documento_referencia"],
                    fila["concepto"],
                    fila["descripcion"],
                    fila["tercero"],
                    fila["centro_costo"],
                    fila["modulo_origen"],
                    fila["debito"],
                    fila["credito"]
                ])

        messagebox.showinfo(
            "Exportar",
            f"Archivo creado correctamente:\n\n{ruta}"
        )

    except OSError as error:
        messagebox.showerror("Exportar", str(error))


# ============================================================
# LIMPIAR FILTROS
# ============================================================

def limpiar_filtros():
    entrada_desde.delete(0, tk.END)
    entrada_hasta.delete(0, tk.END)
    combo_cuenta.set("TODAS")
    entrada_tercero.delete(0, tk.END)
    combo_modulo.set("TODOS")
    consultar_mayor()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Libro Mayor")
ventana.geometry("1550x900")
ventana.minsize(1200, 740)
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
    text="LIBRO MAYOR",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Saldos y movimientos agrupados por cuenta",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=29, pady=(3, 0))

contenedor = tk.Frame(ventana, bg=COLOR_FONDO)
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

etiqueta_filtro("Cuenta", 2)
combo_cuenta = ttk.Combobox(
    filtros,
    state="readonly",
    width=40
)
combo_cuenta.grid(row=1, column=2, padx=(0, 8))

etiqueta_filtro("Tercero", 3)
entrada_tercero = ttk.Entry(filtros, width=22)
entrada_tercero.grid(row=1, column=3, padx=(0, 8))

etiqueta_filtro("Módulo", 4)
combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=20
)
combo_modulo.grid(row=1, column=4, padx=(0, 10))

tk.Button(
    filtros,
    text="Consultar",
    command=consultar_mayor,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
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
    padx=16,
    pady=7
).grid(row=1, column=6, padx=4)

tk.Button(
    filtros,
    text="Exportar resumen",
    command=exportar_resumen,
    bg=COLOR_VERDE,
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).grid(row=1, column=7, padx=4)

tk.Button(
    filtros,
    text="Exportar detalle",
    command=exportar_detalle,
    bg="#7C3AED",
    fg="white",
    relief="flat",
    bd=0,
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).grid(row=1, column=8, padx=4)

# Resumen tarjetas
resumen = tk.Frame(contenedor, bg=COLOR_FONDO)
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
lbl_saldo_inicial = crear_tarjeta(1, "SALDO INICIAL")
lbl_debitos = crear_tarjeta(2, "DÉBITOS")
lbl_creditos = crear_tarjeta(3, "CRÉDITOS")
lbl_saldo_final = crear_tarjeta(4, "SALDO FINAL")

# Resumen cuentas
panel_resumen = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_resumen.pack(fill="both", expand=True, pady=(0, 12))

tk.Label(
    panel_resumen,
    text="Resumen por cuenta",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(10, 5))

columnas_resumen = (
    "Cuenta",
    "Nombre",
    "Naturaleza",
    "Saldo inicial",
    "Débitos",
    "Créditos",
    "Saldo final"
)

tabla_resumen = ttk.Treeview(
    panel_resumen,
    columns=columnas_resumen,
    show="headings",
    height=8
)

anchos_resumen = {
    "Cuenta": 100,
    "Nombre": 330,
    "Naturaleza": 100,
    "Saldo inicial": 130,
    "Débitos": 130,
    "Créditos": 130,
    "Saldo final": 130
}

for columna in columnas_resumen:
    tabla_resumen.heading(columna, text=columna)
    tabla_resumen.column(
        columna,
        width=anchos_resumen[columna],
        anchor="e" if columna in (
            "Saldo inicial", "Débitos", "Créditos", "Saldo final"
        ) else "w"
    )

tabla_resumen.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 10)
)

tabla_resumen.bind(
    "<<TreeviewSelect>>",
    cargar_detalle
)

# Detalle
panel_detalle = tk.Frame(
    contenedor,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
panel_detalle.pack(fill="both", expand=True)

cabecera_detalle = tk.Frame(panel_detalle, bg=COLOR_TARJETA)
cabecera_detalle.pack(fill="x", padx=14, pady=(10, 5))

lbl_cuenta_seleccionada = tk.Label(
    cabecera_detalle,
    text="Sin selección",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
)
lbl_cuenta_seleccionada.pack(side="left")

totales_detalle = tk.Frame(cabecera_detalle, bg=COLOR_TARJETA)
totales_detalle.pack(side="right")

def dato_detalle(titulo):
    marco = tk.Frame(totales_detalle, bg=COLOR_TARJETA)
    marco.pack(side="left", padx=10)

    tk.Label(
        marco,
        text=titulo,
        bg=COLOR_TARJETA,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="e")

    valor = tk.Label(
        marco,
        text="$0.00",
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 9, "bold")
    )
    valor.pack(anchor="e")
    return valor

lbl_detalle_inicial = dato_detalle("INICIAL")
lbl_detalle_debitos = dato_detalle("DÉBITOS")
lbl_detalle_creditos = dato_detalle("CRÉDITOS")
lbl_detalle_final = dato_detalle("FINAL")

columnas_detalle = (
    "Fecha",
    "Comprobante",
    "Documento",
    "Concepto",
    "Descripción",
    "Tercero",
    "Centro costo",
    "Módulo",
    "Débito",
    "Crédito",
    "Saldo"
)

tabla_detalle = ttk.Treeview(
    panel_detalle,
    columns=columnas_detalle,
    show="headings",
    height=8
)

anchos_detalle = {
    "Fecha": 135,
    "Comprobante": 130,
    "Documento": 110,
    "Concepto": 250,
    "Descripción": 220,
    "Tercero": 170,
    "Centro costo": 110,
    "Módulo": 130,
    "Débito": 115,
    "Crédito": 115,
    "Saldo": 115
}

for columna in columnas_detalle:
    tabla_detalle.heading(columna, text=columna)
    tabla_detalle.column(
        columna,
        width=anchos_detalle[columna],
        anchor="e" if columna in ("Débito", "Crédito", "Saldo") else "w"
    )

scroll_x = ttk.Scrollbar(
    panel_detalle,
    orient="horizontal",
    command=tabla_detalle.xview
)

tabla_detalle.configure(
    xscrollcommand=scroll_x.set
)

tabla_detalle.pack(
    fill="both",
    expand=True,
    padx=14,
    pady=(0, 0)
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
consultar_mayor()

ventana.mainloop()
