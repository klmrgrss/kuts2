# controllers/work_experience.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from fastlite import NotFoundError
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from monsterui.all import *
import traceback
from typing import List, Optional

# Import the V2 view and the data model
from ui.work_experience_view_v2 import render_work_experience_form_v2
from models import WorkExperience


class WorkExperienceController:
    # ... (__init__, _get_saved_activities, show_workex_tab, show_workex_edit_form, save_workex_experience methods are unchanged) ...
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

    def show_workex_tab(self, request: Request, experience_to_edit: Optional[dict] = None):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        
        page_title = "Töökogemus | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)
        available_activities = self._get_saved_activities(user_email)
        
        work_experience_content = None
        footer = None

        if not available_activities:
            warning_message = Card(CardBody(P("Enne töökogemuse lisamist vali tegevusalad 'Taotletavad kutsed' lehel.", cls="text-warning text-center"), A(Button("Vali kutsed", cls="btn btn-secondary mt-4"), href="/app/kutsed")), cls="border-warning")
            work_experience_content = Div(warning_message, cls="max-w-5xl mx-auto")
        else:
            experiences = [exp for exp in self.experience_table(order_by='id') if exp.get('user_email') == user_email]
            
            selected_activity = request.query_params.get('activity')
            
            if request.method == "GET" and not selected_activity and not experience_to_edit and available_activities:
                 if len(available_activities) == 1:
                     selected_activity = available_activities[0]

            work_experience_content, footer = render_work_experience_form_v2(
                available_activities=available_activities, 
                experiences=experiences, 
                experience=experience_to_edit, 
                selected_activity=selected_activity
            )

        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="workex", request=request, badge_counts=badge_counts)
            oob_footer = Div(footer, id="footer-container", hx_swap_oob="innerHTML") if footer else Div(id="footer-container", hx_swap_oob="innerHTML")
            return work_experience_content, oob_footer, Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML"), Title(page_title, id="page-title", hx_swap_oob="innerHTML")
        else:
            return app_layout(
                request=request, 
                title=page_title, 
                content=work_experience_content, 
                footer=footer,
                active_tab="workex", 
                badge_counts=badge_counts, 
                container_class="max-w-7xl"
            )

    def show_workex_edit_form(self, request: Request, experience_id: int):
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        try:
            experience_data = self.experience_table[experience_id]
            if experience_data.get('user_email') != user_email: return Div("Access Denied", cls="text-red-500 p-4")
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

        model_fields = [f.name for f in WorkExperience.__dataclass_fields__.values()]
        experience_data = {
            key: form_data.get(key) for key in model_fields if form_data.get(key) is not None
        }
        experience_data['user_email'] = user_email
        experience_data['permit_required'] = 1 if form_data.get("permit_required") == 'on' else 0
        
        required_fields = ["role", "company_name", "start_date", "associated_activity", "work_description", "object_address"]
        if any(not experience_data.get(field) for field in required_fields):
            return RedirectResponse("/app/workex?error=missing_fields", status_code=303)

        try:
            if is_edit:
                current_record = self.experience_table[experience_id]
                if current_record.get('user_email') != user_email: return Response("Forbidden", status_code=403)
                self.experience_table.update(experience_data, id=experience_id)
            else:
                experience_data.pop('id', None)
                self.experience_table.insert(experience_data)
        except Exception as e:
            traceback.print_exc()
            return RedirectResponse("/app/workex?error=save_failed", status_code=303)

        return self.show_workex_tab(request)

    def delete_workex_experience(self, request: Request, experience_id: int):
        user_email = request.session.get("user_email")
        if not user_email:
            return ToastAlert("Authentication Error", alert_type="error")

        try:
            experience_to_delete = self.experience_table[experience_id]
            if experience_to_delete.get('user_email') != user_email:
                return ToastAlert("Access Denied", alert_type="error")

            # --- FIX: Call delete with a positional argument, not a keyword argument ---
            self.experience_table.delete(experience_id)
            print(f"--- [DELETE WORKEX] Successfully deleted record ID: {experience_id} for user {user_email}")

            return self.show_workex_tab(request)

        except NotFoundError:
            print(f"--- ERROR [DELETE WORKEX] Record ID: {experience_id} not found.")
            return self.show_workex_tab(request)
        except Exception as e:
            print(f"--- ERROR [DELETE WORKEX] Failed to delete record ID: {experience_id}. Error: {e}")
            traceback.print_exc()
            return ToastAlert("Kustutamine ebaõnnestus.", alert_type="error")