# controllers/work_experience.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response # Needed for delete response
from fastlite import NotFoundError # Or your specific DB error
from ui.layouts import app_layout
from ui.nav_components import tab_nav # For OOB swap
from controllers.utils import get_badge_counts
from monsterui.all import * # Import MonsterUI components if needed for warning message
import traceback # Keep for debugging
from typing import List, Optional # Ensure List and Optional are imported

# Import the view functions (which now handle the new date inputs)
from ui.work_experience_view import render_experience_item, render_work_experience_form, render_work_experience_list


class WorkExperienceController:
    def __init__(self, db):
        self.db = db
        self.experience_table = db.t.work_experience
        self.applied_qual_table = db.t.applied_qualifications # Keep access to this

    def _get_saved_activities(self, user_email: str) -> list[str]:
        # --- This method remains unchanged ---
        activities = []
        try:
            all_quals = self.applied_qual_table(order_by='id')
            user_quals = [q for q in all_quals if q.get('user_email') == user_email]
            activities = sorted(list(set(q.get('qualification_name') for q in user_quals if q.get('qualification_name'))))
        except Exception as e:
            print(f"--- ERROR fetching saved activities for {user_email}: {e} ---")
        return activities

    # --- MODIFIED: _render_add_button uses outerHTML swap ---
    def _render_add_button(self):
         """Renders the Add button within a Div configured for OOB outerHTML swap."""
         add_button = Button(
             "+ Lisa töökogemus",
             hx_get="/app/tookogemus/add_form",
             hx_target="#add-experience-form-container", # Target for loading the form
             hx_swap="innerHTML", # Swap for loading the form
             cls="btn btn-primary mt-4",
         )
         # This Div will REPLACE the existing #add-button-container element
         # via an OOB outerHTML swap when returned by save/cancel actions.
         return Div(add_button, id="add-button-container", hx_swap_oob="outerHTML") # <-- Use outerHTML
    # --- END MODIFICATION ---

    def show_work_experience_tab(self, request: Request):
        # --- This method remains unchanged ---
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        page_title = "Töökogemus | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)
        warning_message = None
        available_activities = self._get_saved_activities(user_email)
        if not available_activities:
            warning_message = Card(CardBody(P("Enne töökogemuse lisamist vali tegevusalad 'Taotletavad kutsed' lehel.", cls="text-warning text-center"), A(Button("Vali kutsed", cls="btn btn-secondary mt-4"), href="/app/kutsed")), cls="border-warning")
        experiences = []
        if not warning_message:
            try:
                all_experiences = self.experience_table(order_by='id')
                experiences = [exp for exp in all_experiences if exp.get('user_email') == user_email]
            except Exception as e:
                print(f"--- ERROR fetching experiences for view: {e} ---")
                experiences = []
        work_experience_content = render_work_experience_list(experiences=experiences, warning_message=warning_message)
        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="tookogemus", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            return work_experience_content, oob_nav, oob_title
        else:
            return app_layout(request=request, title=page_title, content=work_experience_content, active_tab="tookogemus", badge_counts=badge_counts)

    def show_add_form(self, request: Request):
        # --- This method remains unchanged ---
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        available_activities = self._get_saved_activities(user_email)
        if not available_activities: return Div("Viga: Enne töökogemuse lisamist peavad olema valitud kutsed.", cls="text-red-500 p-4")
        # Pass experience=None for adding
        form_html = render_work_experience_form(available_activities=available_activities, experience=None)
        oob_hide_button = Div(id="add-button-container", hx_swap_oob="innerHTML") # Hide button by clearing container
        return form_html, oob_hide_button

    def show_edit_form(self, request: Request, experience_id: int):
        # --- This method remains unchanged (already passes experience dict) ---
        user_email = request.session.get("user_email")
        if not user_email: return Div("Authentication Error", cls="text-red-500 p-4")
        available_activities = self._get_saved_activities(user_email)
        if not available_activities: return Div("Viga: Seotud kutseid ei leitud. Vali esmalt kutsed.", cls="text-red-500 p-4")
        try:
            experience_data = self.experience_table[experience_id]
            if experience_data.get('user_email') != user_email: return Div("Access Denied", cls="text-red-500 p-4")
            form_html = render_work_experience_form(available_activities=available_activities, experience=experience_data)
            oob_hide_button = Div(id="add-button-container", hx_swap_oob="innerHTML")
            return form_html, oob_hide_button
        except NotFoundError:
            print(f"--- ERROR: Experience ID {experience_id} not found for editing ---")
            return Div(f"Error: Work experience with ID {experience_id} not found.", cls="text-red-500 p-4")
        except Exception as e:
            print(f"--- ERROR fetching experience {experience_id} for edit: {e} ---")
            return Div(f"An error occurred: {e}", cls="text-red-500 p-4")

    def cancel_form(self, request: Request):
        # --- This method remains unchanged (uses _render_add_button) ---
        user_email = request.session.get("user_email")
        oob_show_button = None
        if user_email and self._get_saved_activities(user_email):
            oob_show_button = self._render_add_button() # Will now return outerHTML swap instruction
        else:
            oob_show_button = Div(id="add-button-container", hx_swap_oob="innerHTML") # Still clear if no activities
        return "", oob_show_button

    async def save_work_experience(self, request: Request):
        # --- This method remains unchanged (uses correct fields/validation and _render_add_button) ---
        user_email = request.session.get("user_email")
        if not user_email:
            return Div("Authentication Error", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")

        available_activities = self._get_saved_activities(user_email)
        if not available_activities:
            return Div("Viga: Kutseid pole valitud.", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")

        try:
            form_data = await request.form()
        except Exception as e:
            print(f"--- ERROR: Could not read form data in save_work_experience: {e} ---")
            return Div("Error reading form data", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")

        experience_id_str = form_data.get("experience_id")
        is_edit = experience_id_str and experience_id_str != 'None' and experience_id_str.isdigit()
        experience_id = int(experience_id_str) if is_edit else None

        # Uses new required fields
        required_fields = ["role", "company_name", "start_date", "associated_activity"]
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        if missing_fields:
             error_msg = f"Puuduvad kohustuslikud väljad: {', '.join(missing_fields)}"
             return Div(error_msg, id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")

        selected_activity = form_data.get("associated_activity")
        if selected_activity not in available_activities:
            error_msg = f"Vigane seotud tegevusala valik: '{selected_activity}'. Palun vali nimekirjast."
            return Div(error_msg, id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")

        # Uses new date fields
        experience_data = {
            "user_email": user_email, "role": form_data.get("role"),
            "start_date": form_data.get("start_date"), "end_date": form_data.get("end_date") or None,
            "work_description": form_data.get("work_description"), "contract_type": form_data.get("contract_type"),
            "competency": form_data.get("competency") or "", "work_keywords": form_data.get("work_keywords"),
            "permit_required": 1 if form_data.get("permit_required") == 'on' else 0,
            "object_address": form_data.get("object_address"), "object_purpose": form_data.get("object_purpose"),
            "ehr_code": form_data.get("ehr_code"), "company_name": form_data.get("company_name"),
            "company_code": form_data.get("company_code"), "company_contact": form_data.get("company_contact"),
            "company_email": form_data.get("company_email"), "company_phone": form_data.get("company_phone"),
            "client_name": form_data.get("client_name"), "client_code": form_data.get("client_code"),
            "client_contact": form_data.get("client_contact"), "client_email": form_data.get("client_email"),
            "client_phone": form_data.get("client_phone"), "application_id": form_data.get("application_id") or "",
            "other_work": form_data.get("other_work") or "", "construction_activity": form_data.get("construction_activity") or "",
            "other_activity": form_data.get("other_activity") or "", "other_role": form_data.get("other_role") or "",
            "associated_activity": selected_activity
        }

        print(f"--- DEBUG: Attempting to save data: {experience_data} ---")

        try:
            saved_exp_data = None
            actual_id = None

            if is_edit:
                if experience_id is None: raise ValueError("Edit error: experience_id is None.")
                # Ownership check...
                try:
                    current_record = self.experience_table[experience_id]
                    if current_record.get('user_email') != user_email: return Div("Access Denied", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")
                except NotFoundError: return Div("Error: Cannot update non-existent record.", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")
                # Update...
                self.experience_table.update(experience_data, id=experience_id)
                saved_exp_data = self.experience_table[experience_id]
            else:
                # Insert...
                if 'id' in experience_data: del experience_data['id']
                inserted_result = self.experience_table.insert(experience_data)
                # Process insert result...
                if isinstance(inserted_result, dict) and 'id' in inserted_result:
                    saved_exp_data = inserted_result; actual_id = saved_exp_data.get('id')
                elif isinstance(inserted_result, int):
                    actual_id = inserted_result
                    try: saved_exp_data = self.experience_table[actual_id]
                    except NotFoundError: print(f"--- ERROR: Fetch failed post-insert ID {actual_id} ---"); saved_exp_data = experience_data
                else: print(f"--- WARNING: Insert result type {type(inserted_result)} ---")

                if not (saved_exp_data and actual_id):
                    print(f"--- ERROR: Failed to get data/ID post-insert ---")
                    return Div("Error processing insert.", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")
                experience_id = actual_id

            # OOB Swaps (uses _render_add_button which now returns outerHTML swap)
            badge_counts = get_badge_counts(self.db, user_email)
            updated_tab_nav = tab_nav(active_tab="tookogemus", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            saved_item_html = render_experience_item(saved_exp_data)
            oob_clear_form = Div(id="add-experience-form-container", hx_swap_oob="innerHTML") # Clear form
            oob_show_button = self._render_add_button() # Show button (using outerHTML swap now)

            # Return Response
            if is_edit:
                oob_updated_item = Div(saved_item_html, hx_swap_oob="outerHTML", id=f"experience-{experience_id}")
                return oob_updated_item, oob_nav, oob_clear_form, oob_show_button
            else:
                oob_new_item = Div(saved_item_html, hx_swap_oob="beforeend", id="work-experience-list")
                return oob_nav, oob_new_item, oob_clear_form, oob_show_button

        except Exception as e:
            print(f"--- ERROR [save_work_experience] DB operation Failed ---")
            traceback.print_exc()
            return Div(f"Error saving experience. Check logs.", id="form-error-message", cls="text-red-500 mt-2", hx_swap_oob="innerHTML")


    def delete_work_experience(self, request: Request, experience_id: int):
        # --- This method remains unchanged ---
        user_email = request.session.get("user_email")
        if not user_email: return Response("Authentication Error", status_code=403)
        try:
            try:
                experience_to_delete = self.experience_table[experience_id]
                if experience_to_delete.get('user_email') != user_email: return Response("Forbidden", status_code=403)
            except NotFoundError: return Response("", status_code=200)
            self.experience_table.delete(experience_id)
            badge_counts = get_badge_counts(self.db, user_email)
            updated_tab_nav = tab_nav(active_tab="tookogemus", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            return Response("", status_code=200), oob_nav
        except Exception as e:
            print(f"--- ERROR [delete_work_experience]: DB Delete Failed for ID {experience_id}: {e} ---")
            return Response(f"Error deleting experience: {e}", status_code=500)