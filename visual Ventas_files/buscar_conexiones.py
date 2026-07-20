import os

for archivo in os.listdir("."):
    if archivo.endswith(".py"):

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                contenido = f.read()

            if "sqlite3.connect" in contenido:
                print("\n" + "=" * 50)
                print(archivo)

                for linea in contenido.splitlines():
                    if "sqlite3.connect" in linea:
                        print(linea.strip())

        except:
            pass