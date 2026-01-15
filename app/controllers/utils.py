# app/controllers/utils.py
from utils.log import error, debug

def get_badge_counts(db, uid: str) -> dict:
    if not uid: return {}
    counts = {}

    # Work Experience Count
    try:
        # Optimized fetch
        rows = db.t.work_experience('user_email = ?', [uid])
        c = len(rows)
        if c > 0: counts['workex'] = c
    except Exception as e:
        error(f"Badge count error {uid}: {e}")

    # Add other badge logic here (e.g. docs count)
    return counts