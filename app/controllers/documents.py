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

# Define the upload directory consistently
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')

class DocumentsController:
    def __init__(self, db):
        self.db = db
        self.documents_table = db.t.documents

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
                db=self.db # <-- FIX: Pass the database connection to the layout
            )

    async def upload_document(self, request: Request, document_type: str):
        user_email = request.session.get("user_email")
        if not user_email: return Response("Authentication Error", status_code=403)

        try:
            form_data = await request.form()
            doc_file = form_data.get("document_file")
            description = form_data.get("description", "")

            # --- File Handling ---
            if not doc_file or not doc_file.filename:
                 return Response("File not provided", status_code=400)

            original_filename = doc_file.filename
            file_content = await doc_file.read()
            file_extension = os.path.splitext(original_filename)[1]
            storage_identifier = f"{uuid.uuid4()}{file_extension}"
            
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            file_path = os.path.join(UPLOAD_DIR, storage_identifier)
            with open(file_path, "wb") as f: f.write(file_content)

            # --- Prepare Data for DB ---
            metadata = {}
            if document_type == 'education':
                metadata = {
                    "institution": form_data.get("institution", ""),
                    "specialty": form_data.get("specialty", ""),
                    "graduation_date": form_data.get("graduation_date", "")
                }
                # Use metadata for description if not provided
                if not description:
                    description = f"{metadata['institution']} - {metadata['specialty']}"

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

            # On success, reload the tab to show the new document in the list
            return self.show_documents_tab(request)

        except Exception as e:
            print(f"--- ERROR [upload_document]: {e} ---")
            traceback.print_exc()
            return Response("File upload failed", status_code=500)