# app/controllers/training.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from ui.training_form import render_training_form
from .utils import get_badge_counts
from utils.log import log, error
from pathlib import Path
import datetime, uuid

UPLOAD_DIR = Path(__file__).parents[2] / 'uploads'

class TrainingController:
    def __init__(self, db):
        self.db = db
        self.tbl = db.t.training_files

    def show_training_tab(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Div("Autentimisviga", cls="text-red-500 p-4")

        content = render_training_form()
        
        if req.headers.get('HX-Request'):
             counts = get_badge_counts(self.db, uid)
             return (content, Div(tab_nav("taiendkoolitus", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"), Title("Täiendkoolitus | Taotlemine", id="page-title", hx_swap_oob="innerHTML"))
        
        return app_layout(req, "Täiendkoolitus | Taotlemine", content, "taiendkoolitus", self.db, badge_counts=get_badge_counts(self.db, uid))

    async def upload_training_files(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return ToastAlert("Autentimine vajalik", alert_type="error")

        try:
            form = await req.form()
            files = form.getlist("training_files")
            desc = form.get("file_description", "")

            if not files: return ToastAlert("Faile ei leitud", alert_type="error")

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            
            for f in files:
                if not f.filename: continue
                # if f.content_type != "application/pdf": return ToastAlert(f"Vale failitüüp: {f.filename} (Ainult PDF)", alert_type="error")
                
                content = await f.read()
                if len(content) > 10*1024*1024: return ToastAlert(f"Fail liiga suur: {f.filename}", alert_type="error")
                
                sname = f"{uid}_{uuid.uuid4().hex}_{f.filename}"
                (UPLOAD_DIR / sname).write_bytes(content)

                self.tbl.insert({
                    "user_email": uid, "file_description": desc, "original_filename": f.filename,
                    "storage_identifier": sname, "upload_timestamp": str(datetime.datetime.now())
                })

            return Response(headers={'HX-Redirect': '/app/taiendkoolitus'})
        except Exception as e:
            error(f"Training upload error {uid}: {e}")
            return ToastAlert(f"Viga: {e}", alert_type="error")