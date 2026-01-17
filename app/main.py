# app/main.py
import sys, os, json, datetime, traceback
from pathlib import Path
from dotenv import load_dotenv
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import FileResponse, Response, RedirectResponse
from fastlite import NotFoundError

# Core & UI
from fasthtml.common import *
from monsterui.all import *
from ui.landing.page import render_landing_page
from ui.layouts import public_layout

# Logic & Auth
from database import setup_database
from auth.bootstrap import ensure_default_users
from auth.guards import require_role
from auth.middleware import AuthMiddleware
from auth.roles import ADMIN, APPLICANT, EVALUATOR, ALL_ROLES, normalize_role
from logic.validator import ValidationEngine
from utils.log import log, debug, error

# Controllers
from controllers.auth import AuthController
from controllers.applicant import ApplicantController
from controllers.qualifications import QualificationController
from controllers.work_experience import WorkExperienceController
from controllers.training import TrainingController
from controllers.employment_proof import EmploymentProofController
from controllers.documents import DocumentsController
from controllers.review import ReviewController
from controllers.evaluator import EvaluatorController
from controllers.evaluator_search_controller import EvaluatorSearchController
from controllers.evaluator_workbench_controller import EvaluatorWorkbenchController
from controllers.dashboard import DashboardController

# --- Setup ---
APP_ROOT = str(Path(__file__).parent)
if APP_ROOT not in sys.path: sys.path.insert(0, APP_ROOT)

load_dotenv()
APP_DIR, STATIC_DIR = Path(__file__).parent, Path(__file__).parent/'static'
UPLOAD_DIR = APP_DIR.parent/'Uploads'
debug(f"Static: {STATIC_DIR}, Uploads: {UPLOAD_DIR}")

db = setup_database()
if not db: raise RuntimeError("Database setup failed")
ensure_default_users(db)

# Wiring
try:
    val_eng = ValidationEngine(APP_DIR/'config'/'rules.toml')
    auth_ctrl = AuthController(db)
    qual_ctrl = QualificationController(db)
    appl_ctrl = ApplicantController(db)
    work_ctrl = WorkExperienceController(db)
    train_ctrl = TrainingController(db)
    emp_ctrl = EmploymentProofController(db)
    doc_ctrl = DocumentsController(db)
    rev_ctrl = ReviewController(db)
    
    # Cyclic dependencies in Evaluator controllers handled by manual linking
    eval_search = EvaluatorSearchController(db, val_eng)
    eval_main = EvaluatorController(db, eval_search, None, val_eng)
    eval_bench = EvaluatorWorkbenchController(db, val_eng, eval_main, eval_search)
    eval_main.workbench_controller = eval_bench
    eval_main.search_controller = eval_search
    
    dash_ctrl = DashboardController(db, appl_ctrl, eval_main)
except AttributeError as e: raise RuntimeError(f"Controller init failed: {e}")

# App Init
routes = []
if STATIC_DIR.is_dir(): routes.append(Mount('/static', app=StaticFiles(directory=STATIC_DIR, html=True), name='static'))
else: raise RuntimeError("Static directory missing")

SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "default-insecure-key-for-local-dev")
app, rt = fast_app(
    hdrs=Theme.blue.headers(),
    middleware=[
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=14*86400),
        Middleware(AuthMiddleware, db=db, session_secret=SESSION_SECRET_KEY),
    ],
    routes=routes,
    debug=True
)

# --- Public Routes ---
@rt("/")
def get_landing(req): return public_layout("Tere tulemast!", render_landing_page())

@rt("/favicon.ico")
def get_favicon(req): return FileResponse(STATIC_DIR/'favicon.ico')

@rt("/test")
def get_test(req): return Div(H1("Test Route"), P("This is a test route"))

@rt("/logout")
def get_logout(req): return auth_ctrl.logout(req)

# --- Smart-ID Auth (Legacy logic preserved but compacted) ---
@rt("/auth/smart-id/form")
def get_smart_id_form(req): return auth_ctrl.get_login_form()

@rt("/auth/smart-id/initiate", methods=["POST"])
async def post_smart_id(req, national_id: str): return await auth_ctrl.initiate_smart_id(national_id)

@rt("/auth/smart-id/status/{session_id:str}")
async def get_smart_id_status(req, session_id: str): return await auth_ctrl.check_smart_id_status(req, session_id)

# --- App Routes (Applicant) ---
# Common Guard: APPLICANT, EVALUATOR, ADMIN
G_APP = [APPLICANT, EVALUATOR, ADMIN]

@rt("/dashboard")
@require_role(*G_APP)
def get_dashboard(req): return dash_ctrl.show_dashboard(req, req.state.current_user)

@rt("/dashboard/evaluators", methods=["POST"])
@require_role(ADMIN)
async def post_dashboard_eval(req): return await dash_ctrl.add_evaluator(req)

@rt("/dashboard/evaluators/{id_code}", methods=["DELETE"])
@require_role(ADMIN)
def delete_dashboard_eval(req, id_code: str): return dash_ctrl.delete_evaluator(req, id_code)

@rt("/app")
@require_role(*G_APP)
def get_app_root(req): return RedirectResponse("/dashboard", status_code=303)

@rt("/app/taotleja")
@require_role(*G_APP)
def get_applicant(req): return appl_ctrl.show_applicant_tab(req)

@rt("/app/kutsed")
@require_role(*G_APP)
def get_qual(req): return qual_ctrl.show_qualifications_tab(req)

@rt('/app/kutsed/toggle', methods=["POST"])
@require_role(*G_APP)
async def post_qual_toggle(req, section_id: int, app_id: str): return await qual_ctrl.handle_toggle(req, section_id, app_id)

@rt('/app/kutsed/submit', methods=["POST"])
@require_role(*G_APP)
async def post_qual_submit(req): return await qual_ctrl.submit_qualifications(req)

@rt("/app/workex")
@require_role(*G_APP)
def get_workex(req): return work_ctrl.show_workex_tab(req)

@rt("/app/workex/{eid:int}/edit")
@require_role(*G_APP)
def get_workex_edit(req, eid: int): return work_ctrl.show_workex_edit_form(req, eid)

@rt("/app/workex/save", methods=["POST"])
@require_role(*G_APP)
async def post_workex_save(req): return await work_ctrl.save_workex_experience(req)

@rt("/app/workex/{eid:int}/delete", methods=["DELETE"])
@require_role(*G_APP)
def del_workex(req, eid: int): return work_ctrl.delete_workex_experience(req, eid)

@rt("/app/taiendkoolitus")
@require_role(*G_APP)
def get_train(req): return train_ctrl.show_training_tab(req)

@rt("/app/taiendkoolitus/upload", methods=['POST'])
@require_role(*G_APP)
async def post_train_upload(req): return await train_ctrl.upload_training_files(req)

@rt("/app/tootamise_toend")
@require_role(*G_APP)
def get_emp_proof(req): return emp_ctrl.show_employment_proof_tab(req)

@rt("/app/tootamise_toend/upload", methods=['POST'])
@require_role(*G_APP)
async def post_emp_upload(req): return await emp_ctrl.upload_employment_proof(req)

@rt("/app/dokumendid")
@require_role(*G_APP)
def get_docs(req): return doc_ctrl.show_documents_tab(req)

@rt("/app/dokumendid/upload", methods=['POST'])
@require_role(*G_APP)
async def post_doc_upload(req, document_type: str): return await doc_ctrl.upload_document(req, document_type)

@rt("/app/ulevaatamine")
@require_role(*G_APP)
def get_review(req): return rev_ctrl.show_review_tab(req)

@rt("/app/ulevaatamine/submit", methods=['POST'])
@require_role(*G_APP)
async def post_rev_submit(req): return await rev_ctrl.submit_application(req)

# --- Evaluator Routes ---
G_EVAL = [EVALUATOR, ADMIN]

@rt("/evaluator/application/{user_email}")
@require_role(*G_EVAL)
def get_eval_app(req, user_email: str): return eval_main.show_application_detail(req, user_email)

@rt("/evaluator/application/{user_email}/qualification/{rid:int}/update", methods=["POST"])
@require_role(*G_EVAL)
async def post_qual_status(req, user_email: str, rid: int): return await eval_main.update_qualification_status(req, user_email, rid)

@rt("/evaluator/d")
@require_role(*G_EVAL)
def get_eval_dash_v2(req): return eval_main.show_dashboard_v2(req)

@rt("/evaluator/d/application/{qual_id:str}")
@require_role(*G_EVAL)
def get_eval_app_v2(req, qual_id: str): return eval_main.show_v2_application_detail(req, qual_id)

@rt("/evaluator/d/search_applications", methods=["POST"])
@require_role(*G_EVAL)
async def post_eval_search(req):
    form = await req.form()
    return eval_search.search_applications(req, form.get("search", ""))

@rt("/evaluator/d/re-evaluate/{qual_id:str}", methods=["POST"])
@require_role(*G_EVAL)
async def post_re_eval(req, qual_id: str): return await eval_bench.re_evaluate_application(req, qual_id)

@rt("/evaluator/test")
@require_role(*G_EVAL)
def get_eval_test(req): return eval_main.show_test_search_page(req)

@rt("/evaluator/test/search", methods=["POST"])
@require_role(*G_EVAL)
def post_eval_test_search(req, search: str = ""): return eval_main.handle_test_search(req, search)

# --- File Security ---
@rt("/files/view/{doc_id:int}")
@require_role(*G_APP)
def view_secure_file(req, doc_id: int):
    # This complex logic is preserved but logging reduced and style tightened
    user = req.state.current_user
    email = user["email"]
    try:
        doc = doc_ctrl.documents_table[doc_id]
        if doc.get('user_email') != email and user["role"] not in {ADMIN, EVALUATOR}:
            error(f"Access denied: {email} -> {doc.get('user_email')}")
            return Response("Access Denied", 403)
        
        sid = doc.get('storage_identifier')
        if not sid: return Response("Incomplete record", 500)
        
        if sid.startswith("local:"):
            if not doc_ctrl.local_storage_dir: return Response("Local storage config error", 500)
            path = (doc_ctrl.local_storage_dir / sid.split("local:", 1)[1]).resolve()
            # Path traversal check omitted for brevity but should be implied by `resolve` comparison in original code
            # Re-adding simple check:
            if doc_ctrl.local_storage_dir.resolve() not in path.parents: return Response("Invalid path", 400)
            if not path.exists(): return Response("File not found", 404)
            return FileResponse(path, filename=doc.get('original_filename') or path.name)
            
        # GCS
        if not doc_ctrl.bucket: return Response("Cloud config error", 500)
        blob = doc_ctrl.bucket.blob(sid)
        if not blob.exists(): return Response("File not found", 404)
        url = blob.generate_signed_url(version="v4", expiration=datetime.timedelta(minutes=10), method="GET")
        return RedirectResponse(url, 307)
    except Exception as e:
        error(f"File view error: {e}")
        return Response("Error", 500)

serve()