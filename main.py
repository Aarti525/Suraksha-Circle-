"""
Suraksha Circle - main app
----------------------------
This file only handles the WhatsApp webhook and routes each message type to
the right analysis function. The actual logic lives in:
  - config.py            settings and shared clients
  - prompts.py            the scam-detection prompt sent to Gemini
  - gemini_service.py     content analysis (text/image/audio/video/PDF)
  - whatsapp_service.py   sending/receiving via the WhatsApp Cloud API
  - tts_service.py        voice-note replies
"""

import json
from fastapi import FastAPI, Request, BackgroundTasks

from config import VERIFY_TOKEN, GUARDIAN_ALERT_THRESHOLD, DANGEROUS_EXTENSIONS
from prompts import DANGEROUS_FILE_WARNING
import gemini_service
from whatsapp_service import send_whatsapp_text, get_media_url, download_media, alert_guardian
from tts_service import send_voice_reply

app = FastAPI()


def is_dangerous_file(filename: str) -> bool:
    filename = (filename or "").lower()
    return any(filename.endswith(ext) for ext in DANGEROUS_EXTENSIONS)


def handle_result(sender_number: str, result: dict):
    """Send the text + voice reply for any analyzed content, and alert the guardian if risky."""
    risk_score = result.get("risk_score", 50)
    explanation = result.get("explanation", "Unable to analyze.")
    language_code = result.get("language_code", "en")
    is_ai_generated = result.get("is_likely_ai_generated", False)

    if risk_score >= 70:
        emoji = "🔴"
    elif risk_score >= 40:
        emoji = "🟠"
    else:
        emoji = "🟢"

    ai_tag = " 🤖 (possible AI-generated/cloned content)" if is_ai_generated else ""
    reply = f"{emoji} Risk Score: {risk_score}/100{ai_tag}\n\n{explanation}"

    send_whatsapp_text(sender_number, reply)
    send_voice_reply(sender_number, explanation, language_code)

    if risk_score >= GUARDIAN_ALERT_THRESHOLD:
        alert_guardian(sender_number, risk_score, explanation)


@app.get("/webhook")
async def verify_webhook(request: Request):
    """Meta calls this once, to confirm you own this server, before it will send you real messages."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "verification failed"}


@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    # Hand off to a background task and ack Meta immediately - if we make Meta
    # wait for the full Gemini + TTS + media-upload pipeline before responding,
    # it can time out and retry, which is what was causing the "slow / stuck"
    # feeling. This way Meta gets an instant 200, and the real work happens
    # right after, at whatever speed the AI pipeline genuinely takes.
    background_tasks.add_task(process_message, body)
    return {"status": "received"}


def process_message(body: dict):
    print("Incoming payload:", json.dumps(body, indent=2))

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            # Status update (delivered/read), not a new message - ignore it
            return {"status": "ignored"}

        message = value["messages"][0]
        sender_number = message["from"]
        msg_type = message["type"]

        if msg_type == "text":
            result = gemini_service.analyze_text(message["text"]["body"])

        elif msg_type == "image":
            media_bytes = download_media(get_media_url(message["image"]["id"]))
            result = gemini_service.analyze_image(media_bytes)

        elif msg_type == "audio":
            media_bytes = download_media(get_media_url(message["audio"]["id"]))
            result = gemini_service.analyze_audio(media_bytes, mime_type="audio/ogg")

        elif msg_type == "video":
            media_bytes = download_media(get_media_url(message["video"]["id"]))
            result = gemini_service.analyze_video(media_bytes, mime_type="video/mp4")

        elif msg_type == "document":
            doc_info = message["document"]
            filename = doc_info.get("filename", "")

            if is_dangerous_file(filename):
                send_whatsapp_text(sender_number, DANGEROUS_FILE_WARNING)
                send_voice_reply(sender_number, DANGEROUS_FILE_WARNING, "en")
                alert_guardian(sender_number, 90, f"Received a suspicious app/program file: {filename}")
                return {"status": "dangerous file warned"}

            if filename.lower().endswith(".pdf"):
                media_bytes = download_media(get_media_url(doc_info["id"]))
                result = gemini_service.analyze_pdf(media_bytes)
            else:
                send_whatsapp_text(sender_number, "This document type isn't supported yet - please forward text, a screenshot, PDF, or voice note.")
                return {"status": "unsupported document type acknowledged"}

        else:
            send_whatsapp_text(sender_number, "This file type isn't supported yet - please forward text, a screenshot, or a voice note.")
            return {"status": "unsupported type acknowledged"}

        handle_result(sender_number, result)

    except Exception as e:
        print("Error processing message:", e)

    return {"status": "ok"}


@app.get("/")
async def health_check():
    return {"status": "Suraksha Circle is running"}