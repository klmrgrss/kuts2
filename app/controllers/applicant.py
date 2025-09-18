# controllers/applicant.py
from fasthtml.common import *
from starlette.requests import Request
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from monsterui.all import *
from fastlite import NotFoundError
from typing import Optional

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

    def show_applicant_tab(self, request: Request):
        """Renders the 'Taotleja' tab content with live DB data."""
        user_email = request.session.get("user_email")
        if not user_email:
             return Div("Authentication Error", cls="text-red-500 p-4")

        page_title = "Taotleja andmed | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

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
            print(f"--- WARN [ApplicantController]: User not found in 'users' table for email: {user_email} ---")
            db_data = {
                "E-post": user_email, "Sünniaeg": "Andmed puuduvad",
                "Kehtivad kutsetunnistused": "Andmed puuduvad", "Taotluse seisund": "Viga andmete laadimisel"
            }
        except Exception as e:
            print(f"--- ERROR [ApplicantController]: Could not fetch data for {user_email}. Error: {e} ---")
            db_data["Taotluse seisund"] = "Viga andmete laadimisel"

        applicant_content = Div(
            Span( applicant_name, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300" ),
            Div(
                Div(
                    *[Div( P(key, cls="font-semibold text-muted-foreground w-1/3"), P(value, cls="w-2/3") ) for key, value in db_data.items()],
                    cls="space-y-3"
                ),
                Hr(cls="my-6 border-border"),
                Div(
                    A( Button("Jätka taotluse täitmist", cls=ButtonT.primary), href="/app/kutsed" ),
                    A("Logi välja", href="/logout", cls="text-sm text-muted-foreground hover:underline"),
                    cls="flex justify-between items-center"
                ),
                cls="p-6"
            ),
            cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
        )

        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---")
            updated_tab_nav = tab_nav(active_tab="taotleja", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            # Note: The "taotleja" tab is not in the TABS dict, so it won't be highlighted.
            # You would need to add it to TABS in nav_components.py for it to appear/be active.
            return applicant_content, oob_nav, oob_title
        else:
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---")
            return app_layout(
                request=request,
                title=page_title,
                content=applicant_content,
                active_tab="taotleja",
                badge_counts=badge_counts,
                db=self.db # Pass the db connection
            )