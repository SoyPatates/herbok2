import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# Discord
# ==========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN bulunamadı.")


# ==========================
# Channels
# ==========================

TASARIM_KANALI = int(os.getenv("TASARIM_KANALI", "0"))

SOHBET_KANALLARI = [
    int(x)
    for x in os.getenv("SOHBET_KANALLARI", "").split(",")
    if x.strip()
]

# ==========================
# Memory
# ==========================

MAX_HISTORY = 20

# ==========================
# Gemini
# ==========================

TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 1024

# ==========================
# OpenRouter
# ==========================

OPENROUTER_API_KEYS = [
    key.strip()
    for key in os.getenv("OPENROUTER_API_KEYS", "").split(",")
    if key.strip()
]

if not OPENROUTER_API_KEYS:
    raise RuntimeError("OPENROUTER_API_KEYS bulunamadı veya boş.")