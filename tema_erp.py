"""
====================================================
ERP CAFÉ ALTO DE LA CRUZ
Tema Corporativo
Versión 1.0
====================================================
"""

# ==================================================
# COLORES OFICIALES
# ==================================================

COLOR_NUEVO = "#28A745"          # Verde
COLOR_GUARDAR = "#198754"        # Verde oscuro
COLOR_EDITAR = "#FFC107"         # Amarillo
COLOR_BUSCAR = "#0D6EFD"         # Azul
COLOR_ACTIVAR = "#FD7E14"        # Naranja
COLOR_ELIMINAR = "#DC3545"       # Rojo
COLOR_EXPORTAR = "#5A8F29"       # Verde oliva
COLOR_IMPORTAR = "#6F42C1"       # Morado
COLOR_CANCELAR = "#6C757D"       # Gris

# ==================================================
# FUENTES
# ==================================================

FUENTE_TITULO = ("Arial", 16, "bold")
FUENTE_SUBTITULO = ("Arial", 12)
FUENTE_NORMAL = ("Arial", 10)
FUENTE_BOTON = ("Arial", 10, "bold")

# ==================================================
# TAMAÑOS
# ==================================================

ANCHO_BOTON = 25
ALTO_BOTON = 1

# ==================================================
# BOTONES
# ==================================================

import tkinter as tk


def crear_boton(
    ventana,
    texto,
    color,
    comando,
    ancho=ANCHO_BOTON
):

    return tk.Button(
        ventana,
        text=texto,
        width=ancho,
        height=ALTO_BOTON,
        bg=color,
        fg="white",
        activebackground=color,
        activeforeground="white",
        font=FUENTE_BOTON,
        relief="raised",
        bd=2,
        cursor="hand2",
        command=comando
    )
# ==================================================
# BOTONES PREDEFINIDOS
# ==================================================

def boton_nuevo(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_NUEVO,
        comando
    )


def boton_guardar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_GUARDAR,
        comando
    )


def boton_editar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_EDITAR,
        comando
    )


def boton_buscar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_BUSCAR,
        comando
    )


def boton_eliminar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_ELIMINAR,
        comando
    )


def boton_activar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_ACTIVAR,
        comando
    )


def boton_exportar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_EXPORTAR,
        comando
    )


def boton_importar(ventana, texto, comando):
    return crear_boton(
        ventana,
        texto,
        COLOR_IMPORTAR,
        comando
    )