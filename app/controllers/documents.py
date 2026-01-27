# app/controllers/documents.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from ui.documents_page import render_documents_page
from google.cloud import storage
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
from utils.log import log, error, debug
from pathlib import Path
import os, uuid, json, datetime

GCS_BUCKET = os.environ.get("GCS_BUCKET_NAME", "your-gcs-bucket-name-here")
ALLOW_LOCAL = os.environ.get("ALLOW_LOCAL_STORAGE_FALLBACK", "").lower() in {"1", "true", "yes"}

class DocumentsController:
    def __init__(self, db):
        self.db, self.tbl = db, db.t.documents
        self.documents_table = self.tbl # Alias for main.py compatibility
        self.bucket, self.local_dir = self._setup_storage()
        self.local_storage_dir = self.local_dir # Alias for main.py compatibility

    def _setup_storage(self):
        try:
            if not GCS_BUCKET or "name-here" in GCS_BUCKET: raise ValueError("GCS Bucket not config")
            
            creds = None
            if raw := os.environ.get("GCS_SA_JSON"):
                info = json.loads(raw)
                creds = service_account.Credentials.from_service_account_info(info)
            
            client = storage.Client(credentials=creds, project=creds.project_id if creds else None)
            bucket = client.bucket(GCS_BUCKET)
            debug(f"GCS connected: {GCS_BUCKET}")
            return bucket, None
        except Exception as e:
            error(f"GCS init failed: {e}")
            if ALLOW_LOCAL:
                ldir = Path(__file__).parents[2] / "Uploads"
                ldir.mkdir(parents=True, exist_ok=True)
                debug(f"Using local storage: {ldir}")
                return None, ldir
            error("Cloud storage required & local disabled")
            return None, None

    def show_documents_tab(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Div("Autentimisviga", cls="text-red-500 p-4")

        docs = self.tbl('user_email = ?', [uid]) # Optimized fetch
        content = render_documents_page(docs)

        if req.headers.get('HX-Request'):
             counts = get_badge_counts(self.db, uid)
             return (content, Div(id="footer-container", hx_swap_oob="innerHTML"), Div(tab_nav("dokumendid", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"), Title("Dokumentide lisamine | Ehitamise kutsed", id="page-title", hx_swap_oob="innerHTML"))
        
        return app_layout(req, "Dokumentide lisamine | Ehitamise kutsed", content, "dokumendid", self.db, badge_counts=get_badge_counts(self.db, uid))

    async def upload_document(self, req: Request, dtype: str):
        uid = req.session.get("user_email")
        if not uid: return Response("Autentimisviga", 403)
        if not self.bucket and not self.local_dir: return Response("Salvestusruumi viga", 503)

        try:
            form = await req.form()
            f = form.get("document_file")
            desc = form.get("description", "")
            
            if not f or not f.filename: return Response("Fail puudub", 400)
            
            fname = secure_filename(f.filename) or f"file_{uuid.uuid4().hex}"
            ext = Path(fname).suffix
            content = await f.read()
            sid = ""

            if self.bucket:
                sid = f"{uid}/{uuid.uuid4()}{ext}"
                self.bucket.blob(sid).upload_from_string(content, content_type=f.content_type)
            else:
                uname = secure_filename(uid) or uuid.uuid4().hex
                path = self.local_dir / uname / f"{uuid.uuid4()}{ext}"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                sid = f"local:{path.relative_to(self.local_dir)}"

            meta = {}
            if dtype == 'education':
                meta = {"institution": form.get("institution", ""), "specialty": form.get("specialty", ""), "graduation_date": form.get("graduation_date", "")}
                if not desc:
                    # Construct description from metadata if available
                    parts = [meta['institution'], meta['specialty']]
                    desc = " - ".join([p for p in parts if p])
                    # If still empty, use filename (or leave empty to let UI handle it)
                    if not desc: desc = fname

            self.tbl.insert({
                "user_email": uid, "document_type": dtype, "description": desc,
                "metadata": json.dumps(meta), "original_filename": fname,
                "storage_identifier": sid, "upload_timestamp": str(datetime.datetime.now())
            })
            
            return Response(headers={'HX-Redirect': '/app/dokumendid'})
        except Exception as e:
            error(f"Upload error {uid}: {e}")
            return Response("Üleslaadimine ebaõnnestus", 500)

    def delete_document(self, req: Request, doc_id: int):
        uid = req.session.get("user_email")
        if not uid: return Response("Autentimisviga", 403)
        
        try:
            doc = self.tbl[doc_id]
            if not doc: return Response("Dokumenti ei leitud", 404)
            if doc.get('user_email') != uid: return Response("Puudub õigus", 403)
            
            # Delete from DB
            self.tbl.delete(doc_id)
            
            # Optional: Delete from storage
            # (Simplification: We keep files for audit or soft-delete in real apps, 
            # but here we could delete. For now, just DB removal is sufficient for the UI view)
            
            # Return updated list
            debug(f"Document {doc_id} deleted by {uid}")
            
            # Re-render the tab content
            # We call show_documents_tab but need to ensure it returns the partial content expected by HTMX
            # We can mock the HX-Request header or just split the logic.
            # Easiest reuse:
            docs = self.tbl('user_email = ?', [uid])
            return render_documents_page(docs)
            
        except Exception as e:
            error(f"Delete error {uid}: {e}")
            return Response("Kustutamine ebaõnnestus", 500)