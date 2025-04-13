# controllers/training.py

import datetime
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from ui.training_form import render_training_form  # Import the form rendering function
import os
from .utils import get_badge_counts  # Assuming you have a utility function for badge counts

class TrainingController:
    def __init__(self, db):
        self.db = db
        # Assuming a table named 'training_files' exists
        self.training_files_table = db.t.training_files

    def show_training_tab(self, request: Request):
        """Renders the 'Täiendkoolitus' tab content."""
        user_email = request.session.get("user_email")
        if not user_email:
            return Div("Authentication Error", cls="text-red-500 p-4")

        page_title = "Täiendkoolitus | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

        # --- Render Content Fragment ---
        # Call the form rendering function
        training_content = render_training_form()

        # --- Check for HTMX Request Header ---
        if request.headers.get('HX-Request'):
            print(f"--- DEBUG: Returning {page_title} tab fragment + OOB nav/title for HTMX ---") # Updated log
            # 1. Content Fragment (training_content)

            # 2. OOB Navigation Swap
            updated_tab_nav = tab_nav(active_tab="taiendkoolitus", request=request, badge_counts=badge_counts) # Use 'taiendkoolitus' ID
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")

            # 3. OOB Title Swap
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")

            # 4. Return all three components
            return training_content, oob_nav, oob_title
        else:
            # Full page load
            print(f"--- DEBUG: Returning full app_layout for {page_title} tab ---") # Updated log
            return app_layout(
                request=request,
                title=page_title, # Pass title for full page load
                content=training_content,
                active_tab="taiendkoolitus",
                badge_counts=badge_counts  # Pass badge counts for the navbar
            )


    async def upload_training_files(self, request: Request):
        """Handles the upload of training files."""
        user_email = request.session.get("user_email")
        if not user_email:
            return ToastAlert("Authentication Error", alert_type="error")

        try:
            form_data = await request.form()
            files = form_data.get("training_files")  # Get the uploaded files

            if not files:
                return ToastAlert("No files uploaded", alert_type="error")

            # --- Process each uploaded file ---
            for file in files:
                # Basic file validation (MIME type, size)
                if file.content_type != "application/pdf":
                    return ToastAlert(f"Invalid file type for {file.filename}. Only PDF files are allowed.", alert_type="error")

                if len(await file.read()) > 10 * 1024 * 1024:  # 10MB limit
                    return ToastAlert(f"File size for {file.filename} exceeds the 10MB limit.", alert_type="error")

                # --- Save the file ---
                file_content = await file.read()  # Read file content
                # Generate a unique filename (you might want to use a more robust method)
                storage_filename = f"{user_email}_{file.filename}"
                file_path = os.path.join("uploads", storage_filename)  # Define your upload directory

                # Ensure the upload directory exists
                os.makedirs("uploads", exist_ok=True)

                with open(file_path, "wb") as f:
                    f.write(file_content)

                # --- Save file metadata to the database ---
                file_record = {
                    "user_email": user_email,
                    "file_description": form_data.get("file_description"),  # Get file description
                    "original_filename": file.filename,
                    "storage_identifier": storage_filename,
                    "upload_timestamp": str(datetime.datetime.now()),  # Or use a more specific timestamp
                }
                self.training_files_table.insert(file_record)

            return Response(headers={'HX-Redirect': '/app/taiendkoolitus'})  # Redirect on success

        except Exception as e:
            print(f"--- ERROR [upload_training_files]: File upload failed for {user_email}: {e} ---")
            return ToastAlert(f"File upload failed: {e}", alert_type="error")