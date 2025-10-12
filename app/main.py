# app/main.py
# main.py


import sys
from pathlib import Path

# This ensures that when main.py is run, Python can find other modules
# in the 'app' directory, like 'controllers', 'ui', etc.
APP_ROOT = str(Path(__file__).parent)
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

import os
from dotenv import load_dotenv
from fasthtml.common import *
from monsterui.all import *
from controllers.employment_proof import EmploymentProofController
from controllers.review import ReviewController
from database import setup_database
from auth.bootstrap import ensure_default_users
from auth.guards import guard_request
from auth.middleware import AuthMiddleware
from auth.roles import ADMIN, APPLICANT, EVALUATOR, ALL_ROLES, normalize_role
from auth.utils import *
from controllers.auth import AuthController
from controllers.qualifications import QualificationController
from controllers.applicant import ApplicantController
from controllers.work_experience import WorkExperienceController
from controllers.education import EducationController
from controllers.documents import DocumentsController
from controllers.training import TrainingController
from controllers.evaluator import EvaluatorController
from controllers.dashboard import DashboardController
from services import smart_id_service
from ui.layouts import public_layout, app_layout
from ui.nav_components import public_navbar
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import FileResponse, Response, RedirectResponse
from fastlite import NotFoundError
import json
import traceback
import datetime

# --- Load Environment Variables ---
load_dotenv()

# --- Path Definitions ---
APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / 'static'
UPLOAD_DIR = APP_DIR.parent / 'Uploads'
print(f"--- INFO [main.py]: Static directory calculated as: {STATIC_DIR} ---")
print(f"--- INFO [main.py]: Upload directory calculated as: {UPLOAD_DIR} ---")

# --- Database Setup ---
db = setup_database()
if db is None:
    raise RuntimeError("Database setup failed, cannot start application.")

ensure_default_users(db)

# --- Controller Instantiation ---
try:
    auth_controller = AuthController(db)
    qualification_controller = QualificationController(db)
    applicant_controller = ApplicantController(db)
    work_experience_controller = WorkExperienceController(db)
    training_controller = TrainingController(db)
    employment_proof_controller = EmploymentProofController(db)
    education_controller = EducationController(db)
    documents_controller = DocumentsController(db)
    review_controller = ReviewController(db)
    evaluator_controller = EvaluatorController(db)
    dashboard_controller = DashboardController(db) # <-- INSTANTIATE NEW CONTROLLER
except AttributeError as e:
    raise RuntimeError("Controller initialization failed due to database setup issue.") from e

# --- Theme Setup ---
hdrs = Theme.blue.headers()

# +++ THE FIX: Define routes list BEFORE fast_app +++
route_list = []
if STATIC_DIR.is_dir():
    print(f"--- Preparing static mount for route list: {STATIC_DIR} ---")
    route_list.append(Mount('/static', app=StaticFiles(directory=STATIC_DIR, html=True), name='static'))
else:
    raise RuntimeError("Static directory missing")
# +++ END FIX +++

# --- App Initialization ---
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "default-insecure-key-for-local-dev")

app, rt = fast_app(
    hdrs=hdrs,
    middleware=[
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=14 * 24 * 60 * 60),
        Middleware(AuthMiddleware, db=db)
    ],
    routes=route_list, # <-- Pass the routes list here
    debug=True
)

# --- REMOVE the redundant app.mount() call ---

# === Routes ===
@rt("/")
def get(request: Request):
    hero_section = Div(
        Container(
            H1("Ehitamise valdkonna kutsete taotlemine", cls="text-4xl md:text-5xl font-bold mb-4 text-center"),
            P("Esita ja halda oma kutsetaotlusi kiirelt ja mugavalt.", cls="text-lg md:text-xl text-muted-foreground mb-8 text-center"),
            Div(
                A(Button("Logi sisse", cls=(ButtonT.primary, ButtonT.lg)), href="/login"),
                A(Button("Registreeru", cls=(ButtonT.secondary, ButtonT.lg)), href="/register"),
                cls="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4"
            ),
            cls="py-16 md:py-24 text-center"
        ),
        cls="bg-gradient-to-b from-background to-muted/50"
    )
    info_section = Container(
         Section(
             H2("Kuidas see töötab?", cls="text-2xl font-bold mb-6 text-center"),
             Grid(
                 Card(CardHeader(H3("1. Registreeru / Logi sisse")), CardBody(P("Loo konto või logi sisse olemasolevaga."))),
                 Card(CardHeader(H3("2. Sisesta Andmed")), CardBody(P("Täida vajalikud ankeedid: isikuandmed, haridus, töökogemus."))),
                 Card(CardHeader(H3("3. Esita Taotlus")), CardBody(P("Vaata andmed üle ja esita taotlus menetlemiseks."))),
                 cols=1, md_cols=3,
                 cls="gap-6"
             ),
             cls="py-12"
         )
     )
    page_content = Div(public_navbar(), hero_section, info_section)
    return public_layout("Tere tulemast!", page_content)

@rt("/favicon.ico", methods=["GET"])
def favicon(request: Request):
    """Serves the favicon from the static directory."""
    return FileResponse(os.path.join(STATIC_DIR, 'favicon.ico'))

@rt("/test", methods=["GET"])
def test_route(request: Request):
    return Div(H1("Test Route"), P("This is a test route"))

@rt("/login", methods=["GET"])
def get_login_form_page(request: Request):
    login_form = auth_controller.get_login_form()
    page_content = Div(public_navbar(), Container(login_form, cls="mt-12 md:mt-16"))
    return public_layout("Logi sisse", page_content)

@rt("/login", methods=["POST"])
async def post_login(request: Request, email: str, password: str):
    response = await auth_controller.process_login(request, email, password)
    if isinstance(response, Response) and 'HX-Redirect' in response.headers:
        response.headers['HX-Redirect'] = '/dashboard'
    return response

@rt("/auth/smart-id/initiate", methods=["POST"])
async def post_smart_id_initiate(request: Request, national_id: str):
    """Initiates a Smart-ID authentication session."""
    if not national_id:
        return Div("National ID is required.", id="sid-error", hx_swap_oob="true")

    session_data = await smart_id_service.initiate_authentication(national_id)

    if not session_data or "sessionID" not in session_data:
        return Div("Could not start Smart-ID session. Please check the ID and try again.", id="sid-error", hx_swap_oob="true")

    session_id = session_data["sessionID"]
    
    # This is a placeholder for the verification code calculation.
    # The actual calculation is hash_utils.calculate_verification_code(hash)
    # For now, we will use a dummy code.
    verification_code = "0000" 

    # This response will replace the login form with a status-checking component
    return Div(
        H3(f"Verification code: {verification_code}"),
        P("Please enter PIN1 in your Smart-ID app."),
        Div(cls="loading loading-lg"),
        hx_get=f"/auth/smart-id/status/{session_id}",
        hx_trigger="load delay:2s", # Start polling after 2 seconds
        hx_swap="innerHTML",
        id="smart-id-login-flow"
    )

@rt("/auth/smart-id/status/{session_id:str}", methods=["GET"])
async def get_smart_id_status(request: Request, session_id: str):
    """Polls for the status of a Smart-ID session."""
    status_data = await smart_id_service.check_session_status(session_id)

    if not status_data:
        return Div("Error checking session status. Please try again.", id="sid-error")

    state = status_data.get("state")

    if state == "RUNNING":
        # If still running, return the same component to continue polling
        return Div(
            H3("Verification code: 0000"), # Replace with actual code if needed
            P("Waiting for you to enter PIN1..."),
            Div(cls="loading loading-lg"),
            hx_get=f"/auth/smart-id/status/{session_id}",
            hx_trigger="load delay:2s",
            hx_swap="innerHTML",
            id="smart-id-login-flow"
        )
    
    elif state == "COMPLETE":
        # In the next step, we will implement this method in AuthController
        return await auth_controller.process_smart_id_login(request, status_data)

    else: # Handle timeout, error, etc.
        error_message = f"Login failed. Status: {state}. Please try again."
        # In the next step, we will modify get_login_form to handle this error
        return Div(error_message, id="sid-error")

@rt("/register", methods=["GET"])
def get_register_form_page(request: Request):
    register_form = auth_controller.get_register_form()
    page_content = Div(public_navbar(), Container(register_form, cls="mt-12 md:mt-16"))
    return public_layout("Registreeru", page_content)

@rt("/register", methods=["POST"])
async def post_register(request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
    response = await auth_controller.process_registration(request, email, password, confirm_password, full_name, birthday)
    if isinstance(response, Response) and 'HX-Redirect' in response.headers:
        response.headers['HX-Redirect'] = '/dashboard'
    return response

@rt("/logout", methods=["GET"])
def get_logout(request: Request):
    return auth_controller.logout(request)

@rt("/dashboard", methods=["GET"])
def get_dashboard(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return dashboard_controller.show_dashboard(request, guard)

@rt("/app", methods=["GET"])
def get_app_root(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return RedirectResponse("/dashboard", status_code=303)

@rt("/app/taotleja", methods=["GET"])
def get_applicant(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return applicant_controller.show_applicant_tab(request)

@rt("/app/kutsed", methods=["GET"])
def get_qualifications(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return qualification_controller.show_qualifications_tab(request)

@rt('/app/kutsed/toggle', methods=["POST"])
async def post_qual_toggle(request: Request, section_id: int, app_id: str):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await qualification_controller.handle_toggle(request, section_id, app_id)

@rt('/app/kutsed/submit', methods=["POST"])
async def post_qual_submit(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await qualification_controller.submit_qualifications(request)

@rt("/app/workex", methods=["GET"])
def get_workex(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return work_experience_controller.show_workex_tab(request)

@rt("/app/workex/{experience_id:int}/edit", methods=["GET"])
def get_workex_edit_form(request: Request, experience_id: int):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return work_experience_controller.show_workex_edit_form(request, experience_id)

@rt("/app/workex/save", methods=["POST"])
async def post_save_workex_experience(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await work_experience_controller.save_workex_experience(request)

@rt("/app/workex/{experience_id:int}/delete", methods=["DELETE"])
def delete_workex_experience(request: Request, experience_id: int):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return work_experience_controller.delete_workex_experience(request, experience_id)

@rt("/app/haridus", methods=["GET"])
def get_education(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return education_controller.show_education_tab(request)

@rt("/app/haridus/submit", methods=['POST'])
async def post_edu_submit(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await education_controller.submit_education_form(request)

@rt("/app/taiendkoolitus", methods=["GET"])
def get_training(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return training_controller.show_training_tab(request)

@rt("/app/taiendkoolitus/upload", methods=['POST'])
async def post_training_upload(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await training_controller.upload_training_files(request)

@rt("/app/tootamise_toend", methods=["GET"])
def get_employment_proof(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return employment_proof_controller.show_employment_proof_tab(request)

@rt("/app/tootamise_toend/upload", methods=['POST'])
async def post_emp_proof_upload(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await employment_proof_controller.upload_employment_proof(request)

@rt("/app/dokumendid", methods=["GET"])
def get_documents(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return documents_controller.show_documents_tab(request)

@rt("/app/dokumendid/upload", methods=['POST'])
async def post_document_upload(request: Request, document_type: str):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await documents_controller.upload_document(request, document_type)

@rt("/app/ulevaatamine", methods=["GET"])
def get_review(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return review_controller.show_review_tab(request)

@rt("/app/ulevaatamine/submit", methods=['POST'])
async def post_review_submit(request: Request):
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await review_controller.submit_application(request)

@rt("/evaluator/dashboard", methods=["GET"])
def get_evaluator_dashboard(request: Request):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.show_dashboard(request)

@rt("/evaluator/application/{user_email}", methods=["GET"])
def get_evaluator_application(request: Request, user_email: str):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.show_application_detail(request, user_email)

@rt("/evaluator/application/{user_email}/qualification/{record_id:int}/update", methods=["POST"])
async def post_update_qual_status(request: Request, user_email: str, record_id: int):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return await evaluator_controller.update_qualification_status(request, user_email, record_id)

@rt("/evaluator/d", methods=["GET"])
def get_evaluator_dashboard_v2(request: Request):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.show_dashboard_v2(request)

@rt("/evaluator/d/application/{qual_id:str}", methods=["GET"])
def get_v2_application_detail(request: Request, qual_id: str):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.show_v2_application_detail(request, qual_id)

@rt("/evaluator/d/search_applications", methods=["POST"])
def search_v2_applications(request: Request, search: str = ""):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.search_applications(request, search)

@rt("/evaluator/test", methods=["GET"])
def get_evaluator_test_page(request: Request):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.show_test_search_page(request)

@rt("/evaluator/test/search", methods=["POST"])
def post_evaluator_test_search(request: Request, search: str = ""):
    guard = guard_request(request, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard
    return evaluator_controller.handle_test_search(request, search)

@rt("/files/view/{doc_id:int}", methods=["GET"])
def view_secure_file(request: Request, doc_id: int):
    """
    Looks up a document by its integer ID, verifies ownership,
    generates a secure GCS URL, and redirects the user.
    """
    print(f"\n--- LOG [view_secure_file]: Route entered for document ID: {doc_id} ---")
    guard = guard_request(request, APPLICANT, EVALUATOR, ADMIN)
    if isinstance(guard, Response):
        return guard

    user_email = guard.get("email")
    print(f"--- LOG [view_secure_file]: Authenticated user: {user_email} ---")

    try:
        doc_record = documents_controller.documents_table[doc_id]
        print(f"--- LOG [view_secure_file]: Found DB record for ID {doc_id}: {doc_record} ---")

        doc_owner = doc_record.get('user_email')
        session_role = request.session.get("role")
        if session_role in ALL_ROLES:
            user_role = session_role
        else:
            user_role = normalize_role(session_role or guard.get("role"))
        is_owner = doc_owner == user_email
        has_privileged_role = user_role in {ADMIN, EVALUATOR}

        if not is_owner and not has_privileged_role:
            print(f"--- SECURITY [view_secure_file]: User '{user_email}' attempted to access file belonging to '{doc_owner}'. DENIED. ---")
            return Response("Access Denied", status_code=403)

        if not is_owner:
            print(f"--- LOG [view_secure_file]: Privileged user '{user_email}' with role '{user_role}' granted access to '{doc_owner}'. ---")
        else:
            print(f"--- LOG [view_secure_file]: Ownership confirmed for user '{user_email}'. ---")

    except NotFoundError:
        print(f"--- ERROR [view_secure_file]: No document record found in DB for ID: {doc_id} ---")
        return Response("File record not found", status_code=404)
    except Exception as e:
        print(f"--- ERROR [view_secure_file]: DB check failed for ID {doc_id}: {e} ---")
        traceback.print_exc()
        return Response("Error validating file access", status_code=500)

    storage_identifier = doc_record.get('storage_identifier')
    if not storage_identifier:
        print(f"--- ERROR [view_secure_file]: DB record for ID {doc_id} is missing a 'storage_identifier'. ---")
        return Response("File record is incomplete.", status_code=500)

    if storage_identifier.startswith("local:"):
        if not documents_controller.local_storage_dir:
            print("--- ERROR [view_secure_file]: Local storage directory is not configured. ---")
            return Response("Local storage not available", status_code=500)

        relative_path = storage_identifier.split("local:", 1)[1]
        safe_relative_path = Path(relative_path)
        local_base = documents_controller.local_storage_dir.resolve()
        target_path = (local_base / safe_relative_path).resolve()

        if local_base not in target_path.parents and local_base != target_path:
            print(f"--- SECURITY [view_secure_file]: Attempted path traversal for document ID {doc_id}. ---")
            return Response("Invalid file path", status_code=400)

        if not target_path.exists():
            print(f"--- ERROR [view_secure_file]: Local file missing at path: '{target_path}'. ---")
            return Response("File not found", status_code=404)

        filename = doc_record.get('original_filename') or target_path.name
        print(f"--- LOG [view_secure_file]: Serving local file '{target_path}' for user '{user_email}'. ---")
        return FileResponse(target_path, filename=filename, media_type='application/octet-stream')

    if not documents_controller.bucket:
        print(f"--- ERROR [view_secure_file]: GCS bucket is not configured. ---")
        return Response("Cloud Storage not configured", status_code=500)

    try:
        blob = documents_controller.bucket.blob(storage_identifier)
        if not blob.exists():
            print(f"--- ERROR [view_secure_file]: GCS blob not found at path: '{storage_identifier}' ---")
            return Response("File not found in cloud storage", status_code=404)

        print(f"--- LOG [view_secure_file]: GCS blob found. Generating signed URL... ---")
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=10),
            method="GET",
        )
        print(f"--- LOG [view_secure_file]: Success! Redirecting user to signed URL. ---")
        return RedirectResponse(url=signed_url, status_code=307)

    except Exception as e:
        print(f"--- ERROR [view_secure_file]: GCS signed URL generation failed for '{storage_identifier}': {e} ---")
        traceback.print_exc()
        return Response("Could not generate secure link for the file.", status_code=500)

# Start server
serve()