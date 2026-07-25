"""
Gemini service - handles all calls to the Gemini API for scam analysis,
across every content type (text, image, audio, video, PDF).
"""

import json
from google.genai import types
from config import gemini_client, GEMINI_MODEL
from prompts import SCAM_ANALYSIS_PROMPT

FALLBACK_RESULT = {
    "language_code": "en",
    "risk_score": 50,
    "is_likely_ai_generated": False,
    "explanation": "Could not fully analyze this content. Please be cautious and verify with a trusted family member before taking any action.",
}


def _parse_response(raw_text: str) -> dict:
    """Gemini sometimes wraps JSON in ```json fences - strip those before parsing."""
    cleaned = raw_text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return FALLBACK_RESULT


def analyze_text(content_text: str) -> dict:
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=SCAM_ANALYSIS_PROMPT + content_text,
    )
    return _parse_response(response.text)


def analyze_image(image_bytes: bytes) -> dict:
    prompt = SCAM_ANALYSIS_PROMPT + (
        "\n(The message content is an image - it may be a screenshot of a "
        "chat/payment/notice, a QR code, or a deepfake image. If it's a QR "
        "code, decode the URL/data it encodes and analyze that. If it looks "
        "like an AI-generated or manipulated image, flag it as such.)"
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")],
    )
    return _parse_response(response.text)


def analyze_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> dict:
    prompt = SCAM_ANALYSIS_PROMPT + (
        "\n(The message content is an audio voice note - listen to it. Pay "
        "close attention to whether the voice sounds AI-cloned/synthetic: "
        "unnatural pacing, flat emotional tone, or robotic quality.)"
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)],
    )
    return _parse_response(response.text)


def analyze_video(video_bytes: bytes, mime_type: str = "video/mp4") -> dict:
    prompt = SCAM_ANALYSIS_PROMPT + (
        "\n(The message content is a video - watch and listen to it. Check "
        "for deepfake signs: unnatural blinking, lip-sync mismatch, lighting/"
        "shadow inconsistencies, or a familiar public figure endorsing an "
        "investment scheme - which is almost always a deepfake.)"
    )
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, types.Part.from_bytes(data=video_bytes, mime_type=mime_type)],
    )
    return _parse_response(response.text)


def analyze_pdf(pdf_bytes: bytes) -> dict:
    prompt = SCAM_ANALYSIS_PROMPT + "\n(The message content is a PDF document - read its content and analyze it.)"
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")],
    )
    return _parse_response(response.text)
