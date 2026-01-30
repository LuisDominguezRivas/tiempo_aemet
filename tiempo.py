import requests
import sys

from api import API_KEY, BASE_URL 
# ===============================
# FUNCIONES
# ===============================
def llamada_aemet(url):
    """Hace la llamada AEMET en 2 pasos (obligatorio)"""
    r = requests.get(url)
    if r.status_code != 200:
        print("Error HTTP:", r.status_code)
        print(r.text)
        sys.exit(1)

    respuesta = r.json()

    if "datos" not in respuesta:
        print("Respuesta inesperada:", respuesta)
        sys.exit(1)

    # Segunda llamada REAL a los datos
    datos_url = respuesta["datos"]
    datos = requests.get(datos_url)

    if datos.status_code != 200:
        print("Datos expirados o error:", datos.status_code)
        sys.exit(1)

    return datos.json()


def obtener_codigo_municipio(nombre):
    """Busca el ID del municipio por nombre"""
    url = f"{BASE_URL}/maestro/municipios?api_key={API_KEY}"
    municipios = llamada_aemet(url)
    nombre = nombre.lower()

    for m in municipios:
        if m["nombre"].lower() == nombre:
            return m["id"][2:]

    return None


def prediccion_horaria(codigo):
    """Muestra la predicción horaria (temperatura + estado)"""
    url = f"{BASE_URL}/prediccion/especifica/municipio/horaria/{codigo}?api_key={API_KEY}"
    datos = llamada_aemet(url)

    # AEMET devuelve un array con la predicción
    pred = datos[0]["prediccion"]["dia"]

    for dia in pred:
        fecha = dia["fecha"]
        print(f"\n📅 {fecha}")

        # Recorremos las horas
        for t in dia["temperatura"]:
            h = t["periodo"]
            temp = t["value"]
            # Buscar el estado del cielo correspondiente
            estado = next((c["descripcion"] for c in dia["estadoCielo"] if c["periodo"] == h), "N/A")
            print(f"{h}:00 → {temp} ºC | {estado}")


# ===============================
# PROGRAMA PRINCIPAL
# ===============================
municipio = input("Introduce el municipio (ejemplo: Montehermoso): ").strip()
codigo = obtener_codigo_municipio(municipio)

if not codigo:
    print("❌ Municipio no encontrado")
    sys.exit(1)

print(f"✅ Municipio encontrado. Código: {codigo}\n")
prediccion_horaria(codigo)
