# app/ui/evaluator/work_exp_objects.py

from fasthtml.common import *
# Removed MonsterUI import as Card/etc are not used here
# from monsterui.all import *
import json
from typing import List, Dict, Any # Added Any for FT type hint clarity

def render_work_experience_objects(applicant_work_exp: List[Dict]) -> FT:
    """
    Renders the container for the AG Grid displaying work experience objects (ehitusobjektid)
    for the evaluator view, without card styling.

    Args:
        applicant_work_exp: List of work experience dictionaries.
    """
    # Ensure data is always a list
    applicant_work_exp = applicant_work_exp or []
    work_exp_json = json.dumps(applicant_work_exp)

    # Heading for the section
    work_experience_heading = H4(
        "Seotud Töökogemused (Ehitusobjektid)",
        cls="text-lg font-medium mb-2" # Styling for the heading
    )

    # AG Grid container Div
    # This structure is moved from the controller
    work_experience_ag_grid = Div(
        id="ag-grid-work-experience",
        cls="ag-theme-quartz", # Apply AG Grid theme
        # Set height style directly or manage via CSS/JS
        style="height: 150px; width: 100%;",
        data_work_experience=work_exp_json # Pass data to JS
    )

    # Return the heading and grid container, wrapped in a Div with bottom margin
    return Div(
        work_experience_heading,
        work_experience_ag_grid,
        # Add margin below this section for spacing
        #cls="mb-4" # Or adjust as needed (e.g., mt-4 mb-4)
    )