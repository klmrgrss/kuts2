# app/controllers/documents.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from ui.documents_page import render_documents_page
import os
import uuid
import json
import traceback
import datetime
# --- Add GCS and security imports ---
from google.cloud import storage
from werkzeug.utils import secure_filename

# --- Define the GCS bucket name (replace with your actual bucket name) ---
# It's best practice to load this from an environment variable.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name-here")


class DocumentsController:
    def __init__(self, db):
        self.db = db
        self.documents_table = db.t.documents
        # --- Initialize the GCS client ---
        # This will automatically use the credentials from your .env file
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(GCS_BUCKET_NAME)
            # --- ADD THIS LINE FOR CONFIRMATION ---
            print(f"--- SUCCESS: Successfully connected to GCS and bucket '{GCS_BUCKET_NAME}'. ---")
        except Exception as e:
            print(f"--- FATAL ERROR: Could not connect to GCS. Is GOOGLE_APPLICATION_CREDENTIALS set? Error: {e} ---")
            self.storage_client = None
            self.bucket = None


    def show_documents_tab(self, request: Request):
        user_email = request.session.get("user_email")
        if not user_email:
            return Div("Authentication Error", cls="text-red-500 p-4")

        page_title = "Dokumentide lisamine | Ehitamise valdkonna kutsete taotlemine"
        badge_counts = get_badge_counts(self.db, user_email)

        # Fetch existing documents to display them on the page
        all_docs = self.documents_table(order_by='id')
        user_documents = [doc for doc in all_docs if doc.get('user_email') == user_email]

        # Render the page content using a new view function
        content = render_documents_page(user_documents)

        if request.headers.get('HX-Request'):
            updated_tab_nav = tab_nav(active_tab="dokumendid", request=request, badge_counts=badge_counts)
            oob_nav = Div(updated_tab_nav, id="tab-navigation-container", hx_swap_oob="outerHTML")
            oob_title = Title(page_title, id="page-title", hx_swap_oob="innerHTML")
            return content, oob_nav, oob_title
        else:
            return app_layout(
                request=request, title=page_title, content=content,
                active_tab="dokumendid", badge_counts=badge_counts,
                db=self.db
            )

    async def upload_document(self, request: Request, document_type: str):
        user_email = request.session.get("user_email")
        if not user_email: return Response("Authentication Error", status_code=403)
        if not self.bucket: return Response("Cloud Storage is not configured correctly.", status_code=500)

        try:
            form_data = await request.form()
            doc_file = form_data.get("document_file")
            description = form_data.get("description", "")

            if not doc_file or not doc_file.filename:
                 return Response("File not provided", status_code=400)

            # --- Secure File Handling ---
            original_filename = secure_filename(doc_file.filename)
            file_content = await doc_file.read()
            file_extension = os.path.splitext(original_filename)[1]
            # Create a unique identifier for storage to prevent filename collisions
            storage_identifier = f"{user_email}/{uuid.uuid4()}{file_extension}"

            # --- Upload to Google Cloud Storage ---
            blob = self.bucket.blob(storage_identifier)
            blob.upload_from_string(
                file_content,
                content_type=doc_file.content_type
            )
            print(f"--- SUCCESS [GCS Upload]: Uploaded '{original_filename}' to '{storage_identifier}' in bucket '{GCS_BUCKET_NAME}'.")


            # --- Prepare Data for DB ---
            metadata = {}
            if document_type == 'education':
                metadata = {
                    "institution": form_data.get("institution", ""),
                    "specialty": form_data.get("specialty", ""),
                    "graduation_date": form_data.get("graduation_date", "")
                }
                if not description:
                    description = f"{metadata.get('institution', '')} - {metadata.get('specialty', '')}"

            db_data = {
                "user_email": user_email,
                "document_type": document_type,
                "description": description,
                "metadata": json.dumps(metadata),
                "original_filename": original_filename,
                "storage_identifier": storage_identifier, # Save the GCS path
                "upload_timestamp": str(datetime.datetime.now())
            }

            self.documents_table.insert(db_data)

            # --- THE FIX: On success, tell the browser to redirect to the documents tab ---
            # This triggers a new GET request, ensuring the page reloads with the new file list.
            return Response(headers={'HX-Redirect': '/app/dokumendid'})


        except Exception as e:
            print(f"--- ERROR [upload_document]: {e} ---")
            traceback.print_exc()
            return Response("File upload failed", status_code=500)