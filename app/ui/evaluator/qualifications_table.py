# ui/evaluator/qualifications_table.py

from fasthtml.common import *
# Removed MonsterUI import as Card/CardBody/CardHeader are no longer used
# from monsterui.all import *
import json

def render_qualifications_table(qualifications_data: list, applicant_email: str) -> FT:
    """
    Renders the container for the AG Grid evaluator's qualifications table
    WITHOUT card styling.

    Args:
        qualifications_data: List of applied qualification dictionaries.
        applicant_email: The email of the applicant being viewed.
    """
    qualifications_json = json.dumps(qualifications_data)

    # Container Div for AG Grid (remains the same)
    ag_grid_container = Div(
        id="ag-grid-qualifications",
        #cls="ag-theme-quartz", # Apply AG Grid theme
        style="height: 110px; width: 100%;", # Optional: Adjust or remove explicit style
        data_qualifications=qualifications_json,
        data_applicant_email=applicant_email
    )

    # Script reference (remains the same)
    init_script_ref = Script(src="/static/js/ag_grid_evaluator.js", defer=True)

    # --- Return content wrapped in a simple Div with margin ---
    # Removed Card(), CardHeader(), CardBody() wrappers
    return Div(
        # Heading (was inside CardHeader)
        H4("Taotletavad Kvalifikatsioonid ja Hinnang", cls="text-lg font-medium mb-2"), # Apply styling directly
        # AG Grid container
        ag_grid_container,
        # Include the script reference (doesn't render visually)
        init_script_ref,
        # Apply bottom margin to this outer Div for spacing
        cls="mb-4" # Or mt-4/mb-4 as needed
    )