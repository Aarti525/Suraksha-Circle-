"""
WhatsApp service - all direct interaction with the Meta WhatsApp Cloud API:
sending text/audio replies, uploading/downloading media, alerting the guardian.
"""

import requests
from config import WHATSAPP_TOKEN, PHONE_NUMBER_ID, GRAPH_URL, GUARDIAN_PHONE_NUMBER


def send_whatsapp_text(to_number: str, message: str):
    url = f"{GRAPH_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }
    r = requests.post(url, headers=headers, json=payload)
    print("Send message response:", r.status_code, r.text)


def send_whatsapp_audio(to_number: str, media_id: str):
    url = f"{GRAPH_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "audio",
        "audio": {"id": media_id},
    }
    r = requests.post(url, headers=headers, json=payload)
    print("Send audio response:", r.status_code, r.text)


def upload_whatsapp_media(file_bytes: bytes, mime_type: str) -> str:
    """Upload a file (e.g. our TTS voice reply) to WhatsApp, returns a media_id to reference when sending."""
    url = f"{GRAPH_URL}/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {"file": ("reply.mp3", file_bytes, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}
    r = requests.post(url, headers=headers, files=files, data=data)
    print("Upload media response:", r.status_code, r.text)
    return r.json().get("id")


def get_media_url(media_id: str) -> str:
    url = f"{GRAPH_URL}/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.json().get("url")


def download_media(media_url: str) -> bytes:
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    r = requests.get(media_url, headers=headers)
    return r.content


def alert_guardian(sender_number: str, risk_score: int, explanation: str):
    if not GUARDIAN_PHONE_NUMBER:
        return
    alert_msg = (
        f"⚠️ Suraksha Circle Alert\n\n"
        f"A message sent to {sender_number} was flagged with risk score {risk_score}/100.\n\n"
        f"AI explanation: {explanation}\n\n"
        f"Please check in with them directly."
    )
    send_whatsapp_text(GUARDIAN_PHONE_NUMBER, alert_msg)
