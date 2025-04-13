# controllers/employment_proof.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from ui.employment_proof_form import render_employment_proof_form  # Import the form
from .utils import get_badge_counts  

import os
import datetime

class EmploymentProofController:
    def __init__(self, db):
        self.db = db
        # Assuming a table named 'employment_proof' exists
        self.employment_proof_table = db.t.employment_proof

    def show_employment_proof_tab(self, request: Request):
        """Renders the 'Töötamise tõend' tab content."""
        user_email = request.session.get("user_email")
        if not user_email:
            return Div("Authentication Error", cls="text-red-500 p-4")
        
        page_title = "Töötamise tõend | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

        # --- Render Content Fragment ---
        # Call the form rendering function
        employment_proof_content = render_employment_proof_form()

        # --- Check for HTMX Request Header ---
        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---") # Updated log
            # 1. Content Fragment (training_content)

            # 2. OOB Navigation Swap
            updated_tab_nav = tab_nav(active_tab="tootamise_toend", request=request, badge_counts=badge_counts) # Use 'tootamise_toend' ID
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

            # 3. OOB Title Swap
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")

            # 4. Return all three components
            return employment_proof_content, oob_nav, oob_title
        else:
            # Full page load
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---") # Updated log
            return app_layout(
                request=request,
                title=page_title, # Pass title for full page load
                content=employment_proof_content,
                active_tab="tootamise_toend",
                badge_counts=badge_counts  
            )

    async def upload_employment_proof(self, request: Request):
        """Handles the upload of the employment proof file (ASiC-E)."""
        user_email = request.session.get("user_email")
        if not user_email:
            return ToastAlert("Authentication Error", alert_type="error")

        try:
            form_data = await request.form()
            proof_file = form_data.get("employment_proof")  # Get the uploaded file

            if not proof_file:
                return ToastAlert("No file uploaded", alert_type="error")

            # --- Basic file validation ---
            # You'll need to adjust this based on the specifics of ASiC-E
            # and any libraries you might use for validation
            # For example, check the MIME type or file extension
            if proof_file.content_type != "application/octet-stream":  # Example: Adjust as needed
                return ToastAlert(
                    f"Invalid file type. Please upload a valid ASiC-E file.",
                    alert_type="error",
                )

            if len(await proof_file.read()) > 10 * 1024 * 1024:  # 10MB limit (adjust as needed)
                return ToastAlert(
                    f"File size exceeds the 10MB limit.", alert_type="error"
                )

            # --- Save the file ---
            file_content = await proof_file.read()
            # Generate a unique filename
            storage_filename = f"{user_email}_employment_proof_{proof_file.filename}"
            file_path = os.path.join("uploads", storage_filename)

            # Ensure the upload directory exists
            os.makedirs("uploads", exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(file_content)

            # --- Save file metadata to the database ---
            # Since employment_proof table uses user_email as primary key,
            # we either INSERT a new record or UPDATE an existing one.
            file_record = {
                "user_email": user_email,
                "file_description": form_data.get(
                    "file_description"
                ),  # Get file description
                "original_filename": proof_file.filename,
                "storage_identifier": storage_filename,
                "upload_timestamp": str(datetime.datetime.now()),
            }

            # --- Database operation: INSERT or UPDATE ---
            try:
                # Check if a record with this user_email already exists
                existing_record = self.employment_proof_table[user_email]
                # If it exists, UPDATE
                self.employment_proof_table.update(file_record, user_email=user_email)
                print(f"--- DB: Updated employment proof for {user_email} ---")
            except NotFoundError:
                # If it doesn't exist, INSERT
                self.employment_proof_table.insert(file_record, pk='user_email')
                print(f"--- DB: Inserted employment proof for {user_email} ---")

            return Response(headers={'HX-Redirect': '/app/tootamise_toend'})  # Redirect on success

        except Exception as e:
            print(
                f"--- ERROR [upload_employment_proof]: File upload failed for {user_email}: {e} ---"
            )
            return ToastAlert(f"File upload failed: {e}", alert_type="error")