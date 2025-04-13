# main.py

# --- Imports ---
import os
from pathlib import Path  # <-- Added
from fasthtml.common import *
from monsterui.all import *
# Using absolute imports for local modules
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
from controllers.training import TrainingController
from controllers.evaluator import EvaluatorController
from ui.layouts import public_layout, app_layout
from ui.nav_components import public_navbar
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route, Mount # Ensure Mount is imported
from starlette.staticfiles import StaticFiles # Ensure StaticFiles is imported
from starlette.requests import Request # Ensure Request is imported
from starlette.responses import FileResponse, Response, RedirectResponse # Ensure these are imported
import json
import traceback

# --- Path Definitions ---
# Get the directory containing THIS file (main.py)
# Assuming this file is at /app/app/main.py inside container, APP_DIR is /app/app
APP_DIR = Path(__file__).parent
# Define static directory relative to this file's directory
STATIC_DIR = APP_DIR / 'static'
# Define upload directory relative to the PARENT of this file's directory
# Assumes uploads is parallel to the inner app dir, e.g., /app/uploads
UPLOAD_DIR = APP_DIR.parent / 'uploads'
print(f"--- INFO [main.py]: Static directory calculated as: {STATIC_DIR} ---")
print(f"--- INFO [main.py]: Upload directory calculated as: {UPLOAD_DIR} ---")

# --- Database Setup ---
db = setup_database()
if db is None:
    # Handle database setup failure early if necessary
    print("--- FATAL: Database setup failed in main.py. Subsequent operations will fail. ---")
    # Application will likely crash when controllers are initialized below
    # Consider raising an exception here for clearer failure:
    # raise RuntimeError("Database setup failed, cannot start application.")

# --- Controller Instantiation ---
# These will fail if db is None
try:
    auth_controller = AuthController(db)
    qualification_controller = QualificationController(db)
    applicant_controller = ApplicantController(db)
    work_experience_controller = WorkExperienceController(db)
    training_controller = TrainingController(db)
    employment_proof_controller = EmploymentProofController(db)
    education_controller = EducationController(db)
    review_controller = ReviewController(db)
    evaluator_controller = EvaluatorController(db)
except AttributeError as e:
    print(f"--- FATAL: Failed to initialize controllers, likely because db setup failed: {e} ---")
    # Optionally re-raise or exit
    raise RuntimeError("Controller initialization failed due to database setup issue.") from e


# --- Theme Setup ---
hdrs = Theme.blue.headers()

# --- Build Routes List ---
route_list = []
# Check if static directory exists before creating the Mount
if STATIC_DIR.is_dir():
    print(f"--- Mounting static directory: {STATIC_DIR} ---")
    route_list.append(Mount('/static', app=StaticFiles(directory=STATIC_DIR, html=True), name='static'))
else:
    print(f"--- WARNING: Static directory NOT FOUND at calculated path: {STATIC_DIR}. Skipping static mount. ---")
    # Depending on your app's needs, you might want to raise an error here
    # raise RuntimeError(f"Required static directory not found: {STATIC_DIR}")

# Add other non-@rt routes here if you have any...


# --- App Initialization with Middleware and Routes ---
# Read secret key from environment variable
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "default-insecure-key-for-local-dev")

app, rt = fast_app(
    hdrs=hdrs,
    middleware=[
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=14 * 24 * 60 * 60),
        Middleware(AuthMiddleware)
    ],
    routes=route_list # Pass the list containing the conditional static mount
)


# === Public Routes ===

@rt("/")
def get_root(request: Request): # Renamed function for clarity
    """Displays the public landing page or redirects logged-in users."""
    # Your existing landing page logic here...
    # Example placeholder:
    hero_section = Div( Container( H1("Ehitamise valdkonna kutsete taotlemine", cls="text-4xl md:text-5xl font-bold mb-4 text-center"), P("Esita ja halda oma kutsetaotlusi kiirelt ja mugavalt.", cls="text-lg md:text-xl text-muted-foreground mb-8 text-center"), Div( A(Button("Logi sisse", cls=(ButtonT.primary, ButtonT.lg)), href="/login"), A(Button("Registreeru", cls=(ButtonT.secondary, ButtonT.lg)), href="/register"), cls="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4" ), cls="py-16 md:py-24 text-center" ), cls="bg-gradient-to-b from-background to-muted/50" )
    info_section = Container( Section( H2("Kuidas see töötab?", cls="text-2xl font-bold mb-6 text-center"), Grid( Card(CardHeader(H3("1. Registreeru / Logi sisse")), CardBody(P("Loo konto või logi sisse olemasolevaga."))), Card(CardHeader(H3("2. Sisesta Andmed")), CardBody(P("Täida vajalikud ankeedid: isikuandmed, haridus, töökogemus."))), Card(CardHeader(H3("3. Esita Taotlus")), CardBody(P("Vaata andmed üle ja esita taotlus menetlemiseks."))), cols=1, md_cols=3, cls="gap-6" ), cls="py-12" ) )
    page_content = Div( public_navbar(), hero_section, info_section )
    return public_layout("Tere tulemast!", page_content)


@rt("/login")
def get_login_form_page(request: Request): # Renamed function
    """Displays the login form."""
    login_form = auth_controller.get_login_form()
    page_content = Div( public_navbar(), Container(login_form, cls="mt-12 md:mt-16") )
    return public_layout("Logi sisse", page_content)


@rt("/login", methods=["POST"]) # Explicitly POST
def post_login(request: Request, email: str, password: str): # Renamed function
    """Processes login form submission."""
    return auth_controller.process_login(request, email, password)


@rt("/register")
def get_register_form_page(request: Request): # Renamed function
    """Displays the registration form."""
    register_form = auth_controller.get_register_form()
    page_content = Div( public_navbar(), Container(register_form, cls="mt-12 md:mt-16") )
    return public_layout("Registreeru", page_content)


@rt("/register", methods=["POST"]) # Explicitly POST
def post_register(request: Request, email: str, password: str, confirm_password: str, full_name: str, birthday: str): # Renamed function
    """Processes registration form submission."""
    return auth_controller.process_registration( request, email, password, confirm_password, full_name, birthday )


@rt("/logout")
def get_logout(request: Request): # Renamed function
    """Logs the user out."""
    return auth_controller.logout(request)


# === Protected Routes ===

@rt("/app")
def get_app_root(request: Request): # Correct function name
    """Redirects the base /app route to the default tab."""
    return RedirectResponse("/app/taotleja", status_code=303) # Redirect to Applicant tab

# Applicant ("Taotleja")
@rt("/app/taotleja")
def get_applicant(request: Request):
    return applicant_controller.show_applicant_tab(request)

# Qualifications ("Taotletavad kutsed")
@rt("/app/kutsed")
def get_qualifications(request: Request):
    return qualification_controller.show_qualifications_tab(request)

@rt('/app/kutsed/toggle')
async def post_qual_toggle(request: Request, section_id:int, app_id:str):
    return await qualification_controller.handle_toggle(request, section_id, app_id)

@rt('/app/kutsed/submit')
async def post_qual_submit(request: Request):
    return await qualification_controller.submit_qualifications(request)

# Work Experience ("Töökogemus")
@rt("/app/tookogemus")
def get_work_experience(request: Request):
    return work_experience_controller.show_work_experience_tab(request)

@rt("/app/tookogemus/add_form")
def get_work_experience_add_form(request: Request):
    return work_experience_controller.show_add_form(request)

@rt("/app/tookogemus/save", methods=['POST'])
async def post_save_work_experience(request: Request):
    return await work_experience_controller.save_work_experience(request)

@rt("/app/tookogemus/cancel_form")
def get_cancel_work_experience_form(request: Request):
    return work_experience_controller.cancel_form(request)

@rt("/app/tookogemus/{experience_id:int}", methods=['DELETE']) # Explicitly DELETE
def delete_exp(request: Request, experience_id:int):
    return work_experience_controller.delete_work_experience(request, experience_id)

@rt("/app/tookogemus/{experience_id:int}/edit")
def get_work_experience_edit_form(request: Request, experience_id: int):
    return work_experience_controller.show_edit_form(request, experience_id)

# Education ("Haridus")
@rt("/app/haridus")
def get_education(request: Request):
    return education_controller.show_education_tab(request)

@rt("/app/haridus/submit", methods=['POST']) # Explicitly POST
async def post_edu_submit(request: Request):
    return await education_controller.submit_education_form(request)

# Training ("Täiendkoolitus")
@rt("/app/taiendkoolitus")
def get_training(request: Request):
    return training_controller.show_training_tab(request)

@rt("/app/taiendkoolitus/upload", methods=['POST']) # Explicitly POST
async def post_training_upload(request: Request):
    return await training_controller.upload_training_files(request)

# Employment Proof ("Töötamise tõend")
@rt("/app/tootamise_toend")
def get_employment_proof(request: Request):
    return employment_proof_controller.show_employment_proof_tab(request)

@rt("/app/tootamise_toend/upload", methods=['POST']) # Explicitly POST
async def post_emp_proof_upload(request: Request):
    return await employment_proof_controller.upload_employment_proof(request)

# Review ("Taotluse ülevaatamine")
@rt("/app/ulevaatamine")
def get_review(request: Request):
    return review_controller.show_review_tab(request)

@rt("/app/ulevaatamine/submit", methods=['POST']) # Explicitly POST
async def post_review_submit(request: Request):
    return await review_controller.submit_application(request)

# === Evaluator Routes ===

@rt("/evaluator/dashboard")
def get_evaluator_dashboard(request: Request):
    return evaluator_controller.show_dashboard(request)

@rt("/evaluator/application/{user_email}")
def get_evaluator_application(request: Request, user_email: str):
    return evaluator_controller.show_application_detail(request, user_email)

@rt("/evaluator/application/{user_email}/qualification/{record_id:int}/update", methods=["POST"])
async def post_update_qual_status(request: Request, user_email: str, record_id: int): # Renamed function
    return await evaluator_controller.update_qualification_status(request, user_email, record_id)

# === File Download Route ===
@rt("/files/download/{identifier:str}")
async def download_file_route(request: Request, identifier: str): # Renamed function
    """Serves the requested file from the uploads directory."""
    print(f"--- DEBUG [Download]: Request received for identifier: {identifier} ---")

    # Basic security check
    if ".." in identifier or identifier.startswith("/"):
        print(f"--- WARN [Download]: Potential path traversal attempt blocked: {identifier} ---")
        return Response("Invalid filename", status_code=400)

    # Construct the full file path using the calculated UPLOAD_DIR
    file_path = UPLOAD_DIR / identifier # Use pathlib joining

    print(f"--- DEBUG [Download]: Checking for file at path: {file_path} ---")
    try:
        file_exists = file_path.is_file()
        print(f"--- DEBUG [Download]: Path.is_file() result: {file_exists} ---")
    except Exception as e:
        print(f"--- ERROR [Download]: Error checking file existence for {file_path}: {e} ---")
        return Response("Error accessing file path", status_code=500)


    if file_exists:
        try:
            # Use the original identifier (which should be the secure UUID version)
            # You might want to map this identifier back to an original filename for the user if stored
            filename_for_download = identifier
            print(f"--- INFO [Download]: Serving file: {file_path} as {filename_for_download} ---")
            # Use FileResponse for efficient serving
            return FileResponse(str(file_path), filename=filename_for_download, media_type='application/octet-stream')
        except Exception as e:
            print(f"--- ERROR [Download]: Failed to serve file {file_path}: {e} ---")
            traceback.print_exc() # Log full traceback for server-side debugging
            return Response("Error serving file", status_code=500)
    else:
        print(f"--- ERROR [Download]: File not found at path: {file_path} ---")
        return Response(f"File not found: {identifier}", status_code=404)


# === End Routes ===

# Keep serve() as requested, but note it's mainly for local development
# Railway uses the START COMMAND defined in settings.
serve()