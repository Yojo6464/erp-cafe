import tkinter as tk
import sqlite3

# =====================================
# BASE DE DATOS
# =====================================

RUTA_DB = r"C:\Users\jrive\visual\erp_cafe.db"

# =====================================
# FUNCION VALOR
# =====================================

def valor(sql):

    try:

        con = sqlite3.connect(RUTA_DB)
        cur = con.cursor()

        cur.execute(sql)

        dato = cur.fetchone()

        con.close()

        if dato is None:
            return 0

        if dato[0] is None:
            return 0

        return dato[0]

    except:

        return 0

# =====================================
# ACTUALIZAR
# =====================================

def actualizar():

    total_empleados = valor(
        "SELECT COUNT(*) FROM empleados"
    )

    empleados_activos = valor(
        "SELECT COUNT(*) FROM empleados WHERE estado='Activo'"
    )

    nomina_acumulada = valor(
        "SELECT IFNULL(SUM(neto_pagar),0) FROM nomina"
    )

    prestaciones_acumuladas = valor(
        "SELECT IFNULL(SUM(total_prestaciones),0) FROM prestaciones"
    )

    salario_promedio = valor(
        "SELECT IFNULL(AVG(salario),0) FROM empleados"
    )

    costo_total = (
        nomina_acumulada
        + prestaciones_acumuladas
    )

    lbl_total_empleados.config(
        text=str(total_empleados)
    )

    lbl_activos.config(
        text=str(empleados_activos)
    )

    lbl_nomina.config(
        text=f"${nomina_acumulada:,.0f}"
    )

    lbl_prestaciones.config(
        text=f"${prestaciones_acumuladas:,.0f}"
    )

    lbl_costo.config(
        text=f"${costo_total:,.0f}"
    )

    lbl_promedio.config(
        text=f"${salario_promedio:,.0f}"
    )

# =====================================
# VENTANA
# =====================================

ventana = tk.Tk()

ventana.title(
    "ERP Café Alto de la Cruz - Dashboard RRHH V1"
)

ventana.geometry("1100x600")

# =====================================
# TITULO
# =====================================

titulo = tk.Label(
    ventana,
    text="DASHBOARD RECURSOS HUMANOS",
    font=("Arial",24,"bold")
)

titulo.pack(pady=20)

frame = tk.Frame(ventana)

frame.pack(pady=30)

# =====================================
# FILA 1
# =====================================

tk.Label(
    frame,
    text="TOTAL EMPLEADOS",
    font=("Arial",14,"bold")
).grid(row=0,column=0,padx=40,pady=20)

lbl_total_empleados = tk.Label(
    frame,
    text="0",
    font=("Arial",18)
)

lbl_total_empleados.grid(row=1,column=0)

tk.Label(
    frame,
    text="EMPLEADOS ACTIVOS",
    font=("Arial",14,"bold")
).grid(row=0,column=1,padx=40,pady=20)

lbl_activos = tk.Label(
    frame,
    text="0",
    font=("Arial",18)
)

lbl_activos.grid(row=1,column=1)

tk.Label(
    frame,
    text="SALARIO PROMEDIO",
    font=("Arial",14,"bold")
).grid(row=0,column=2,padx=40,pady=20)

lbl_promedio = tk.Label(
    frame,
    text="$0",
    font=("Arial",18)
)

lbl_promedio.grid(row=1,column=2)

# =====================================
# FILA 2
# =====================================

tk.Label(
    frame,
    text="NOMINA ACUMULADA",
    font=("Arial",14,"bold")
).grid(row=2,column=0,padx=40,pady=20)

lbl_nomina = tk.Label(
    frame,
    text="$0",
    font=("Arial",18)
)

lbl_nomina.grid(row=3,column=0)

tk.Label(
    frame,
    text="PRESTACIONES ACUMULADAS",
    font=("Arial",14,"bold")
).grid(row=2,column=1,padx=40,pady=20)

lbl_prestaciones = tk.Label(
    frame,
    text="$0",
    font=("Arial",18)
)

lbl_prestaciones.grid(row=3,column=1)

tk.Label(
    frame,
    text="COSTO TOTAL PERSONAL",
    font=("Arial",14,"bold")
).grid(row=2,column=2,padx=40,pady=20)

lbl_costo = tk.Label(
    frame,
    text="$0",
    font=("Arial",18)
)

lbl_costo.grid(row=3,column=2)

# =====================================
# BOTON
# =====================================

btn_actualizar = tk.Button(
    ventana,
    text="Actualizar Dashboard",
    width=25,
    height=2,
    command=actualizar
)

btn_actualizar.pack(pady=20)

actualizar()

ventana.mainloop()