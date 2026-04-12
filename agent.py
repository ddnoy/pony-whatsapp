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
from calendar_tools import list_upcoming_events, get_free_slots, create_event

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Keywords that trigger calendar lookup
CALENDAR_KEYWORDS = [
    "יומן", "פגישה", "פגישות", "אירוע", "אירועים", "מחר", "השבוע",
    "היום", "מתי", "פנוי", "זמן", "קבע", "לקבוע", "תזכיר", "תזכורת",
    "calendar", "meeting", "schedule", "appointment", "free", "busy"
]

CREATE_KEYWORDS = ["קבע", "צור", "הוסף", "תוסיף", "תקבע", "תיצור", "לקבוע", "create", "add", "schedule"]


def _is_calendar_query(message: str) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in CALENDAR_KEYWORDS)


def _is_create_query(message: str) -> bool:
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in CREATE_KEYWORDS)


def _get_calendar_context(message: str) -> str:
    """Fetch relevant calendar data based on message content."""
    try:
        # Check for specific date mentions
        import re
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", message)

        if date_match:
            date = date_match.group(1)
            return f"[נתוני יומן לתאריך {date}:]\n{get_free_slots(date)}"
        else:
            return f"[אירועים קרובים ביומן:]\n{list_upcoming_events(10)}"
    except Exception as e:
        return f"[שגיאה בגישה ליומן: {e}]"


def get_response(phone: str, message: str, sender_name: str = "") -> str:
    """Process a message and return an AI response."""

    # Load conversation history
    history = get_history(phone, limit=settings.MAX_HISTORY)

    # Build system prompt with calendar data if needed
    system_prompt = settings.SYSTEM_PROMPT

    if _is_calendar_query(message):
        calendar_context = _get_calendar_context(message)
        system_prompt += f"""

יש לך גישה ליומן Google Calendar של דויד. הנה המידע העדכני:

{calendar_context}

השתמש במידע זה כדי לענות על שאלות דויד לגבי היומן שלו. אם דויד מבקש לקבוע פגישה, ציין את הפרטים בצורה ברורה.
"""

    # Build contents list
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
            system_instruction=system_prompt,
        )
    )
    reply = response.text

    # Save conversation
    save_message(phone, "user", message)
    save_message(phone, "assistant", reply)

    return reply
