# app/controllers/qualifications.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response
from ui.qualification_form import render_qualification_form
from ui.layouts import ToastAlert, app_layout
from ui.nav_components import tab_nav
from ui.checkbox_group import render_checkbox_group
from config.qualification_data import kt
from monsterui.all import *
from monsterui.daisy import Toast, AlertT, ToastHT, ToastVT
from .utils import get_badge_counts
from utils.log import log, debug, error

class QualificationController:
    def __init__(self, db): self.db, self.tbl = db, db.t.applied_qualifications

    def _prepare_data(self, uid: str):
        """Prepare form data efficiently using set lookups."""
        saved = self.tbl('user_email = ?', [uid])
        my_quals = {(r['level'], r['qualification_name'], r['specialisation']) for r in saved}
        
        secs, cid = {}, 0
        for lvl_name, lvl_data in kt.items():
            for cat, items in lvl_data.items():
                if cat == "costs" or not isinstance(items, list): continue
                cid += 1
                effective = [cat] if items == ["Valikkompetentsid puuduvad"] else items
                
                # Check how many items in this section are saved
                found = [spec for spec in effective if (lvl_name, cat, spec) in my_quals]
                
                secs[cid] = {
                    "level": lvl_name, "category": cat, "items": effective, "id": cid,
                    "preselected": {f"qual_{cid}_{effective.index(s)}": True for s in found},
                    "toggle_on": len(effective) > 0 and len(found) == len(effective)
                }
        return secs
    
    def show_qualifications_tab(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Div("Sisselogimine on vajalik", cls="text-red-500 p-4")
        
        try:
            sections = self._prepare_data(uid)
            content, footer = render_qualification_form(sections=sections, app_id=uid)
            
            if req.headers.get('HX-Request'):
                counts = get_badge_counts(self.db, uid)
                return (
                    content,
                    Div(tab_nav("kutsed", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"),
                    Title("Taotletavad kutsed | Ehitamise kutsed", id="page-title", hx_swap_oob="innerHTML"),
                    Div(footer, id="footer-container", hx_swap_oob="innerHTML") if footer else ""
                )
            
            return app_layout(req, "Taotletavad kutsed | Ehitamise kutsed", content, "kutsed", self.db, footer=footer, badge_counts=get_badge_counts(self.db, uid))
        except Exception as e:
            error(f"Qual init error {uid}: {e}")
            return app_layout(req, "Viga", Div(f"Viga: {e}", cls="text-red-500"), "kutsed", self.db)

    async def handle_toggle(self, req: Request, sid: int, app_id: str):
        try:
            form = await req.form()
            on = form.get(f"toggle-{sid}") == "on"
            uid = req.session.get("user_email", app_id)
            
            all_sec = self._prepare_data(uid)
            sec = all_sec.get(sid)
            if not sec: return Div("Viga: sektsiooni ei leitud", cls="text-red-500")
            
            checked = {f"qual_{sid}_{i}": True for i in range(len(sec["items"]))} if on else {}
            return render_checkbox_group(sid, sec["items"], {"level": sec["level"], "category": sec["category"]}, checked)
        except Exception as e:
            error(f"Toggle error: {e}")
            return Div("Tehniline viga", cls="text-red-500")

    async def submit_qualifications(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Alert("Sisselogimine vajalik", cls="text-red-500", id="msg", hx_swap_oob="innerHTML")
        
        try:
            form = await req.form()
            secs = self._prepare_data(uid)
            rows = []
            
            for k, v in form.items():
                if not k.startswith("qual_") or v != "on": continue
                try:
                    p = k.split("_")
                    sid, idx = int(p[1]), int(p[2])
                    sec = secs.get(sid)
                    if sec and 0 <= idx < len(sec["items"]):
                        rows.append({
                            "user_email": uid, "qualification_name": sec["category"],
                            "level": sec["level"], "specialisation": sec["items"][idx],
                            "activity": sec["category"], "is_renewal": 0, "application_date": None
                        })
                except Exception as e: error(f"Parse key error {k}: {e}")

            # Atomic replacement (ideally use transaction, but here explicit steps)
            self.tbl.delete_where('user_email=?', [uid])
            if rows: self.tbl.insert_all(rows)
            
            return self.show_qualifications_tab(req)
        except Exception as e:
            error(f"Save error {uid}: {e}")
            return Alert(f"Salvestamine ebaõnnestus: {e}", cls="text-red-500", id="msg", hx_swap_oob="innerHTML")