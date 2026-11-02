import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": "✅ [REDACTED] stock bot test: Telegram notifications are working.",
    },
    timeout=20,
)
response.raise_for_status()
data = response.json()
if not data.get("ok"):
    raise RuntimeError(data)

print("Telegram test message sent successfully.")
