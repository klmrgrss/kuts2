# controllers/applicant.py
from fasthtml.common import *
from starlette.requests import Request
from ui.layouts import app_layout
from ui.nav_components import tab_nav # Needed for OOB swap
from .utils import get_badge_counts
from monsterui.all import *

# You might need database access later:
# from fastlite import NotFoundError

class ApplicantController:
    def __init__(self, db):
        self.db = db
        # Add table access if needed, e.g., self.applicant_profile_table = db.t.applicant_profile

    def show_applicant_tab(self, request: Request):
        """Renders the 'Taotleja' tab content within a Card."""
        user_email = request.session.get("user_email")
        if not user_email:
             return Div("Authentication Error", cls="text-red-500 p-4")

        page_title = "Taotleja andmed | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

        # Define the standard title style
        TITLE_CLASS = "text-xl font-semibold mb-4" # Example standard title class

        # --- TODO: Fetch actual applicant data later ---
        # Example:
        # try:
        #     profile_data = self.applicant_profile_table[user_email]
        # except NotFoundError:
        #     profile_data = {} # Or default data

        # --- Placeholder View Content Wrapped in Card ---
        # Replace this with a call to a dedicated view function later
        # from ui.components.applicant_view import render_applicant_view
        applicant_content = Card( # Wrap content in Card
            CardBody( # Use CardBody
                H3("Taotleja andmed", cls=TITLE_CLASS), # Use Standard Title
                P(f"Siin hakatakse kuvama kasutaja {user_email} andmeid"),
                P("Nimi"),
                P("Sünniaeg"),
                P("Kehtivad kutsetunnistused"),
                P("Taotluse seisund"),
                # Example: Add a form here later
                # Form(...)
                # cls="p-4 bg-gray-50 rounded shadow-inner" # Remove inner specific styling
            )
        )

        # --- Check for HTMX Request Header ---
        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---") # Updated log
            # 1. Content Fragment (applicant_content - now wrapped in Card)

            # 2. OOB Navigation Swap
            updated_tab_nav = tab_nav(active_tab="taotleja", request=request, badge_counts=badge_counts) # Ensure 'taotleja' is the active tab ID
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

            # 3. OOB Title Swap
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")

            # 4. Return all three components
            return applicant_content, oob_nav, oob_title
        else:
            # Full page load
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---") # Updated log
            return app_layout(
                request=request,
                title=page_title, # Pass title for full page load
                content=applicant_content, # Pass card-wrapped content
                active_tab="taotleja",
                badge_counts=badge_counts # Set the correct active tab ID
            )