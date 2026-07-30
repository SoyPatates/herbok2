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
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
]

if not OPENROUTER_API_KEYS:
    raise RuntimeError("OPENROUTER_API_KEYS boş.")