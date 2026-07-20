import sqlite3
from datetime import datetime


class ClientesService:

    def __init__(self, conexion):
        self.conexion = conexion
        self.cursor = conexion.cursor()

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
        """, (
            fecha,
            nombre,
            telefono,
            ciudad,
            correo
        ))

        self.conexion.commit()

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

        registros = self.cursor.fetchall()

        return [tuple(fila) for fila in registros]