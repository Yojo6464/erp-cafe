import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

# ============================================================
# ERP CAFÉ ALTO DE LA CRUZ
# ADMINISTRACIÓN DE USUARIOS v1.0
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, "erp_cafe.db")

USUARIO_SESION = os.environ.get("ERP_USUARIO", "")
ROL_SESION = os.environ.get("ERP_ROL", "")

COLOR_FONDO = "#EEF3F8"
COLOR_AZUL = "#0F5C8E"
COLOR_OSCURO = "#153B5B"
COLOR_VERDE = "#15803D"
COLOR_NARANJA = "#C56A00"
COLOR_ROJO = "#B42318"
COLOR_TEXTO = "#1F2937"
COLOR_SUAVE = "#64748B"
COLOR_BLANCO = "#FFFFFF"
COLOR_BORDE = "#D7E0E8"

usuario_seleccionado_id = None


# ============================================================
# BASE DE DATOS Y SEGURIDAD
# ============================================================

def conectar():
    return sqlite3.connect(RUTA_DB, timeout=20)


def inicializar_bd():
    with conectar() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_erp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                clave_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'CONSULTA',
                estado TEXT NOT NULL DEFAULT 'ACTIVO',
                creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TEXT
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS auditoria_erp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT,
                rol TEXT,
                accion TEXT NOT NULL,
                detalle TEXT,
                modulo TEXT
            )
        """)

        conexion.commit()


def generar_hash(clave, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    clave_hash = hashlib.pbkdf2_hmac(
        "sha256",
        clave.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()

    return clave_hash, salt


def registrar_auditoria(conexion, accion, detalle):
    conexion.execute("""
        INSERT INTO auditoria_erp(
            usuario, rol, accion, detalle, modulo
        )
        VALUES (?, ?, ?, ?, 'Usuarios')
    """, (
        USUARIO_SESION or "usuario_local",
        ROL_SESION or "ADMINISTRADOR",
        accion,
        detalle
    ))


def validar_administrador():
    if not ROL_SESION:
        return True

    return ROL_SESION.upper() == "ADMINISTRADOR"


# ============================================================
# UTILIDADES
# ============================================================

def limpiar_formulario():
    global usuario_seleccionado_id

    usuario_seleccionado_id = None

    entry_usuario.config(state="normal")
    entry_usuario.delete(0, "end")

    entry_nombre.delete(0, "end")
    combo_rol.set("CONSULTA")
    combo_estado.set("ACTIVO")

    lbl_modo.config(
        text="NUEVO USUARIO",
        fg=COLOR_VERDE
    )

    entry_usuario.focus_set()


def obtener_datos_formulario():
    usuario = entry_usuario.get().strip().lower()
    nombre = entry_nombre.get().strip()
    rol = combo_rol.get().strip().upper()
    estado = combo_estado.get().strip().upper()

    if not usuario:
        raise ValueError("Ingrese el nombre de usuario.")

    if " " in usuario:
        raise ValueError(
            "El nombre de usuario no debe contener espacios."
        )

    if not nombre:
        raise ValueError("Ingrese el nombre completo.")

    if rol not in ROLES:
        raise ValueError("Seleccione un rol válido.")

    if estado not in ("ACTIVO", "INACTIVO"):
        raise ValueError("Seleccione un estado válido.")

    return usuario, nombre, rol, estado


# ============================================================
# CRUD DE USUARIOS
# ============================================================

def cargar_usuarios():
    criterio = entry_buscar.get().strip()

    sql = """
        SELECT
            id,
            usuario,
            nombre,
            rol,
            estado,
            creado_en,
            COALESCE(ultimo_acceso, '')
        FROM usuarios_erp
        WHERE 1 = 1
    """
    parametros = []

    if criterio:
        patron = f"%{criterio}%"
        sql += """
            AND (
                usuario LIKE ?
                OR nombre LIKE ?
                OR rol LIKE ?
                OR estado LIKE ?
            )
        """
        parametros.extend([patron, patron, patron, patron])

    sql += " ORDER BY nombre, usuario"

    with conectar() as conexion:
        filas = conexion.execute(sql, parametros).fetchall()

    tabla.delete(*tabla.get_children())

    for fila in filas:
        tag = (
            "inactivo"
            if str(fila[4]).upper() == "INACTIVO"
            else "activo"
        )

        tabla.insert(
            "",
            "end",
            iid=str(fila[0]),
            values=(
                fila[1],
                fila[2],
                fila[3],
                fila[4],
                fila[5],
                fila[6]
            ),
            tags=(tag,)
        )

    actualizar_indicadores()


def actualizar_indicadores():
    with conectar() as conexion:
        total = conexion.execute("""
            SELECT COUNT(*) FROM usuarios_erp
        """).fetchone()[0]

        activos = conexion.execute("""
            SELECT COUNT(*)
            FROM usuarios_erp
            WHERE UPPER(estado) = 'ACTIVO'
        """).fetchone()[0]

        administradores = conexion.execute("""
            SELECT COUNT(*)
            FROM usuarios_erp
            WHERE UPPER(rol) = 'ADMINISTRADOR'
              AND UPPER(estado) = 'ACTIVO'
        """).fetchone()[0]

        ingresos_hoy = conexion.execute("""
            SELECT COUNT(*)
            FROM usuarios_erp
            WHERE date(ultimo_acceso) = date('now', 'localtime')
        """).fetchone()[0]

    lbl_total.config(text=str(total))
    lbl_activos.config(text=str(activos))
    lbl_admin.config(text=str(administradores))
    lbl_ingresos.config(text=str(ingresos_hoy))


def crear_usuario():
    try:
        usuario, nombre, rol, estado = obtener_datos_formulario()
    except ValueError as error:
        messagebox.showerror("Usuario", str(error))
        return

    clave = simpledialog.askstring(
        "Contraseña inicial",
        "Ingrese la contraseña inicial.\n"
        "Debe tener mínimo 6 caracteres:",
        show="*",
        parent=ventana
    )

    if clave is None:
        return

    if len(clave) < 6:
        messagebox.showerror(
            "Usuario",
            "La contraseña debe tener mínimo 6 caracteres."
        )
        return

    confirmacion = simpledialog.askstring(
        "Confirmar contraseña",
        "Repita la contraseña:",
        show="*",
        parent=ventana
    )

    if confirmacion is None:
        return

    if clave != confirmacion:
        messagebox.showerror(
            "Usuario",
            "Las contraseñas no coinciden."
        )
        return

    clave_hash, salt = generar_hash(clave)
    conexion = conectar()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        conexion.execute("""
            INSERT INTO usuarios_erp(
                usuario, nombre, clave_hash, salt, rol, estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            usuario,
            nombre,
            clave_hash,
            salt,
            rol,
            estado
        ))

        registrar_auditoria(
            conexion,
            "CREAR USUARIO",
            f"Usuario: {usuario}; nombre: {nombre}; rol: {rol}"
        )

        conexion.commit()

        messagebox.showinfo(
            "Usuario",
            "Usuario creado correctamente."
        )

        limpiar_formulario()
        cargar_usuarios()

    except sqlite3.IntegrityError:
        conexion.rollback()
        messagebox.showerror(
            "Usuario",
            "Ese nombre de usuario ya existe."
        )

    except Exception as error:
        conexion.rollback()
        messagebox.showerror(
            "Usuario",
            f"No fue posible crear el usuario.\n\n{error}"
        )

    finally:
        conexion.close()


def seleccionar_usuario(evento=None):
    global usuario_seleccionado_id

    seleccion = tabla.selection()
    if not seleccion:
        return

    usuario_seleccionado_id = int(seleccion[0])
    valores = tabla.item(seleccion[0], "values")

    entry_usuario.config(state="normal")
    entry_usuario.delete(0, "end")
    entry_usuario.insert(0, valores[0])
    entry_usuario.config(state="readonly")

    entry_nombre.delete(0, "end")
    entry_nombre.insert(0, valores[1])

    combo_rol.set(valores[2])
    combo_estado.set(valores[3])

    lbl_modo.config(
        text=f"EDITANDO: {valores[0]}",
        fg=COLOR_NARANJA
    )


def actualizar_usuario():
    if usuario_seleccionado_id is None:
        messagebox.showwarning(
            "Usuario",
            "Seleccione un usuario de la tabla."
        )
        return

    try:
        usuario, nombre, rol, estado = obtener_datos_formulario()
    except ValueError as error:
        messagebox.showerror("Usuario", str(error))
        return

    with conectar() as conexion:
        actual = conexion.execute("""
            SELECT usuario, rol, estado
            FROM usuarios_erp
            WHERE id = ?
        """, (usuario_seleccionado_id,)).fetchone()

    if not actual:
        messagebox.showerror(
            "Usuario",
            "No se encontró el usuario."
        )
        return

    if (
        actual[0].lower() == USUARIO_SESION.lower()
        and estado == "INACTIVO"
    ):
        messagebox.showerror(
            "Usuario",
            "No puede inactivar el usuario de la sesión actual."
        )
        return

    if (
        str(actual[1]).upper() == "ADMINISTRADOR"
        and rol != "ADMINISTRADOR"
    ):
        with conectar() as conexion:
            administradores = conexion.execute("""
                SELECT COUNT(*)
                FROM usuarios_erp
                WHERE UPPER(rol) = 'ADMINISTRADOR'
                  AND UPPER(estado) = 'ACTIVO'
            """).fetchone()[0]

        if administradores <= 1:
            messagebox.showerror(
                "Usuario",
                "Debe conservar al menos un administrador activo."
            )
            return

    conexion = conectar()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        conexion.execute("""
            UPDATE usuarios_erp
            SET nombre = ?,
                rol = ?,
                estado = ?
            WHERE id = ?
        """, (
            nombre,
            rol,
            estado,
            usuario_seleccionado_id
        ))

        registrar_auditoria(
            conexion,
            "ACTUALIZAR USUARIO",
            (
                f"Usuario: {usuario}; nombre: {nombre}; "
                f"rol: {rol}; estado: {estado}"
            )
        )

        conexion.commit()

        messagebox.showinfo(
            "Usuario",
            "Usuario actualizado correctamente."
        )

        limpiar_formulario()
        cargar_usuarios()

    except Exception as error:
        conexion.rollback()
        messagebox.showerror(
            "Usuario",
            f"No fue posible actualizar el usuario.\n\n{error}"
        )

    finally:
        conexion.close()


def cambiar_contrasena():
    if usuario_seleccionado_id is None:
        messagebox.showwarning(
            "Contraseña",
            "Seleccione un usuario."
        )
        return

    usuario = tabla.item(
        str(usuario_seleccionado_id),
        "values"
    )[0]

    nueva_clave = simpledialog.askstring(
        "Cambiar contraseña",
        f"Nueva contraseña para '{usuario}':",
        show="*",
        parent=ventana
    )

    if nueva_clave is None:
        return

    if len(nueva_clave) < 6:
        messagebox.showerror(
            "Contraseña",
            "La contraseña debe tener mínimo 6 caracteres."
        )
        return

    confirmacion = simpledialog.askstring(
        "Confirmar contraseña",
        "Repita la nueva contraseña:",
        show="*",
        parent=ventana
    )

    if confirmacion is None:
        return

    if nueva_clave != confirmacion:
        messagebox.showerror(
            "Contraseña",
            "Las contraseñas no coinciden."
        )
        return

    clave_hash, salt = generar_hash(nueva_clave)
    conexion = conectar()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        conexion.execute("""
            UPDATE usuarios_erp
            SET clave_hash = ?,
                salt = ?,
                estado = 'ACTIVO'
            WHERE id = ?
        """, (
            clave_hash,
            salt,
            usuario_seleccionado_id
        ))

        registrar_auditoria(
            conexion,
            "CAMBIAR CONTRASEÑA",
            f"Usuario: {usuario}"
        )

        conexion.commit()

        messagebox.showinfo(
            "Contraseña",
            "Contraseña actualizada correctamente."
        )

        cargar_usuarios()

    except Exception as error:
        conexion.rollback()
        messagebox.showerror(
            "Contraseña",
            f"No fue posible cambiar la contraseña.\n\n{error}"
        )

    finally:
        conexion.close()


def cambiar_estado():
    if usuario_seleccionado_id is None:
        messagebox.showwarning(
            "Estado",
            "Seleccione un usuario."
        )
        return

    valores = tabla.item(
        str(usuario_seleccionado_id),
        "values"
    )

    usuario = valores[0]
    estado_actual = str(valores[3]).upper()
    nuevo_estado = (
        "INACTIVO"
        if estado_actual == "ACTIVO"
        else "ACTIVO"
    )

    if (
        usuario.lower() == USUARIO_SESION.lower()
        and nuevo_estado == "INACTIVO"
    ):
        messagebox.showerror(
            "Estado",
            "No puede inactivar el usuario de la sesión actual."
        )
        return

    if (
        str(valores[2]).upper() == "ADMINISTRADOR"
        and nuevo_estado == "INACTIVO"
    ):
        with conectar() as conexion:
            administradores = conexion.execute("""
                SELECT COUNT(*)
                FROM usuarios_erp
                WHERE UPPER(rol) = 'ADMINISTRADOR'
                  AND UPPER(estado) = 'ACTIVO'
            """).fetchone()[0]

        if administradores <= 1:
            messagebox.showerror(
                "Estado",
                "Debe conservar al menos un administrador activo."
            )
            return

    if not messagebox.askyesno(
        "Confirmar estado",
        f"¿Desea cambiar el usuario '{usuario}' "
        f"a estado {nuevo_estado}?"
    ):
        return

    conexion = conectar()

    try:
        conexion.execute("BEGIN IMMEDIATE")

        conexion.execute("""
            UPDATE usuarios_erp
            SET estado = ?
            WHERE id = ?
        """, (
            nuevo_estado,
            usuario_seleccionado_id
        ))

        registrar_auditoria(
            conexion,
            "CAMBIAR ESTADO USUARIO",
            f"Usuario: {usuario}; estado: {nuevo_estado}"
        )

        conexion.commit()

        messagebox.showinfo(
            "Estado",
            f"Usuario actualizado a {nuevo_estado}."
        )

        limpiar_formulario()
        cargar_usuarios()

    except Exception as error:
        conexion.rollback()
        messagebox.showerror(
            "Estado",
            f"No fue posible cambiar el estado.\n\n{error}"
        )

    finally:
        conexion.close()


def ver_auditoria_usuario():
    if usuario_seleccionado_id is None:
        messagebox.showwarning(
            "Auditoría",
            "Seleccione un usuario."
        )
        return

    usuario = tabla.item(
        str(usuario_seleccionado_id),
        "values"
    )[0]

    with conectar() as conexion:
        filas = conexion.execute("""
            SELECT
                fecha_hora,
                accion,
                modulo,
                detalle
            FROM auditoria_erp
            WHERE LOWER(usuario) = LOWER(?)
            ORDER BY id DESC
            LIMIT 200
        """, (usuario,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title(f"Auditoría - {usuario}")
    top.geometry("1050x600")
    top.configure(bg=COLOR_FONDO)

    tk.Label(
        top,
        text=f"AUDITORÍA DEL USUARIO: {usuario}",
        bg=COLOR_OSCURO,
        fg="white",
        font=("Segoe UI", 15, "bold"),
        pady=14
    ).pack(fill="x")

    columnas = (
        "FechaHora",
        "Accion",
        "Modulo",
        "Detalle"
    )

    tabla_auditoria = ttk.Treeview(
        top,
        columns=columnas,
        show="headings"
    )

    tabla_auditoria.heading(
        "FechaHora",
        text="Fecha y hora"
    )
    tabla_auditoria.heading(
        "Accion",
        text="Acción"
    )
    tabla_auditoria.heading(
        "Modulo",
        text="Módulo"
    )
    tabla_auditoria.heading(
        "Detalle",
        text="Detalle"
    )

    tabla_auditoria.column(
        "FechaHora",
        width=160
    )
    tabla_auditoria.column(
        "Accion",
        width=210
    )
    tabla_auditoria.column(
        "Modulo",
        width=140
    )
    tabla_auditoria.column(
        "Detalle",
        width=500
    )

    tabla_auditoria.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=15
    )

    for fila in filas:
        tabla_auditoria.insert(
            "",
            "end",
            values=fila
        )


# ============================================================
# INTERFAZ
# ============================================================

ROLES = (
    "ADMINISTRADOR",
    "GERENCIA",
    "COMPRAS",
    "PRODUCCIÓN",
    "INVENTARIO",
    "VENTAS",
    "TESORERÍA",
    "CONTABILIDAD",
    "CONSULTA"
)

inicializar_bd()

ventana = tk.Tk()
ventana.title(
    "ERP Café Alto de la Cruz - Administración de Usuarios"
)
ventana.geometry("1350x800")
ventana.minsize(1100, 680)
ventana.configure(bg=COLOR_FONDO)

try:
    ventana.state("zoomed")
except tk.TclError:
    pass

if not validar_administrador():
    messagebox.showerror(
        "Acceso denegado",
        "Solo un usuario con rol ADMINISTRADOR puede "
        "administrar usuarios."
    )
    ventana.destroy()
    raise SystemExit

estilo = ttk.Style()
try:
    estilo.theme_use("clam")
except tk.TclError:
    pass

estilo.configure(
    "Treeview",
    rowheight=28,
    font=("Segoe UI", 9)
)
estilo.configure(
    "Treeview.Heading",
    font=("Segoe UI", 9, "bold")
)

header = tk.Frame(
    ventana,
    bg=COLOR_OSCURO,
    height=82
)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="ADMINISTRACIÓN DE USUARIOS",
    font=("Segoe UI", 22, "bold"),
    bg=COLOR_OSCURO,
    fg="white"
).pack(
    side="left",
    padx=24,
    pady=20
)

tk.Label(
    header,
    text=(
        f"Sesión: {USUARIO_SESION or 'local'} | "
        f"Rol: {ROL_SESION or 'ADMINISTRADOR'}"
    ),
    font=("Segoe UI", 9),
    bg=COLOR_OSCURO,
    fg="#BFDBFE"
).pack(
    side="right",
    padx=24
)

# Indicadores
panel_kpi = tk.Frame(
    ventana,
    bg=COLOR_FONDO
)
panel_kpi.pack(
    fill="x",
    padx=18,
    pady=(14, 5)
)

for columna in range(4):
    panel_kpi.grid_columnconfigure(
        columna,
        weight=1
    )


def crear_kpi(columna, titulo, color):
    marco = tk.Frame(
        panel_kpi,
        bg=COLOR_BLANCO,
        highlightbackground=COLOR_BORDE,
        highlightthickness=1
    )
    marco.grid(
        row=0,
        column=columna,
        sticky="ew",
        padx=6
    )

    tk.Frame(
        marco,
        bg=color,
        width=5
    ).pack(
        side="left",
        fill="y"
    )

    interno = tk.Frame(
        marco,
        bg=COLOR_BLANCO
    )
    interno.pack(
        fill="both",
        expand=True,
        padx=14,
        pady=10
    )

    tk.Label(
        interno,
        text=titulo,
        bg=COLOR_BLANCO,
        fg=COLOR_SUAVE,
        font=("Segoe UI", 8, "bold")
    ).pack(anchor="w")

    valor = tk.Label(
        interno,
        text="0",
        bg=COLOR_BLANCO,
        fg=COLOR_TEXTO,
        font=("Segoe UI", 16, "bold")
    )
    valor.pack(
        anchor="w",
        pady=(3, 0)
    )

    return valor


lbl_total = crear_kpi(
    0,
    "USUARIOS REGISTRADOS",
    COLOR_AZUL
)
lbl_activos = crear_kpi(
    1,
    "USUARIOS ACTIVOS",
    COLOR_VERDE
)
lbl_admin = crear_kpi(
    2,
    "ADMINISTRADORES",
    "#7C3AED"
)
lbl_ingresos = crear_kpi(
    3,
    "INGRESOS HOY",
    COLOR_NARANJA
)

# Formulario
formulario = tk.LabelFrame(
    ventana,
    text="DATOS DEL USUARIO",
    bg=COLOR_BLANCO,
    fg=COLOR_TEXTO,
    font=("Segoe UI", 10, "bold"),
    padx=14,
    pady=12
)
formulario.pack(
    fill="x",
    padx=18,
    pady=10
)

for columna in range(5):
    formulario.grid_columnconfigure(
        columna,
        weight=1
    )

tk.Label(
    formulario,
    text="Usuario",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE
).grid(
    row=0,
    column=0,
    sticky="w"
)

entry_usuario = ttk.Entry(
    formulario
)
entry_usuario.grid(
    row=1,
    column=0,
    sticky="ew",
    padx=(0, 10)
)

tk.Label(
    formulario,
    text="Nombre completo",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE
).grid(
    row=0,
    column=1,
    sticky="w"
)

entry_nombre = ttk.Entry(
    formulario
)
entry_nombre.grid(
    row=1,
    column=1,
    columnspan=2,
    sticky="ew",
    padx=(0, 10)
)

tk.Label(
    formulario,
    text="Rol",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE
).grid(
    row=0,
    column=3,
    sticky="w"
)

combo_rol = ttk.Combobox(
    formulario,
    values=ROLES,
    state="readonly"
)
combo_rol.grid(
    row=1,
    column=3,
    sticky="ew",
    padx=(0, 10)
)

tk.Label(
    formulario,
    text="Estado",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE
).grid(
    row=0,
    column=4,
    sticky="w"
)

combo_estado = ttk.Combobox(
    formulario,
    values=["ACTIVO", "INACTIVO"],
    state="readonly"
)
combo_estado.grid(
    row=1,
    column=4,
    sticky="ew"
)

lbl_modo = tk.Label(
    formulario,
    text="NUEVO USUARIO",
    bg=COLOR_BLANCO,
    fg=COLOR_VERDE,
    font=("Segoe UI", 9, "bold")
)
lbl_modo.grid(
    row=2,
    column=0,
    sticky="w",
    pady=(12, 0)
)

botones = tk.Frame(
    formulario,
    bg=COLOR_BLANCO
)
botones.grid(
    row=2,
    column=1,
    columnspan=4,
    sticky="e",
    pady=(12, 0)
)

tk.Button(
    botones,
    text="Crear usuario",
    command=crear_usuario,
    bg=COLOR_VERDE,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).pack(
    side="left",
    padx=4
)

tk.Button(
    botones,
    text="Actualizar datos",
    command=actualizar_usuario,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).pack(
    side="left",
    padx=4
)

tk.Button(
    botones,
    text="Cambiar contraseña",
    command=cambiar_contrasena,
    bg="#7C3AED",
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).pack(
    side="left",
    padx=4
)

tk.Button(
    botones,
    text="Activar / Inactivar",
    command=cambiar_estado,
    bg=COLOR_NARANJA,
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).pack(
    side="left",
    padx=4
)

tk.Button(
    botones,
    text="Limpiar",
    command=limpiar_formulario,
    bg="#475569",
    fg="white",
    relief="flat",
    font=("Segoe UI", 9, "bold"),
    cursor="hand2",
    padx=16,
    pady=7
).pack(
    side="left",
    padx=4
)

# Búsqueda
busqueda = tk.Frame(
    ventana,
    bg=COLOR_BLANCO
)
busqueda.pack(
    fill="x",
    padx=18,
    pady=(0, 8)
)

tk.Label(
    busqueda,
    text="Buscar:",
    bg=COLOR_BLANCO,
    fg=COLOR_TEXTO
).pack(
    side="left",
    padx=(12, 5),
    pady=10
)

entry_buscar = ttk.Entry(
    busqueda,
    width=35
)
entry_buscar.pack(
    side="left",
    padx=5
)
entry_buscar.bind(
    "<Return>",
    lambda evento: cargar_usuarios()
)

tk.Button(
    busqueda,
    text="Buscar",
    command=cargar_usuarios,
    bg=COLOR_AZUL,
    fg="white",
    relief="flat",
    cursor="hand2",
    padx=14,
    pady=6
).pack(
    side="left",
    padx=5
)

tk.Button(
    busqueda,
    text="Ver auditoría seleccionada",
    command=ver_auditoria_usuario,
    bg=COLOR_OSCURO,
    fg="white",
    relief="flat",
    cursor="hand2",
    padx=14,
    pady=6
).pack(
    side="right",
    padx=12
)

# Tabla
columnas = (
    "Usuario",
    "Nombre",
    "Rol",
    "Estado",
    "Creado",
    "UltimoAcceso"
)

tabla = ttk.Treeview(
    ventana,
    columns=columnas,
    show="headings"
)

tabla.heading(
    "Usuario",
    text="Usuario"
)
tabla.heading(
    "Nombre",
    text="Nombre completo"
)
tabla.heading(
    "Rol",
    text="Rol"
)
tabla.heading(
    "Estado",
    text="Estado"
)
tabla.heading(
    "Creado",
    text="Creado"
)
tabla.heading(
    "UltimoAcceso",
    text="Último acceso"
)

tabla.column(
    "Usuario",
    width=160
)
tabla.column(
    "Nombre",
    width=280
)
tabla.column(
    "Rol",
    width=160,
    anchor="center"
)
tabla.column(
    "Estado",
    width=110,
    anchor="center"
)
tabla.column(
    "Creado",
    width=170,
    anchor="center"
)
tabla.column(
    "UltimoAcceso",
    width=170,
    anchor="center"
)

tabla.pack(
    fill="both",
    expand=True,
    padx=18,
    pady=(0, 12)
)

tabla.tag_configure(
    "activo",
    foreground=COLOR_VERDE
)
tabla.tag_configure(
    "inactivo",
    foreground=COLOR_ROJO
)

tabla.bind(
    "<<TreeviewSelect>>",
    seleccionar_usuario
)

barra_estado = tk.Frame(
    ventana,
    bg=COLOR_BLANCO,
    height=28
)
barra_estado.pack(fill="x")

tk.Label(
    barra_estado,
    text=f"Base de datos: {RUTA_DB}",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(
    side="left",
    padx=12
)

tk.Label(
    barra_estado,
    text="Administración de Usuarios v1.0",
    bg=COLOR_BLANCO,
    fg=COLOR_SUAVE,
    font=("Segoe UI", 8)
).pack(
    side="right",
    padx=12
)

limpiar_formulario()
cargar_usuarios()
ventana.mainloop()
