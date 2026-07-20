import os

ruta = r"C:\Users\jrive\visual"

for archivo in sorted(os.listdir(ruta)):

    if archivo.endswith(".py"):

        print(archivo)