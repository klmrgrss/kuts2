# app/controllers/work_experience.py
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from fastlite import NotFoundError
from ui.layouts import app_layout, ToastAlert
from ui.nav_components import tab_nav
from .utils import get_badge_counts
from monsterui.all import *
from ui.work_experience_view_v2 import render_work_experience_form_v2
from models import WorkExperience
from utils.log import log, error

class WorkExperienceController:
    def __init__(self, db): 
        self.db = db
        self.exp_tbl = db.t.work_experience
        self.qual_tbl = db.t.applied_qualifications

    def _get_activities(self, uid: str) -> list[str]:
        try:
            quals = self.qual_tbl('user_email = ?', [uid])
            return sorted({q['qualification_name'] for q in quals if q.get('qualification_name')})
        except Exception as e:
            error(f"Act fetch error {uid}: {e}")
            return []

    def show_workex_tab(self, req: Request, edit_data: dict = None):
        uid = req.session.get("user_email")
        if not uid: return Div("Autentimisviga", cls="text-red-500 p-4")

        acts = self._get_activities(uid)
        content, footer = None, None
        
        if not acts:
            content = Div(
                Div(
                    P("Ühtegi tegevusala pole valitud. Töökogemuse lisamiseks vali esmalt taotletavad kutsed"), # Removed font-bold
                    cls="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative text-center mb-6"
                ),
                Div(
                    A(Button("Vali taotletavad kutsed", cls="btn btn-error text-white"), href="/app/kutsed"),
                    cls="flex justify-center"
                ),
                cls="max-w-5xl mx-auto" # Match form width
            )
        else:
            exps = self.exp_tbl('user_email = ?', [uid])
            sel_act = req.query_params.get('activity')
            if not sel_act and not edit_data and len(acts) == 1: sel_act = acts[0]
            
            content, footer = render_work_experience_form_v2(
                available_activities=acts, 
                experiences=exps, 
                experience=edit_data, 
                selected_activity=sel_act
            )

        if req.headers.get('HX-Request'):
             counts = get_badge_counts(self.db, uid)
             ft = Div(footer, id="footer-container", hx_swap_oob="innerHTML") if footer else Div(id="footer-container", hx_swap_oob="innerHTML")
             return content, ft, Div(tab_nav("workex", req, counts), id="tab-navigation-container", hx_swap_oob="outerHTML"), Title("Töökogemuse lisamine | Ehitamise kutsed", id="page-title", hx_swap_oob="innerHTML")

        return app_layout(req, "Töökogemuse lisamine | Ehitamise kutsed", content, "workex", self.db, footer=footer, badge_counts=get_badge_counts(self.db, uid), container_class="max-w-7xl")

    def show_workex_edit_form(self, req: Request, eid: int):
        uid = req.session.get("user_email")
        if not uid: return Div("Autentimisviga", cls="text-red-500 p-4")
        try:
            row = self.exp_tbl[eid]
            if row['user_email'] != uid: return Div("Ligipääs puudub", cls="text-red-500")
            return self.show_workex_tab(req, edit_data=row)
        except NotFoundError: return Div("Kirjet ei leitud", cls="text-red-500")

    async def save_workex_experience(self, req: Request):
        uid = req.session.get("user_email")
        if not uid: return Response("Autentimisviga", 403)
        
        try:
            form = await req.form()
            eid_str = form.get("experience_id")
            is_edit = eid_str and eid_str != 'None' and eid_str.isdigit()
            eid = int(eid_str) if is_edit else None

            # Dynamic field mapping
            data = {k: form.get(k) for k in WorkExperience.__dataclass_fields__ if form.get(k) is not None}
            data.update({
                'user_email': uid,
                'permit_required': 1 if form.get("permit_required") == 'on' else 0,
                'start_date': form.get("start_date"), # Explicit to ensure no overwrite if None? original logic overwrite if not None.
                'end_date': form.get("end_date")
            })
            if not data['start_date']: data.pop('start_date', None)
            if not data['end_date']: data.pop('end_date', None)

            if not data.get("role"): return RedirectResponse("/app/workex?error=missing_fields", 303)

            if is_edit:
                if self.exp_tbl[eid]['user_email'] != uid: return Response("Forbidden", 403)
                self.exp_tbl.update(data, id=eid)
            else:
                data.pop('id', None)
                self.exp_tbl.insert(data)
                
            return self.show_workex_tab(req)
        except Exception as e:
            error(f"Workex save error {uid}: {e}")
            return RedirectResponse("/app/workex?error=save_failed", 303)

    def delete_workex_experience(self, req: Request, eid: int):
        uid = req.session.get("user_email")
        if not uid: return ToastAlert("Autentimine vajalik", alert_type="error")
        try:
            if self.exp_tbl[eid]['user_email'] != uid: return ToastAlert("Ligipääs puudub", alert_type="error")
            self.exp_tbl.delete(eid)
            return self.show_workex_tab(req)
        except Exception as e:
            error(f"Workex del error {uid}: {e}")
            return ToastAlert("Kustutamine ebaõnnestus", alert_type="error")