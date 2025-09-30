# controllers/applicant.py
from fasthtml.common import *
from starlette.requests import Request
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from monsterui.all import *
from fastlite import NotFoundError
from typing import Optional, Tuple

def format_estonian_date(iso_date_str: Optional[str]) -> str:
    """Converts 'YYYY-MM-DD' to 'DD.MM.YYYY'. Returns a fallback on error."""
    if not iso_date_str:
        return "Andmed puuduvad"
    try:
        year, month, day = iso_date_str.split('-')
        if not (year.isdigit() and month.isdigit() and day.isdigit() and len(year) == 4):
            return iso_date_str
        return f"{day}.{month}.{year}"
    except (ValueError, TypeError):
        return iso_date_str

class ApplicantController:
    def __init__(self, db):
        self.db = db
        self.users_table = db.t.users
        self.qualifications_table = db.t.applied_qualifications

    def _get_applicant_data(self, user_email: str) -> Tuple[dict, str]:
        """
        Internal helper to fetch data for the applicant dashboard.
        Returns a tuple of (data_dict, applicant_name).
        """
        applicant_name = "Taotleja andmed"
        db_data = {}
        try:
            user_data = self.users_table[user_email]
            applicant_name = user_data.get('full_name') or applicant_name
            db_data["E-post"] = user_email
            db_data["Sünniaeg"] = format_estonian_date(user_data.get('birthday'))
            db_data["Kehtivad kutsetunnistused"] = "Andmed puuduvad"
            all_quals = self.qualifications_table(order_by='id')
            user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            db_data["Taotluse seisund"] = "Koostamisel" if user_quals else "Alustamata"
        except NotFoundError:
            print(f"--- WARN [ApplicantController]: User not found for email: {user_email} ---")
            db_data = { "E-post": user_email, "Sünniaeg": "Andmed puuduvad", "Kehtivad kutsetunnistused": "Andmed puuduvad", "Taotluse seisund": "Viga" }
        except Exception as e:
            print(f"--- ERROR [ApplicantController]: Could not fetch data for {user_email}. Error: {e} ---")
            db_data["Taotluse seisund"] = "Viga andmete laadimisel"
        
        return db_data, applicant_name

    def show_applicant_tab(self, request: Request):
        """
        This method is now DEPRECATED for full page loads but could be repurposed
        for an HTMX target if needed in the future. For now, it redirects to the dashboard.
        """
        return RedirectResponse(url="/dashboard", status_code=303)