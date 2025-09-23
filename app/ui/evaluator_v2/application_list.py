# klmrgrss/kuts2/kuts2-eval/app/ui/evaluator_v2/application_list.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
from ui.shared_components import LevelPill

def render_application_list(applications: List[Dict], include_oob: bool = True) -> FT:
    """
    Renders the list of application items.
    Conditionally includes the hx_swap_oob attribute.
    """
    if not applications:
        return P("No applications found.", cls="p-4 text-center text-gray-500")

    application_items = []
    for app in applications:
        # Define base attributes for the link
        attrs = {
            "hx_get": f"/evaluator/d/application/{app.get('qual_id')}",
            "hx_target": "#ev-center-panel",
            "hx_swap": "innerHTML",
            "_": "on click remove .bg-blue-100 from <a/> in #application-list-container then add .bg-blue-100 to me",
            "cls": "block p-3 border-b hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        }
        
        # *** THE FIX IS HERE ***
        # Only add the hx_swap_oob attribute if the flag is True
        if include_oob:
            attrs["hx_swap_oob"] = "innerHTML:#ev-right-panel"

        item = A(
            Div(
                Div(
                    P(app.get('applicant_name', 'N/A'), cls="font-semibold text-sm truncate"),
                    LevelPill(app.get('level', '')),
                    cls="flex justify-between items-baseline"
                ),
                P(app.get('qualification_name', 'N/A'), cls="text-xs text-gray-600 truncate"),
            ),
            **attrs
        )
        application_items.append(item)
    
    return tuple(application_items)