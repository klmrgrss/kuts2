# klmrgrss/kuts2/kuts2-sticky-bar/app/controllers/qualifications.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
import json
# Import NotFoundError from fastlite or wherever it's defined in your setup
from fastlite import NotFoundError # Adjust import if necessary
from ui.qualification_form import render_qualification_form
from ui.layouts import ToastAlert, app_layout
from ui.nav_components import tab_nav
from config.qualification_data import kt
from ui.checkbox_group import render_checkbox_group # Adjust path
from monsterui.all import *
from monsterui.daisy import Toast, AlertT, ToastHT, ToastVT
from .utils import get_badge_counts

# ... other imports ...
from config.qualification_data import kt # Adjust path as needed

class QualificationController:
    def __init__(self, db):
        self.db = db
        self.applied_qual_table = db.t.applied_qualifications

    def _prepare_qualification_data(self, user_email: str):
        """
        Fetches and prepares data needed for the qualification form,
        INCLUDING pre-selecting based on saved DB entries.
        """
        print(f"--- DEBUG [_prepare_qualification_data]: Preparing data for {user_email} ---")
        sections = {}
        section_counter = 0
        # Build the basic section structure from kt
        # ... (logic to populate sections from kt remains the same) ...
        for level_name, level_data in kt.items():
           for category, items in level_data.items():
               if category != "costs" and isinstance(items, list):
                   section_counter += 1
                   effective_items = [category] if items == ["Valikkompetentsid puuduvad"] else items
                   sections[section_counter] = {
                       "level": level_name, "category": category, "items": effective_items,
                       "id": section_counter, "preselected": {}, "toggle_on": False
                   }


        # --- Fetching and Processing Saved Selections ---
        try:
            # --- MODIFIED DB QUERY ---
            print(f"--- DEBUG [_prepare_qualification_data]: Fetching saved quals for {user_email} ---")
            all_saved_quals = self.applied_qual_table(order_by='id') # Fetch all first
            saved_quals = [q for q in all_saved_quals if q.get('user_email') == user_email]
            # --- END MODIFIED QUERY ---

            print(f"--- DEBUG [_prepare_qualification_data]: Found {len(saved_quals)} saved quals ---")

            items_selected_in_section = {sec_id: set() for sec_id in sections}

            for idx, saved_qual in enumerate(saved_quals):
                print(f"--- DEBUG [Loop {idx}]: Processing saved_qual: {saved_qual} ---") # Log each saved qual
                s_level = saved_qual.get('level')
                s_category = saved_qual.get('qualification_name')
                s_specialisation = saved_qual.get('specialisation')
                found_match = False # Flag to check if we found a match

                for section_id, section_info in sections.items():
                    if section_info["level"] == s_level and section_info["category"] == s_category:
                        print(f"--- DEBUG [Loop {idx}]: Matched section {section_id} ({s_level}/{s_category}) ---")
                        try:
                            item_index = section_info["items"].index(s_specialisation)
                            form_field_name = f"qual_{section_id}_{item_index}"
                            sections[section_id]["preselected"][form_field_name] = True
                            items_selected_in_section[section_id].add(s_specialisation)
                            print(f"--- DEBUG [Loop {idx}]:   Set preselected for {form_field_name} ---")
                            found_match = True
                        except ValueError:
                             print(f"--- WARNING [Loop {idx}]: Saved specialisation '{s_specialisation}' not in section items: {section_info['items']} ---")
                        break # Stop searching sections once the category/level match

                if not found_match:
                     print(f"--- WARNING [Loop {idx}]: No matching section found for saved qual: L={s_level}, C={s_category} ---")


            # Second pass to check for toggles
            for section_id, section_info in sections.items():
                 # Check against the number of items actually processed and found for that section
                 if len(section_info["items"]) > 0 and len(items_selected_in_section[section_id]) == len(section_info["items"]):
                     sections[section_id]["toggle_on"] = True
                     print(f"--- DEBUG: Setting toggle_on for section {section_id} ---")

        except Exception as e:
            print(f"--- ERROR processing saved qualifications for {user_email}: {e} ---")


        print(f"--- DEBUG [_prepare_qualification_data]: Returning sections data ---")
        # print(sections) # Optional: print the final sections structure
        return sections
    
    def show_qualifications_tab(self, request: Request):
        """
        Renders the 'Taotletavad kutsed' tab, returning either
        full page or content + OOB tab nav based on request type.
        """
        # --- Authentication & Data Fetching (Error handling included) ---
        user_email = request.session.get("user_email")
        if not user_email:
             return Div("Authentication Error", cls="text-red-500 p-4")
        
        page_title = "Taotletavad kutsed | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)


        try:
            prepared_sections = self._prepare_qualification_data(user_email)
        except Exception as e:
             print(f"ERROR preparing data for {user_email}: {e}")
             error_content = Div(f"Error loading qualification data: {e}", cls="text-red-500 p-4")
             if request.headers.get('HX-Request'):
                 return error_content
             else:
                 # Pass db to app_layout in the error case as well
                 return app_layout(request=request, title="Error", content=error_content, active_tab="kutsed", db=self.db)

        # --- Render Content Fragment ---
        qualification_content, footer = render_qualification_form(
            sections=prepared_sections,
            app_id=user_email
        )

        # --- Check for HTMX Request Header ---
        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---")
            updated_tab_nav = tab_nav(active_tab="kutsed", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            oob_footer = Div(footer, id="footer-container", hx_swap_oob="innerHTML") if footer else ""

            return qualification_content, oob_nav, oob_title, oob_footer
        else:
            # --- Full Page Load Response ---
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---")
            return app_layout(
                request=request,
                title=page_title,
                content=qualification_content,
                footer=footer,
                active_tab="kutsed",
                badge_counts=badge_counts,
                db=self.db # <-- THE FIX IS HERE
            )


    async def handle_toggle(self, request: Request, section_id: int, app_id: str):
        """Handles the HTMX toggle request."""
        print(f"--- DEBUG: Entering handle_toggle for section {section_id} ---")

        try:
            form_data = await request.form()
            print(f"--- DEBUG: Form data received: {form_data} ---")
        except Exception as e:
             print(f"--- ERROR: Could not read form data in handle_toggle: {e} ---")
             return Div("Error reading form data", cls="text-red-500")

        toggle_state = form_data.get(f"toggle-{section_id}") == "on"
        print(f"--- DEBUG: Toggle state for section {section_id}: {toggle_state} ---")

        user_email = request.session.get("user_email", app_id)
        try:
            sections_data = self._prepare_qualification_data(user_email)
            target_section_data = sections_data.get(section_id)
        except Exception as e:
             print(f"--- ERROR: Could not get section data in handle_toggle: {e} ---")
             return Div("Error retrieving section data", cls="text-red-500")

        if not target_section_data:
            return Div("Error: Section not found", cls="text-red-500")

        try:
            checked_state = {}
            if toggle_state:
                for i in range(len(target_section_data["items"])):
                    checked_state[f"qual_{section_id}_{i}"] = True

            updated_checkbox_group = render_checkbox_group(
                section_id=section_id,
                items=target_section_data["items"],
                section_info={"level": target_section_data["level"], "category": target_section_data["category"]},
                checked_state=checked_state
            )
            print(f"--- DEBUG: Returning updated checkbox group for section {section_id} ---")
            return updated_checkbox_group

        except Exception as e:
             print(f"--- ERROR: Could not render checkbox group in handle_toggle: {e} ---")
             return Div("Error rendering checkbox group", cls="text-red-500")

    async def submit_qualifications(self, request: Request):
        """
        Handles POST submission for the qualification selection form.
        """
        user_email = request.session.get("user_email")
        if not user_email:
            return Alert("Authentication Error", cls="text-red-500", id="form-guidance-message", hx_swap_oob="innerHTML")

        try:
            form_data = await request.form()
            print(f"--- DEBUG [submit_qualifications]: Raw form data: {form_data} ---")
        except Exception as e:
            print(f"--- ERROR: Could not read form data in submit_qualifications: {e} ---")
            return Alert("Error reading form data", cls="text-red-500", id="form-guidance-message", hx_swap_oob="innerHTML")

        rows_to_insert = []
        sections_data = self._prepare_qualification_data(user_email)

        for key, value in form_data.items():
            if not key.startswith("qual_") or value != "on":
                continue
            try:
                parts = key.split("_")
                section_id = int(parts[1])
                item_index = int(parts[2])
                
                section_info = sections_data.get(section_id)
                if section_info and 0 <= item_index < len(section_info["items"]):
                    item = section_info["items"][item_index]
                    
                    rows_to_insert.append({
                        "user_email": user_email,
                        "qualification_name": section_info["category"],
                        "level": section_info["level"],
                        "specialisation": item,
                        "activity": section_info["category"],
                        "is_renewal": 0,
                        "application_date": None
                    })
            except (ValueError, IndexError, KeyError) as e:
                print(f"--- ERROR Parsing qualification key '{key}': {e} ---")

        try:
            print(f"--- DB [submit_qualifications]: Deleting existing for {user_email} ---")
            deleted_count = self.applied_qual_table.delete_where('user_email=?', [user_email])
            print(f"--- DB [submit_qualifications]: Deleted {deleted_count} rows ---")

            if rows_to_insert:
                print(f"--- DB [submit_qualifications]: Inserting {len(rows_to_insert)} new rows for {user_email} ---")
                for row in rows_to_insert:
                    self.applied_qual_table.insert(row)

            print(f"--- SUCCESS [submit_qualifications]: Saved selections for {user_email} ---")
            # After saving, just call the method that renders the tab.
            # The scrolling logic is now handled in the view.
            return self.show_qualifications_tab(request)

        except Exception as e:
            print(f"--- ERROR [submit_qualifications] DB Operation Failed for {user_email}: {e} ---")
            error_message = f"Database error saving selections: {e}"
            return Alert(error_message, cls="text-red-500", id="form-guidance-message", hx_swap_oob="innerHTML")