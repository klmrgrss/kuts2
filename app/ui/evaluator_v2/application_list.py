# app/ui/evaluator_v2/application_list.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
# NO Fragment import is needed

def render_application_list(applications: List[Dict]) -> FT:
    """Renders just the list of application items as a tuple of elements."""
    if not applications:
        # Returning a P element is fine here as it's a single component
        return P("No applications found.", cls="p-4 text-center text-gray-500")

    application_items = []
    for app in applications:
        item = A(
            Div(
                Div(
                    P(app.get('applicant_name', 'N/A'), cls="font-semibold text-sm truncate"),
                    Span(app.get('submission_date', ''), cls="text-xs text-gray-500"),
                    cls="flex justify-between items-baseline"
                ),
                P(app.get('qualification_name', 'N/A'), cls="text-xs text-gray-600 truncate"),
            ),
            hx_get=f"/evaluator/d/application/{app.get('qual_id')}",
            hx_target="#ev-center-panel",
            hx_swap="innerHTML",
            hx_swap_oob="innerHTML:#ev-right-panel",
            _=("on click remove .bg-blue-100 from <a/> in #application-list-container then add .bg-blue-100 to me"),
            cls="block p-3 border-b hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        )
        application_items.append(item)
    
    # --- THIS IS THE CORRECT IMPLEMENTATION ---
    # Return a tuple of all the generated items.
    # FastHTML will render them as a sequence of sibling elements.
    return tuple(application_items)