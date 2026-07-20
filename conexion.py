import sqlite3
from SIGA_CAFE.config.configuracion import RUTA_DB

def obtener_conexion():

    conexion = sqlite3.connect(RUTA_DB)

    conexion.row_factory = sqlite3.Row

    return conexion