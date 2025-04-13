# main.py

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
from controllers.training import TrainingController
from controllers.evaluator import EvaluatorController
from ui.layouts import public_layout, app_layout
from ui.nav_components import public_navbar
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request # Add if not present
from starlette.responses import FileResponse, Response # Add if not present
import json
import traceback # Added for error handling
import os # Added for file path handling

SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "default-insecure-key-for-local-dev")

# --- Define Upload Directory consistently ---
# Calculate path relative to this file (main.py inside 'app')
script_dir_main = os.path.dirname(__file__)
# Go one level up to get the project root
project_root_main = os.path.abspath(os.path.join(script_dir_main, '..'))
UPLOAD_DIR = os.path.join(project_root_main, 'uploads')
print(f"--- INFO [main.py]: Corrected Upload directory configured as: {UPLOAD_DIR} ---")
# ---


# --- Database Setup ---
db = setup_database() 

# --- Controller Instantiation ---
auth_controller = AuthController(db)
qualification_controller = QualificationController(db)
applicant_controller = ApplicantController(db) 
work_experience_controller = WorkExperienceController(db)
training_controller = TrainingController(db)
employment_proof_controller = EmploymentProofController(db)
education_controller = EducationController(db)
review_controller = ReviewController(db)
evaluator_controller = EvaluatorController(db)

# --- Theme Setup ---
hdrs = Theme.blue.headers() 

# --- App Initialization with Middleware ---
app, rt = fast_app(
    hdrs=hdrs,
    middleware=[
        Middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=14 * 24 * 60 * 60),
        Middleware(AuthMiddleware)
    ],
        routes=[
        Mount('/static', app=StaticFiles(directory='app/static', html=True), name='static')
        # html=True allows serving index.html, maybe not needed here
        # Ensure this path 'app/static' is correct relative to where main.py runs
    ]
    
)


# === Public Routes ===


@rt("/")
def get(request: Request): # Renamed function for clarity
    """Displays the public landing page or redirects logged-in users."""
    # if request.session.get("authenticated"):
    #     # Redirect logged-in users to the main app dashboard
    #     return RedirectResponse("/app", status_code=303)

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
    )

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
     )

    # Combine navbar and content sections
    page_content = Div(
        public_navbar(), # Add the public navbar at the top
        hero_section,
        info_section
        # Add more sections here if needed
    )

    # Use public_layout, passing the combined content
    # public_layout takes title and then *content
    return public_layout("Tere tulemast!", page_content) # Pass combined content as a single item


@rt("/login")
def get(request: Request): # Renamed function
    """Displays the login form."""
    # if request.session.get("authenticated"):
    #     return RedirectResponse("/app", status_code=303)

    login_form = auth_controller.get_login_form()
    # Use public_layout - pass navbar separately or modify public_layout
    # Option: Wrap form in Div with navbar
    page_content = Div(
         public_navbar(),
         Container(login_form, cls="mt-12 md:mt-16") # Add spacing below navbar
     )
    return public_layout("Logi sisse", page_content) # Pass title and combined content


@rt("/login", methods=["POST"]) # Explicitly POST
def post(request: Request, email: str, password: str): # Renamed function
    return auth_controller.process_login(request, email, password)


@rt("/register")
def get(request: Request): # Renamed function
    """Displays the registration form."""
    # if request.session.get("authenticated"):
    #     return RedirectResponse("/app", status_code=303)

    register_form = auth_controller.get_register_form()
    # Option: Wrap form in Div with navbar
    page_content = Div(
         public_navbar(),
         Container(register_form, cls="mt-12 md:mt-16") # Add spacing below navbar
     )
    return public_layout("Registreeru", page_content) # Pass title and combined content

@rt("/register", methods=["POST"]) # Explicitly POST
# Rely on automatic form binding (ensure names match)
def post(request: Request,
                  email: str,
                  password: str,
                  confirm_password: str,
                  full_name: str,
                  birthday: str): # Renamed function
    """Processes the registration form submission."""
    return auth_controller.process_registration(
        request, email, password, confirm_password, full_name, birthday
    )

@rt("/logout")
def get(request: Request): # Renamed function
    """Logs the user out."""
    return auth_controller.logout(request) # Redirects to /login handled by controller

# === Protected Routes ===

@rt("/app")
def get(request: Request): # Correct function name
    """Redirects the base /app route to the default tab."""
    # Instead of rendering a generic dashboard, redirect to the default tab's URL.
    # The AuthMiddleware already ensures the user is authenticated before reaching here.
    return RedirectResponse("/app/taotleja", status_code=303) # Redirect to Applicant tab

# Applicant ("Taotleja")
@rt("/app/taotleja")
def get_applicant(request: Request):
    return applicant_controller.show_applicant_tab(request) # Uses applicant_controller

# Qualifications ("Taotletavad kutsed")
@rt("/app/kutsed")
def get_qualifications(request: Request):
    return qualification_controller.show_qualifications_tab(request) # Uses qualification_controller

@rt('/app/kutsed/toggle')
async def post_qual_toggle(request: Request, section_id:int, app_id:str):
    return await qualification_controller.handle_toggle(request, section_id, app_id) # Uses qualification_controller

@rt('/app/kutsed/submit')
async def post_qual_submit(request: Request):
    return await qualification_controller.submit_qualifications(request) # Uses qualification_controller

# Work Experience ("Töökogemus")
@rt("/app/tookogemus")
def get_work_experience(request: Request):
    return work_experience_controller.show_work_experience_tab(request) # Uses work_experience_controller

@rt("/app/tookogemus/add_form")
def get_work_experience_add_form(request: Request):
    return work_experience_controller.show_add_form(request) # Uses work_experience_controller

# --- MODIFY THIS ROUTE ---
# Change from /add to /save
@rt("/app/tookogemus/save", methods=['POST'])
async def post_save_work_experience(request: Request):
    # Point to a potentially renamed or modified controller method
    return await work_experience_controller.save_work_experience(request)
# --- END MODIFICATION ---

@rt("/app/tookogemus/cancel_form")
def get_cancel_work_experience_form(request: Request):
    return work_experience_controller.cancel_form(request) # Uses work_experience_controller

@rt("/app/tookogemus/{experience_id:int}", methods=['DELETE']) # Explicitly DELETE
def delete_exp(request: Request, experience_id:int):
    return work_experience_controller.delete_work_experience(request, experience_id) # Uses work_experience_controller


@rt("/app/tookogemus/{experience_id:int}/edit")
def get_work_experience_edit_form(request: Request, experience_id: int):
    return work_experience_controller.show_edit_form(request, experience_id)


# Education ("Haridus")
@rt("/app/haridus")
def get_education(request: Request):
    return education_controller.show_education_tab(request) # Uses education_controller

@rt("/app/haridus/submit", methods=['POST']) # Explicitly POST
async def post_edu_submit(request: Request):
    return await education_controller.submit_education_form(request) # Uses education_controller

# Training ("Täiendkoolitus")
@rt("/app/taiendkoolitus")
def get_training(request: Request):
    return training_controller.show_training_tab(request) # Uses training_controller

@rt("/app/taiendkoolitus/upload", methods=['POST']) # Explicitly POST
async def post_training_upload(request: Request):
    return await training_controller.upload_training_files(request) # Uses training_controller

# Employment Proof ("Töötamise tõend")
@rt("/app/tootamise_toend")
def get_employment_proof(request: Request):
    return employment_proof_controller.show_employment_proof_tab(request) # Uses employment_proof_controller

@rt("/app/tootamise_toend/upload", methods=['POST']) # Explicitly POST
async def post_emp_proof_upload(request: Request):
    return await employment_proof_controller.upload_employment_proof(request) # Uses employment_proof_controller

# Review ("Taotluse ülevaatamine")
@rt("/app/ulevaatamine")
def get_review(request: Request):
    return review_controller.show_review_tab(request) # Uses review_controller

@rt("/app/ulevaatamine/submit", methods=['POST']) # Explicitly POST
async def post_review_submit(request: Request):
    return await review_controller.submit_application(request) # Uses review_controller

# === Evaluator Routes ===

@rt("/evaluator/dashboard")
def get_evaluator_dashboard(request: Request):
    return evaluator_controller.show_dashboard(request)

@rt("/evaluator/application/{user_email}")
def get_evaluator_application(request: Request, user_email: str):
    return evaluator_controller.show_application_detail(request, user_email)

@rt("/evaluator/application/{user_email}/qualification/{record_id:int}/update", methods=["POST"])
async def post(request: Request, user_email: str, record_id: int):
    # Assuming your EvaluatorController instance is named evaluator_controller
    return await evaluator_controller.update_qualification_status(request, user_email, record_id)

# +++ ADD the new download function +++
@rt("/files/download/{identifier:str}")
async def download_file(request: Request, identifier: str):
    """Serves the requested file from the uploads directory."""
    print(f"--- DEBUG [Download]: Request received for identifier: {identifier} ---")

    if ".." in identifier or identifier.startswith("/"):
        print(f"--- WARN [Download]: Potential path traversal attempt blocked: {identifier} ---")
        return Response("Invalid filename", status_code=400)

    # Construct the full file path using the corrected UPLOAD_DIR
    file_path = os.path.join(UPLOAD_DIR, identifier)

    # +++ Add Debugging +++
    print(f"--- DEBUG [Download]: Checking for file at path: {file_path} ---")
    file_exists = os.path.isfile(file_path)
    print(f"--- DEBUG [Download]: os.path.isfile result: {file_exists} ---")
    # +++ End Debugging +++

    if file_exists:
        try:
            # Attempt to serve the file
            # Still using identifier as filename for simplicity
            filename_for_download = identifier
            print(f"--- INFO [Download]: Serving file: {file_path} as {filename_for_download} ---")
            return FileResponse(file_path, filename=filename_for_download, media_type='application/octet-stream')
        except Exception as e:
            # Log any unexpected errors during FileResponse creation/sending
            print(f"--- ERROR [Download]: Failed to serve file {file_path}: {e} ---")
            traceback.print_exc() # Print full traceback to console
            return Response("Error serving file", status_code=500)
    else:
        # File not found at the checked path
        print(f"--- ERROR [Download]: File not found at path: {file_path} ---")
        return Response(f"File not found: {identifier}", status_code=404)

# === End Protected Routes ===
serve() 