# controllers/education.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from ui.education_form import render_education_form
from fastlite import NotFoundError
import os
import datetime
import uuid # <-- Import UUID module
import traceback # <-- Import traceback for better error logging
from .utils import get_badge_counts

# Define the upload directory relative to the project root (consistent with database.py)
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
UPLOAD_DIR = os.path.join(project_root, 'uploads')


class EducationController:
    def __init__(self, db):
        self.db = db
        self.education_table = db.t.education

    def show_education_tab(self, request: Request):
        # --- This method remains unchanged ---
        user_email = request.session.get("user_email")
        if not user_email:
            return Div("Authentication Error", cls="text-red-500 p-4")

        education_options = {
            1: {"title": "Spetsialiseerumisele vastav kõrgharidus", "tooltip": "Siia kuuluvad ehitusega seotud kõrgharidused, mis vastavad taotletavale spetsialiseerumisele.", "items": [("Ehitusalane magister, 300 EAP", "Ehitusalane magister, 300 EAP"), ("Ehitusalane rakenduskõrgharidus, 240 EAP", "Ehitusalane rakenduskõrgharidus, 240 EAP"), ("Ehitusalane bakalaureus, 180 EAP", "Ehitusalane bakalaureus, 180 EAP")]},
            2: {"title": "Spetsialiseerumisele mittevastav kõrgharidus", "tooltip": "Siia kuuluvad ehitusega seotud kõrgharidused, mis EI vasta taotletavale spetsialiseerumisele.", "items": [("Ehitusalane magister, 300 EAP", "Ehitusalane magister, 300 EAP"), ("Ehitusalane rakenduskõrgharidus, 240 EAP", "Ehitusalane rakenduskõrgharidus, 240 EAP"), ("Ehitusalane bakalaureus, 180 EAP", "Ehitusalane bakalaureus, 180 EAP")]},
            3: {"title": "Tehnika alane kõrgharidus", "tooltip": "Siia kuuluvad tehnika, tootmise ja tehnoloogia valdkonna kõrgharidused.", "items": [("Magister, 300 EAP", "Magister, 300 EAP"), ("Rakenduskõrgharidus, 240 EAP", "Rakenduskõrgharidus, 240 EAP")]},
            4: {"title": "Üldkeskharidus", "tooltip": "Siia kuuluvad üldkeskharidusel baseeruvad haridused.", "items": [("Ehitustehniline keskeriharidus (ehitustehnik)", "Ehitustehniline keskeriharidus (ehitustehnik)"), ("Spetsialiseerumisele vastav muu keskeriharidus", "Spetsialiseerumisele vastav muu keskeriharidus")]},
            5: {"title": "Muu", "tooltip": "Märgi siia muu haridus, mida nimekirjas pole.", "items": [("Muu haridus", "Muu haridus")]},
        }

        existing_data = {}
        try:
            all_edu_records = self.education_table(order_by='id')
            user_edu_list = [edu for edu in all_edu_records if edu.get('user_email') == user_email]
            record = user_edu_list[0] if user_edu_list else None
            if record:
                existing_data['selected_level'] = record.get('education_detail')
                existing_data['other_text'] = record.get('other_education_text', '') # Assuming separate column? Or check logic below
                # If 'other' text is stored IN education_detail when category is 'Muu haridus'
                # This logic depends on how you save "Other" in submit_education_form
                if record.get('education_category') == 'Muu haridus':
                    existing_data['other_text'] = record.get('education_detail')
                # existing_data['other_text'] = record.get('education_detail') if record.get('education_category') == 'Muu haridus' else ''

                existing_data['institution'] = record.get('institution')
                existing_data['specialty'] = record.get('specialty')
                existing_data['graduation_date'] = record.get('graduation_date')
                # We might load document info here later if needed for display
                # existing_data['original_filename'] = record.get('original_filename')
                print(f"--- DEBUG: Fetched existing education data: {existing_data} ---")
            else:
                 print(f"--- DEBUG: No existing education data found for {user_email} ---")
        except Exception as e:
            print(f"--- ERROR fetching/processing existing education data: {e} ---")
            # traceback.print_exc() # Uncomment for full traceback
            existing_data = {}

        sections_data_for_view = education_options
        print(f"--- DEBUG [Controller]: Passing sections with keys: {list(sections_data_for_view.keys())} to render_education_form ---")
        education_content = render_education_form(
            sections_data=sections_data_for_view,
            existing_data=existing_data
        )
        page_title = "Haridus | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---")
            updated_tab_nav = tab_nav(active_tab="haridus", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            return education_content, oob_nav, oob_title
        else:
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---")
            return app_layout(
                request=request, title=page_title, content=education_content,
                active_tab="haridus", badge_counts=badge_counts
            )

    async def submit_education_form(self, request: Request):
        user_email = request.session.get("user_email")
        if not user_email:
            return ToastAlert("Authentication Error", alert_type="error")

        try:
            form_data = await request.form()

            selected_level_value = form_data.get("education_level")
            other_education_text = form_data.get("other_education_text", "").strip()
            institution = form_data.get("institution", "").strip()
            specialty = form_data.get("specialty", "").strip()
            graduation_date = form_data.get("graduation_date")
            education_document = form_data.get("education_document") # Uploaded file object

            # Determine final education detail
            final_education_category = selected_level_value
            final_education_detail = selected_level_value
            if selected_level_value == "Muu haridus" and other_education_text:
                final_education_category = "Muu haridus"
                final_education_detail = other_education_text
            elif selected_level_value == "Muu haridus" and not other_education_text:
                 final_education_detail = "Muu haridus (täpsustamata)"

            # --- File Handling ---
            storage_identifier = None # Will store the generated safe filename (UUID.ext)
            original_filename = None  # Will store the original uploaded filename

            if education_document and hasattr(education_document, 'filename') and education_document.filename:
                original_filename = education_document.filename # Store original name
                # Basic validation (add more if needed)
                if not original_filename.lower().endswith(('.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png')):
                     return ToastAlert("Invalid file type. Allowed: pdf, doc, docx, jpg, png", alert_type="error")

                file_content = await education_document.read()
                if len(file_content) > 10 * 1024 * 1024: # 10MB limit
                    return ToastAlert(f"File size for {original_filename} exceeds 10MB limit.", alert_type="error")

                # --- Generate Secure Storage Identifier ---
                file_extension = os.path.splitext(original_filename)[1]
                storage_identifier = f"{uuid.uuid4()}{file_extension}" # UUID + original extension
                # ---

                # Ensure upload directory exists (uses UPLOAD_DIR defined at top)
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                file_path = os.path.join(UPLOAD_DIR, storage_identifier) # Use secure identifier

                try:
                    with open(file_path, "wb") as f:
                        f.write(file_content)
                    print(f"--- Saved education document: {storage_identifier} (Original: {original_filename}) ---")
                except IOError as e:
                     print(f"--- ERROR saving education file {storage_identifier}: {e} ---")
                     traceback.print_exc()
                     return ToastAlert("Error saving uploaded file.", alert_type="error")
            else:
                 print(f"--- No education document uploaded or filename missing ---")


            # --- Prepare Data for DB ---
            # (Includes the new document identifier fields)
            db_data = {
                "user_email": user_email,
                "education_category": final_education_category,
                "education_detail": final_education_detail,
                "institution": institution,
                "specialty": specialty,
                "graduation_date": graduation_date,
                # --- ADD File identifiers ---
                "document_storage_identifier": storage_identifier, # The safe UUID.ext name
                "original_filename": original_filename       # The original uploaded name
                # ---
            }

            # --- Save to Database (Upsert: Delete existing then insert) ---
            print(f"--- DB: Preparing to save education data for {user_email} ---")
            try:
                # Delete existing record(s) for the user first
                deleted_count = self.education_table.delete_where('user_email=?', [user_email])
                print(f"--- DB: Deleted {deleted_count} existing education record(s) for {user_email} ---")
            except NotFoundError:
                 print(f"--- DB: No existing education record to delete for {user_email} ---")
                 pass # OK if record didn't exist
            except Exception as e:
                print(f"--- ERROR deleting existing education record for {user_email}: {e} ---")
                traceback.print_exc()
                # Decide if we should proceed with insert or return error
                return ToastAlert("Error preparing database for update.", alert_type="error")

            # Insert the new record
            try:
                self.education_table.insert(db_data)
                print(f"--- SUCCESS [submit_education_form]: Inserted education data for {user_email}: {db_data} ---")
            except Exception as e:
                 print(f"--- ERROR inserting education data for {user_email}: {e} ---")
                 traceback.print_exc()
                 return ToastAlert("Error saving education data to database.", alert_type="error")

            # --- Redirect on success ---
            return Response(headers={'HX-Redirect': '/app/taiendkoolitus'}) # Go to next tab

        except Exception as e:
            print(f"--- ERROR [submit_education_form]: Form processing failed for {user_email}: {e} ---")
            traceback.print_exc(); # Print detailed error
            return ToastAlert(f"Salvestamine ebaõnnestus: {e}", alert_type="error")