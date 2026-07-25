"""
Voice reply service - converts text explanations into spoken WhatsApp voice notes.
"""

import io
from gtts import gTTS
from whatsapp_service import upload_whatsapp_media, send_whatsapp_audio


def text_to_speech_bytes(text: str, lang_code: str) -> bytes:
    """Convert text to spoken audio (mp3 bytes). Falls back to English if gTTS doesn't support the language code."""
    try:
        tts = gTTS(text=text, lang=lang_code)
    except Exception:
        tts = gTTS(text=text, lang="en")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def send_voice_reply(to_number: str, explanation: str, lang_code: str):
    """Best-effort voice reply - if this fails, the text reply already went out, so we just log and move on."""
    try:
        audio_bytes = text_to_speech_bytes(explanation, lang_code)
        media_id = upload_whatsapp_media(audio_bytes, "audio/mpeg")
        if media_id:
            send_whatsapp_audio(to_number, media_id)
    except Exception as e:
        print("Voice reply failed:", e)
