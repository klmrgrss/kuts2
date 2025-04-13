# gem/controllers/review.py

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response # For submit response
from fastlite import NotFoundError # Import if needed for specific checks

# Import layouts and nav components
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from ui.review_view import render_review_page

# Import view function (will be created in Phase 2)
# from ui.review_view import render_review_page # Placeholder for now

class ReviewController:
    def __init__(self, db):
        self.db = db
        # Accessor for tables (adjust names if needed based on database.py)
        self.users_table = db.t.users
        self.profile_table = db.t.applicant_profile
        self.qual_table = db.t.applied_qualifications
        self.exp_table = db.t.work_experience
        self.edu_table = db.t.education
        self.training_files_table = db.t.training_files
        self.emp_proof_table = db.t.employment_proof

    def _fetch_data_for_user(self, table, user_email: str, is_list: bool = True):
        """Helper to fetch data from a table for a specific user."""
        try:
            # Using the fetch-all-then-filter pattern
            all_records = table(order_by='id') # Assumes an 'id' column exists for ordering
            user_records = [r for r in all_records if r.get('user_email') == user_email]
            if is_list:
                return user_records
            else:
                # Return the first record found, or None
                return user_records[0] if user_records else None
        except Exception as e:
            # Log specific table fetching error
            # table_name = table.table # Adjust if fastlite API differs
            print(f"--- ERROR fetching data for {user_email}: {e} ---")
            return [] if is_list else None

    def _get_all_application_data(self, user_email: str) -> dict:
        """Fetches all application data for the review page."""
        print(f"--- DEBUG [ReviewController]: Fetching all data for {user_email} ---")
        data = {}

        # Fetch Profile (users + applicant_profile) - Assuming user_email is PK for both
        try:
            data['user'] = self.users_table[user_email] # Direct lookup if PK
        except NotFoundError:
             data['user'] = {}
             print(f"--- WARNING: User record not found for {user_email} ---")
        except Exception as e:
             data['user'] = {}
             print(f"--- ERROR fetching user data for {user_email}: {e} ---")

        try:
            # Assuming user_email is PK, otherwise use _fetch_data_for_user
            data['profile'] = self.profile_table[user_email]
        except NotFoundError:
             data['profile'] = {}
             print(f"--- WARNING: Applicant profile not found for {user_email} ---")
        except Exception as e:
            data['profile'] = {}
            print(f"--- ERROR fetching profile data for {user_email}: {e} ---")


        # Fetch Lists using the helper function
        data['qualifications'] = self._fetch_data_for_user(self.qual_table, user_email, is_list=True)
        data['experience'] = self._fetch_data_for_user(self.exp_table, user_email, is_list=True)
        data['experience_count'] = len(data['experience']) 
        data['education'] = self._fetch_data_for_user(self.edu_table, user_email, is_list=False) # Expecting one education record
        data['training_files'] = self._fetch_data_for_user(self.training_files_table, user_email, is_list=True)

        # Fetch Employment Proof (assuming one record per user, user_email=PK)
        try:
            data['employment_proof'] = self.emp_proof_table[user_email]
        except NotFoundError:
             data['employment_proof'] = {}
        except Exception as e:
            data['employment_proof'] = {}
            print(f"--- ERROR fetching employment proof data for {user_email}: {e} ---")


        print(f"--- DEBUG [ReviewController]: Data fetched. Keys: {list(data.keys())} ---")
        return data

    def show_review_tab(self, request: Request):
        """Renders the 'Taotluse ülevaatamine' tab."""
        user_email = request.session.get("user_email")
        if not user_email:
             # Handle authentication error appropriately
             # Maybe redirect or return an error component
             return Div("Authentication Error", cls="text-red-500 p-4") # Placeholder

        page_title = "Taotluse ülevaatamine | Ehitamise valdkonna kutsete taotlemine"

        # Fetch all data needed for the review
        application_data = self._get_all_application_data(user_email)

        review_content = render_review_page(application_data)

        # Determine response type (Full page or HTMX fragment)
        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---") # Updated log
            # 1. Content Fragment (review_content)

            # 2. OOB Navigation Swap
            updated_tab_nav = tab_nav(active_tab="ulevaatamine", request=request, badge_counts={}) # Use 'ulevaatamine' ID
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

            # 3. OOB Title Swap
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")

            # 4. Return all three components
            return review_content, oob_nav, oob_title
        else:
            # Full page load
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---") # Updated log
            return app_layout(
                request=request,
                title=page_title, # Pass title for full page load
                content=review_content,
                active_tab="ulevaatamine" # Use 'ulevaatamine' ID
            )

    async def submit_application(self, request: Request):
        """Handles the final application submission."""
        user_email = request.session.get("user_email")
        if not user_email:
             # Return error response, e.g., a ToastAlert or error message div
             return Div("Authentication Error - Cannot Submit", cls="text-red-500") # Placeholder

        print(f"--- INFO: Received submission request from {user_email} ---")

        # --- TODO: Implement actual submission logic ---
        # 1. Validate if application is complete (optional, or rely on review)
        # 2. Update application status in the database (e.g., set status='Submitted')
        # 3. Trigger email sending to applicant (and maybe admin)
        # 4. Handle potential errors during submission (DB update, email sending)
        # ---

        # For now, return a simple success message or redirect
        # Option 1: Redirect to a dedicated "Success" page (needs new route/page)
        # return Response(headers={'HX-Redirect': '/app/submission_success'})

        # Option 2: Return a success message to be displayed on the review page (needs target div)
        success_message = Div(
            H3("Taotlus esitatud!"),
            P(f"Sinu taotlus on edukalt esitatud menetlemiseks. Koopia saadeti aadressile {user_email}."),
            # Maybe add a link back to the dashboard/start
            A(Button("Tagasi avalehele"), href="/app"),
            id="tab-content-container", # Replace the whole tab content
            cls="p-6 text-center"
        )
        # Need to also swap the nav to prevent user clicking back into review?
        updated_tab_nav = tab_nav(active_tab="ulevaatamine", request=request, badge_counts={}) # Keep nav state? Or disable?
        oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

        return success_message, oob_nav # Example: Replace content + update nav