import streamlit as st
import requests
import azure.cognitiveservices.speech as speechsdk
from pathlib import Path

AZURE_TRANSLATOR_KEY = st.secrets["AZURE_TRANSLATOR_KEY"]
AZURE_TRANSLATOR_REGION = "francecentral"
AZURE_TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"




AZURE_SPEECH_KEY = st.secrets["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = "francecentral"

IDIOMAS = {
    "en": "en-US-AriaNeural",
    "es": "es-ES-AlvaroNeural",
    "ja": "ja-JP-NanamiNeural"
}

OUTPUT_DIR = Path("audios")
OUTPUT_DIR.mkdir(exist_ok=True)

def traducir(texto, idioma):
    url = f"{AZURE_TRANSLATOR_ENDPOINT}/translate?api-version=3.0&to={idioma}"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-Type": "application/json"
    }
    body = [{"text": texto}]
    r = requests.post(url, headers=headers, json=body)

    if r.status_code != 200:
        st.error(f"❌ Error del traductor ({r.status_code}): {r.text}")
        return texto

    data = r.json()
    if isinstance(data, dict) and "error" in data:
        st.error(f"⚠ Respuesta de error: {data['error']['message']}")
        return texto

    try:
        return data[0]["translations"][0]["text"]
    except Exception:
        st.error(f"⚠Respuesta inesperada: {data}")
        return texto


def generar_audio(texto, idioma):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = IDIOMAS[idioma]

    file_path = OUTPUT_DIR / f"audioguia_{idioma}.mp3"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(file_path))
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(texto).get()

    return file_path

st.title("Generador de Audioguías (Azure)")
texto = st.text_area("Escribe el texto base:", height=200)

if st.button("Generar audios"):
    if not texto.strip():
        st.warning("Por favor, escribe algo primero.")
    else:
        st.info("Generando audioguías...")
        for idioma in IDIOMAS:
            traducido = traducir(texto, idioma)
            st.subheader(f"Traducción ({idioma})")
            st.write(traducido)

            audio_path = generar_audio(traducido, idioma)
            st.audio(str(audio_path), format="audio/mp3")
            with open(audio_path, "rb") as f:
                st.download_button(f"Descargar audio ({idioma})", f, file_name=audio_path.name)
        st.success("¡Listo! Audios generados.")
