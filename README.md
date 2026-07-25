# Suraksha Circle

A WhatsApp-native, regional-language scam-detection assistant built for elderly and low-literacy users in India, with automatic family-guardian alerts on high-risk messages.

## What it does

A user forwards a suspicious WhatsApp message — text, image, audio, video, or PDF — to the bot. Suraksha Circle analyzes it with Gemini, returns a risk score and explanation in the same language it was received in, and speaks the response back as a voice note so nothing needs to be read. If the risk score crosses a threshold, a designated family guardian is alerted automatically.

## Features

- Full pipeline for text, images (including QR codes and Marathi-language content), audio, video, and PDF attachments
- Risk-score replies matched to the input's language, delivered as both text and voice notes
- Detects traditional scams, AI-generated scams (voice cloning, deepfakes, AI investment fraud — flagged via `is_likely_ai_generated`), and current-era tactics: FASTag/toll scams, quishing, remote-access (AnyDesk-style) scams, task-based job scams, and fake utility bill scams
- APK/EXE attachments get a blanket "don't scan, don't open" warning instead of a false safety verdict
- Automatic guardian alert when `risk_score >= 70`

## Tech stack

- **Backend:** FastAPI (Python), using `BackgroundTasks` to acknowledge WhatsApp webhooks instantly and process messages asynchronously
- **Messaging:** Meta WhatsApp Cloud API (free tier)
- **AI:** Google Gemini via the `google-genai` SDK
- **Voice replies:** gTTS
- **Local dev tunneling:** ngrok

## Project structure

```
SurakshaCircle/
├── main.py               # FastAPI app & webhook routes
├── config.py              # Environment/config loading
├── prompts.py              # Gemini prompt templates
├── gemini_service.py       # Gemini API integration & scam analysis
├── whatsapp_service.py     # WhatsApp Cloud API integration
├── tts_service.py          # gTTS voice reply generation
└── requirements.txt
```

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_key_here
   WHATSAPP_ACCESS_TOKEN=your_token_here
   WHATSAPP_PHONE_NUMBER_ID=your_id_here
   VERIFY_TOKEN=your_verify_token_here
   ```
3. Run the server:
   ```bash
   python -m uvicorn main:app --reload
   ```
4. Point a WhatsApp Cloud API webhook (via ngrok during development) at your `/webhook` endpoint.

## Status

Core detection pipeline is complete and working end-to-end. Currently deploying to Railway for always-on hosting with a permanent WhatsApp access token, replacing the local dev setup.

## Roadmap

- [ ] Deploy to Railway with a permanent webhook URL
- [ ] Optional web dashboard for guardians

---

Built as a college project to make scam detection accessible to the family members who need it most, in the language they're most comfortable with.
