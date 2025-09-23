# klmrgrss/kuts2/kuts2-eval/app/ui/evaluator_v2/application_list.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
from ui.shared_components import LevelPill
from config.qualification_data import QUALIFICATION_LEVEL_STYLES

def render_application_list(applications: List[Dict], include_oob: bool = True) -> FT:
    """
    Renders the list of application items.
    Conditionally includes the hx_swap_oob attribute.
    """
    if not applications:
        return P("No applications found.", cls="p-4 text-center text-gray-500")

    application_items = []
    for app in applications:
        attrs = {
            "hx_get": f"/evaluator/d/application/{app.get('qual_id')}",
            "hx_target": "#ev-center-panel",
            "hx_swap": "innerHTML",
            "_": "on click remove .bg-blue-100 from <a/> in #application-list-container then add .bg-blue-100 to me",
            "cls": "block p-3 border-b hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        }
        
        if include_oob:
            attrs["hx_swap_oob"] = "innerHTML:#ev-right-panel"
        
        level_abbr = QUALIFICATION_LEVEL_STYLES.get(app.get('level'), {}).get('abbr', 'N/A')
        qual_name = app.get('qualification_name', 'N/A')
        
        count_str = f"({app.get('selected_specialisations_count')}/{app.get('total_specialisations')})"

        # --- REVISED STRUCTURE for correct truncation ---
        second_line_content = Div(
            # This span takes up the available space and allows the text inside to be truncated
            Span(f"{level_abbr}/{qual_name}/", cls="truncate"),
            # This span does not shrink, ensuring the count is always visible
            Span(count_str, cls="flex-shrink-0"),
            # The parent div is a flex container
            cls="flex justify-between items-baseline text-xs text-gray-600"
        )


        item = A(
            Div(
                P(app.get('applicant_name', 'N/A'), cls="font-semibold text-sm truncate"),
                cls="flex justify-between items-baseline"
            ),
            second_line_content, # Use the new flexbox-based component
            **attrs
        )
        application_items.append(item)
    
    return tuple(application_items)