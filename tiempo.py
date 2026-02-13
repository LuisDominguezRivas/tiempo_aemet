# ===============================
# IMPORTACIONES
# ===============================

import requests         # Para hacer llamadas HTTP a la API de AEMET
import sys              # Para poder terminar el programa con sys.exit() en caso de error
import os               # Para trabajar con archivos y comprobar si existen
import json             # Para leer y escribir archivos JSON (cache de municipios)
import unicodedata      # Para eliminar acentos y caracteres especiales
from datetime import datetime  # Para trabajar con fechas y formatearlas

from api import API_KEY, BASE_URL  # Importa tu clave API y la URL base de AEMET desde api.py

# ===============================
# CONFIGURACIÓN
# ===============================

CACHE_MUNICIPIOS = "municipios.json"  # Archivo local donde guardaremos los municipios

# Diccionario para mostrar meses en español en lugar de números
MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# ===============================
# FUNCIÓN PARA NORMALIZAR TEXTO
# ===============================

def normalizar(texto):
    """
    Convierte un nombre de municipio a una versión limpia para buscar:
    - Minúsculas
    - Sin acentos
    - Sin espacios ni guiones
    - Permite nombres con / o comas
    """
    texto = texto.lower()  # Convertir a minúsculas
    texto = unicodedata.normalize("NFD", texto)  # Separar caracteres de sus acentos
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # Quitar acentos

    partes = texto.split("/")  # Si hay nombres alternativos separados por /, separamos

    resultado = []

    for municipio in partes:
        aux = municipio.split(",")  # Si hay formato "Nombre, El" lo separamos

        if len(aux) > 1:
            aux = aux[1] + aux[0]  # Reordenamos "El Barco de Ávila"
        else:
            aux = aux[0]  # Si no hay coma, usamos tal cual

        limpio = aux.replace("-", "").replace(" ", "")  # Quitar guiones y espacios
        resultado.append(limpio)  # Guardamos el nombre limpio

    return resultado  # Devolvemos lista de nombres limpios

# ===============================
# FUNCIÓN PARA FORMATEAR FECHA
# ===============================

def formatear_fecha(fecha_iso):
    """
    Convierte la fecha de la API (formato ISO) a formato humano:
    Ejemplo: "2026-01-31T00:00:00" → "31 enero 2026"
    """
    fecha = fecha_iso.split("T")[0]  # Solo nos quedamos con "YYYY-MM-DD"
    f = datetime.strptime(fecha, "%Y-%m-%d")  # Convertimos string → objeto fecha
    return f"{f.day} {MESES[f.month]} {f.year}"  # Devolvemos en formato "día mes año"

# ===============================
# FUNCIÓN PARA HACER LLAMADAS A AEMET
# ===============================

def llamada_aemet(url):
    """
    Hace la llamada a la API AEMET en dos pasos:
    1) Llamada al endpoint de la API
    2) Llamada a la URL real que contiene los datos
    """
    r = requests.get(url)  # Primera llamada a la API

    if r.status_code != 200:  # Si hay error HTTP
        print("Error HTTP:", r.status_code)
        sys.exit(1)  # Salir del programa

    respuesta = r.json()  # Convertimos la respuesta a JSON

    if "datos" not in respuesta:  # Comprobamos que venga la URL real
        print("Respuesta inesperada:", respuesta)
        sys.exit(1)

    r2 = requests.get(respuesta["datos"])  # Segunda llamada a la URL real de datos

    if r2.status_code != 200:
        print("Datos expirados:", r2.status_code)
        sys.exit(1)

    return r2.json()  # Devolvemos los datos reales

# ===============================
# FUNCIÓN PARA CARGAR MUNICIPIOS (CACHE)
# ===============================

def cargar_municipios():
    """
    Carga los municipios desde un archivo local si existe.
    Si no, los descarga de AEMET y los guarda en un diccionario normalizado.
    """
    if os.path.exists(CACHE_MUNICIPIOS):  # Si el archivo ya existe
        with open(CACHE_MUNICIPIOS, "r", encoding="utf-8") as f:
            return json.load(f)  # Lo leemos y devolvemos

    print("Descargando municipios desde AEMET...")  # Mensaje informativo

    url = f"{BASE_URL}/maestro/municipios?api_key={API_KEY}"
    municipios = llamada_aemet(url)  # Descargamos lista completa

    data = {}  # Diccionario limpio: clave → código de municipio

    for m in municipios:
        claves = normalizar(m["nombre"])  # Normalizamos el nombre

        for clave in claves:
            data[clave] = m["id"][2:]  # Guardamos código sin prefijo 'id'

    # Guardamos el diccionario en cache
    with open(CACHE_MUNICIPIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data  # Devolvemos diccionario limpio

# ===============================
# FUNCIÓN PARA BUSCAR CÓDIGO DE MUNICIPIO
# ===============================

def obtener_codigo_municipio(nombre):
    """
    Busca el código interno de AEMET para el municipio dado por el usuario
    """
    municipios = cargar_municipios()  # Cargamos cache o API
    claves = normalizar(nombre)  # Normalizamos nombre de entrada

    for clave in claves:  # Puede haber varias versiones
        if clave in municipios:
            return municipios[clave]  # Devolvemos código encontrado

    return None  # Si no se encuentra

# ===============================
# FUNCIÓN PARA MOSTRAR PREDICCIÓN HORARIA
# ===============================

def prediccion_horaria(codigo):
    """
    Muestra la predicción horaria para hoy y próximos días:
    - hora
    - temperatura
    - estado del cielo
    """
    url = f"{BASE_URL}/prediccion/especifica/municipio/horaria/{codigo}?api_key={API_KEY}"
    datos = llamada_aemet(url)  # Descargamos datos

    dias = datos[0]["prediccion"]["dia"]  # Lista de días

    for dia in dias:
        print(f"\n{formatear_fecha(dia['fecha'])}")  # Fecha en formato humano

        for t in dia["temperatura"]:  # Recorremos cada hora
            hora = t["periodo"]  # Hora
            temp = t["value"]    # Temperatura

            # Buscamos el estado del cielo correspondiente a esa hora
            estado = next(
                (e["descripcion"] for e in dia["estadoCielo"] if e["periodo"] == hora),
                "N/A"  # Si no hay información
            )

            print(f"{hora}:00 → {temp} ºC | {estado}")  # Mostramos línea final

# ===============================
# PROGRAMA PRINCIPAL
# ===============================

municipio = input("Introduce el municipio: ").strip()  # Pedimos al usuario

codigo = obtener_codigo_municipio(municipio)  # Obtenemos código interno

if not codigo:  # Si no se encuentra
    print("Municipio no encontrado")
    sys.exit(1)  # Salir del programa

prediccion_horaria(codigo)  # Mostramos predicción horaria
