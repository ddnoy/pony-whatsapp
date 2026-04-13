# -*- coding: utf-8 -*-
"""
פוני - AI conversation logic with Gemini function calling.
"""

import os
import json
import logging
from google import genai
from google.genai import types
from config import settings
from database import get_history, save_message
from calendar_tools import list_upcoming_events, get_free_slots, create_event
from email_tools import send_email

logger = logging.getLogger("פוני")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Function declarations for Gemini function calling
TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="list_calendar_events",
            description="מציג אירועים קרובים ביומן של דויד",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "max_results": types.Schema(
                        type=types.Type.INTEGER,
                        description="כמה אירועים להציג, ברירת מחדל 10"
                    )
                }
            )
        ),
        types.FunctionDeclaration(
            name="get_free_slots",
            description="בודק מה יש ביומן של דויד בתאריך מסוים ומה הזמן הפנוי",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "date": types.Schema(
                        type=types.Type.STRING,
                        description="תאריך בפורמט YYYY-MM-DD למשל 2026-04-15"
                    )
                },
                required=["date"]
            )
        ),
        types.FunctionDeclaration(
            name="create_calendar_event",
            description="יוצר אירוע חדש ביומן של דויד",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "summary": types.Schema(
                        type=types.Type.STRING,
                        description="כותרת האירוע"
                    ),
                    "start": types.Schema(
                        type=types.Type.STRING,
                        description="זמן התחלה בפורמט ISO 8601 למשל 2026-04-15T10:00:00+03:00"
                    ),
                    "end": types.Schema(
                        type=types.Type.STRING,
                        description="זמן סיום בפורמט ISO 8601 למשל 2026-04-15T11:00:00+03:00"
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="תיאור האירוע (אופציונלי)"
                    )
                },
                required=["summary", "start", "end"]
            )
        ),
        types.FunctionDeclaration(
            name="send_email",
            description="שולח מייל בשם דויד",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "to": types.Schema(
                        type=types.Type.STRING,
                        description="כתובת המייל של הנמען"
                    ),
                    "subject": types.Schema(
                        type=types.Type.STRING,
                        description="נושא המייל"
                    ),
                    "body": types.Schema(
                        type=types.Type.STRING,
                        description="תוכן המייל"
                    )
                },
                required=["to", "subject", "body"]
            )
        ),
    ])
]


def _execute_function(name: str, args: dict) -> str:
    """Execute a function call from Gemini."""
    try:
        if name == "list_calendar_events":
            return list_upcoming_events(args.get("max_results", 10))
        elif name == "get_free_slots":
            return get_free_slots(args["date"])
        elif name == "create_calendar_event":
            return create_event(
                args["summary"],
                args["start"],
                args["end"],
                args.get("description", "")
            )
        elif name == "send_email":
            return send_email(args["to"], args["subject"], args["body"])
        else:
            return f"פונקציה לא מוכרת: {name}"
    except Exception as e:
        logger.error(f"Function {name} error: {e}")
        return f"שגיאה בביצוע {name}: {e}"


def get_response(phone: str, message: str, sender_name: str = "") -> str:
    """Process a message and return an AI response."""

    history = get_history(phone, limit=settings.MAX_HISTORY)

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    config = types.GenerateContentConfig(
        system_instruction=settings.SYSTEM_PROMPT,
        tools=TOOLS,
    )

    # Agentic loop - handle function calls
    max_iterations = 5
    for _ in range(max_iterations):
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=contents,
            config=config,
        )

        # Check for function calls
        has_function_call = False
        function_results = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_function_call = True
                fc = part.function_call
                result = _execute_function(fc.name, dict(fc.args))
                logger.info(f"Function call: {fc.name} -> {result[:80]}")
                function_results.append(
                    types.Part(function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": result}
                    ))
                )

        if has_function_call:
            # Add model response and function results to conversation
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=function_results))
        else:
            # Final text response
            reply = response.text
            save_message(phone, "user", message)
            save_message(phone, "assistant", reply)
            return reply

    # Fallback
    reply = response.text
    save_message(phone, "user", message)
    save_message(phone, "assistant", reply)
    return reply
