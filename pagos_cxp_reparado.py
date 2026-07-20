import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# =====================================
# CONEXIÓN
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

conexion = sqlite3.connect(RUTA_DB)
cursor = conexion.cursor()


# =====================================
# FUNCIONES
# =====================================

def cargar_cuentas():
    tabla.delete(*tabla.get_children())

    cursor.execute("""
        SELECT
            id,
            proveedor,
            valor,
            saldo,
            vencimiento,
            estado
        FROM cuentas_pagar
        ORDER BY id DESC
    """)

    for fila in cursor.fetchall():
        tabla.insert("", tk.END, values=fila)


def cargar_bancos():
    cursor.execute("""
        SELECT
            id,
            banco,
            saldo
        FROM bancos
        WHERE estado='ACTIVA'
        ORDER BY banco
    """)

    bancos = cursor.fetchall()

    combo_banco["values"] = [
        f"{fila[0]} - {fila[1]} - ${float(fila[2]):,.0f}"
        for fila in bancos
    ]

    if bancos:
        combo_banco.current(0)


def cargar_historial(cuenta_id):
    tabla_historial.delete(*tabla_historial.get_children())

    cursor.execute("""
        SELECT
            id,
            fecha,
            valor
        FROM pagos_cxp
        WHERE cuenta_id=?
        ORDER BY id DESC
    """, (cuenta_id,))

    for fila in cursor.fetchall():
        tabla_historial.insert("", tk.END, values=fila)


def seleccionar_cuenta(event=None):
    seleccion = tabla.selection()

    if not seleccion:
        return

    datos = tabla.item(seleccion[0])["values"]
    cuenta_id = int(datos[0])

    cargar_historial(cuenta_id)


def registrar_pago():
    seleccion = tabla.selection()

    if not seleccion:
        messagebox.showerror(
            "Error",
            "Seleccione una cuenta por pagar."
        )
        return

    banco_texto = combo_banco.get().strip()

    if banco_texto == "":
        messagebox.showerror(
            "Error",
            "Seleccione un banco."
        )
        return

    try:
        valor_pago = float(entry_pago.get().strip())
    except ValueError:
        messagebox.showerror(
            "Error",
            "Ingrese un valor de pago válido."
        )
        return

    if valor_pago <= 0:
        messagebox.showerror(
            "Error",
            "El valor del pago debe ser mayor que cero."
        )
        return

    try:
        banco_id = int(banco_texto.split(" - ")[0])
    except (ValueError, IndexError):
        messagebox.showerror(
            "Error",
            "No fue posible identificar el banco seleccionado."
        )
        return

    datos = tabla.item(seleccion[0])["values"]
    cuenta_id = int(datos[0])
    proveedor = str(datos[1])

    try:
        cursor.execute("""
            SELECT saldo, estado
            FROM cuentas_pagar
            WHERE id=?
        """, (cuenta_id,))

        cuenta = cursor.fetchone()

        if cuenta is None:
            messagebox.showerror(
                "Error",
                "La cuenta por pagar ya no existe."
            )
            return

        saldo_actual = float(cuenta[0])
        estado_actual = str(cuenta[1])

        if estado_actual == "PAGADA" or saldo_actual <= 0:
            messagebox.showerror(
                "Error",
                "La cuenta seleccionada ya está pagada."
            )
            return

        if valor_pago > saldo_actual:
            messagebox.showerror(
                "Error",
                "El pago supera el saldo pendiente."
            )
            return

        cursor.execute("""
            SELECT banco, saldo
            FROM bancos
            WHERE id=? AND estado='ACTIVA'
        """, (banco_id,))

        banco_db = cursor.fetchone()

        if banco_db is None:
            messagebox.showerror(
                "Error",
                "El banco seleccionado no existe o no está activo."
            )
            return

        nombre_banco = str(banco_db[0])
        saldo_banco_actual = float(banco_db[1])

        if valor_pago > saldo_banco_actual:
            messagebox.showerror(
                "Error",
                "El banco seleccionado no tiene saldo suficiente."
            )
            return

        nuevo_saldo_cxp = saldo_actual - valor_pago
        nuevo_estado = "PENDIENTE"

        if nuevo_saldo_cxp <= 0:
            nuevo_saldo_cxp = 0
            nuevo_estado = "PAGADA"

        nuevo_saldo_banco = saldo_banco_actual - valor_pago
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("BEGIN")

        cursor.execute("""
            INSERT INTO pagos_cxp(
                cuenta_id,
                fecha,
                valor
            )
            VALUES(?,?,?)
        """, (
            cuenta_id,
            fecha,
            valor_pago
        ))

        cursor.execute("""
            UPDATE cuentas_pagar
            SET saldo=?,
                estado=?
            WHERE id=?
        """, (
            nuevo_saldo_cxp,
            nuevo_estado,
            cuenta_id
        ))

        cursor.execute("""
            UPDATE bancos
            SET saldo=?
            WHERE id=?
        """, (
            nuevo_saldo_banco,
            banco_id
        ))

        cursor.execute("""
            INSERT INTO movimientos_bancos(
                fecha,
                banco_id,
                tipo,
                concepto,
                valor,
                saldo_anterior,
                saldo_nuevo,
                autorizado_por
            )
            VALUES(?,?,?,?,?,?,?,?)
        """, (
            fecha,
            banco_id,
            "PAGO CXP",
            f"Pago CxP #{cuenta_id} - {proveedor}",
            valor_pago,
            saldo_banco_actual,
            nuevo_saldo_banco,
            "GERENCIA"
        ))

        conexion.commit()

        messagebox.showinfo(
            "Pago registrado",
            (
                f"Pago realizado desde {nombre_banco}.\n\n"
                f"Valor pagado: ${valor_pago:,.0f}\n"
                f"Saldo CxP: ${nuevo_saldo_cxp:,.0f}\n"
                f"Estado CxP: {nuevo_estado}\n"
                f"Saldo banco: ${nuevo_saldo_banco:,.0f}"
            )
        )

        entry_pago.delete(0, tk.END)
        cargar_cuentas()
        cargar_bancos()
        cargar_historial(cuenta_id)

    except sqlite3.Error as error:
        conexion.rollback()
        messagebox.showerror(
            "Error de base de datos",
            str(error)
        )


# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Pagos CxP")
ventana.geometry("1200x750")


titulo = tk.Label(
    ventana,
    text="PAGOS DE CUENTAS POR PAGAR",
    font=("Arial", 18, "bold")
)
titulo.pack(pady=10)


# =====================================
# TABLA CUENTAS
# =====================================

tabla = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Proveedor",
        "Valor",
        "Saldo",
        "Vencimiento",
        "Estado"
    ),
    show="headings"
)

for col in (
    "ID",
    "Proveedor",
    "Valor",
    "Saldo",
    "Vencimiento",
    "Estado"
):
    tabla.heading(col, text=col)


tabla.column("ID", width=70, anchor="center")
tabla.column("Proveedor", width=250)
tabla.column("Valor", width=130, anchor="e")
tabla.column("Saldo", width=130, anchor="e")
tabla.column("Vencimiento", width=140, anchor="center")
tabla.column("Estado", width=120, anchor="center")

tabla.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

tabla.bind("<<TreeviewSelect>>", seleccionar_cuenta)


# =====================================
# PAGO
# =====================================

frame_pago = tk.Frame(ventana)
frame_pago.pack(pady=10)


tk.Label(
    frame_pago,
    text="Banco"
).pack(side="left")

combo_banco = ttk.Combobox(
    frame_pago,
    width=35,
    state="readonly"
)
combo_banco.pack(side="left", padx=10)


tk.Label(
    frame_pago,
    text="Valor Pago"
).pack(side="left")

entry_pago = tk.Entry(
    frame_pago,
    width=20
)
entry_pago.pack(side="left", padx=10)


tk.Button(
    frame_pago,
    text="Registrar Pago",
    command=registrar_pago
).pack(side="left")


# =====================================
# HISTORIAL
# =====================================

subtitulo = tk.Label(
    ventana,
    text="Historial de Pagos",
    font=("Arial", 12, "bold")
)
subtitulo.pack()


tabla_historial = ttk.Treeview(
    ventana,
    columns=(
        "ID",
        "Fecha",
        "Valor"
    ),
    show="headings"
)

tabla_historial.heading("ID", text="ID")
tabla_historial.heading("Fecha", text="Fecha")
tabla_historial.heading("Valor", text="Valor Pagado")

tabla_historial.column("ID", width=100, anchor="center")
tabla_historial.column("Fecha", width=250, anchor="center")
tabla_historial.column("Valor", width=180, anchor="e")

tabla_historial.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


# =====================================
# INICIO
# =====================================

cargar_bancos()
cargar_cuentas()

ventana.mainloop()
conexion.close()
