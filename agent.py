# -*- coding: utf-8 -*-
"""
פוני - AI conversation logic.
Handles message processing, conversation history, and LLM calls.
"""

import os
from google import genai
from google.genai import types
from config import settings
from database import get_history, save_message

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_response(phone: str, message: str, sender_name: str = "") -> str:
    """Process a message and return an AI response."""

    # Load conversation history
    history = get_history(phone, limit=settings.MAX_HISTORY)

    # Build contents list: history + new message
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    # Call Gemini
    response = client.models.generate_content(
        model=settings.LLM_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=settings.SYSTEM_PROMPT,
        )
    )
    reply = response.text

    # Save conversation
    save_message(phone, "user", message)
    save_message(phone, "assistant", reply)

    return reply
