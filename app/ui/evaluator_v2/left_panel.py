# app/ui/evaluator_v2/left_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict
from .application_list import render_application_list


def render_left_panel(applications: List[Dict]) -> FT:
    """
    Renders the full left panel, including the search/filter controls
    and the initial list of applications.
    """
    header = Div(
        Div(
            Input(
                id="search-input", name="search", type="search",
                #placeholder="Otsi nime või kutse järgi...",
                hx_get="/evaluator/d/search_applications",
                hx_trigger="keyup changed delay:500ms, search",
                hx_target="#application-list-container",
                hx_swap="innerHTML",
                hx_include="[name='search']"
            ),
            UkIcon("search", cls="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"),
            cls="relative"
        ),
        Button(UkIcon("filter", cls="w-5 h-5"), cls="btn btn-ghost btn-square"),
        cls="p-3 border-b flex items-center gap-x-2 bg-gray-50 sticky top-0 z-10"
    )

    return Div(
        header,
        # This div is the permanent target for the swap
        Div(
            render_application_list(applications),
            id="application-list-container"
        ),
        cls="h-full bg-white border-r"
    )