from datetime import datetime

def ahora():

    return datetime.now()

def fecha():

    return ahora().strftime("%Y-%m-%d")

def hora():

    return ahora().strftime("%H:%M:%S")

def fecha_hora():

    return ahora().strftime("%Y-%m-%d %H:%M:%S")