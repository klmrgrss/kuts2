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
from pathlib import Path
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
        self.storage_client = None
        self.bucket = None
        self.local_storage_dir: Path | None = None

        bucket_name = GCS_BUCKET_NAME
        try:
            if not bucket_name or bucket_name == "your-gcs-bucket-name-here":
                raise ValueError("GCS bucket name is not configured.")

            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(bucket_name)
            print(f"--- SUCCESS: Successfully connected to GCS and bucket '{bucket_name}'. ---")
        except Exception as e:
            print(f"--- WARNING: Falling back to local storage. GCS unavailable: {e} ---")
            self.storage_client = None
            self.bucket = None

            fallback_dir = Path(__file__).resolve().parents[2] / "Uploads"
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                self.local_storage_dir = fallback_dir
                print(f"--- INFO: Using local upload directory at '{self.local_storage_dir}'. ---")
            except Exception as dir_err:
                print(f"--- FATAL ERROR: Could not prepare local upload directory: {dir_err} ---")
                self.local_storage_dir = None


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
        if not user_email:
            return Response("Authentication Error", status_code=403)
        if not self.bucket and not self.local_storage_dir:
            return Response("Storage is not configured correctly.", status_code=500)

        try:
            form_data = await request.form()
            doc_file = form_data.get("document_file")
            description = form_data.get("description", "")

            if not doc_file or not doc_file.filename:
                 return Response("File not provided", status_code=400)

            # --- Secure File Handling ---
            original_filename = secure_filename(doc_file.filename)
            if not original_filename:
                return Response("Invalid filename", status_code=400)
            file_content = await doc_file.read()
            file_extension = os.path.splitext(original_filename)[1]
            # Create a unique identifier for storage to prevent filename collisions
            storage_identifier = f"{user_email}/{uuid.uuid4()}{file_extension}"

            if self.bucket:
                # --- Upload to Google Cloud Storage ---
                blob = self.bucket.blob(storage_identifier)
                blob.upload_from_string(
                    file_content,
                    content_type=doc_file.content_type
                )
                print(f"--- SUCCESS [GCS Upload]: Uploaded '{original_filename}' to '{storage_identifier}' in bucket '{GCS_BUCKET_NAME}'.")
            else:
                sanitized_email = secure_filename(user_email)
                if not sanitized_email:
                    sanitized_email = uuid.uuid4().hex
                user_folder = self.local_storage_dir / sanitized_email
                user_folder.mkdir(parents=True, exist_ok=True)
                unique_name = f"{uuid.uuid4()}{file_extension}"
                local_path = user_folder / unique_name
                with open(local_path, "wb") as out_file:
                    out_file.write(file_content)
                storage_identifier = f"local:{(Path(sanitized_email) / unique_name).as_posix()}"
                print(f"--- SUCCESS [Local Upload]: Stored '{original_filename}' at '{local_path}'. ---")


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
                "storage_identifier": storage_identifier,
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