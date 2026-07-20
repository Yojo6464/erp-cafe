import logging

from config.configuracion import LOGS_DIR

archivo_log = LOGS_DIR / "siga.log"

logging.basicConfig(

    filename=archivo_log,

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)

def registrar(mensaje):

    logging.info(mensaje)

def registrar_error(error):

    logging.error(error)