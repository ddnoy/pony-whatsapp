# -*- coding: utf-8 -*-
"""
Google Calendar integration for פוני.
Provides tools to read and create calendar events.
"""

import os
import json
import logging
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger("פוני-calendar")

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """Build Google Calendar service from credentials."""
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    creds_info = json.loads(creds_json)
    # Fix private key newlines if escaped (common in env vars)
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def get_calendar_id():
    return os.getenv("GOOGLE_CALENDAR_ID", "primary")


def list_upcoming_events(max_results: int = 10) -> str:
    """Get upcoming events from Google Calendar."""
    try:
        service = _get_service()
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId=get_calendar_id(),
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        if not events:
            return "אין אירועים קרובים ביומן."
        result = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            summary = e.get("summary", "ללא כותרת")
            result.append(f"- {summary}: {start}")
        return "\n".join(result)
    except Exception as ex:
        logger.error(f"Calendar list_events error: {ex}")
        return f"שגיאה בגישה ליומן: {ex}"


def create_event(summary: str, start: str, end: str, description: str = "") -> str:
    """Create a new event in Google Calendar.
    start/end should be ISO 8601 strings, e.g. '2026-04-15T10:00:00+03:00'
    """
    try:
        service = _get_service()
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": "Asia/Jerusalem"},
            "end": {"dateTime": end, "timeZone": "Asia/Jerusalem"},
        }
        created = service.events().insert(
            calendarId=get_calendar_id(), body=event
        ).execute()
        return f"האירוע '{summary}' נוצר בהצלחה ביומן."
    except Exception as ex:
        logger.error(f"Calendar create_event error: {ex}")
        return f"שגיאה ביצירת אירוע: {ex}"


def get_free_slots(date: str, duration_minutes: int = 60) -> str:
    """Find free time slots on a given date (YYYY-MM-DD)."""
    try:
        service = _get_service()
        day_start = f"{date}T06:00:00+03:00"
        day_end = f"{date}T22:00:00+03:00"
        events_result = service.events().list(
            calendarId=get_calendar_id(),
            timeMin=day_start,
            timeMax=day_end,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        if not events:
            return f"ביום {date} אתה פנוי לחלוטין בין 06:00 ל-22:00."
        busy = []
        for e in events:
            start = e["start"].get("dateTime", "")
            end = e["end"].get("dateTime", "")
            summary = e.get("summary", "תפוס")
            if start and end:
                busy.append(f"  - {summary}: {start[11:16]}-{end[11:16]}")
        busy_str = "\n".join(busy)
        return f"ביום {date} יש לך:\n{busy_str}"
    except Exception as ex:
        logger.error(f"Calendar get_free_slots error: {ex}")
        return f"שגיאה בבדיקת היומן: {ex}"
