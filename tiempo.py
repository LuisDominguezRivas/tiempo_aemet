# ===============================
# Importaciones
# ===============================
import requests      # Para hacer llamadas HTTP a la API de AEMET
import sys           # Para salir del programa si ocurre un error
import os            # Para comprobar existencia de archivos y manejar rutas
import json          # Para manejar datos JSON
import unicodedata   # Para normalizar texto (quitar acentos)
from datetime import datetime  # Para formatear fechas
from gtts import gTTS           # Para generar audio a partir de texto (voz)

# ===============================
# Configuración API y archivos
# ===============================
from api import API_KEY, BASE_URL   # Tu API key y URL base de AEMET

CACHE_MUNICIPIOS = "municipios.json"  # Archivo local donde guardamos municipios

# Diccionario para convertir número de mes a nombre en español
MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

# ===============================
# FUNCIONES
# ===============================

def normalizar(texto):
    """
    Normaliza un texto para búsqueda de municipios:
    - convierte a minúsculas
    - quita acentos
    - elimina guiones y espacios
    - permite separar por '/' o ',' en caso de nombres compuestos
    """
    texto = texto.lower()  # minúsculas
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # quita acentos
    palabras = texto.split("/")  # por si hay nombres con "/"
    resultado = []

    for municipio in palabras:
        auxiliar = municipio.split(",")  # por si hay ","
        if len(auxiliar) > 1:
            auxiliar = auxiliar[1] + auxiliar[0]
        else:
            auxiliar = auxiliar[0]

        resultado.append(auxiliar.replace("-", "").replace(" ", ""))
    return resultado


def formatear_fecha(fecha_iso):
    """
    Convierte una fecha ISO ('YYYY-MM-DD') a formato español '31 enero 2026'
    """
    fecha = fecha_iso.split("T")[0]  # nos quedamos solo con la fecha
    f = datetime.strptime(fecha, "%Y-%m-%d")
    return f"{f.day} {MESES[f.month]} {f.year}"


def llamada_aemet(url):
    """
    Hace la llamada a AEMET en 2 pasos:
    1) Llamada inicial que devuelve la URL de los datos
    2) Llamada a la URL real para obtener JSON final
    """
    r = requests.get(url)
    if r.status_code != 200:
        print("Error HTTP:", r.status_code)
        sys.exit(1)

    respuesta = r.json()
    if "datos" not in respuesta:
        print("Respuesta inesperada:", respuesta)
        sys.exit(1)

    # Segunda llamada para obtener los datos reales
    r2 = requests.get(respuesta["datos"])
    if r2.status_code != 200:
        print("Datos expirados o error:", r2.status_code)
        sys.exit(1)

    return r2.json()


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

    # Creamos diccionario limpio con claves normalizadas
    data = {}
    for m in municipios:
        for clave in normalizar(m["nombre"]):
            data[clave] = m["id"][2:]  # quitamos prefijo 'id'

    # Guardamos en archivo local para futuras ejecuciones
    with open(CACHE_MUNICIPIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def obtener_codigo_municipio(nombre):
    """
    Busca el código del municipio por nombre
    """
    municipios = cargar_municipios()
    clave = normalizar(nombre)[0]  # Normalizamos nombre de entrada
    return municipios.get(clave)   # Devuelve None si no se encuentra


def prediccion_horaria(codigo):
    """
    Consulta a AEMET y muestra la predicción horaria.
    Además, genera un archivo de audio con la predicción en español usando gTTS.
    """
    url = f"{BASE_URL}/prediccion/especifica/municipio/horaria/{codigo}?api_key={API_KEY}"
    datos = llamada_aemet(url)
    dias = datos[0]["prediccion"]["dia"]

    # Variable para juntar todo el texto de la predicción
    texto_prediccion = ""

    for dia in dias:
        fecha = formatear_fecha(dia["fecha"])
        texto_prediccion += f"\n{fecha}\n"

        print(f"\n{fecha}")  # Mostramos la fecha

        for t in dia["temperatura"]:
            hora = t["periodo"]
            temp = t["value"]

            # Buscamos descripción del estado del cielo para esa hora
            estado = next(
                (e["descripcion"] for e in dia["estadoCielo"] if e["periodo"] == hora),
                "N/A"
            )

            linea = f"{hora}:00 → {temp} ºC | {estado}"
            print(linea)  # Mostramos la predicción
            texto_prediccion += linea + "\n"  # Añadimos al texto de audio

    # ===============================
    # GENERAR AUDIO CON gTTS
    # ===============================
    tts = gTTS(text=texto_prediccion, lang="es", slow=False)
    archivo_audio = "prediccion_voz.mp3"
    tts.save(archivo_audio)
    print(f"\n✅ Audio generado → {archivo_audio}")


# ===============================
# PROGRAMA PRINCIPAL
# ===============================
municipio = input("Introduce el municipio: ").strip()
codigo = obtener_codigo_municipio(municipio)

if not codigo:
    print(" Municipio no encontrado")
    sys.exit(1)

# Ejecutamos predicción horaria y generamos audio
prediccion_horaria(codigo)
