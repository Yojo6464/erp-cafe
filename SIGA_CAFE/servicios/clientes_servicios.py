import sqlite3
from datetime import datetime


class ClientesService:

    def __init__(self, conexion):
        self.conexion = conexion
        self.cursor = conexion.cursor()

    # ===========================
    # GUARDAR
    # ===========================

    def guardar(self, nombre, telefono, ciudad, correo):

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("""
            INSERT INTO clientes
            (
                fecha_registro,
                nombre,
                telefono,
                ciudad,
                correo
            )
            VALUES (?,?,?,?,?)
        """,
        (
            fecha,
            nombre,
            telefono,
            ciudad,
            correo
        ))

        self.conexion.commit()

    # ===========================
    # LISTAR
    # ===========================

    def listar(self):

        self.cursor.execute("""
            SELECT
                id,
                nombre,
                telefono,
                ciudad,
                correo
            FROM clientes
            ORDER BY nombre
        """)

        return self.cursor.fetchall()

    # ===========================
    # ELIMINAR
    # ===========================

    def eliminar(self, id_cliente):

        self.cursor.execute("""
            DELETE FROM clientes
            WHERE id=?
        """, (id_cliente,))

        self.conexion.commit()

    # ===========================
    # ACTUALIZAR
    # ===========================

    def actualizar(
            self,
            id_cliente,
            nombre,
            telefono,
            ciudad,
            correo
    ):

        self.cursor.execute("""
            UPDATE clientes
            SET
                nombre=?,
                telefono=?,
                ciudad=?,
                correo=?
            WHERE id=?
        """,
        (
            nombre,
            telefono,
            ciudad,
            correo,
            id_cliente
        ))

        self.conexion.commit()