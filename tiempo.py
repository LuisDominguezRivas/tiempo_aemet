import requests
import sys
import os
import json
from datetime import datetime  # 🔹 Import añadido para formatear fechas

from api import API_KEY, BASE_URL

# ===============================
# CONFIGURACIÓN CACHE MUNICIPIOS
# ===============================
CACHE_MUNICIPIOS = "municipios.json"

# 🔹 Diccionario de meses en español
MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# ===============================
# FUNCIONES
# ===============================
def formatear_fecha(fecha_iso):
    """
    Convierte 'YYYY-MM-DD' o 'YYYY-MM-DDTHH:MM:SS'
    en '31 enero 2026'.
    """
    # Nos quedamos solo con la parte de la fecha
    fecha_solo = fecha_iso.split("T")[0]
    fecha = datetime.strptime(fecha_solo, "%Y-%m-%d")
    return f"{fecha.day} {MESES[fecha.month]} {fecha.year}"


def llamada_aemet(url):
    """
    Hace la llamada AEMET en 2 pasos (obligatorio):
    1) llamada a la API
    2) llamada a la URL real de datos
    """
    r = requests.get(url)

    if r.status_code != 200:
        print("❌ Error HTTP:", r.status_code)
        print(r.text)
        sys.exit(1)

    respuesta = r.json()

    if "datos" not in respuesta:
        print("❌ Respuesta inesperada:", respuesta)
        sys.exit(1)

    # Segunda llamada REAL a los datos
    datos_url = respuesta["datos"]
    datos = requests.get(datos_url)

    if datos.status_code != 200:
        print("❌ Datos expirados o error:", datos.status_code)
        sys.exit(1)

    return datos.json()


def cargar_municipios():
    """
    Carga los municipios desde archivo local si existe.
    Si no existe, los descarga de AEMET y los guarda.
    """
    if os.path.exists(CACHE_MUNICIPIOS):
        with open(CACHE_MUNICIPIOS, "r", encoding="utf-8") as f:
            return json.load(f)

    print("📡 Descargando municipios desde AEMET...")
    url = f"{BASE_URL}/maestro/municipios?api_key={API_KEY}"
    municipios = llamada_aemet(url)

    with open(CACHE_MUNICIPIOS, "w", encoding="utf-8") as f:
        json.dump(municipios, f, ensure_ascii=False, indent=2)

    return municipios


def obtener_codigo_municipio(nombre):
    """
    Busca el código del municipio por nombre (sin mostrarlo por pantalla)
    """
    municipios = cargar_municipios()
    nombre = nombre.lower()

    for m in municipios:
        if m["nombre"].lower() == nombre:
            # Devolvemos el código SIN 'id'
            return m["id"][2:]

    return None


def prediccion_horaria(codigo):
    """
    Muestra la predicción horaria:
    temperatura + estado del cielo
    """
    url = f"{BASE_URL}/prediccion/especifica/municipio/horaria/{codigo}?api_key={API_KEY}"
    datos = llamada_aemet(url)

    pred = datos[0]["prediccion"]["dia"]

    for dia in pred:
        # 🔹 Formatear la fecha a formato humano
        fecha_bonita = formatear_fecha(dia["fecha"])
        print(f"\n📅 {fecha_bonita}")

        for t in dia["temperatura"]:
            hora = t["periodo"]
            temp = t["value"]

            estado = next(
                (e["descripcion"] for e in dia["estadoCielo"] if e["periodo"] == hora),
                "N/A"
            )

            print(f"{hora}:00 → {temp} ºC | {estado}")


# ===============================
# PROGRAMA PRINCIPAL
# ===============================
municipio = input("Introduce el municipio (ejemplo: Montehermoso): ").strip()
codigo = obtener_codigo_municipio(municipio)

if not codigo:
    print("❌ Municipio no encontrado")
    sys.exit(1)

# 🔥 CAMBIO REALIZADO 🔥
# La fecha ahora se muestra en formato "31 enero 2026"
# El código del municipio sigue oculto al usuario

prediccion_horaria(codigo)
