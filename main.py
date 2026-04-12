# -*- coding: utf-8 -*-
"""
פוני - Telegram AI Agent
Webhook server that receives messages from Telegram and responds using AI.
"""

import time
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from config import settings
from agent import get_response
from database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("פוני")

_seen_messages: dict[str, float] = {}
DEDUP_WINDOW = 60


def _cleanup_seen():
    now = time.time()
    expired = [k for k, v in _seen_messages.items() if now - v > DEDUP_WINDOW]
    for k in expired:
        del _seen_messages[k]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("פוני מוכן לפעולה!")
    yield


app = FastAPI(title="פוני", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "פוני"}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle incoming messages from Telegram."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    sender_name = message.get("from", {}).get("first_name", "")
    message_id = str(message.get("message_id", ""))

    if not text.strip():
        return {"ok": True}

    # Skip group messages
    if message["chat"]["type"] != "private":
        return {"ok": True}

    # Deduplication
    _cleanup_seen()
    if message_id in _seen_messages:
        return {"ok": True}
    _seen_messages[message_id] = time.time()

    logger.info(f"Message from {sender_name} ({chat_id}): {text[:50]}...")

    try:
        reply = get_response(str(chat_id), text, sender_name)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = "סליחה, משהו השתבש. נסה שוב בעוד רגע."

    try:
        await send_telegram_message(chat_id, reply)
        logger.info(f"Reply sent to {chat_id}: {reply[:50]}...")
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")

    return {"ok": True}


async def send_telegram_message(chat_id: int, text: str):
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
