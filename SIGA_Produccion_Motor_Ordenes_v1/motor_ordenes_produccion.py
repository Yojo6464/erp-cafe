from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

ESTADOS = {"BORRADOR", "PLANEADA", "APROBADA", "LIBERADA", "EN PROCESO", "SUSPENDIDA", "TERMINADA", "CERRADA", "ANULADA"}
TRANSICIONES = {
    "BORRADOR": {"PLANEADA", "APROBADA", "ANULADA"},
    "PLANEADA": {"APROBADA", "BORRADOR", "ANULADA"},
    "APROBADA": {"LIBERADA", "ANULADA"},
    "LIBERADA": {"EN PROCESO", "SUSPENDIDA", "ANULADA"},
    "EN PROCESO": {"SUSPENDIDA", "TERMINADA"},
    "SUSPENDIDA": {"LIBERADA", "EN PROCESO", "ANULADA"},
    "TERMINADA": {"CERRADA"},
    "CERRADA": set(),
    "ANULADA": set(),
}

class ErrorProduccion(Exception):
    pass
class ErrorValidacion(ErrorProduccion):
    pass
class ErrorEstado(ErrorProduccion):
    pass
class ErrorEstructura(ErrorProduccion):
    pass

@dataclass(frozen=True)
class ResultadoDisponibilidad:
    componente: str
    presentacion: str
    requerido: float
    disponible: float
    faltante: float
    unidad: str
    cumple: bool

class MotorOrdenesProduccion:
    def __init__(self, ruta_db: str | Path = r"C:\Users\jrive\visual\erp_cafe.db", usuario: str = "sistema") -> None:
        self.ruta_db = Path(ruta_db)
        self.usuario = (usuario or "sistema").strip()
        if not self.ruta_db.exists():
            raise FileNotFoundError(f"No existe la base de datos: {self.ruta_db}")
        self._validar_estructura_minima()

    @contextmanager
    def conexion(self):
        con = sqlite3.connect(str(self.ruta_db), timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _ahora() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    @staticmethod
    def _hoy() -> str:
        return date.today().isoformat()
    @staticmethod
    def _normalizar_estado(valor: str) -> str:
        estado = (valor or "").strip().upper()
        return {"EN_PROCESO": "EN PROCESO", "CANCELADA": "ANULADA"}.get(estado, estado)
    @staticmethod
    def _columnas(con: sqlite3.Connection, tabla: str) -> dict[str, sqlite3.Row]:
        return {f["name"].lower(): f for f in con.execute(f'PRAGMA table_info("{tabla}")').fetchall()}
    @staticmethod
    def _tablas(con: sqlite3.Connection) -> set[str]:
        return {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    @staticmethod
    def _columna_alias(columnas: dict[str, sqlite3.Row], *opciones: str, obligatoria: bool = False) -> Optional[str]:
        for opcion in opciones:
            if opcion.lower() in columnas:
                return opcion.lower()
        if obligatoria:
            raise ErrorEstructura("No se encontró columna compatible entre: " + ", ".join(opciones))
        return None

    def _validar_estructura_minima(self) -> None:
        requeridas = {"productos_produccion", "formulas_produccion", "formulas_componentes", "ordenes_produccion_v2", "ordenes_historial_v2", "inventario"}
        with self.conexion() as con:
            faltantes = sorted(requeridas - self._tablas(con))
            if faltantes:
                raise ErrorEstructura("Faltan tablas necesarias: " + ", ".join(faltantes))
            integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
            if str(integridad).lower() != "ok":
                raise ErrorEstructura(f"La base de datos no superó integrity_check: {integridad}")

    def _siguiente_numero(self, con: sqlite3.Connection) -> str:
        anio = datetime.now().year
        prefijo = f"OP-{anio}-"
        fila = con.execute("SELECT numero FROM ordenes_produccion_v2 WHERE numero LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefijo}%",)).fetchone()
        ultimo = 0
        if fila:
            try:
                ultimo = int(str(fila["numero"]).split("-")[-1])
            except (TypeError, ValueError):
                pass
        return f"{prefijo}{ultimo + 1:06d}"

    def _producto(self, con: sqlite3.Connection, producto_id: int) -> sqlite3.Row:
        fila = con.execute("SELECT * FROM productos_produccion WHERE id=? AND UPPER(estado)='ACTIVO'", (producto_id,)).fetchone()
        if not fila:
            raise ErrorValidacion(f"El producto {producto_id} no existe o no está activo.")
        return fila

    def _formula(self, con: sqlite3.Connection, formula_id: int, producto_id: Optional[int] = None, exigir_activa: bool = False) -> sqlite3.Row:
        sql = "SELECT * FROM formulas_produccion WHERE id=?"
        params: list[Any] = [formula_id]
        if producto_id is not None:
            sql += " AND producto_id=?"
            params.append(producto_id)
        fila = con.execute(sql, params).fetchone()
        if not fila:
            raise ErrorValidacion(f"La fórmula {formula_id} no existe o no corresponde al producto.")
        if exigir_activa and str(fila["estado"]).upper() != "ACTIVA":
            raise ErrorValidacion(f"La fórmula {fila['codigo']} no está ACTIVA.")
        return fila

    def _registrar_historial(self, con: sqlite3.Connection, orden_id: int, estado_anterior: str, estado_nuevo: str, accion: str, observacion: str = "") -> None:
        columnas = self._columnas(con, "ordenes_historial_v2")
        ahora = self._ahora()
        posibles = {
            "orden_id": orden_id, "fecha": ahora, "fecha_evento": ahora,
            "estado_anterior": estado_anterior, "estado_nuevo": estado_nuevo,
            "accion": accion, "evento": accion, "usuario": self.usuario,
            "creado_por": self.usuario, "observacion": observacion,
            "observaciones": observacion, "detalle": observacion, "creado_en": ahora,
        }
        datos = {n: posibles[n] for n in columnas if n != "id" and n in posibles}
        if "orden_id" not in datos:
            raise ErrorEstructura("ordenes_historial_v2 no contiene orden_id.")
        nombres = list(datos)
        con.execute(f'INSERT INTO ordenes_historial_v2 ({", ".join(nombres)}) VALUES ({", ".join("?" for _ in nombres)})', [datos[n] for n in nombres])

    def crear_orden(self, producto_id: int, formula_id: int, cantidad_programada: float, fecha_programada: str, lote_planeado: str, centro_trabajo: str = "", responsable: str = "", prioridad: str = "NORMAL", observaciones: str = "", estado_inicial: str = "BORRADOR") -> int:
        if cantidad_programada <= 0:
            raise ErrorValidacion("La cantidad programada debe ser mayor que cero.")
        if not fecha_programada:
            raise ErrorValidacion("La fecha programada es obligatoria.")
        if not lote_planeado.strip():
            raise ErrorValidacion("El lote planeado es obligatorio.")
        estado = self._normalizar_estado(estado_inicial)
        if estado not in {"BORRADOR", "PLANEADA"}:
            raise ErrorValidacion("Una orden nueva solo puede iniciar en BORRADOR o PLANEADA.")
        with self.conexion() as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                producto = self._producto(con, producto_id)
                self._formula(con, formula_id, producto_id=producto_id)
                numero, ahora = self._siguiente_numero(con), self._ahora()
                cur = con.execute("""
                    INSERT INTO ordenes_produccion_v2 (
                        numero, fecha_emision, fecha_programada, producto_id, formula_id,
                        cantidad_programada, cantidad_producida, unidad, lote_planeado,
                        centro_trabajo, responsable, prioridad, estado, observaciones,
                        creada_por, creada_en, actualizada_en
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (numero, self._hoy(), fecha_programada, producto_id, formula_id, float(cantidad_programada), producto["unidad"], lote_planeado.strip(), centro_trabajo.strip(), responsable.strip(), prioridad.strip().upper() or "NORMAL", estado, observaciones.strip(), self.usuario, ahora, ahora))
                orden_id = int(cur.lastrowid)
                self._registrar_historial(con, orden_id, "", estado, "CREAR ORDEN", f"Orden {numero} creada.")
                con.commit()
                return orden_id
            except Exception:
                con.rollback()
                raise

    def obtener_orden(self, orden_id: int) -> dict[str, Any]:
        with self.conexion() as con:
            fila = con.execute("""
                SELECT o.*, p.codigo producto_codigo, p.nombre producto_nombre,
                       p.presentacion producto_presentacion, f.codigo formula_codigo,
                       f.version formula_version, f.estado formula_estado
                FROM ordenes_produccion_v2 o
                JOIN productos_produccion p ON p.id=o.producto_id
                JOIN formulas_produccion f ON f.id=o.formula_id
                WHERE o.id=?
            """, (orden_id,)).fetchone()
            if not fila:
                raise ErrorValidacion(f"No existe la orden {orden_id}.")
            return dict(fila)

    def listar_ordenes(self, estado: Optional[str] = None, limite: int = 500) -> list[dict[str, Any]]:
        limite = max(1, min(int(limite), 5000))
        where, params = "", []
        if estado:
            where, params = "WHERE UPPER(o.estado)=?", [self._normalizar_estado(estado)]
        with self.conexion() as con:
            filas = con.execute(f"""
                SELECT o.id, o.numero, o.fecha_emision, o.fecha_programada,
                       o.cantidad_programada, o.cantidad_producida, o.unidad,
                       o.lote_planeado, o.prioridad, o.estado, o.responsable,
                       o.costo_total_real, o.costo_unitario_real,
                       p.codigo producto_codigo, p.nombre producto_nombre,
                       p.presentacion producto_presentacion,
                       f.codigo formula_codigo, f.version formula_version
                FROM ordenes_produccion_v2 o
                JOIN productos_produccion p ON p.id=o.producto_id
                JOIN formulas_produccion f ON f.id=o.formula_id
                {where} ORDER BY o.id DESC LIMIT ?
            """, [*params, limite]).fetchall()
            return [dict(f) for f in filas]

    def cambiar_estado(self, orden_id: int, nuevo_estado: str, observacion: str = "") -> None:
        nuevo = self._normalizar_estado(nuevo_estado)
        if nuevo not in ESTADOS:
            raise ErrorEstado(f"Estado no válido: {nuevo_estado}")
        with self.conexion() as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                orden = con.execute("SELECT * FROM ordenes_produccion_v2 WHERE id=?", (orden_id,)).fetchone()
                if not orden:
                    raise ErrorValidacion(f"No existe la orden {orden_id}.")
                anterior = self._normalizar_estado(orden["estado"])
                if nuevo not in TRANSICIONES.get(anterior, set()):
                    raise ErrorEstado(f"No se permite cambiar de {anterior} a {nuevo}.")
                if nuevo in {"APROBADA", "LIBERADA"}:
                    self._formula(con, int(orden["formula_id"]), int(orden["producto_id"]), exigir_activa=(nuevo == "LIBERADA"))
                if nuevo == "LIBERADA":
                    faltantes = [x for x in self._disponibilidad_conexion(con, orden_id) if not x.cumple]
                    if faltantes:
                        resumen = "; ".join(f"{x.componente}: faltan {x.faltante:.4f} {x.unidad}" for x in faltantes)
                        raise ErrorValidacion("No se puede liberar por falta de materiales. " + resumen)
                ahora = self._ahora()
                cambios: dict[str, Any] = {"estado": nuevo, "actualizada_en": ahora}
                if nuevo == "APROBADA": cambios.update(aprobada_por=self.usuario, aprobada_en=ahora)
                elif nuevo == "LIBERADA": cambios.update(liberada_por=self.usuario, liberada_en=ahora)
                elif nuevo == "EN PROCESO": cambios.update(iniciada_por=self.usuario, iniciada_en=ahora)
                elif nuevo == "TERMINADA": cambios.update(terminada_por=self.usuario, terminada_en=ahora)
                elif nuevo == "ANULADA": cambios.update(anulada_por=self.usuario, anulada_en=ahora, motivo_anulacion=observacion.strip())
                con.execute(f'UPDATE ordenes_produccion_v2 SET {", ".join(f"{k}=?" for k in cambios)} WHERE id=?', [*cambios.values(), orden_id])
                self._registrar_historial(con, orden_id, anterior, nuevo, f"CAMBIO DE ESTADO A {nuevo}", observacion)
                con.commit()
            except Exception:
                con.rollback()
                raise

    def aprobar(self, orden_id: int, observacion: str = "") -> None: self.cambiar_estado(orden_id, "APROBADA", observacion)
    def liberar(self, orden_id: int, observacion: str = "") -> None: self.cambiar_estado(orden_id, "LIBERADA", observacion)
    def iniciar(self, orden_id: int, observacion: str = "") -> None: self.cambiar_estado(orden_id, "EN PROCESO", observacion)
    def suspender(self, orden_id: int, observacion: str = "") -> None: self.cambiar_estado(orden_id, "SUSPENDIDA", observacion)
    def terminar(self, orden_id: int, observacion: str = "") -> None: self.cambiar_estado(orden_id, "TERMINADA", observacion)
    def anular(self, orden_id: int, motivo: str) -> None:
        if not motivo.strip(): raise ErrorValidacion("El motivo de anulación es obligatorio.")
        self.cambiar_estado(orden_id, "ANULADA", motivo)
    def cerrar(self, orden_id: int, observacion: str = "") -> None:
        if float(self.obtener_orden(orden_id)["cantidad_producida"] or 0) <= 0:
            raise ErrorValidacion("No se puede cerrar una orden sin cantidad producida.")
        self.cambiar_estado(orden_id, "CERRADA", observacion)

    def _componentes_formula_conexion(self, con: sqlite3.Connection, formula_id: int) -> list[dict[str, Any]]:
        cols = self._columnas(con, "formulas_componentes")
        cf = self._columna_alias(cols, "formula_id", obligatoria=True)
        cn = self._columna_alias(cols, "componente", "producto", "nombre_componente", "material", "descripcion", obligatoria=True)
        cp = self._columna_alias(cols, "presentacion", "componente_presentacion", "referencia")
        cc = self._columna_alias(cols, "cantidad", "cantidad_base", "cantidad_requerida", obligatoria=True)
        cu = self._columna_alias(cols, "unidad", "unidad_medida", "um")
        cm = self._columna_alias(cols, "merma_pct", "merma", "porcentaje_merma")
        cco = self._columna_alias(cols, "costo_unitario", "costo", "costo_estandar")
        ct = self._columna_alias(cols, "tipo", "tipo_componente", "categoria")
        filas = con.execute(f'SELECT * FROM formulas_componentes WHERE "{cf}"=? ORDER BY id', (formula_id,)).fetchall()
        out = []
        for f in filas:
            out.append({
                "id": f["id"] if "id" in f.keys() else None,
                "formula_id": formula_id,
                "componente": str(f[cn] or "").strip(),
                "presentacion": str(f[cp] or "").strip() if cp else "",
                "cantidad": float(f[cc] or 0),
                "unidad": str(f[cu] or "UND").strip() if cu else "UND",
                "merma_pct": float(f[cm] or 0) if cm else 0.0,
                "costo_unitario": float(f[cco] or 0) if cco else 0.0,
                "tipo": str(f[ct] or "").strip() if ct else "",
            })
        return out

    def componentes_formula(self, formula_id: int) -> list[dict[str, Any]]:
        with self.conexion() as con:
            return self._componentes_formula_conexion(con, formula_id)

    def requerimientos_orden(self, orden_id: int) -> list[dict[str, Any]]:
        with self.conexion() as con:
            orden = con.execute("SELECT * FROM ordenes_produccion_v2 WHERE id=?", (orden_id,)).fetchone()
            if not orden: raise ErrorValidacion(f"No existe la orden {orden_id}.")
            formula = self._formula(con, int(orden["formula_id"]))
            base = float(formula["cantidad_base"] or 1)
            if base <= 0: raise ErrorValidacion("La cantidad base de la fórmula debe ser mayor que cero.")
            factor = float(orden["cantidad_programada"]) / base
            out = []
            for c in self._componentes_formula_conexion(con, int(orden["formula_id"])):
                neta = c["cantidad"] * factor
                total = neta * (1 + c["merma_pct"] / 100)
                out.append({**c, "factor_orden": factor, "cantidad_neta": round(neta, 6), "cantidad_requerida": round(total, 6), "costo_estimado": round(total * c["costo_unitario"], 2)})
            return out

    def validar_disponibilidad(self, orden_id: int) -> list[ResultadoDisponibilidad]:
        with self.conexion() as con:
            return self._disponibilidad_conexion(con, orden_id)

    def _disponibilidad_conexion(self, con: sqlite3.Connection, orden_id: int) -> list[ResultadoDisponibilidad]:
        orden = con.execute("SELECT * FROM ordenes_produccion_v2 WHERE id=?", (orden_id,)).fetchone()
        if not orden: raise ErrorValidacion(f"No existe la orden {orden_id}.")
        formula = self._formula(con, int(orden["formula_id"]))
        factor = float(orden["cantidad_programada"]) / float(formula["cantidad_base"] or 1)
        out = []
        for c in self._componentes_formula_conexion(con, int(orden["formula_id"])):
            requerido = c["cantidad"] * factor * (1 + c["merma_pct"] / 100)
            if c["presentacion"]:
                fila = con.execute("SELECT COALESCE(SUM(cantidad),0) disponible FROM inventario WHERE UPPER(TRIM(producto))=UPPER(TRIM(?)) AND UPPER(TRIM(presentacion))=UPPER(TRIM(?))", (c["componente"], c["presentacion"])).fetchone()
            else:
                fila = con.execute("SELECT COALESCE(SUM(cantidad),0) disponible FROM inventario WHERE UPPER(TRIM(producto))=UPPER(TRIM(?))", (c["componente"],)).fetchone()
            disponible = float(fila["disponible"] or 0)
            faltante = max(0.0, requerido - disponible)
            out.append(ResultadoDisponibilidad(c["componente"], c["presentacion"], round(requerido, 6), round(disponible, 6), round(faltante, 6), c["unidad"], faltante <= 0.000001))
        return out

    def resumen(self) -> dict[str, Any]:
        with self.conexion() as con:
            por_estado = {f["estado"]: f["cantidad"] for f in con.execute("SELECT UPPER(estado) estado, COUNT(*) cantidad FROM ordenes_produccion_v2 GROUP BY UPPER(estado)").fetchall()}
            return {
                "total_ordenes": sum(por_estado.values()),
                "por_estado": por_estado,
                "productos_activos": con.execute("SELECT COUNT(*) FROM productos_produccion WHERE UPPER(estado)='ACTIVO'").fetchone()[0],
                "formulas_activas": con.execute("SELECT COUNT(*) FROM formulas_produccion WHERE UPPER(estado)='ACTIVA'").fetchone()[0],
            }

if __name__ == "__main__":
    print(MotorOrdenesProduccion().resumen())
