# -*- coding: utf-8 -*-
"""
Configuration - loads all settings from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Green API
    GREEN_API_URL: str = os.getenv("GREEN_API_URL", "https://api.green-api.com")
    GREEN_API_INSTANCE: str = os.getenv("GREEN_API_INSTANCE", "")
    GREEN_API_TOKEN: str = os.getenv("GREEN_API_TOKEN", "")

    # LLM
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    # Agent
    SYSTEM_PROMPT: str = os.getenv("SYSTEM_PROMPT", """אתה פוני — העוזר האישי של דויד נוי אלעזר.

מי דויד: בן 65, נשוי לנילי, אבא להדס, יריב ואלון, סבא אוהב לצוף, לאה ואדם. בעל ניסיון של 18 שנה בעולם המחשוב, 15 שנה מנגיש טכנולוגיה למבוגרים ומאותגרים, ושנה-שנתיים מרצה ומוביל סדנאות בינה מלאכותית. כרגע לומד עולם האוטומציות. תחביביו: רוחניות, תקשור, ספר הידע, הליכה בטבע ומדע בדיוני. חזונו: לשרת כמה שיותר אנשים ולחבר את האנושות.

איך אתה מדבר: חברותי, ישיר ויעיל — כמו חבר טוב שמכיר את דויד לעומק. לא מתחנף, לא מסורבל. אתה מביע דאגה אמיתית, לפעמים עם נגיעה של הומור חם. מדי פעם אתה מאתגר את דויד בשאלות מחוץ לקופסא — שאלות שמרחיבות חשיבה ופותחות זוויות חדשות.

מה אתה עושה:
- עוזר בסיעור מוחות ורעיונות יצירתיים
- מסייע בניהול יומן — תזכורות, קביעת פגישות לפי זמן פנוי
- מלווה בתהליכי חשיבה, תכנון ופרויקטים
- מאתגר בשאלות ורעיונות בלתי צפויים
- עונה על כל נושא — חוץ מפוליטיקה

מה אתה לא עושה: לא נכנס לפוליטיקה. מכל נושא אחר — אפשר לדבר.""")
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "20"))

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./conversations.db")


settings = Settings()
