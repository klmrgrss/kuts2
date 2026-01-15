# app/controllers/employment_proof.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from ui.employment_proof_form import render_employment_proof_form
from .utils import get_badge_counts
from utils.log import log, error
from pathlib import Path
import datetime, uuid

UPLOAD_DIR = Path(__file__).parents[2] / 'uploads'

class EmploymentProofController:
    def __init__(self, db):
        self.db = db
        self.tbl = db.t.employment_proof

    def show_employment_proof_tab(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Div("Autentimisviga", cls="text-red-500 p-4")

        content = render_employment_proof_form()
        
        if req.headers.get('HX-Request'):
             counts = get_badge_counts(self.db, uid)
             return (content, Div(tab_nav("tootamise_toend", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"), Title("Töötamise tõend | Taotlemine", id="page-title", hx_swap_oob="innerHTML"))
        
        return app_layout(req, "Töötamise tõend | Taotlemine", content, "tootamise_toend", self.db, badge_counts=get_badge_counts(self.db, uid))

    async def upload_employment_proof(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return ToastAlert("Autentimine vajalik", alert_type="error")

        try:
            form = await req.form()
            f = form.get("employment_proof")
            if not f or not f.filename: return ToastAlert("Fail puudub", alert_type="error")
            
            # Relaxed validation for containers
            # if f.content_type not in ["application/octet-stream", "application/vnd.etsi.asic-e+zip"]: pass 

            content = await f.read()
            if len(content) > 10*1024*1024: return ToastAlert("Fail liiga suur (>10MB)", alert_type="error")

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            sname = f"{uid}_employment_proof_{f.filename}"
            (UPLOAD_DIR / sname).write_bytes(content)

            # Upsert
            self.tbl.insert({
                "user_email": uid,
                "file_description": form.get("file_description"),
                "original_filename": f.filename,
                "storage_identifier": sname,
                "upload_timestamp": str(datetime.datetime.now())
            }, pk='user_email', replace=True)

            return Response(headers={'HX-Redirect': '/app/tootamise_toend'})
        except Exception as e:
            error(f"Emp proof upload error {uid}: {e}")
            return ToastAlert(f"Viga: {e}", alert_type="error")