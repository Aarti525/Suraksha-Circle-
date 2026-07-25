"""
Config - loads environment variables and sets up shared clients.
Keep all secrets/settings here so the rest of the app never touches os.getenv directly.
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GUARDIAN_PHONE_NUMBER = os.getenv("GUARDIAN_PHONE_NUMBER")

GRAPH_URL = "https://graph.facebook.com/v21.0"
GEMINI_MODEL = "gemini-3.5-flash"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Risk score threshold above which we alert the guardian
GUARDIAN_ALERT_THRESHOLD = 70

# File types we refuse to "safety scan" - see prompts.py for reasoning
DANGEROUS_EXTENSIONS = {".apk", ".exe", ".msi", ".bat", ".sh", ".jar"}
