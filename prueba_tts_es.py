# Importamos la librería gTTS para texto a voz
# Necesitarás instalarla si no la tienes:
# pip install gTTS
from gtts import gTTS

# Importamos os para poder reproducir el audio (opcional)
import os

# ===============================
# TEXTO A CONVERTIR
# ===============================
texto = "Hola, esta es una prueba de texto a voz en español con gTTS."

# ===============================
# CREAR OBJETO TTS
# ===============================
# text       -> el texto que queremos convertir
# lang       -> idioma, 'es' para español
# slow=False -> velocidad normal de lectura
tts = gTTS(text=texto, lang='es', slow=False)

# ===============================
# GUARDAR AUDIO EN ARCHIVO
# ===============================
# Guardamos el resultado en un archivo mp3 llamado voz_prueba_es.mp3
archivo_salida = "voz_prueba_es.mp3"
tts.save(archivo_salida)
print(f"✅ Audio generado correctamente → {archivo_salida}")

# ===============================
# REPRODUCIR AUDIO (OPCIONAL)
# ===============================
# Dependiendo del sistema operativo se puede usar 'start' (Windows), 'afplay' (Mac), 'mpg321' (Linux)
# Comentado para que no dependa del SO
# os.system(f"start {archivo_salida}")
