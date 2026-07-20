import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import os
import sys
from datetime import datetime

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"
RUTA_MODULOS = r"C:\Users\jrive\visual"

EMPRESA = "Café Alto de la Cruz"
VERSION = "ERP 1.1"
USUARIO = "Jorge Rivera"

COLOR_FONDO = "#EEF3F8"
COLOR_SIDEBAR = "#153B5B"
COLOR_SIDEBAR_ACTIVO = "#1F567D"
COLOR_SUPERIOR = "#FFFFFF"
COLOR_TARJETA = "#FFFFFF"
COLOR_TEXTO = "#1F2937"
COLOR_TEXTO_SUAVE = "#64748B"
COLOR_AZUL = "#0F5C8E"
COLOR_VERDE = "#15803D"
COLOR_NARANJA = "#C56A00"
COLOR_ROJO = "#B42318"
COLOR_BORDE = "#D7E0E8"

print("=" * 60)
print("ESTE ES EL MAIN_ERP QUE SE ESTÁ EJECUTANDO")
print(__file__)
print("=" * 60)


# ============================================================
# UTILIDADES DE BASE DE DATOS
# ============================================================

def ejecutar_valor(sql, parametros=(), predeterminado=0):
    """Ejecuta una consulta que devuelve un solo valor."""
    conexion = None

    try:
        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        fila = cursor.fetchone()

        if not fila or fila[0] is None:
            return predeterminado

        return fila[0]

    except sqlite3.Error as error:
        print("-" * 60)
        print("ERROR DE CONSULTA EN DASHBOARD")
        print(sql.strip())
        print(error)
        print("-" * 60)
        return predeterminado

    finally:
        if conexion:
            conexion.close()


def tabla_existe(nombre_tabla):
    sql = """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type='table' AND name=?
    """
    return ejecutar_valor(sql, (nombre_tabla,), 0) > 0



def columnas_tabla(nombre_tabla):
    """Devuelve las columnas existentes de una tabla."""
    if not tabla_existe(nombre_tabla):
        return set()

    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_DB)
        cursor = conexion.cursor()
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        return {fila[1] for fila in cursor.fetchall()}
    except sqlite3.Error:
        return set()
    finally:
        if conexion:
            conexion.close()


def valor_por_periodo(tabla, columna_valor, columna_fecha, periodo):
    """Suma valores por día o mes, únicamente si la estructura existe."""
    columnas = columnas_tabla(tabla)

    if columna_valor not in columnas or columna_fecha not in columnas:
        return 0

    if periodo == "hoy":
        filtro = f"date({columna_fecha}) = date('now', 'localtime')"
    elif periodo == "mes":
        filtro = (
            f"strftime('%Y-%m', {columna_fecha}) = "
            "strftime('%Y-%m', 'now', 'localtime')"
        )
    else:
        return 0

    return ejecutar_valor(
        f"""
        SELECT IFNULL(SUM({columna_valor}), 0)
        FROM {tabla}
        WHERE {filtro}
        """
    )


def comprobar_base_datos():
    if not os.path.exists(RUTA_DB):
        return False

    try:
        with sqlite3.connect(RUTA_DB) as conexion:
            conexion.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False


# ============================================================
# APERTURA DE MÓDULOS
# ============================================================

def abrir_modulo(nombre_archivo):
    ruta = os.path.join(RUTA_MODULOS, nombre_archivo)

    print("=" * 60)
    print("MÓDULO SOLICITADO:", nombre_archivo)
    print("RUTA:", ruta)
    print("EXISTE:", os.path.exists(ruta))
    print("=" * 60)

    if not os.path.exists(ruta):
        messagebox.showerror(
            "Módulo no encontrado",
            f"No se encontró el archivo:\n\n{ruta}"
        )
        return

    try:
        subprocess.Popen([sys.executable, ruta], cwd=RUTA_MODULOS)
    except OSError as error:
        messagebox.showerror(
            "Error al abrir módulo",
            f"No fue posible abrir:\n{nombre_archivo}\n\n{error}"
        )


def modulo_en_desarrollo(nombre):
    messagebox.showinfo(
        nombre,
        f"El módulo {nombre} está preparado para su próxima integración."
    )



def accion_rapida(nombre, archivo=None):
    if archivo:
        abrir_modulo(archivo)
    else:
        modulo_en_desarrollo(nombre)


def mostrar_acerca_de():
    messagebox.showinfo(
        "Acerca del sistema",
        f"{EMPRESA}\n{VERSION}\n\n"
        "Dashboard Ejecutivo desarrollado en Python y SQLite."
    )


def mostrar_ruta_base():
    messagebox.showinfo(
        "Base de datos",
        f"Ruta configurada:\n\n{RUTA_DB}\n\n"
        f"Estado: {'Conectada' if comprobar_base_datos() else 'No disponible'}"
    )


def crear_respaldo():
    if not os.path.exists(RUTA_DB):
        messagebox.showerror(
            "Respaldo",
            "No se encontró la base de datos configurada."
        )
        return

    carpeta = os.path.join(RUTA_MODULOS, "backups")
    os.makedirs(carpeta, exist_ok=True)

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(carpeta, f"erp_cafe_{marca}.db")

    try:
        origen = sqlite3.connect(RUTA_DB)
        copia = sqlite3.connect(destino)
        with copia:
            origen.backup(copia)
        copia.close()
        origen.close()

        messagebox.showinfo(
            "Respaldo creado",
            f"El respaldo fue creado correctamente:\n\n{destino}"
        )
    except sqlite3.Error as error:
        messagebox.showerror(
            "Error de respaldo",
            f"No fue posible crear el respaldo.\n\n{error}"
        )


# ============================================================
# COMPONENTES VISUALES
# ============================================================

def crear_boton_menu(contenedor, texto, comando):
    boton = tk.Button(
        contenedor,
        text=texto,
        command=comando,
        anchor="w",
        padx=18,
        relief="flat",
        bd=0,
        bg=COLOR_SIDEBAR,
        fg="white",
        activebackground=COLOR_SIDEBAR_ACTIVO,
        activeforeground="white",
        font=("Segoe UI", 10, "bold"),
        cursor="hand2"
    )
    boton.pack(fill="x", padx=8, pady=3, ipady=10)

    boton.bind(
        "<Enter>",
        lambda evento: boton.config(bg=COLOR_SIDEBAR_ACTIVO)
    )
    boton.bind(
        "<Leave>",
        lambda evento: boton.config(bg=COLOR_SIDEBAR)
    )
    return boton


def crear_tarjeta(contenedor, fila, columna, titulo, color_acento):
    marco = tk.Frame(
        contenedor,
        bg=COLOR_TARJETA,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=fila,
        column=columna,
        sticky="nsew",
        padx=8,
        pady=8
    )

    barra = tk.Frame(marco, bg=color_acento, width=6)
    barra.pack(side="left", fill="y")

    contenido = tk.Frame(marco, bg=COLOR_TARJETA)
    contenido.pack(side="left", fill="both", expand=True, padx=16, pady=13)

    tk.Label(
        contenido,
        text=titulo,
        font=("Segoe UI", 9, "bold"),
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO_SUAVE
    ).pack(anchor="w")

    valor = tk.Label(
        contenido,
        text="$0",
        font=("Segoe UI", 18, "bold"),
        bg=COLOR_TARJETA,
        fg=COLOR_TEXTO
    )
    valor.pack(anchor="w", pady=(5, 0))

    return valor


def moneda(valor):
    try:
        return f"${float(valor):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def numero(valor):
    try:
        return f"{int(valor):,}"
    except (TypeError, ValueError):
        return "0"


# ============================================================
# ACTUALIZACIÓN DEL DASHBOARD
# ============================================================

def obtener_indicadores():
    ventas = ejecutar_valor("""
        SELECT IFNULL(SUM(total), 0)
        FROM ventas_cafe
    """)

    cartera = ejecutar_valor("""
        SELECT IFNULL(SUM(valor), 0)
        FROM cuentas_cobrar_v1
        WHERE UPPER(estado) = 'PENDIENTE'
    """)

    bancos = ejecutar_valor("""
        SELECT IFNULL(SUM(saldo), 0)
        FROM bancos
        WHERE UPPER(estado) = 'ACTIVA'
    """)

    clientes = ejecutar_valor("""
        SELECT COUNT(*)
        FROM clientes
    """)

    proveedores = ejecutar_valor("""
        SELECT COUNT(*)
        FROM proveedores
    """)

    produccion = ejecutar_valor("""
        SELECT IFNULL(SUM(cafe_tostado), 0)
        FROM produccion_cafe
    """)

    inventario = ejecutar_valor("""
        SELECT IFNULL(
            SUM(cantidad * COALESCE(costo_unitario, costo, 0)),
            0
        )
        FROM inventario
    """)

    productos = ejecutar_valor("""
        SELECT COUNT(*)
        FROM inventario
    """)

    cuentas_pagar = ejecutar_valor("""
        SELECT IFNULL(SUM(saldo), 0)
        FROM cuentas_pagar
        WHERE saldo > 0
    """)

    nomina = ejecutar_valor("""
        SELECT IFNULL(SUM(neto_pagar), 0)
        FROM nomina
    """)

    prestaciones = ejecutar_valor("""
        SELECT IFNULL(SUM(total_prestaciones), 0)
        FROM prestaciones
    """)

    ventas_hoy = 0
    ventas_mes = 0
    columnas_ventas = columnas_tabla("ventas_cafe")

    posibles_fechas = [
        "fecha", "fecha_venta", "created_at",
        "fecha_registro", "fecha_emision"
    ]

    columna_fecha = next(
        (col for col in posibles_fechas if col in columnas_ventas),
        None
    )

    if columna_fecha and "total" in columnas_ventas:
        ventas_hoy = valor_por_periodo(
            "ventas_cafe", "total", columna_fecha, "hoy"
        )
        ventas_mes = valor_por_periodo(
            "ventas_cafe", "total", columna_fecha, "mes"
        )

    utilidad = ventas * 0.40
    costo_personal = nomina + prestaciones
    liquidez = bancos - cuentas_pagar

    return {
        "ventas": ventas,
        "ventas_hoy": ventas_hoy,
        "ventas_mes": ventas_mes,
        "cartera": cartera,
        "bancos": bancos,
        "clientes": clientes,
        "proveedores": proveedores,
        "productos": productos,
        "produccion": produccion,
        "inventario": inventario,
        "cuentas_pagar": cuentas_pagar,
        "utilidad": utilidad,
        "nomina": nomina,
        "prestaciones": prestaciones,
        "costo_personal": costo_personal,
        "liquidez": liquidez
    }


def actualizar_alertas(datos):
    alertas = []

    if datos["cartera"] > 0:
        alertas.append(
            ("ADVERTENCIA", f"Cartera pendiente por {moneda(datos['cartera'])}.")
        )

    if datos["cuentas_pagar"] > 0:
        alertas.append(
            ("ADVERTENCIA", f"Cuentas por pagar por {moneda(datos['cuentas_pagar'])}.")
        )

    if datos["liquidez"] < 0:
        alertas.append(
            ("CRÍTICO", "El saldo bancario no cubre las cuentas por pagar.")
        )

    if datos["inventario"] <= 0:
        alertas.append(
            ("CRÍTICO", "No se encontró valor de inventario disponible.")
        )

    if datos["clientes"] == 0:
        alertas.append(
            ("REVISAR", "No hay clientes registrados.")
        )

    if not alertas:
        alertas.append(
            ("NORMAL", "No existen alertas financieras críticas.")
        )

    texto_alertas.config(state="normal")
    texto_alertas.delete("1.0", "end")

    for nivel, mensaje in alertas:
        texto_alertas.insert("end", f"{nivel}: ", nivel)
        texto_alertas.insert("end", f"{mensaje}\n\n")

    texto_alertas.tag_config(
        "CRÍTICO", foreground=COLOR_ROJO, font=("Segoe UI", 9, "bold")
    )
    texto_alertas.tag_config(
        "ADVERTENCIA", foreground=COLOR_NARANJA, font=("Segoe UI", 9, "bold")
    )
    texto_alertas.tag_config(
        "REVISAR", foreground=COLOR_AZUL, font=("Segoe UI", 9, "bold")
    )
    texto_alertas.tag_config(
        "NORMAL", foreground=COLOR_VERDE, font=("Segoe UI", 9, "bold")
    )

    texto_alertas.config(state="disabled")


def dibujar_resumen(datos):
    lienzo.delete("all")

    ancho = max(lienzo.winfo_width(), 500)
    alto = max(lienzo.winfo_height(), 190)

    margen = 45
    base_y = alto - 35
    alto_maximo = alto - 75

    valores = [
        ("Ventas", datos["ventas"]),
        ("Bancos", datos["bancos"]),
        ("Inventario", datos["inventario"]),
        ("CxP", datos["cuentas_pagar"])
    ]

    maximo = max([float(v) for _, v in valores] + [1])
    espacio = (ancho - (2 * margen)) / len(valores)
    ancho_barra = min(75, espacio * 0.55)

    colores = [COLOR_AZUL, COLOR_VERDE, COLOR_NARANJA, COLOR_ROJO]

    lienzo.create_line(
        margen,
        base_y,
        ancho - margen,
        base_y,
        fill=COLOR_BORDE,
        width=2
    )

    for indice, ((etiqueta, valor), color) in enumerate(zip(valores, colores)):
        centro_x = margen + espacio * indice + espacio / 2
        altura = (float(valor) / maximo) * alto_maximo if maximo else 0

        x1 = centro_x - ancho_barra / 2
        x2 = centro_x + ancho_barra / 2
        y1 = base_y - altura

        lienzo.create_rectangle(
            x1,
            y1,
            x2,
            base_y,
            fill=color,
            outline=""
        )

        lienzo.create_text(
            centro_x,
            base_y + 17,
            text=etiqueta,
            fill=COLOR_TEXTO_SUAVE,
            font=("Segoe UI", 9, "bold")
        )

        lienzo.create_text(
            centro_x,
            max(y1 - 12, 12),
            text=moneda(valor),
            fill=COLOR_TEXTO,
            font=("Segoe UI", 8, "bold")
        )


def actualizar_dashboard():
    datos = obtener_indicadores()

    lbl_ventas.config(text=moneda(datos["ventas"]))
    lbl_cartera.config(text=moneda(datos["cartera"]))
    lbl_bancos.config(text=moneda(datos["bancos"]))
    lbl_clientes.config(text=numero(datos["clientes"]))
    lbl_produccion.config(text=f"{datos['produccion']:,.0f} Kg")
    lbl_inventario.config(text=moneda(datos["inventario"]))
    lbl_cxp.config(text=moneda(datos["cuentas_pagar"]))
    lbl_utilidad.config(text=moneda(datos["utilidad"]))
    lbl_nomina.config(text=moneda(datos["nomina"]))
    lbl_prestaciones.config(text=moneda(datos["prestaciones"]))
    lbl_costo_personal.config(text=moneda(datos["costo_personal"]))
    lbl_ventas_hoy.config(text=moneda(datos["ventas_hoy"]))
    lbl_ventas_mes.config(text=moneda(datos["ventas_mes"]))
    lbl_proveedores.config(text=numero(datos["proveedores"]))
    lbl_productos.config(text=numero(datos["productos"]))
    lbl_liquidez.config(text=moneda(datos["liquidez"]))

    actualizar_alertas(datos)
    dibujar_resumen(datos)

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lbl_ultima_actualizacion.config(
        text=f"Última actualización: {ahora}"
    )

    if comprobar_base_datos():
        lbl_estado_bd.config(
            text="● Base de datos conectada",
            fg=COLOR_VERDE
        )
    else:
        lbl_estado_bd.config(
            text="● Base de datos desconectada",
            fg=COLOR_ROJO
        )


def refresco_automatico():
    actualizar_dashboard()
    ventana.after(5000, refresco_automatico)


def actualizar_reloj():
    ahora = datetime.now()
    lbl_fecha.config(text=ahora.strftime("%A, %d de %B de %Y"))
    lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
    ventana.after(1000, actualizar_reloj)


def salir():
    if messagebox.askyesno(
        "Cerrar ERP",
        "¿Desea cerrar el sistema?"
    ):
        ventana.destroy()


# ============================================================
# VENTANA PRINCIPAL
# ============================================================

ventana = tk.Tk()
ventana.title(f"{EMPRESA} - Dashboard Ejecutivo")
ventana.geometry("1450x850")
ventana.minsize(1180, 700)
ventana.configure(bg=COLOR_FONDO)
ventana.protocol("WM_DELETE_WINDOW", salir)

barra_menu = tk.Menu(ventana)

menu_archivo = tk.Menu(barra_menu, tearoff=0)
menu_archivo.add_command(label="Actualizar dashboard", command=actualizar_dashboard)
menu_archivo.add_command(label="Crear respaldo", command=crear_respaldo)
menu_archivo.add_separator()
menu_archivo.add_command(label="Salir", command=salir)
barra_menu.add_cascade(label="Archivo", menu=menu_archivo)

menu_procesos = tk.Menu(barra_menu, tearoff=0)
menu_procesos.add_command(
    label="Inventario",
    command=lambda: abrir_modulo("inventario_interfaz_v1_0.py")
)
menu_procesos.add_command(
    label="Proveedores",
    command=lambda: abrir_modulo("proveedores.py")
)
menu_procesos.add_command(
    label="Bancos",
    command=lambda: abrir_modulo("bancos.py")
)
menu_procesos.add_command(
    label="Cuentas por pagar",
    command=lambda: abrir_modulo("cuentas_pagar.py")
)
barra_menu.add_cascade(label="Procesos", menu=menu_procesos)

menu_herramientas = tk.Menu(barra_menu, tearoff=0)
menu_herramientas.add_command(
    label="Estado de base de datos",
    command=mostrar_ruta_base
)
barra_menu.add_cascade(label="Herramientas", menu=menu_herramientas)

menu_ayuda = tk.Menu(barra_menu, tearoff=0)
menu_ayuda.add_command(label="Acerca de", command=mostrar_acerca_de)
barra_menu.add_cascade(label="Ayuda", menu=menu_ayuda)

ventana.config(menu=barra_menu)

try:
    ventana.state("zoomed")
except tk.TclError:
    pass

# Estilo ttk
estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

# Diseño general
ventana.grid_rowconfigure(0, weight=1)
ventana.grid_columnconfigure(1, weight=1)

# ============================================================
# MENÚ LATERAL
# ============================================================

sidebar = tk.Frame(ventana, bg=COLOR_SIDEBAR, width=235)
sidebar.grid(row=0, column=0, sticky="ns")
sidebar.grid_propagate(False)

tk.Label(
    sidebar,
    text="ERP CAFÉ",
    font=("Segoe UI", 20, "bold"),
    bg=COLOR_SIDEBAR,
    fg="white"
).pack(anchor="w", padx=22, pady=(24, 0))

tk.Label(
    sidebar,
    text="ALTO DE LA CRUZ",
    font=("Segoe UI", 10, "bold"),
    bg=COLOR_SIDEBAR,
    fg="#BFD7EA"
).pack(anchor="w", padx=24, pady=(0, 24))

tk.Label(
    sidebar,
    text="MÓDULOS",
    font=("Segoe UI", 8, "bold"),
    bg=COLOR_SIDEBAR,
    fg="#91AFC5"
).pack(anchor="w", padx=22, pady=(0, 6))

crear_boton_menu(
    sidebar,
    "▣  Dashboard",
    actualizar_dashboard
)

crear_boton_menu(
    sidebar,
    "▦  Inventario",
    lambda: abrir_modulo("inventario_interfaz_v1_0.py")
)

crear_boton_menu(
    sidebar,
    "▤  Compras",
    lambda: modulo_en_desarrollo("Compras")
)

crear_boton_menu(
    sidebar,
    "▥  Producción",
    lambda: modulo_en_desarrollo("Producción")
)

crear_boton_menu(
    sidebar,
    "$  Ventas",
    lambda: modulo_en_desarrollo("Ventas")
)

crear_boton_menu(
    sidebar,
    "👥  Clientes",
    lambda: modulo_en_desarrollo("Clientes")
)

crear_boton_menu(
    sidebar,
    "▧  Proveedores",
    lambda: abrir_modulo("proveedores.py")
)

crear_boton_menu(
    sidebar,
    "▰  Bancos",
    lambda: abrir_modulo("bancos.py")
)

crear_boton_menu(
    sidebar,
    "▤  Cuentas por pagar",
    lambda: abrir_modulo("cuentas_pagar.py")
)

crear_boton_menu(
    sidebar,
    "✓  Solicitudes de pago",
    lambda: abrir_modulo("solicitudes_pagos.py")
)

crear_boton_menu(
    sidebar,
    "☑  Aprobación de pagos",
    lambda: abrir_modulo("aprobacion_pagos.py")
)

crear_boton_menu(
    sidebar,
    "$  Pagos CxP",
    lambda: abrir_modulo("pagos_cxp.py")
)

crear_boton_menu(
    sidebar,
    "⇄  Transferencias",
    lambda: abrir_modulo("transferencias_bancarias.py")
)

crear_boton_menu(
    sidebar,
    "▥  Reportes",
    lambda: modulo_en_desarrollo("Reportes")
)

tk.Frame(sidebar, bg="#315A78", height=1).pack(
    fill="x",
    padx=18,
    pady=15
)

crear_boton_menu(sidebar, "⏻  Salir", salir)

# ============================================================
# ÁREA PRINCIPAL
# ============================================================

principal = tk.Frame(ventana, bg=COLOR_FONDO)
principal.grid(row=0, column=1, sticky="nsew")
principal.grid_rowconfigure(1, weight=1)
principal.grid_columnconfigure(0, weight=1)

# Barra superior
barra_superior = tk.Frame(
    principal,
    bg=COLOR_SUPERIOR,
    height=80,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
barra_superior.grid(row=0, column=0, sticky="ew")
barra_superior.grid_propagate(False)
barra_superior.grid_columnconfigure(0, weight=1)

bloque_titulo = tk.Frame(barra_superior, bg=COLOR_SUPERIOR)
bloque_titulo.grid(row=0, column=0, sticky="w", padx=25, pady=12)

tk.Label(
    bloque_titulo,
    text="Dashboard Ejecutivo",
    font=("Segoe UI", 20, "bold"),
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO
).pack(anchor="w")

lbl_fecha = tk.Label(
    bloque_titulo,
    text="",
    font=("Segoe UI", 9),
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO_SUAVE
)
lbl_fecha.pack(anchor="w")

bloque_usuario = tk.Frame(barra_superior, bg=COLOR_SUPERIOR)
bloque_usuario.grid(row=0, column=1, sticky="e", padx=25, pady=10)

lbl_hora = tk.Label(
    bloque_usuario,
    text="",
    font=("Segoe UI", 14, "bold"),
    bg=COLOR_SUPERIOR,
    fg=COLOR_AZUL
)
lbl_hora.pack(anchor="e")

tk.Label(
    bloque_usuario,
    text=f"Usuario: {USUARIO}",
    font=("Segoe UI", 9),
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO_SUAVE
).pack(anchor="e")

# Contenedor desplazable
contenedor_canvas = tk.Canvas(
    principal,
    bg=COLOR_FONDO,
    highlightthickness=0
)
contenedor_canvas.grid(row=1, column=0, sticky="nsew")

scroll_vertical = ttk.Scrollbar(
    principal,
    orient="vertical",
    command=contenedor_canvas.yview
)
scroll_vertical.grid(row=1, column=1, sticky="ns")

contenedor_canvas.configure(yscrollcommand=scroll_vertical.set)

contenido = tk.Frame(contenedor_canvas, bg=COLOR_FONDO)
ventana_contenido = contenedor_canvas.create_window(
    (0, 0),
    window=contenido,
    anchor="nw"
)

def ajustar_scroll(evento=None):
    contenedor_canvas.configure(
        scrollregion=contenedor_canvas.bbox("all")
    )

def ajustar_ancho(evento):
    contenedor_canvas.itemconfigure(
        ventana_contenido,
        width=evento.width
    )

contenido.bind("<Configure>", ajustar_scroll)
contenedor_canvas.bind("<Configure>", ajustar_ancho)

# Encabezado de sección
encabezado = tk.Frame(contenido, bg=COLOR_FONDO)
encabezado.pack(fill="x", padx=24, pady=(22, 6))

tk.Label(
    encabezado,
    text="Resumen general",
    font=("Segoe UI", 16, "bold"),
    bg=COLOR_FONDO,
    fg=COLOR_TEXTO
).pack(side="left")

tk.Button(
    encabezado,
    text="Actualizar ahora",
    command=actualizar_dashboard,
    relief="flat",
    bd=0,
    padx=18,
    pady=8,
    bg=COLOR_AZUL,
    fg="white",
    activebackground="#0B4B75",
    activeforeground="white",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2"
).pack(side="right")

# Accesos rápidos
panel_accesos = tk.Frame(contenido, bg=COLOR_FONDO)
panel_accesos.pack(fill="x", padx=24, pady=(4, 10))

tk.Label(
    panel_accesos,
    text="Accesos rápidos",
    font=("Segoe UI", 11, "bold"),
    bg=COLOR_FONDO,
    fg=COLOR_TEXTO
).pack(anchor="w", pady=(0, 8))

botones_acceso = tk.Frame(panel_accesos, bg=COLOR_FONDO)
botones_acceso.pack(fill="x")

accesos = [
    ("Inventario", lambda: abrir_modulo("inventario_interfaz_v1_0.py")),
    ("Proveedores", lambda: abrir_modulo("proveedores.py")),
    ("Bancos", lambda: abrir_modulo("bancos.py")),
    ("Cuentas por pagar", lambda: abrir_modulo("cuentas_pagar.py")),
    ("Solicitudes de pago", lambda: abrir_modulo("solicitudes_pagos.py")),
    ("Crear respaldo", crear_respaldo),
]

for indice, (texto, comando) in enumerate(accesos):
    botones_acceso.grid_columnconfigure(indice, weight=1)
    tk.Button(
        botones_acceso,
        text=texto,
        command=comando,
        relief="flat",
        bd=0,
        padx=12,
        pady=10,
        bg=COLOR_SUPERIOR,
        fg=COLOR_TEXTO,
        activebackground="#E2E8F0",
        activeforeground=COLOR_TEXTO,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1,
        font=("Segoe UI", 9, "bold"),
        cursor="hand2"
    ).grid(row=0, column=indice, sticky="ew", padx=4)

# Tarjetas
panel_tarjetas = tk.Frame(contenido, bg=COLOR_FONDO)
panel_tarjetas.pack(fill="x", padx=16, pady=4)

for columna in range(4):
    panel_tarjetas.grid_columnconfigure(columna, weight=1, uniform="kpi")

lbl_ventas = crear_tarjeta(
    panel_tarjetas, 0, 0, "VENTAS", COLOR_AZUL
)
lbl_cartera = crear_tarjeta(
    panel_tarjetas, 0, 1, "CARTERA", COLOR_NARANJA
)
lbl_bancos = crear_tarjeta(
    panel_tarjetas, 0, 2, "BANCOS", COLOR_VERDE
)
lbl_clientes = crear_tarjeta(
    panel_tarjetas, 0, 3, "CLIENTES", "#7C3AED"
)

lbl_produccion = crear_tarjeta(
    panel_tarjetas, 1, 0, "PRODUCCIÓN", "#0369A1"
)
lbl_inventario = crear_tarjeta(
    panel_tarjetas, 1, 1, "VALOR INVENTARIO", "#0F766E"
)
lbl_cxp = crear_tarjeta(
    panel_tarjetas, 1, 2, "CUENTAS POR PAGAR", COLOR_ROJO
)
lbl_utilidad = crear_tarjeta(
    panel_tarjetas, 1, 3, "UTILIDAD ESTIMADA", "#15803D"
)

lbl_nomina = crear_tarjeta(
    panel_tarjetas, 2, 0, "NÓMINA", "#475569"
)
lbl_prestaciones = crear_tarjeta(
    panel_tarjetas, 2, 1, "PRESTACIONES", "#6D28D9"
)
lbl_costo_personal = crear_tarjeta(
    panel_tarjetas, 2, 2, "COSTO DE PERSONAL", "#BE123C"
)
lbl_liquidez = crear_tarjeta(
    panel_tarjetas, 2, 3, "LIQUIDEZ DISPONIBLE", "#0E7490"
)

lbl_ventas_hoy = crear_tarjeta(
    panel_tarjetas, 3, 0, "VENTAS DE HOY", "#2563EB"
)
lbl_ventas_mes = crear_tarjeta(
    panel_tarjetas, 3, 1, "VENTAS DEL MES", "#0891B2"
)
lbl_proveedores = crear_tarjeta(
    panel_tarjetas, 3, 2, "PROVEEDORES", "#7E22CE"
)
lbl_productos = crear_tarjeta(
    panel_tarjetas, 3, 3, "REGISTROS DE INVENTARIO", "#334155"
)

# Zona inferior
zona_inferior = tk.Frame(contenido, bg=COLOR_FONDO)
zona_inferior.pack(fill="both", expand=True, padx=24, pady=(8, 24))
zona_inferior.grid_columnconfigure(0, weight=2)
zona_inferior.grid_columnconfigure(1, weight=1)
zona_inferior.grid_rowconfigure(0, weight=1)

# Gráfica resumen
marco_grafica = tk.Frame(
    zona_inferior,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
marco_grafica.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 8)
)

tk.Label(
    marco_grafica,
    text="Comparativo financiero",
    font=("Segoe UI", 12, "bold"),
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO
).pack(anchor="w", padx=18, pady=(15, 5))

tk.Label(
    marco_grafica,
    text="Ventas, bancos, inventario y cuentas por pagar",
    font=("Segoe UI", 9),
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO_SUAVE
).pack(anchor="w", padx=18)

lienzo = tk.Canvas(
    marco_grafica,
    bg=COLOR_TARJETA,
    highlightthickness=0,
    height=230
)
lienzo.pack(fill="both", expand=True, padx=12, pady=10)

# Alertas
marco_alertas = tk.Frame(
    zona_inferior,
    bg=COLOR_TARJETA,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
marco_alertas.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=(8, 0)
)

tk.Label(
    marco_alertas,
    text="Alertas ejecutivas",
    font=("Segoe UI", 12, "bold"),
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO
).pack(anchor="w", padx=18, pady=(15, 5))

tk.Label(
    marco_alertas,
    text="Situaciones que requieren revisión",
    font=("Segoe UI", 9),
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO_SUAVE
).pack(anchor="w", padx=18)

texto_alertas = tk.Text(
    marco_alertas,
    height=10,
    wrap="word",
    relief="flat",
    bd=0,
    bg=COLOR_TARJETA,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 10),
    padx=18,
    pady=12,
    cursor="arrow"
)
texto_alertas.pack(fill="both", expand=True)
texto_alertas.config(state="disabled")

# Barra de estado
barra_estado = tk.Frame(
    principal,
    bg=COLOR_SUPERIOR,
    height=34,
    highlightbackground=COLOR_BORDE,
    highlightthickness=1
)
barra_estado.grid(row=2, column=0, sticky="ew")
barra_estado.grid_propagate(False)
barra_estado.grid_columnconfigure(1, weight=1)

lbl_estado_bd = tk.Label(
    barra_estado,
    text="● Verificando base de datos",
    font=("Segoe UI", 8, "bold"),
    bg=COLOR_SUPERIOR,
    fg=COLOR_NARANJA
)
lbl_estado_bd.grid(row=0, column=0, sticky="w", padx=16)

lbl_ultima_actualizacion = tk.Label(
    barra_estado,
    text="Última actualización: --",
    font=("Segoe UI", 8),
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO_SUAVE
)
lbl_ultima_actualizacion.grid(row=0, column=1)

tk.Label(
    barra_estado,
    text=f"{VERSION}  |  {EMPRESA}",
    font=("Segoe UI", 8),
    bg=COLOR_SUPERIOR,
    fg=COLOR_TEXTO_SUAVE
).grid(row=0, column=2, sticky="e", padx=16)

# ============================================================
# INICIO DEL SISTEMA
# ============================================================

actualizar_reloj()
ventana.after(250, actualizar_dashboard)
ventana.after(5000, refresco_automatico)
ventana.mainloop()
