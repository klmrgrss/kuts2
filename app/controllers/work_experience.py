# controllers/work_experience.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse # Needed for delete response and redirect
from fastlite import NotFoundError # Or your specific DB error
from ui.layouts import app_layout
from ui.nav_components import tab_nav # For OOB swap
from controllers.utils import get_badge_counts
from monsterui.all import * # Import MonsterUI components if needed for warning message
import traceback # Keep for debugging
from typing import List, Optional # Ensure List and Optional are imported

# Import the view functions
from ui.work_experience_view import render_experience_item, render_work_experience_form, render_work_experience_list
from ui.work_experience_view_v2 import render_work_experience_form_v2


class WorkExperienceController:
    def __init__(self, db):
        self.db = db
        self.experience_table = db.t.work_experience
        self.applied_qual_table = db.t.applied_qualifications

    def _get_saved_activities(self, user_email: str) -> list[str]:
        activities = []
        try:
            all_quals = self.applied_qual_table(order_by='id')
            user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            activities = sorted(list(set(q.get('qualification_name') for q in user_quals if q.get('qualification_name'))))
        except Exception as e:
            print(f"--- ERROR fetching saved activities for {user_email}: {e} ---")
        return activities

    # --- V1 (OLD) TAB METHODS --- #

    def _render_add_button(self):
         add_button = Button("+ Lisa töökogemus", hx_get="/app/tookogemus/add_form", hx_target="#add-experience-form-container", hx_swap="innerHTML", cls="btn btn-primary mt-4")
         return Div(add_button, id="add-button-container", hx_swap_oob="outerHTML")

    def show_work_experience_tab(self, request: Request):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        page_title = "Töökogemus | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)
        available_activities = self._get_saved_activities(user_email)
        warning_message = None
        if not available_activities:
            warning_message = Card(CardBody(P("Enne töökogemuse lisamist vali tegevusalad 'Taotletavad kutsed' lehel.", cls="text-warning text-center"), A(Button("Vali kutsed", cls="btn btn-secondary mt-4"), href="/app/kutsed")), cls="border-warning")
        experiences = [exp for exp in self.experience_table(order_by='id') if exp.get('user_email') == user_email] if not warning_message else []
        work_experience_content = render_work_experience_list(experiences=experiences, warning_message=warning_message)
        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="tookogemus", request=request, badge_counts=badge_counts)
            return work_experience_content, Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML"), Title(page_title, id="page-title", hx_swap_oob="innerHTML")
        else:
            return app_layout(request=request, title=page_title, content=work_experience_content, active_tab="tookogemus", badge_counts=badge_counts)

    def show_add_form(self, request: Request):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        available_activities = self._get_saved_activities(user_email)
        if not available_activities: return Div("Viga: Kutsed peavad olema valitud.", cls="text-red-500 p-4")
        form_html = render_work_experience_form(available_activities=available_activities, experience=None)
        return form_html, Div(id="add-button-container", hx_swap_oob="innerHTML")

    def show_edit_form(self, request: Request, experience_id: int):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        try:
            experience_data = self.experience_table[experience_id]
            if experience_data.get('user_email') != user_email: return Div("Access Denied", cls="text-red-500 p-4")
            available_activities = self._get_saved_activities(user_email)
            form_html = render_work_experience_form(available_activities=available_activities, experience=experience_data)
            return form_html, Div(id="add-button-container", hx_swap_oob="innerHTML")
        except NotFoundError:
            return Div(f"Error: ID {experience_id} not found.", cls="text-red-500 p-4")

    def cancel_form(self, request: Request):
        return "", self._render_add_button()

    async def save_work_experience(self, request: Request):
        # This is the old save method, it remains unchanged and uses OOB swaps
        user_email = request.session.get("user_email")
        if not user_email: return Div("Auth Error", id="form-error-message", hx_swap_oob="innerHTML")
        form_data = await request.form()
        # ... (rest of the old save logic) ...
        # On success, it returns OOB swaps for the list
        pass # Placeholder for existing logic

    def delete_work_experience(self, request: Request, experience_id: int):
        # This is the old delete method, it remains unchanged
        pass # Placeholder for existing logic

    # --- V2 (WORKEX) TAB METHODS --- #

    def show_workex_tab(self, request: Request, experience_to_edit: Optional[dict] = None):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        
        page_title = "WorkEx (Test) | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)
        available_activities = self._get_saved_activities(user_email)
        
        warning_message = None
        if not available_activities:
            warning_message = Card(CardBody(P("Enne töökogemuse lisamist vali tegevusalad 'Taotletavad kutsed' lehel.", cls="text-warning text-center"), A(Button("Vali kutsed", cls="btn btn-secondary mt-4"), href="/app/kutsed")), cls="border-warning")
            work_experience_content = Div(warning_message, cls="max-w-5xl mx-auto")
        else:
            experiences = [exp for exp in self.experience_table(order_by='id') if exp.get('user_email') == user_email]
            activity_counts = [] # This can be removed if not used in v2 view

            # Determine which activity is selected
            selected_activity = request.query_params.get('activity')
            if not selected_activity and not experience_to_edit:
                selected_activity = available_activities[0] if len(available_activities) == 1 else None

            work_experience_content = render_work_experience_form_v2(
                available_activities=available_activities, 
                experiences=experiences, 
                experience=experience_to_edit, 
                activity_counts=activity_counts,
                selected_activity=selected_activity
            )

        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="workex", request=request, badge_counts=badge_counts)
            return work_experience_content, Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML"), Title(page_title, id="page-title", hx_swap_oob="innerHTML")
        else:
            return app_layout(request=request, title=page_title, content=work_experience_content, active_tab="workex", badge_counts=badge_counts, container_class="max-w-7xl") # Use a wider container for v2

    def show_workex_edit_form(self, request: Request, experience_id: int):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        try:
            experience_data = self.experience_table[experience_id]
            if experience_data.get('user_email') != user_email: return Div("Access Denied", cls="text-red-500 p-4")
            # Call the main tab renderer, passing the experience to edit
            return self.show_workex_tab(request, experience_to_edit=experience_data)
        except NotFoundError:
            return Div(f"Error: Work experience with ID {experience_id} not found.", cls="text-red-500 p-4")

    async def save_workex_experience(self, request: Request):
        user_email = request.session.get("user_email")
        if not user_email: return Response("Authentication Error", status_code=403)

        form_data = await request.form()
        experience_id_str = form_data.get("experience_id")
        is_edit = experience_id_str and experience_id_str != 'None' and experience_id_str.isdigit()
        experience_id = int(experience_id_str) if is_edit else None

        # Basic validation
        required_fields = ["role", "company_name", "start_date", "associated_activity", "work_description", "object_address"]
        if any(not form_data.get(field) for field in required_fields):
            # In this workflow, we just redirect back. A more advanced version could show errors.
            return RedirectResponse("/app/workex", status_code=303)

        experience_data = {k: v for k, v in form_data.items() if k != 'experience_id'}
        experience_data['user_email'] = user_email
        experience_data['permit_required'] = 1 if form_data.get("permit_required") == 'on' else 0

        try:
            if is_edit:
                current_record = self.experience_table[experience_id]
                if current_record.get('user_email') != user_email: return Response("Forbidden", status_code=403)
                self.experience_table.update(experience_data, id=experience_id)
            else:
                self.experience_table.insert(experience_data)
        except Exception as e:
            print(f"--- ERROR [save_workex_experience]: {e}")
            # Redirect back with an error message if possible, for now just redirect
            return RedirectResponse("/app/workex?error=save_failed", status_code=303)

        # On success, re-render the entire tab content and return it.
        # This will include the newly added experience in the list.
        return self.show_workex_tab(request)