import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, "erp_cafe.db")

C_FONDO = "#EEF3F8"
C_AZUL = "#0F5C8E"
C_OSCURO = "#153B5B"
C_VERDE = "#15803D"
C_NARANJA = "#C56A00"
C_ROJO = "#B42318"
C_TEXTO = "#1F2937"
C_SUAVE = "#64748B"
C_BLANCO = "#FFFFFF"
C_BORDE = "#D7E0E8"

detalle_receta = []


def conectar():
    con = sqlite3.connect(RUTA_DB, timeout=20)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar_bd():
    with conectar() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS recetas_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            producto_terminado TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            cantidad_base REAL NOT NULL DEFAULT 1,
            unidad_base TEXT DEFAULT 'UND',
            estado TEXT DEFAULT 'ACTIVA',
            observaciones TEXT DEFAULT '',
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recetas_detalle(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receta_id INTEGER NOT NULL,
            materia_prima TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT DEFAULT '',
            FOREIGN KEY(receta_id) REFERENCES recetas_produccion(id)
        );

        CREATE TABLE IF NOT EXISTS ordenes_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            fecha TEXT NOT NULL,
            receta_id INTEGER NOT NULL,
            producto_terminado TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            cantidad_programada REAL NOT NULL,
            cantidad_producida REAL DEFAULT 0,
            lote_producto TEXT NOT NULL,
            responsable TEXT DEFAULT '',
            mano_obra REAL DEFAULT 0,
            energia REAL DEFAULT 0,
            gas REAL DEFAULT 0,
            costos_indirectos REAL DEFAULT 0,
            costo_materiales REAL DEFAULT 0,
            costo_total REAL DEFAULT 0,
            costo_unitario REAL DEFAULT 0,
            estado TEXT DEFAULT 'PENDIENTE',
            observaciones TEXT DEFAULT '',
            creada_en TEXT DEFAULT CURRENT_TIMESTAMP,
            cerrada_en TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS consumos_produccion(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            producto TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            lote TEXT DEFAULT '',
            cantidad REAL NOT NULL,
            costo_unitario REAL DEFAULT 0,
            costo_total REAL DEFAULT 0,
            FOREIGN KEY(orden_id) REFERENCES ordenes_produccion(id)
        );

        CREATE TABLE IF NOT EXISTS inventario(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            presentacion TEXT,
            cantidad REAL DEFAULT 0,
            lote TEXT DEFAULT '',
            costo_unitario REAL DEFAULT 0,
            fecha_ingreso TEXT DEFAULT '',
            numero_despacho TEXT DEFAULT '',
            stock_minimo INTEGER DEFAULT 0,
            costo REAL DEFAULT 0,
            fecha TEXT DEFAULT '',
            despacho TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS kardex(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            producto TEXT,
            presentacion TEXT,
            movimiento TEXT,
            entrada REAL DEFAULT 0,
            salida REAL DEFAULT 0,
            saldo REAL DEFAULT 0,
            costo_unitario REAL DEFAULT 0,
            lote TEXT DEFAULT '',
            origen TEXT DEFAULT '',
            observaciones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS auditoria_erp(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            rol TEXT,
            accion TEXT NOT NULL,
            detalle TEXT,
            modulo TEXT
        );
        """)
        con.commit()


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hoy():
    return datetime.now().strftime("%Y-%m-%d")


def moneda(v):
    return f"${float(v or 0):,.0f}"


def num(v):
    return f"{float(v or 0):,.2f}"


def validar_numero(valor, nombre, cero=False):
    try:
        n = float(str(valor).replace(",", "").strip())
    except ValueError:
        raise ValueError(f"{nombre} debe ser numérico.")
    if cero:
        if n < 0:
            raise ValueError(f"{nombre} no puede ser negativo.")
    elif n <= 0:
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return n


def auditoria(con, accion, detalle):
    con.execute("""
        INSERT INTO auditoria_erp(usuario, rol, accion, detalle, modulo)
        VALUES(?,?,?,?,?)
    """, (
        os.environ.get("ERP_USUARIO", "usuario_local"),
        os.environ.get("ERP_ROL", "OPERADOR"),
        accion, detalle, "Producción"
    ))


def codigo_receta():
    with conectar() as con:
        n = con.execute("SELECT IFNULL(MAX(id),0)+1 FROM recetas_produccion").fetchone()[0]
    return f"REC-{int(n):05d}"


def numero_orden():
    with conectar() as con:
        n = con.execute("SELECT IFNULL(MAX(id),0)+1 FROM ordenes_produccion").fetchone()[0]
    return f"OP-{datetime.now().strftime('%Y%m%d')}-{int(n):05d}"


def lote_producto():
    with conectar() as con:
        n = con.execute("SELECT IFNULL(MAX(id),0)+1 FROM ordenes_produccion").fetchone()[0]
    return f"PT-{datetime.now().strftime('%Y%m%d')}-{int(n):05d}"


def registrar_kardex(con, producto, presentacion, lote, movimiento, entrada, salida, costo, origen, obs):
    saldo = con.execute("""
        SELECT IFNULL(SUM(entrada-salida),0)
        FROM kardex
        WHERE producto=? AND presentacion=? AND COALESCE(lote,'')=?
    """, (producto, presentacion, lote)).fetchone()[0]
    saldo_nuevo = float(saldo or 0) + entrada - salida
    con.execute("""
        INSERT INTO kardex(
            fecha, producto, presentacion, movimiento,
            entrada, salida, saldo, costo_unitario,
            lote, origen, observaciones
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (ahora(), producto, presentacion, movimiento, entrada, salida,
          saldo_nuevo, costo, lote, origen, obs))


def cargar_catalogos():
    with conectar() as con:
        productos = [r[0] for r in con.execute("""
            SELECT DISTINCT producto FROM inventario
            WHERE TRIM(COALESCE(producto,''))<>''
            ORDER BY producto
        """).fetchall()]
        recetas = con.execute("""
            SELECT id,codigo,producto_terminado,presentacion
            FROM recetas_produccion
            WHERE UPPER(estado)='ACTIVA'
            ORDER BY producto_terminado,presentacion
        """).fetchall()
    cmb_mp["values"] = productos
    cmb_receta["values"] = [f"{r[0]} | {r[1]} | {r[2]} | {r[3]}" for r in recetas]


def cargar_presentaciones(event=None):
    producto = cmb_mp.get().strip()
    with conectar() as con:
        pres = [r[0] for r in con.execute("""
            SELECT DISTINCT presentacion FROM inventario
            WHERE producto=? ORDER BY presentacion
        """, (producto,)).fetchall()]
    cmb_mp_pres["values"] = pres


def limpiar_receta():
    global detalle_receta
    detalle_receta = []
    ent_codigo.config(state="normal")
    ent_codigo.delete(0, "end")
    ent_codigo.insert(0, codigo_receta())
    ent_codigo.config(state="readonly")
    ent_pt.delete(0, "end")
    ent_pt_pres.delete(0, "end")
    ent_base.delete(0, "end")
    ent_base.insert(0, "1")
    cmb_base_unidad.set("UND")
    txt_rec_obs.delete("1.0", "end")
    cmb_mp.set("")
    cmb_mp_pres.set("")
    ent_mp_cant.delete(0, "end")
    cmb_mp_unidad.set("UND")
    mostrar_detalle_receta()


def mostrar_detalle_receta():
    tv_receta.delete(*tv_receta.get_children())
    for i, item in enumerate(detalle_receta, 1):
        tv_receta.insert("", "end", iid=str(i-1), values=(
            i, item["producto"], item["presentacion"],
            num(item["cantidad"]), item["unidad"]
        ))


def agregar_insumo():
    producto = cmb_mp.get().strip()
    presentacion = cmb_mp_pres.get().strip()
    unidad = cmb_mp_unidad.get().strip()
    if not producto or not presentacion:
        messagebox.showerror("Receta", "Ingrese materia prima y presentación.")
        return
    try:
        cantidad = validar_numero(ent_mp_cant.get(), "Cantidad")
    except ValueError as e:
        messagebox.showerror("Receta", str(e))
        return
    detalle_receta.append({
        "producto": producto,
        "presentacion": presentacion,
        "cantidad": cantidad,
        "unidad": unidad
    })
    mostrar_detalle_receta()
    cmb_mp.set("")
    cmb_mp_pres.set("")
    ent_mp_cant.delete(0, "end")


def eliminar_insumo():
    sel = tv_receta.selection()
    if not sel:
        messagebox.showwarning("Receta", "Seleccione un insumo.")
        return
    detalle_receta.pop(int(sel[0]))
    mostrar_detalle_receta()


def guardar_receta():
    producto = ent_pt.get().strip()
    presentacion = ent_pt_pres.get().strip()
    if not producto or not presentacion:
        messagebox.showerror("Receta", "Ingrese producto terminado y presentación.")
        return
    try:
        base = validar_numero(ent_base.get(), "Cantidad base")
    except ValueError as e:
        messagebox.showerror("Receta", str(e))
        return
    if not detalle_receta:
        messagebox.showerror("Receta", "Agregue al menos un insumo.")
        return

    con = conectar()
    try:
        con.execute("BEGIN IMMEDIATE")
        cur = con.execute("""
            INSERT INTO recetas_produccion(
                codigo,producto_terminado,presentacion,cantidad_base,
                unidad_base,estado,observaciones
            ) VALUES(?,?,?,?,?,'ACTIVA',?)
        """, (
            ent_codigo.get().strip(), producto, presentacion, base,
            cmb_base_unidad.get().strip(),
            txt_rec_obs.get("1.0", "end").strip()
        ))
        receta_id = cur.lastrowid
        for item in detalle_receta:
            con.execute("""
                INSERT INTO recetas_detalle(
                    receta_id,materia_prima,presentacion,cantidad,unidad
                ) VALUES(?,?,?,?,?)
            """, (
                receta_id, item["producto"], item["presentacion"],
                item["cantidad"], item["unidad"]
            ))
        auditoria(con, "CREAR RECETA",
                  f"{ent_codigo.get().strip()} - {producto}/{presentacion}")
        con.commit()
        messagebox.showinfo("Receta", "Receta creada correctamente.")
        limpiar_receta()
        cargar_recetas()
        cargar_catalogos()
    except Exception as e:
        con.rollback()
        messagebox.showerror("Receta", f"No se pudo guardar.\n\n{e}")
    finally:
        con.close()


def cargar_recetas():
    with conectar() as con:
        filas = con.execute("""
            SELECT codigo,producto_terminado,presentacion,cantidad_base,
                   unidad_base,estado
            FROM recetas_produccion ORDER BY id DESC
        """).fetchall()
    tv_recetas.delete(*tv_recetas.get_children())
    for f in filas:
        tv_recetas.insert("", "end", values=(f[0],f[1],f[2],num(f[3]),f[4],f[5]))


def receta_id_actual():
    valor = cmb_receta.get().strip()
    if not valor:
        return None
    try:
        return int(valor.split("|")[0].strip())
    except Exception:
        return None


def cargar_receta_orden(event=None):
    rid = receta_id_actual()
    if not rid:
        return
    with conectar() as con:
        r = con.execute("""
            SELECT producto_terminado,presentacion,cantidad_base,unidad_base
            FROM recetas_produccion WHERE id=?
        """, (rid,)).fetchone()
    if r:
        lbl_prod_orden.config(text=f"{r[0]} / {r[1]}")
        lbl_base_orden.config(text=f"Base: {num(r[2])} {r[3]}")
    calcular_requerimientos()


def calcular_requerimientos(event=None):
    rid = receta_id_actual()
    tv_req.delete(*tv_req.get_children())
    if not rid:
        return
    try:
        programada = validar_numero(ent_programada.get() or 0, "Cantidad programada")
    except ValueError:
        return
    with conectar() as con:
        base = con.execute("SELECT cantidad_base FROM recetas_produccion WHERE id=?",(rid,)).fetchone()
        detalles = con.execute("""
            SELECT materia_prima,presentacion,cantidad,unidad
            FROM recetas_detalle WHERE receta_id=? ORDER BY id
        """,(rid,)).fetchall()
        factor = programada / float(base[0] or 1)
        for i,d in enumerate(detalles,1):
            requerida = float(d[2]) * factor
            disponible = con.execute("""
                SELECT IFNULL(SUM(cantidad),0) FROM inventario
                WHERE producto=? AND presentacion=?
            """,(d[0],d[1])).fetchone()[0]
            estado = "OK" if float(disponible or 0) >= requerida else "FALTANTE"
            tv_req.insert("", "end", values=(
                i,d[0],d[1],num(requerida),d[3],num(disponible),estado
            ), tags=("ok" if estado=="OK" else "faltante",))


def limpiar_orden():
    cmb_receta.set("")
    ent_fecha.delete(0,"end"); ent_fecha.insert(0,hoy())
    ent_programada.delete(0,"end")
    ent_lote.delete(0,"end"); ent_lote.insert(0,lote_producto())
    ent_responsable.delete(0,"end")
    for e in (ent_mo,ent_energia,ent_gas,ent_indirectos):
        e.delete(0,"end"); e.insert(0,"0")
    txt_op_obs.delete("1.0","end")
    lbl_num_op.config(text=numero_orden())
    lbl_prod_orden.config(text="Seleccione una receta")
    lbl_base_orden.config(text="")
    tv_req.delete(*tv_req.get_children())


def crear_orden():
    rid = receta_id_actual()
    if not rid:
        messagebox.showerror("Orden", "Seleccione una receta.")
        return
    try:
        programada = validar_numero(ent_programada.get(), "Cantidad programada")
        mo = validar_numero(ent_mo.get() or 0, "Mano de obra", True)
        energia = validar_numero(ent_energia.get() or 0, "Energía", True)
        gas = validar_numero(ent_gas.get() or 0, "Gas", True)
        indirectos = validar_numero(ent_indirectos.get() or 0, "Indirectos", True)
        datetime.strptime(ent_fecha.get().strip(), "%Y-%m-%d")
    except ValueError as e:
        messagebox.showerror("Orden", str(e))
        return
    if not ent_lote.get().strip():
        messagebox.showerror("Orden", "Ingrese el lote.")
        return

    with conectar() as con:
        receta = con.execute("""
            SELECT producto_terminado,presentacion
            FROM recetas_produccion WHERE id=?
        """,(rid,)).fetchone()

    con = conectar()
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute("""
            INSERT INTO ordenes_produccion(
                numero,fecha,receta_id,producto_terminado,presentacion,
                cantidad_programada,lote_producto,responsable,
                mano_obra,energia,gas,costos_indirectos,estado,observaciones
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'PENDIENTE',?)
        """,(
            lbl_num_op.cget("text"), ent_fecha.get().strip(), rid,
            receta[0], receta[1], programada, ent_lote.get().strip(),
            ent_responsable.get().strip(), mo, energia, gas, indirectos,
            txt_op_obs.get("1.0","end").strip()
        ))
        auditoria(con, "CREAR ORDEN", lbl_num_op.cget("text"))
        con.commit()
        messagebox.showinfo("Orden", "Orden creada correctamente.")
        limpiar_orden()
        cargar_ordenes()
        actualizar_kpis()
    except Exception as e:
        con.rollback()
        messagebox.showerror("Orden", f"No se pudo crear.\n\n{e}")
    finally:
        con.close()


def seleccionar_lotes(con, producto, presentacion, requerida):
    filas = con.execute("""
        SELECT id,cantidad,COALESCE(lote,''),COALESCE(costo_unitario,costo,0)
        FROM inventario
        WHERE producto=? AND presentacion=? AND cantidad>0
        ORDER BY COALESCE(fecha_ingreso,fecha,''),id
    """,(producto,presentacion)).fetchall()
    disponible = sum(float(f[1] or 0) for f in filas)
    if disponible < requerida:
        raise ValueError(
            f"Inventario insuficiente para {producto}/{presentacion}. "
            f"Requerido {requerida:,.2f}; disponible {disponible:,.2f}."
        )
    pendiente = requerida
    consumos = []
    for f in filas:
        if pendiente <= 0:
            break
        usar = min(float(f[1] or 0), pendiente)
        consumos.append((f[0], usar, f[2], float(f[3] or 0)))
        pendiente -= usar
    return consumos


def cerrar_orden():
    sel = tv_ordenes.selection()
    if not sel:
        messagebox.showwarning("Cerrar orden", "Seleccione una orden.")
        return
    oid = int(sel[0])
    with conectar() as con:
        op = con.execute("""
            SELECT numero,fecha,receta_id,producto_terminado,presentacion,
                   cantidad_programada,lote_producto,mano_obra,energia,gas,
                   costos_indirectos,estado
            FROM ordenes_produccion WHERE id=?
        """,(oid,)).fetchone()
    if not op or op[11] != "PENDIENTE":
        messagebox.showinfo("Cerrar orden", "La orden no está pendiente.")
        return

    producida = simpledialog.askfloat(
        "Cerrar orden","Cantidad realmente producida:",
        initialvalue=float(op[5])
    )
    if producida is None or producida <= 0:
        return

    if not messagebox.askyesno(
        "Confirmar cierre",
        f"Orden: {op[0]}\nProducto: {op[3]}/{op[4]}\n"
        f"Cantidad: {producida:,.2f}\nLote: {op[6]}\n\n"
        "Se descontarán materias primas y se ingresará producto terminado."
    ):
        return

    con = conectar()
    try:
        con.execute("BEGIN IMMEDIATE")
        base = con.execute("SELECT cantidad_base FROM recetas_produccion WHERE id=?",(op[2],)).fetchone()[0]
        detalles = con.execute("""
            SELECT materia_prima,presentacion,cantidad,unidad
            FROM recetas_detalle WHERE receta_id=?
        """,(op[2],)).fetchall()
        factor = producida / float(base or 1)
        costo_materiales = 0.0

        for d in detalles:
            requerida = float(d[2]) * factor
            for inv_id, usar, lote, costo in seleccionar_lotes(con,d[0],d[1],requerida):
                con.execute("UPDATE inventario SET cantidad=cantidad-? WHERE id=?",(usar,inv_id))
                total_linea = usar * costo
                costo_materiales += total_linea
                con.execute("""
                    INSERT INTO consumos_produccion(
                        orden_id,producto,presentacion,lote,cantidad,
                        costo_unitario,costo_total
                    ) VALUES(?,?,?,?,?,?,?)
                """,(oid,d[0],d[1],lote,usar,costo,total_linea))
                registrar_kardex(
                    con,d[0],d[1],lote,"CONSUMO PRODUCCIÓN",
                    0,usar,costo,op[0],"Consumo automático"
                )

        costo_total = costo_materiales + float(op[7] or 0) + float(op[8] or 0) + float(op[9] or 0) + float(op[10] or 0)
        costo_unitario = costo_total / producida

        existe = con.execute("""
            SELECT id FROM inventario
            WHERE producto=? AND presentacion=? AND COALESCE(lote,'')=?
        """,(op[3],op[4],op[6])).fetchone()
        if existe:
            con.execute("""
                UPDATE inventario
                SET cantidad=cantidad+?,costo_unitario=?,costo=?,
                    fecha_ingreso=?,fecha=?,numero_despacho=?,despacho=?
                WHERE id=?
            """,(producida,costo_unitario,costo_unitario,op[1],op[1],op[0],op[0],existe[0]))
        else:
            con.execute("""
                INSERT INTO inventario(
                    producto,presentacion,cantidad,lote,costo_unitario,
                    fecha_ingreso,numero_despacho,stock_minimo,costo,fecha,despacho
                ) VALUES(?,?,?,?,?,?,?,0,?,?,?)
            """,(op[3],op[4],producida,op[6],costo_unitario,op[1],op[0],costo_unitario,op[1],op[0]))

        registrar_kardex(
            con,op[3],op[4],op[6],"ENTRADA PRODUCCIÓN",
            producida,0,costo_unitario,op[0],"Producto terminado"
        )

        con.execute("""
            UPDATE ordenes_produccion
            SET cantidad_producida=?,costo_materiales=?,costo_total=?,
                costo_unitario=?,estado='CERRADA',cerrada_en=?
            WHERE id=?
        """,(producida,costo_materiales,costo_total,costo_unitario,ahora(),oid))
        auditoria(con,"CERRAR ORDEN",
                  f"{op[0]}; cantidad {producida:.2f}; costo {costo_total:.2f}")
        con.commit()

        messagebox.showinfo(
            "Orden cerrada",
            f"Orden {op[0]} cerrada correctamente.\n\n"
            f"Materiales: {moneda(costo_materiales)}\n"
            f"Costo total: {moneda(costo_total)}\n"
            f"Costo unitario: {moneda(costo_unitario)}"
        )
        cargar_ordenes()
        actualizar_kpis()
    except Exception as e:
        con.rollback()
        messagebox.showerror(
            "No fue posible cerrar",
            f"La operación fue revertida completamente.\n\n{e}"
        )
    finally:
        con.close()


def cargar_ordenes():
    estado = cmb_estado.get().strip()
    sql = """
        SELECT id,numero,fecha,producto_terminado,presentacion,
               cantidad_programada,cantidad_producida,lote_producto,
               responsable,costo_total,costo_unitario,estado
        FROM ordenes_produccion WHERE 1=1
    """
    params = []
    if estado and estado != "TODOS":
        sql += " AND estado=?"
        params.append(estado)
    sql += " ORDER BY id DESC"
    with conectar() as con:
        filas = con.execute(sql,params).fetchall()
    tv_ordenes.delete(*tv_ordenes.get_children())
    for f in filas:
        tv_ordenes.insert("", "end", iid=str(f[0]), values=(
            f[1],f[2],f[3],f[4],num(f[5]),num(f[6]),f[7],f[8],
            moneda(f[9]),moneda(f[10]),f[11]
        ), tags=("cerrada" if f[11]=="CERRADA" else "pendiente",))


def ver_consumos():
    sel = tv_ordenes.selection()
    if not sel:
        messagebox.showwarning("Consumos","Seleccione una orden.")
        return
    oid = int(sel[0])
    with conectar() as con:
        op = con.execute("SELECT numero,producto_terminado,presentacion FROM ordenes_produccion WHERE id=?",(oid,)).fetchone()
        filas = con.execute("""
            SELECT producto,presentacion,lote,cantidad,costo_unitario,costo_total
            FROM consumos_produccion WHERE orden_id=? ORDER BY id
        """,(oid,)).fetchall()

    top = tk.Toplevel(ventana)
    top.title("Consumos de producción")
    top.geometry("980x520")
    top.configure(bg=C_FONDO)
    tk.Label(
        top,text=f"CONSUMOS - {op[0]} - {op[1]}/{op[2]}",
        bg=C_OSCURO,fg="white",font=("Segoe UI",14,"bold"),pady=14
    ).pack(fill="x")
    cols = ("Producto","Presentacion","Lote","Cantidad","Costo","Total")
    tv = ttk.Treeview(top,columns=cols,show="headings")
    for c in cols:
        tv.heading(c,text=c)
    tv.pack(fill="both",expand=True,padx=15,pady=15)
    for f in filas:
        tv.insert("", "end", values=(f[0],f[1],f[2],num(f[3]),moneda(f[4]),moneda(f[5])))


def actualizar_kpis():
    with conectar() as con:
        pendientes = con.execute("SELECT COUNT(*) FROM ordenes_produccion WHERE estado='PENDIENTE'").fetchone()[0]
        cerradas = con.execute("""
            SELECT COUNT(*) FROM ordenes_produccion
            WHERE estado='CERRADA'
              AND strftime('%Y-%m',fecha)=strftime('%Y-%m','now','localtime')
        """).fetchone()[0]
        produccion = con.execute("""
            SELECT IFNULL(SUM(cantidad_producida),0) FROM ordenes_produccion
            WHERE estado='CERRADA'
              AND strftime('%Y-%m',fecha)=strftime('%Y-%m','now','localtime')
        """).fetchone()[0]
        costo = con.execute("""
            SELECT IFNULL(SUM(costo_total),0) FROM ordenes_produccion
            WHERE estado='CERRADA'
              AND strftime('%Y-%m',fecha)=strftime('%Y-%m','now','localtime')
        """).fetchone()[0]
    lbl_kpi_pend.config(text=str(pendientes))
    lbl_kpi_cerr.config(text=str(cerradas))
    lbl_kpi_prod.config(text=num(produccion))
    lbl_kpi_costo.config(text=moneda(costo))


def refrescar():
    cargar_catalogos()
    cargar_recetas()
    cargar_ordenes()
    actualizar_kpis()


# INTERFAZ
inicializar_bd()
ventana = tk.Tk()
ventana.title("ERP Café Alto de la Cruz - Producción Integrada")
ventana.geometry("1480x880")
ventana.minsize(1180,720)
ventana.configure(bg=C_FONDO)
try:
    ventana.state("zoomed")
except tk.TclError:
    pass

style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass
style.configure("Treeview",rowheight=28,font=("Segoe UI",9))
style.configure("Treeview.Heading",font=("Segoe UI",9,"bold"))

header = tk.Frame(ventana,bg=C_OSCURO,height=82)
header.pack(fill="x")
header.pack_propagate(False)
tk.Label(header,text="PRODUCCIÓN INTEGRADA",font=("Segoe UI",22,"bold"),
         bg=C_OSCURO,fg="white").pack(side="left",padx=24,pady=20)
tk.Label(header,text="Recetas, órdenes, consumo y costeo",
         font=("Segoe UI",10),bg=C_OSCURO,fg="#BFDBFE").pack(side="right",padx=24)

kpis = tk.Frame(ventana,bg=C_FONDO)
kpis.pack(fill="x",padx=18,pady=(14,5))
for i in range(4):
    kpis.grid_columnconfigure(i,weight=1)

def tarjeta(col,titulo,color):
    f=tk.Frame(kpis,bg=C_BLANCO,highlightbackground=C_BORDE,highlightthickness=1)
    f.grid(row=0,column=col,sticky="ew",padx=6)
    tk.Frame(f,bg=color,width=5).pack(side="left",fill="y")
    x=tk.Frame(f,bg=C_BLANCO); x.pack(fill="both",expand=True,padx=14,pady=10)
    tk.Label(x,text=titulo,bg=C_BLANCO,fg=C_SUAVE,font=("Segoe UI",8,"bold")).pack(anchor="w")
    l=tk.Label(x,text="0",bg=C_BLANCO,fg=C_TEXTO,font=("Segoe UI",16,"bold"))
    l.pack(anchor="w",pady=(3,0)); return l

lbl_kpi_pend = tarjeta(0,"ÓRDENES PENDIENTES",C_NARANJA)
lbl_kpi_cerr = tarjeta(1,"ÓRDENES CERRADAS MES",C_VERDE)
lbl_kpi_prod = tarjeta(2,"PRODUCCIÓN DEL MES",C_AZUL)
lbl_kpi_costo = tarjeta(3,"COSTO PRODUCCIÓN MES","#7C3AED")

nb=ttk.Notebook(ventana); nb.pack(fill="both",expand=True,padx=18,pady=10)
tab_r=tk.Frame(nb,bg=C_FONDO); tab_o=tk.Frame(nb,bg=C_FONDO); tab_h=tk.Frame(nb,bg=C_FONDO)
nb.add(tab_r,text="  Recetas  "); nb.add(tab_o,text="  Nueva orden  "); nb.add(tab_h,text="  Historial  ")

# Recetas
frm=tk.LabelFrame(tab_r,text="DATOS DE LA RECETA",bg=C_BLANCO,fg=C_TEXTO,
                  font=("Segoe UI",10,"bold"),padx=12,pady=10)
frm.pack(fill="x",padx=10,pady=10)
for i in range(6): frm.grid_columnconfigure(i,weight=1)
labels=["Código","Producto terminado","Presentación","Cantidad base","Unidad"]
for i,t in enumerate(labels):
    tk.Label(frm,text=t,bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=i,sticky="w")
ent_codigo=ttk.Entry(frm); ent_codigo.grid(row=1,column=0,sticky="ew",padx=(0,8))
ent_pt=ttk.Entry(frm); ent_pt.grid(row=1,column=1,sticky="ew",padx=(0,8))
ent_pt_pres=ttk.Entry(frm); ent_pt_pres.grid(row=1,column=2,sticky="ew",padx=(0,8))
ent_base=ttk.Entry(frm); ent_base.grid(row=1,column=3,sticky="ew",padx=(0,8))
cmb_base_unidad=ttk.Combobox(frm,values=["UND","KG","G","L","ML"],state="readonly")
cmb_base_unidad.grid(row=1,column=4,sticky="ew",padx=(0,8))
tk.Label(frm,text="Observaciones",bg=C_BLANCO,fg=C_SUAVE).grid(row=2,column=0,sticky="w",pady=(10,0))
txt_rec_obs=tk.Text(frm,height=2,relief="solid",bd=1)
txt_rec_obs.grid(row=3,column=0,columnspan=6,sticky="ew")

det=tk.LabelFrame(tab_r,text="MATERIAS PRIMAS",bg=C_BLANCO,fg=C_TEXTO,
                  font=("Segoe UI",10,"bold"),padx=12,pady=10)
det.pack(fill="both",expand=True,padx=10,pady=(0,10))
line=tk.Frame(det,bg=C_BLANCO); line.pack(fill="x",pady=(0,8))
for i,t in enumerate(["Materia prima","Presentación","Cantidad","Unidad"]):
    tk.Label(line,text=t,bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=i,sticky="w",padx=4)
cmb_mp=ttk.Combobox(line,state="normal",width=30); cmb_mp.grid(row=1,column=0,sticky="ew",padx=4)
cmb_mp.bind("<<ComboboxSelected>>",cargar_presentaciones)
cmb_mp_pres=ttk.Combobox(line,state="normal",width=22); cmb_mp_pres.grid(row=1,column=1,sticky="ew",padx=4)
ent_mp_cant=ttk.Entry(line,width=14); ent_mp_cant.grid(row=1,column=2,sticky="ew",padx=4)
cmb_mp_unidad=ttk.Combobox(line,values=["UND","KG","G","L","ML"],state="readonly",width=12)
cmb_mp_unidad.grid(row=1,column=3,sticky="ew",padx=4)
tk.Button(line,text="Agregar insumo",command=agregar_insumo,bg=C_AZUL,fg="white",
          relief="flat",font=("Segoe UI",9,"bold"),padx=12,pady=6).grid(row=1,column=4,padx=8)
for i in range(4): line.grid_columnconfigure(i,weight=1)

cols=("N","MateriaPrima","Presentacion","Cantidad","Unidad")
tv_receta=ttk.Treeview(det,columns=cols,show="headings",height=9)
for c in cols: tv_receta.heading(c,text=c)
tv_receta.pack(fill="both",expand=True)
bot=tk.Frame(det,bg=C_BLANCO); bot.pack(fill="x",pady=(8,0))
tk.Button(bot,text="Eliminar insumo",command=eliminar_insumo,bg=C_ROJO,fg="white",
          relief="flat",padx=12,pady=6).pack(side="left")
tk.Button(bot,text="Guardar receta",command=guardar_receta,bg=C_VERDE,fg="white",
          relief="flat",font=("Segoe UI",9,"bold"),padx=18,pady=6).pack(side="right")
tk.Button(bot,text="Nueva / limpiar",command=limpiar_receta,bg=C_OSCURO,fg="white",
          relief="flat",padx=18,pady=6).pack(side="right",padx=8)

tv_recetas=ttk.Treeview(tab_r,columns=("Codigo","Producto","Presentacion","Base","Unidad","Estado"),
                        show="headings",height=6)
for c in ("Codigo","Producto","Presentacion","Base","Unidad","Estado"): tv_recetas.heading(c,text=c)
tv_recetas.pack(fill="x",padx=10,pady=(0,10))

# Nueva orden
of=tk.LabelFrame(tab_o,text="DATOS DE LA ORDEN",bg=C_BLANCO,fg=C_TEXTO,
                 font=("Segoe UI",10,"bold"),padx=12,pady=10)
of.pack(fill="x",padx=10,pady=10)
for i in range(6): of.grid_columnconfigure(i,weight=1)
tk.Label(of,text="Número",bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=0,sticky="w")
lbl_num_op=tk.Label(of,text=numero_orden(),bg=C_BLANCO,fg=C_AZUL,font=("Segoe UI",10,"bold"))
lbl_num_op.grid(row=1,column=0,sticky="w")
tk.Label(of,text="Fecha",bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=1,sticky="w")
ent_fecha=ttk.Entry(of); ent_fecha.grid(row=1,column=1,sticky="ew",padx=(0,8))
tk.Label(of,text="Receta",bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=2,sticky="w")
cmb_receta=ttk.Combobox(of,state="readonly"); cmb_receta.grid(row=1,column=2,columnspan=2,sticky="ew",padx=(0,8))
cmb_receta.bind("<<ComboboxSelected>>",cargar_receta_orden)
tk.Label(of,text="Cantidad programada",bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=4,sticky="w")
ent_programada=ttk.Entry(of); ent_programada.grid(row=1,column=4,sticky="ew",padx=(0,8))
ent_programada.bind("<KeyRelease>",calcular_requerimientos)
tk.Label(of,text="Lote producto",bg=C_BLANCO,fg=C_SUAVE).grid(row=0,column=5,sticky="w")
ent_lote=ttk.Entry(of); ent_lote.grid(row=1,column=5,sticky="ew")
lbl_prod_orden=tk.Label(of,text="Seleccione una receta",bg=C_BLANCO,fg=C_AZUL,font=("Segoe UI",10,"bold"))
lbl_prod_orden.grid(row=2,column=0,columnspan=3,sticky="w",pady=(12,0))
lbl_base_orden=tk.Label(of,text="",bg=C_BLANCO,fg=C_SUAVE); lbl_base_orden.grid(row=2,column=3,sticky="w",pady=(12,0))

tk.Label(of,text="Responsable",bg=C_BLANCO,fg=C_SUAVE).grid(row=3,column=0,sticky="w",pady=(10,0))
ent_responsable=ttk.Entry(of); ent_responsable.grid(row=4,column=0,columnspan=2,sticky="ew",padx=(0,8))
for i,t in enumerate(["Mano de obra","Energía","Gas","Costos indirectos"],start=2):
    tk.Label(of,text=t,bg=C_BLANCO,fg=C_SUAVE).grid(row=3,column=i,sticky="w",pady=(10,0))
ent_mo=ttk.Entry(of); ent_mo.grid(row=4,column=2,sticky="ew",padx=(0,8))
ent_energia=ttk.Entry(of); ent_energia.grid(row=4,column=3,sticky="ew",padx=(0,8))
ent_gas=ttk.Entry(of); ent_gas.grid(row=4,column=4,sticky="ew",padx=(0,8))
ent_indirectos=ttk.Entry(of); ent_indirectos.grid(row=4,column=5,sticky="ew")
tk.Label(of,text="Observaciones",bg=C_BLANCO,fg=C_SUAVE).grid(row=5,column=0,sticky="w",pady=(10,0))
txt_op_obs=tk.Text(of,height=2,relief="solid",bd=1); txt_op_obs.grid(row=6,column=0,columnspan=6,sticky="ew")

rf=tk.LabelFrame(tab_o,text="REQUERIMIENTOS Y DISPONIBILIDAD",bg=C_BLANCO,fg=C_TEXTO,
                 font=("Segoe UI",10,"bold"))
rf.pack(fill="both",expand=True,padx=10,pady=(0,10))
reqcols=("N","MateriaPrima","Presentacion","Requerida","Unidad","Disponible","Estado")
tv_req=ttk.Treeview(rf,columns=reqcols,show="headings")
for c in reqcols: tv_req.heading(c,text=c)
tv_req.pack(fill="both",expand=True,padx=10,pady=10)
tv_req.tag_configure("faltante",foreground=C_ROJO); tv_req.tag_configure("ok",foreground=C_VERDE)

ob=tk.Frame(tab_o,bg=C_FONDO); ob.pack(fill="x",padx=10,pady=(0,10))
tk.Button(ob,text="Crear orden de producción",command=crear_orden,bg=C_VERDE,fg="white",
          relief="flat",font=("Segoe UI",10,"bold"),padx=18,pady=9).pack(side="left")
tk.Button(ob,text="Nueva / limpiar",command=limpiar_orden,bg=C_OSCURO,fg="white",
          relief="flat",font=("Segoe UI",10,"bold"),padx=18,pady=9).pack(side="left",padx=8)

# Historial
hf=tk.Frame(tab_h,bg=C_BLANCO); hf.pack(fill="x",padx=10,pady=10)
tk.Label(hf,text="Estado:",bg=C_BLANCO,fg=C_TEXTO).pack(side="left",padx=(12,5))
cmb_estado=ttk.Combobox(hf,values=["TODOS","PENDIENTE","CERRADA"],state="readonly",width=14)
cmb_estado.pack(side="left",padx=5); cmb_estado.set("TODOS")
tk.Button(hf,text="Actualizar",command=cargar_ordenes,bg=C_AZUL,fg="white",
          relief="flat",padx=14,pady=6).pack(side="left",padx=5)
tk.Button(hf,text="Ver consumos",command=ver_consumos,bg="#475569",fg="white",
          relief="flat",padx=14,pady=6).pack(side="right",padx=5)
tk.Button(hf,text="Cerrar orden seleccionada",command=cerrar_orden,bg=C_VERDE,fg="white",
          relief="flat",font=("Segoe UI",9,"bold"),padx=14,pady=6).pack(side="right",padx=5)

hcols=("Numero","Fecha","Producto","Presentacion","Programada","Producida","Lote",
       "Responsable","CostoTotal","CostoUnitario","Estado")
tv_ordenes=ttk.Treeview(tab_h,columns=hcols,show="headings")
for c in hcols: tv_ordenes.heading(c,text=c)
tv_ordenes.pack(fill="both",expand=True,padx=10,pady=(0,10))
tv_ordenes.tag_configure("pendiente",foreground=C_NARANJA)
tv_ordenes.tag_configure("cerrada",foreground=C_VERDE)

barra=tk.Frame(ventana,bg=C_BLANCO,height=28); barra.pack(fill="x")
tk.Label(barra,text=f"Base de datos: {RUTA_DB}",bg=C_BLANCO,fg=C_SUAVE,font=("Segoe UI",8)).pack(side="left",padx=12)
tk.Label(barra,text="Producción Integrada v1.0",bg=C_BLANCO,fg=C_SUAVE,font=("Segoe UI",8)).pack(side="right",padx=12)

limpiar_receta()
limpiar_orden()
refrescar()
ventana.mainloop()
