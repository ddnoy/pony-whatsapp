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
from calendar_tools import list_upcoming_events, create_event, get_free_slots

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CALENDAR_SYSTEM_ADDON = """

יש לך גישה ליומן Google Calendar של דויד. כשדויד שואל על פגישות, זמן פנוי, או רוצה לקבוע אירוע — השתמש בפונקציות הבאות:
- list_events: מציג אירועים קרובים
- get_free: בודק זמן פנוי בתאריך מסוים (פורמט: YYYY-MM-DD)
- create_event: יוצר אירוע חדש (כותרת, תאריך התחלה, תאריך סיום בפורמט ISO)

כשאתה צריך מידע מהיומן, כתוב שורה בפורמט הבא (בשורה נפרדת):
[CALENDAR:list_events]
[CALENDAR:get_free:2026-04-15]
[CALENDAR:create_event:כותרת|2026-04-15T10:00:00+03:00|2026-04-15T11:00:00+03:00]
"""


def _handle_calendar_commands(text: str) -> tuple[str, str]:
    """Extract and execute calendar commands from response."""
    lines = text.split("\n")
    results = []
    clean_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[CALENDAR:"):
            cmd = stripped[10:-1]  # remove [CALENDAR: and ]
            if cmd == "list_events":
                results.append(list_upcoming_events())
            elif cmd.startswith("get_free:"):
                date = cmd.split(":", 1)[1]
                results.append(get_free_slots(date))
            elif cmd.startswith("create_event:"):
                parts = cmd.split(":", 1)[1].split("|")
                if len(parts) >= 3:
                    results.append(create_event(parts[0], parts[1], parts[2]))
        else:
            clean_lines.append(line)

    clean_text = "\n".join(clean_lines).strip()
    calendar_data = "\n".join(results)
    return clean_text, calendar_data


def get_response(phone: str, message: str, sender_name: str = "") -> str:
    """Process a message and return an AI response."""

    # Load conversation history
    history = get_history(phone, limit=settings.MAX_HISTORY)

    # Build contents list
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    system_prompt = settings.SYSTEM_PROMPT + CALENDAR_SYSTEM_ADDON

    # First LLM call
    response = client.models.generate_content(
        model=settings.LLM_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
    )
    reply = response.text

    # Handle calendar commands
    clean_reply, calendar_data = _handle_calendar_commands(reply)

    # If calendar data was fetched, do a second call with the data
    if calendar_data:
        contents.append(types.Content(role="model", parts=[types.Part(text=clean_reply)]))
        contents.append(types.Content(role="user", parts=[types.Part(
            text=f"[נתוני יומן:]\n{calendar_data}\n\nעכשיו ענה לדויד על סמך המידע הזה.")]))

        response2 = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
        )
        reply = response2.text

    # Save conversation
    save_message(phone, "user", message)
    save_message(phone, "assistant", reply)

    return reply
