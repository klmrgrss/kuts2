# app/ui/evaluator_v2/left_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
from .application_list import render_application_list



def render_left_panel(applications: List[Dict], id_suffix: str = "") -> FT:
    """
    Renders the full left panel, including the search controls
    and the initial list of applications. Accepts an optional id_suffix.
    """
    search_input_id = f"search-input{id_suffix}"
    list_container_id = f"application-list-container{id_suffix}"

    header = Div(
        Div(
            Input(
                id=search_input_id, name="search", type="search",
                placeholder="Otsi nime või kutse järgi...",
                hx_post="/evaluator/d/search_applications",
                hx_trigger="keyup changed delay:500ms, search",
                hx_target=f"#{list_container_id}",
                hx_swap="innerHTML"
            ),
            UkIcon("search", cls="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"),
            cls="relative w-full"
        ),
        cls="p-3 border-b bg-gray-50 sticky top-0 z-10"
    )

    return Div(
        header,
        Div(
            render_application_list(applications),
            id=list_container_id
        ),
        cls="h-full bg-white border-r overflow-auto [scrollbar-width:none]"
    )