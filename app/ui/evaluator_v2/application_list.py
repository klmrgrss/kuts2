# klmrgrss/kuts2/kuts2-eval/app/ui/evaluator_v2/application_list.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
from ui.shared_components import LevelPill
from config.qualification_data import QUALIFICATION_LEVEL_STYLES
import hashlib

def get_safe_dom_id(qual_id: str) -> str:
    """Returns a CSS-safe ID for DOM elements."""
    return "app-" + hashlib.md5(qual_id.encode()).hexdigest()

def render_application_item(app: Dict, include_oob: bool = True, active_qual_id: str = None) -> FT:
    """Renders a single application list item."""
    qual_id = app.get('qual_id', '')
    dom_id = get_safe_dom_id(qual_id)
    
    is_active = (qual_id == active_qual_id)
    base_cls = "block p-3 border-b hover:bg-gray-100 dark:hover:bg-gray-800 dark:border-gray-700 focus:outline-none transition-colors"
    active_cls = "bg-blue-50 dark:bg-blue-900/20 shadow-inner"
    
    final_cls = f"{base_cls} {active_cls}" if is_active else base_cls

    # JS to toggle classes safely (Relative traversal fixes mobile/drawer ID mismatch)
    toggle_js = (
        "this.closest('div').querySelectorAll('a').forEach(el=>{"
        "el.classList.remove('bg-blue-50','dark:bg-blue-900/20','shadow-inner');"
        "});"
        "this.classList.add('bg-blue-50','dark:bg-blue-900/20','shadow-inner');"
    )

    attrs = {
        "hx_get": f"/evaluator/d/application/{qual_id}",
        "hx_target": "#ev-center-panel",
        "hx_swap": "innerHTML",
        "hx_params": "none",
        "onclick": toggle_js,
        "cls": final_cls
    }
    
    if include_oob:
        attrs["hx_swap_oob"] = "innerHTML:#ev-right-panel"
    
    level_abbr = QUALIFICATION_LEVEL_STYLES.get(app.get('level'), {}).get('abbr', 'N/A')
    qual_name = app.get('qualification_name', 'N/A')
    
    # --- REVISED STRUCTURE for correct truncation ---
    second_line_content = Div(
        # This span takes up the available space and allows the text inside to be truncated
        Span(f"{level_abbr} / {qual_name}", cls="truncate"),
        # The parent div is a flex container
        cls="flex justify-between items-baseline text-xs text-gray-600 dark:text-gray-400"
    )

    precheck_met = app.get('precheck_met')
    final_decision = app.get('final_decision')

    # Unified Icon Logic
    # Priority: Human Decision (Color) > Precheck (Gray) > Placeholder
    icon_name = "shield"
    icon_cls = "w-5 h-5 text-gray-200 dark:text-gray-700" # Default placeholder

    if final_decision:
        if final_decision == "Anda":
            icon_name = "shield-check"
            icon_cls = "w-5 h-5 text-green-500"
        elif final_decision == "Mitte anda":
            icon_name = "shield-off"
            icon_cls = "w-5 h-5 text-red-500"
        elif final_decision == "Täiendav tegevus":
            icon_name = "shield-check"
            icon_cls = "w-5 h-5 text-blue-500"
    elif precheck_met is not None:
        icon_cls = "w-5 h-5 text-gray-400 dark:text-gray-500"
        if precheck_met is True:
            icon_name = "shield-check"
        else:
            icon_name = "shield-off"

    return A(
        Div(
            # Single Icon Column
            Div(
                UkIcon(icon_name, cls=icon_cls),
                cls="flex items-center justify-center mr-3 pr-3 border-r border-gray-100 dark:border-gray-700 h-10"
            ),
            # Text Content
            Div(
                Div(
                    P(app.get('applicant_name', 'N/A'), cls="font-semibold text-sm truncate"),
                    cls="flex justify-between items-baseline"
                ),
                second_line_content, 
                cls="flex-grow min-w-0"
            ),
            cls="flex items-center"
        ),
        id=dom_id,
        **attrs
    )

def render_application_list(applications: List[Dict], include_oob: bool = True, active_qual_id: str = None) -> FT:
    """
    Renders the list of application items.
    Conditionally includes the hx_swap_oob attribute.
    """
    if not applications:
        return P("No applications found.", cls="p-4 text-center text-gray-500")

    application_items = [render_application_item(app, include_oob, active_qual_id) for app in applications]
    return tuple(application_items)