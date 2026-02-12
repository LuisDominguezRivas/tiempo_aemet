import requests
import sys
import os
import json
import unicodedata
from datetime import datetime

from api import API_KEY, BASE_URL

# ===============================
# CONFIG
# ===============================
CACHE_MUNICIPIOS = "municipios.json"

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# ===============================
# NORMALIZAR TEXTO
# ===============================
def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("-", "").replace("/", "").replace(" ", "")
    return texto


# ===============================
#  FORMATEAR FECHA HUMANA
# ===============================
def formatear_fecha(fecha_iso):
    fecha = fecha_iso.split("T")[0]
    f = datetime.strptime(fecha, "%Y-%m-%d")
    return f"{f.day} {MESES[f.month]} {f.year}"


# ===============================
# LLAMADA AEMET DOBLE
# ===============================
def llamada_aemet(url):

    r = requests.get(url)

    if r.status_code != 200:
        print("Error HTTP:", r.status_code)
        sys.exit(1)

    respuesta = r.json()

    if "datos" not in respuesta:
        print("Respuesta inesperada:", respuesta)
        sys.exit(1)

    r2 = requests.get(respuesta["datos"])

    if r2.status_code != 200:
        print("Datos expirados:", r2.status_code)
        sys.exit(1)

    return r2.json()


# ===============================
#  CACHE MUNICIPIOS NORMALIZADO
# ===============================
def cargar_municipios():

    if os.path.exists(CACHE_MUNICIPIOS):
        with open(CACHE_MUNICIPIOS, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Descargando municipios desde AEMET...")

    url = f"{BASE_URL}/maestro/municipios?api_key={API_KEY}"
    municipios = llamada_aemet(url)

    #  guardamos diccionario limpio
    data = {}

    for m in municipios:
        clave = normalizar(m["nombre"])
        data[clave] = m["id"][2:]

    with open(CACHE_MUNICIPIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


# ===============================
#  BUSCAR MUNICIPIO
# ===============================
def obtener_codigo_municipio(nombre):

    municipios = cargar_municipios()
    clave = normalizar(nombre)

    return municipios.get(clave)


# ===============================
# PREDICCIÓN HORARIA
# ===============================
def prediccion_horaria(codigo):

    url = f"{BASE_URL}/prediccion/especifica/municipio/horaria/{codigo}?api_key={API_KEY}"
    datos = llamada_aemet(url)

    dias = datos[0]["prediccion"]["dia"]

    for dia in dias:

        print(f"\n{formatear_fecha(dia['fecha'])}")

        for t in dia["temperatura"]:

            hora = t["periodo"]
            temp = t["value"]

            estado = next(
                (e["descripcion"] for e in dia["estadoCielo"] if e["periodo"] == hora),
                "N/A"
            )

            print(f"{hora}:00 → {temp} ºC | {estado}")


# ===============================
# MAIN
# ===============================
municipio = input("Introduce el municipio: ")

codigo = obtener_codigo_municipio(municipio)

if not codigo:
    print("Municipio no encontrado")
    sys.exit(1)

prediccion_horaria(codigo)
