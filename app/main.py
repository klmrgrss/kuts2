# main.py

# --- Imports ---
import os
from pathlib import Path
from fasthtml.common import *
from monsterui.all import *
from controllers.employment_proof import EmploymentProofController
from controllers.review import ReviewController
from database import setup_database
from auth.middleware import AuthMiddleware
from auth.utils import *
from controllers.auth import AuthController
from controllers.qualifications import QualificationController
from controllers.applicant import ApplicantController
from controllers.work_experience import WorkExperienceController
from controllers.education import EducationController
from controllers.documents import DocumentsController
from controllers.training import TrainingController
from controllers.evaluator import EvaluatorController
from ui.layouts import public_layout, app_layout
from ui.nav_components import public_navbar
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import FileResponse, Response, RedirectResponse
import json
import traceback

# --- Prevent Duplicate Initialization ---
APP_DIR = Path(__file__).parent
INIT_FLAG = APP_DIR / '.app_initialized'
if INIT_FLAG.exists():
    print("--- INFO [main.py]: App already initialized, skipping setup ---")
    serve()
else:
    INIT_FLAG.touch()
    print("--- INFO [main.py]: Initializing app ---")

# --- Path Definitions ---
STATIC_DIR = APP_DIR / 'static'
UPLOAD_DIR = APP_DIR.parent / 'Uploads'
print(f"--- INFO [main.py]: Static directory calculated as: {STATIC_DIR} ---")
print(f"--- INFO [main.py]: Upload directory calculated as: {UPLOAD_DIR} ---")

# --- Database Setup ---
db = setup_database()
if db is None:
    print("--- FATAL: Database setup failed in main.py. ---")
    raise RuntimeError("Database setup failed, cannot start application.")

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
except AttributeError as e:
    print(f"--- FATAL: Failed to initialize controllers: {e} ---")
    raise RuntimeError("Controller initialization failed due to database setup issue.") from e

# --- Theme Setup ---
hdrs = Theme.blue.headers()
# +++ Define routes list BEFORE fast_app +++
route_list = []
if STATIC_DIR.is_dir():
    print(f"--- Preparing static mount for route list: {STATIC_DIR} ---")
    route_list.append(Mount('/static', app=StaticFiles(directory=STATIC_DIR, html=True), name='static'))
else:
    print(f"--- ERROR: Static directory NOT FOUND at: {STATIC_DIR}. Cannot mount. ---")
    raise RuntimeError("Static directory missing")
# +++ End defining routes list +++

# --- App Initialization ---
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "default-insecure-key-for-local-dev")

app, rt = fast_app(
    hdrs=hdrs,
    middleware=[
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=14 * 24 * 60 * 60),
        Middleware(AuthMiddleware)
    ],
    routes=route_list,
    debug=True
)

# Mount static directory
if STATIC_DIR.is_dir():
    print(f"--- Mounting static directory: {STATIC_DIR} ---")
    app.mount('/static', StaticFiles(directory=STATIC_DIR, html=True), name='static')
else:
    print(f"--- ERROR: Static directory NOT FOUND at: {STATIC_DIR}. ---")
    raise RuntimeError("Static directory missing")

# Debug routes after initialization
print("--- Registered Routes After Initialization ---")
for route in app.routes:
    methods = getattr(route, "methods", ["GET"])
    if hasattr(route, "app"):
        endpoint_name = type(route.app).__name__ if route.app else "UnknownMount"
    else:
        endpoint = getattr(route, "endpoint", None)
        endpoint_name = endpoint.__name__ if callable(endpoint) else f"Unknown({endpoint})"
    path = getattr(route, "path", f"Mount: {route.name}" if hasattr(route, "name") else "Unknown")
    print(f"Path: {path}, Endpoint: {endpoint_name}, Methods: {methods}")

# === Routes ===
@rt("/")
def get(request: Request): # Renamed function for clarity in your code
    """Displays the public landing page or redirects logged-in users."""
    # ... (optional redirect logic if needed) ...

    # --- Build Landing Page Content for Logged-Out Users ---

    # Hero Section
    hero_section = Div(
        Container( # Center content
            H1("Ehitamise valdkonna kutsete taotlemine", cls="text-4xl md:text-5xl font-bold mb-4 text-center"),
            P("Esita ja halda oma kutsetaotlusi kiirelt ja mugavalt.", cls="text-lg md:text-xl text-muted-foreground mb-8 text-center"),
            Div( # Container for buttons
                A(Button("Logi sisse", cls=(ButtonT.primary, ButtonT.lg)), href="/login"), # Large primary button
                A(Button("Registreeru", cls=(ButtonT.secondary, ButtonT.lg)), href="/register"), # Large secondary button
                cls="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4" # Responsive button layout
            ),
            cls="py-16 md:py-24 text-center" # Padding for hero section
        ),
        cls="bg-gradient-to-b from-background to-muted/50" # Optional subtle background gradient
    ) # [cite: uploaded:app/main.py]

    # Placeholder Info Section (Example)
    info_section = Container(
         Section(
             H2("Kuidas see töötab?", cls="text-2xl font-bold mb-6 text-center"),
             Grid(
                 Card(CardHeader(H3("1. Registreeru / Logi sisse")), CardBody(P("Loo konto või logi sisse olemasolevaga."))),
                 Card(CardHeader(H3("2. Sisesta Andmed")), CardBody(P("Täida vajalikud ankeedid: isikuandmed, haridus, töökogemus."))),
                 Card(CardHeader(H3("3. Esita Taotlus")), CardBody(P("Vaata andmed üle ja esita taotlus menetlemiseks."))),
                 cols=1, md_cols=3, # Responsive grid
                 cls="gap-6" # Gap between cards
             ),
             cls="py-12"
         )
     ) # [cite: uploaded:app/main.py]

    # Combine navbar and content sections
    page_content = Div(
        public_navbar(), # Add the public navbar at the top
        hero_section,
        info_section
        # Add more sections here if needed
    ) # [cite: uploaded:app/main.py]

    # Use public_layout, passing the combined content
    return public_layout("Tere tulemast!", page_content) # Pass title and combined content # [cite: uploaded:app/main.py]


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
    print(f"--- DEBUG [post_login]: Email={email}, Response={response} ---")
    return response

@rt("/register", methods=["GET"])
def get_register_form_page(request: Request):
    register_form = auth_controller.get_register_form()
    page_content = Div(public_navbar(), Container(register_form, cls="mt-12 md:mt-16"))
    return public_layout("Registreeru", page_content)

@rt("/register", methods=["POST"])
async def post_register(request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str):
    response = await auth_controller.process_registration(request, email, password, confirm_password, full_name, birthday)
    print(f"--- DEBUG [post_register]: Email={email}, Response={response} ---")
    return response

@rt("/logout", methods=["GET"])
def get_logout(request: Request):
    response = auth_controller.logout(request)
    print(f"--- DEBUG [get_logout]: Response={response} ---")
    return response

# Override catch-all static route
@rt("/{fname:path}.{ext:css|js|png|jpg|ico}", methods=["GET"])
def block_static(request: Request, fname: str, ext: str):
    print(f"--- WARN: Caught static-like path: {fname}.{ext} ---")
    return Response(f"Static path {fname}.{ext} blocked, use /static/", status_code=400)

# Debug routes after definitions
print("--- Registered Routes After Definitions ---")
for route in app.routes:
    methods = getattr(route, "methods", ["GET"])
    if hasattr(route, "app"):
        endpoint_name = type(route.app).__name__ if route.app else "UnknownMount"
    else:
        endpoint = getattr(route, "endpoint", None)
        endpoint_name = endpoint.__name__ if callable(endpoint) else f"Unknown({endpoint})"
    path = getattr(route, "path", f"Mount: {route.name}" if hasattr(route, "name") else "Unknown")
    print(f"Path: {path}, Endpoint: {endpoint_name}, Methods: {methods}")


@rt("/app", methods=["GET"])
def get_app_root(request: Request):
    return RedirectResponse("/app/taotleja", status_code=303)

@rt("/app/taotleja", methods=["GET"])
def get_applicant(request: Request):
    return applicant_controller.show_applicant_tab(request)
# === Commented Out Original Routes ===

@rt("/app/kutsed", methods=["GET"])
def get_qualifications(request: Request):
    return qualification_controller.show_qualifications_tab(request)

@rt('/app/kutsed/toggle', methods=["POST"])
async def post_qual_toggle(request: Request, section_id: int, app_id: str):
    return await qualification_controller.handle_toggle(request, section_id, app_id)

@rt('/app/kutsed/submit', methods=["POST"])
async def post_qual_submit(request: Request):
    return await qualification_controller.submit_qualifications(request)

@rt("/app/tookogemus", methods=["GET"])
def get_work_experience(request: Request):
    return work_experience_controller.show_work_experience_tab(request)

@rt("/app/tookogemus/add_form", methods=["GET"])
def get_work_experience_add_form(request: Request):
    return work_experience_controller.show_add_form(request)

@rt("/app/tookogemus/save", methods=['POST'])
async def post_save_work_experience(request: Request):
    return await work_experience_controller.save_work_experience(request)

@rt("/app/tookogemus/cancel_form", methods=["GET"])
def get_cancel_work_experience_form(request: Request):
    return work_experience_controller.cancel_form(request)

@rt("/app/tookogemus/{experience_id:int}", methods=['DELETE'])
def delete_exp(request: Request, experience_id: int):
    return work_experience_controller.delete_work_experience(request, experience_id)

@rt("/app/tookogemus/{experience_id:int}/edit", methods=["GET"])
def get_work_experience_edit_form(request: Request, experience_id: int):
    return work_experience_controller.show_edit_form(request, experience_id)

@rt("/app/workex", methods=["GET"])
def get_workex(request: Request):
    return work_experience_controller.show_workex_tab(request)

@rt("/app/workex/{experience_id:int}/edit", methods=["GET"])
def get_workex_edit_form(request: Request, experience_id: int):
    return work_experience_controller.show_workex_edit_form(request, experience_id)

@rt("/app/workex/save", methods=["POST"])
async def post_save_workex_experience(request: Request):
    return await work_experience_controller.save_workex_experience(request)

@rt("/app/haridus", methods=["GET"])
def get_education(request: Request):
    return education_controller.show_education_tab(request)

@rt("/app/haridus/submit", methods=['POST'])
async def post_edu_submit(request: Request):
    return await education_controller.submit_education_form(request)

@rt("/app/taiendkoolitus", methods=["GET"])
def get_training(request: Request):
    return training_controller.show_training_tab(request)

@rt("/app/taiendkoolitus/upload", methods=['POST'])
async def post_training_upload(request: Request):
    return await training_controller.upload_training_files(request)

@rt("/app/tootamise_toend", methods=["GET"])
def get_employment_proof(request: Request):
    return employment_proof_controller.show_employment_proof_tab(request)

@rt("/app/tootamise_toend/upload", methods=['POST'])
async def post_emp_proof_upload(request: Request):
    return await employment_proof_controller.upload_employment_proof(request)

@rt("/app/haridus/submit", methods=['POST'])
async def post_edu_submit(request: Request):
    return await education_controller.submit_education_form(request)

# ADD NEW ROUTES FOR DOCUMENTS TAB
@rt("/app/dokumendid", methods=["GET"])
def get_documents(request: Request):
    return documents_controller.show_documents_tab(request)

@rt("/app/dokumendid/upload", methods=['POST'])
async def post_document_upload(request: Request, document_type: str):
    return await documents_controller.upload_document(request, document_type)
# END NEW ROUTES

@rt("/app/taiendkoolitus", methods=["GET"])
def get_training(request: Request):
    return training_controller.show_training_tab(request)

@rt("/app/ulevaatamine", methods=["GET"])
def get_review(request: Request):
    return review_controller.show_review_tab(request)

@rt("/app/ulevaatamine/submit", methods=['POST'])
async def post_review_submit(request: Request):
    return await review_controller.submit_application(request)

@rt("/evaluator/dashboard", methods=["GET"])
def get_evaluator_dashboard(request: Request):
    return evaluator_controller.show_dashboard(request)

@rt("/evaluator/application/{user_email}", methods=["GET"])
def get_evaluator_application(request: Request, user_email: str):
    return evaluator_controller.show_application_detail(request, user_email)

@rt("/evaluator/application/{user_email}/qualification/{record_id:int}/update", methods=["POST"])
async def post_update_qual_status(request: Request, user_email: str, record_id: int):
    return await evaluator_controller.update_qualification_status(request, user_email, record_id)

@rt("/files/download/{identifier:str}", methods=["GET"])
async def download_file_route(request: Request, identifier: str):
    print(f"--- DEBUG [Download]: Request received for identifier: {identifier} ---")
    if ".." in identifier or identifier.startswith("/"):
        print(f"--- WARN [Download]: Potential path traversal attempt blocked: {identifier} ---")
        return Response("Invalid filename", status_code=400)
    file_path = UPLOAD_DIR / identifier
    print(f"--- DEBUG [Download]: Checking for file at path: {file_path} ---")
    try:
        file_exists = file_path.is_file()
        print(f"--- DEBUG [Download]: Path.is_file() result: {file_exists} ---")
    except Exception as e:
        print(f"--- ERROR [Download]: Error checking file existence for {file_path}: {e} ---")
        return Response("Error accessing file path", status_code=500)
    if file_exists:
        try:
            print(f"--- INFO [Download]: Serving file: {file_path} as {identifier} ---")
            return FileResponse(str(file_path), filename=identifier, media_type='application/octet-stream')
        except Exception as e:
            print(f"--- ERROR [Download]: Failed to serve file {file_path}: {e} ---")
            traceback.print_exc()
            return Response("Error serving file", status_code=500)
    else:
        print(f"--- ERROR [Download]: File not found at: {file_path} ---")
        return Response(f"File not found: {identifier}", status_code=404)


# Clean up initialization flag on exit
import atexit
def cleanup():
    if INIT_FLAG.exists():
        INIT_FLAG.unlink()
atexit.register(cleanup)

# Start server
serve()