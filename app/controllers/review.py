# gem/controllers/review.py

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from fastlite import NotFoundError
from collections import defaultdict

# Import layouts and nav components
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from ui.review_view import render_review_page
from config.qualification_data import kt # <-- Import qualification master data

class ReviewController:
    def __init__(self, db):
        self.db = db
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
            all_records = table(order_by='id')
            user_records = [r for r in all_records if r.get('user_email') == user_email]
            if is_list:
                return user_records
            else:
                return user_records[0] if user_records else None
        except Exception as e:
            print(f"--- ERROR fetching data for {user_email}: {e} ---")
            return [] if is_list else None

    def _process_qualifications(self, qualifications: list) -> list:
        """
        Groups qualifications and identifies if a full specialization ('Tervik') is selected.
        """
        if not qualifications:
            return []

        # Group selected specialisations by their main qualification
        grouped_quals = defaultdict(list)
        for q in qualifications:
            key = (q.get('level'), q.get('qualification_name'))
            grouped_quals[key].append(q.get('specialisation'))

        processed_list = []
        for (level, name), specialisations in grouped_quals.items():
            # Find the corresponding master data in kt
            master_data = kt.get(level, {}).get(name, [])
            
            # Check if all possible specialisations were selected
            # Note: "Valikkompetentsid puuduvad" is a special case.
            is_tervik = (
                len(specialisations) > 0 and
                len(specialisations) == len(master_data) and
                master_data != ["Valikkompetentsid puuduvad"]
            )

            if is_tervik:
                # If it's a full specialization, add a single summary item
                processed_list.append({
                    'level': level,
                    'qualification_name': name,
                    'is_tervik': True # Flag for the view to use
                })
            else:
                # Otherwise, add back the individual items
                for s in specialisations:
                    processed_list.append({
                        'level': level,
                        'qualification_name': name,
                        'specialisation': s,
                        'is_tervik': False
                    })
        return processed_list


    def _get_all_application_data(self, user_email: str) -> dict:
        """Fetches and processes all application data for the review page."""
        print(f"--- DEBUG [ReviewController]: Fetching all data for {user_email} ---")
        data = {}

        try:
            data['user'] = self.users_table[user_email]
        except NotFoundError:
             data['user'] = {}
        
        try:
            data['profile'] = self.profile_table[user_email]
        except NotFoundError:
             data['profile'] = {}

        # Fetch and then process qualifications
        raw_qualifications = self._fetch_data_for_user(self.qual_table, user_email, is_list=True)
        data['qualifications'] = self._process_qualifications(raw_qualifications)
        
        data['experience'] = self._fetch_data_for_user(self.exp_table, user_email, is_list=True)
        data['experience_count'] = len(data['experience']) 
        
        # Fetch document-based education from the 'documents' table
        all_docs = self._fetch_data_for_user(self.db.t.documents, user_email, is_list=True)
        education_docs = [d for d in all_docs if d.get('document_type') == 'education']
        data['education'] = education_docs[0] if education_docs else {}

        data['training_files'] = [d for d in all_docs if d.get('document_type') == 'training']
        
        emp_proof_docs = [d for d in all_docs if d.get('document_type') == 'employment_proof']
        data['employment_proof'] = emp_proof_docs[0] if emp_proof_docs else {}


        print(f"--- DEBUG [ReviewController]: Data fetched. Keys: {list(data.keys())} ---")
        return data

    def show_review_tab(self, request: Request):
        """Renders the 'Taotluse ülevaatamine' tab."""
        user_email = request.session.get("user_email")
        if not user_email:
             return Div("Authentication Error", cls="text-red-500 p-4")

        page_title = "Taotluse ülevaatamine | Ehitamise valdkonna kutsete taotlemine"

        application_data = self._get_all_application_data(user_email)
        review_content = render_review_page(application_data)

        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="ulevaatamine", request=request, badge_counts={})
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            return review_content, oob_nav, oob_title
        else:
            return app_layout(
                request=request,
                title=page_title,
                content=review_content,
                active_tab="ulevaatamine",
                db=self.db
            )

    async def submit_application(self, request: Request):
        """Handles the final application submission."""
        user_email = request.session.get("user_email")
        if not user_email:
             return Div("Authentication Error - Cannot Submit", cls="text-red-500")

        print(f"--- INFO: Received submission request from {user_email} ---")
        
        success_message = Div(
            H3("Taotlus esitatud!"),
            P(f"Sinu taotlus on edukalt esitatud menetlemiseks. Koopia saadeti aadressile {user_email}."),
            A(Button("Tagasi avalehele"), href="/app"),
            id="tab-content-container",
            cls="p-6 text-center"
        )
        updated_tab_nav = tab_nav(active_tab="ulevaatamine", request=request, badge_counts={})
        oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

        return success_message, oob_nav