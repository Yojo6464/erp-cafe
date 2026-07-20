"""
BME-ERP - Libro Diario
Archivo: libro_diario.py

Funciones:
- Consulta movimientos contables cronológicos.
- Filtra por fechas, tipo de comprobante, cuenta, tercero y módulo.
- Muestra débito, crédito y saldo acumulado.
- Resume totales del período consultado.
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
            SELECT DISTINCT tc.codigo
            FROM tipos_comprobante tc
            WHERE tc.estado='ACTIVO'
            ORDER BY tc.codigo
        """)
        combo_tipo["values"] = (
            ["TODOS"] + [fila["codigo"] for fila in cursor.fetchall()]
        )
        combo_tipo.set("TODOS")

        cursor.execute("""
            SELECT DISTINCT c.modulo_origen
            FROM comprobantes c
            WHERE COALESCE(c.modulo_origen, '') <> ''
            ORDER BY c.modulo_origen
        """)
        combo_modulo["values"] = (
            ["TODOS"] + [fila["modulo_origen"] for fila in cursor.fetchall()]
        )
        combo_modulo.set("TODOS")

        cursor.execute("""
            SELECT codigo || ' - ' || nombre AS cuenta
            FROM plan_cuentas
            WHERE permite_movimiento=1
              AND estado='ACTIVA'
            ORDER BY codigo
        """)
        combo_cuenta["values"] = (
            ["TODAS"] + [fila["cuenta"] for fila in cursor.fetchall()]
        )
        combo_cuenta.set("TODAS")

    finally:
        conexion.close()


def construir_filtros():
    condiciones = ["c.estado='CONTABILIZADO'"]
    parametros = []

    desde = entrada_desde.get().strip()
    hasta = entrada_hasta.get().strip()
    tipo = combo_tipo.get().strip()
    modulo = combo_modulo.get().strip()
    cuenta = combo_cuenta.get().strip()
    tercero = entrada_tercero.get().strip()
    texto = entrada_buscar.get().strip()

    if not fecha_valida(desde):
        raise ValueError(
            "La fecha inicial debe tener formato AAAA-MM-DD."
        )

    if not fecha_valida(hasta):
        raise ValueError(
            "La fecha final debe tener formato AAAA-MM-DD."
        )

    if desde:
        condiciones.append("date(c.fecha) >= date(?)")
        parametros.append(desde)

    if hasta:
        condiciones.append("date(c.fecha) <= date(?)")
        parametros.append(hasta)

    if tipo and tipo != "TODOS":
        condiciones.append("tc.codigo=?")
        parametros.append(tipo)

    if modulo and modulo != "TODOS":
        condiciones.append("c.modulo_origen=?")
        parametros.append(modulo)

    if cuenta and cuenta != "TODAS":
        codigo_cuenta = cuenta.split(" - ", 1)[0]
        condiciones.append("pc.codigo=?")
        parametros.append(codigo_cuenta)

    if tercero:
        condiciones.append("""
            COALESCE(t.nombre_razon_social, '') LIKE ?
        """)
        parametros.append(f"%{tercero}%")

    if texto:
        condiciones.append("""
            (
                c.consecutivo LIKE ?
                OR c.concepto LIKE ?
                OR d.descripcion LIKE ?
                OR c.documento_referencia LIKE ?
            )
        """)
        patron = f"%{texto}%"
        parametros.extend([patron, patron, patron, patron])

    return " AND ".join(condiciones), parametros


# ============================================================
# CONSULTA
# ============================================================

def consultar_libro():
    try:
        condicion, parametros = construir_filtros()

        conexion = conectar()

        try:
            cursor = conexion.cursor()
            cursor.execute(f"""
                SELECT
                    d.id,
                    c.fecha,
                    c.consecutivo,
                    tc.codigo AS tipo,
                    c.documento_referencia,
                    pc.codigo AS cuenta_codigo,
                    pc.nombre AS cuenta_nombre,
                    d.descripcion,
                    COALESCE(t.nombre_razon_social, '') AS tercero,
                    COALESCE(cc.codigo, '') AS centro_costo,
                    c.modulo_origen,
                    d.debito,
                    d.credito
                FROM detalle_comprobante d
                INNER JOIN comprobantes c
                    ON c.id=d.comprobante_id
                INNER JOIN tipos_comprobante tc
                    ON tc.id=c.tipo_comprobante_id
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

        tabla.delete(*tabla.get_children())

        total_debito = 0.0
        total_credito = 0.0
        saldo_acumulado = 0.0

        for fila in registros:
            debito = float(fila["debito"] or 0)
            credito = float(fila["credito"] or 0)

            total_debito += debito
            total_credito += credito
            saldo_acumulado += debito - credito

            tabla.insert(
                "",
                "end",
                values=(
                    fila["fecha"],
                    fila["consecutivo"],
                    fila["tipo"],
                    fila["documento_referencia"],
                    fila["cuenta_codigo"],
                    fila["cuenta_nombre"],
                    fila["descripcion"],
                    fila["tercero"],
                    fila["centro_costo"],
                    fila["modulo_origen"],
                    moneda(debito),
                    moneda(credito),
                    moneda(saldo_acumulado)
                )
            )

        lbl_movimientos.config(text=str(len(registros)))
        lbl_debitos.config(text=moneda(total_debito))
        lbl_creditos.config(text=moneda(total_credito))
        lbl_diferencia.config(
            text=moneda(total_debito - total_credito)
        )

        if abs(total_debito - total_credito) <= 0.01:
            lbl_diferencia.config(fg=COLOR_VERDE)
        else:
            lbl_diferencia.config(fg=COLOR_ROJO)

        datos_actuales.clear()
        datos_actuales.extend(registros)

    except Exception as error:
        messagebox.showerror(
            "Libro Diario",
            str(error)
        )


# ============================================================
# EXPORTACIÓN
# ============================================================

datos_actuales = []


def exportar_csv():
    if not datos_actuales:
        messagebox.showwarning(
            "Exportar",
            "No hay movimientos para exportar."
        )
        return

    ruta = filedialog.asksaveasfilename(
        title="Guardar Libro Diario",
        defaultextension=".csv",
        initialfile="libro_diario.csv",
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
                "Fecha",
                "Comprobante",
                "Tipo",
                "Documento",
                "Cuenta",
                "Nombre cuenta",
                "Descripción",
                "Tercero",
                "Centro de costo",
                "Módulo",
                "Débito",
                "Crédito"
            ])

            for fila in datos_actuales:
                escritor.writerow([
                    fila["fecha"],
                    fila["consecutivo"],
                    fila["tipo"],
                    fila["documento_referencia"],
                    fila["cuenta_codigo"],
                    fila["cuenta_nombre"],
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
    combo_tipo.set("TODOS")
    combo_modulo.set("TODOS")
    combo_cuenta.set("TODAS")
    entrada_tercero.delete(0, tk.END)
    entrada_buscar.delete(0, tk.END)
    consultar_libro()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()
ventana.title("BME-ERP - Libro Diario")
ventana.geometry("1550x850")
ventana.minsize(1200, 700)
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
    text="LIBRO DIARIO",
    bg=COLOR_AZUL,
    fg="white",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", padx=28, pady=(16, 0))

tk.Label(
    cabecera,
    text="Movimientos contables cronológicos",
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

etiqueta_filtro("Tipo", 2)
combo_tipo = ttk.Combobox(
    filtros,
    state="readonly",
    width=10
)
combo_tipo.grid(row=1, column=2, padx=(0, 8))

etiqueta_filtro("Módulo", 3)
combo_modulo = ttk.Combobox(
    filtros,
    state="readonly",
    width=18
)
combo_modulo.grid(row=1, column=3, padx=(0, 8))

etiqueta_filtro("Cuenta", 4)
combo_cuenta = ttk.Combobox(
    filtros,
    state="readonly",
    width=34
)
combo_cuenta.grid(row=1, column=4, padx=(0, 8))

etiqueta_filtro("Tercero", 5)
entrada_tercero = ttk.Entry(filtros, width=20)
entrada_tercero.grid(row=1, column=5, padx=(0, 8))

etiqueta_filtro("Buscar", 6)
entrada_buscar = ttk.Entry(filtros, width=24)
entrada_buscar.grid(row=1, column=6, padx=(0, 10))

tk.Button(
    filtros,
    text="Consultar",
    command=consultar_libro,
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
).grid(row=1, column=7, padx=4)

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
).grid(row=1, column=8, padx=4)

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
).grid(row=1, column=9, padx=4)

# Resumen
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

lbl_movimientos = crear_tarjeta(0, "MOVIMIENTOS")
lbl_debitos = crear_tarjeta(1, "TOTAL DÉBITOS")
lbl_creditos = crear_tarjeta(2, "TOTAL CRÉDITOS")
lbl_diferencia = crear_tarjeta(3, "DIFERENCIA")

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
    text="Detalle del Libro Diario",
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", padx=14, pady=(12, 5))

columnas = (
    "Fecha",
    "Comprobante",
    "Tipo",
    "Documento",
    "Cuenta",
    "Nombre cuenta",
    "Descripción",
    "Tercero",
    "Centro costo",
    "Módulo",
    "Débito",
    "Crédito",
    "Saldo"
)

tabla = ttk.Treeview(
    panel_tabla,
    columns=columnas,
    show="headings"
)

anchos = {
    "Fecha": 140,
    "Comprobante": 135,
    "Tipo": 65,
    "Documento": 110,
    "Cuenta": 90,
    "Nombre cuenta": 220,
    "Descripción": 240,
    "Tercero": 170,
    "Centro costo": 110,
    "Módulo": 130,
    "Débito": 115,
    "Crédito": 115,
    "Saldo": 115
}

for columna in columnas:
    tabla.heading(columna, text=columna)
    tabla.column(
        columna,
        width=anchos[columna],
        anchor="e" if columna in ("Débito", "Crédito", "Saldo") else "w"
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
consultar_libro()

ventana.mainloop()
