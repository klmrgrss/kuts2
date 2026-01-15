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
             return (content, Div(tab_nav("dokumendid", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"), Title("Dokumendid | Taotlemine", id="page-title", hx_swap_oob="innerHTML"))
        
        return app_layout(req, "Dokumendid | Taotlemine", content, "dokumendid", self.db, badge_counts=get_badge_counts(self.db, uid))

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
                if not desc: desc = f"{meta['institution']} - {meta['specialty']}"

            self.tbl.insert({
                "user_email": uid, "document_type": dtype, "description": desc,
                "metadata": json.dumps(meta), "original_filename": fname,
                "storage_identifier": sid, "upload_timestamp": str(datetime.datetime.now())
            })
            
            return Response(headers={'HX-Redirect': '/app/dokumendid'})
        except Exception as e:
            error(f"Upload error {uid}: {e}")
            return Response("Üleslaadimine ebaõnnestus", 500)