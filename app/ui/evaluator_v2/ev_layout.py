# app/ui/evaluator_v2/ev_layout.py
from fasthtml.common import *
from monsterui.all import *
from starlette.requests import Request
from ui.layouts import base_layout
from ui.nav_components import evaluator_navbar

def ev_layout(
    request: Request,
    title: str,
    left_panel_content: Any,
    center_panel_content: Any,
    right_panel_content: Any
) -> FT:
    """
    Renders the new three-panel layout for the evaluator dashboard.
    Includes slide-out functionality for narrow screens.
    """
    page_title = f"{title} | Hindamiskeskkond"

    # --- Main Content with Three-Panel Layout ---
    main_content = Div(
        # --- Left Panel (Applications List) ---
        Aside(
            left_panel_content,
            id="ev-left-panel",
            cls="ev-panel"
        ),

        # --- Center Panel (Decision Making) ---
        Main(
            center_panel_content,
            id="ev-center-panel",
            cls="ev-panel"
        ),

        # --- Right Panel (Applicant Details) ---
        Aside(
            right_panel_content,
            id="ev-right-panel",
            cls="ev-panel"
        ),

        # This ID is used by the JS to toggle the slide-out classes
        id="evaluator-v2-container",
        # The core of the desktop layout
        cls="grid grid-cols-[1fr_3fr_1fr] h-[calc(100vh-65px)]"
    )

    # --- Navbar with Toggle Buttons for Mobile ---
    # These buttons will only be visible on narrow screens due to CSS
    navbar_with_toggles = Div(
        # Standard evaluator navbar
        evaluator_navbar(request),
        # Mobile-only toggle buttons
        Div(
            Button(
                UkIcon("menu", cls="w-6 h-6"),
                # JS onclick to toggle the left panel
                onclick="toggleEvaluatorPanel('left')",
                cls="btn btn-ghost lg:hidden"
            ),
            Button(
                UkIcon("user", cls="w-6 h-6"),
                # JS onclick to toggle the right panel
                onclick="toggleEvaluatorPanel('right')",
                cls="btn btn-ghost lg:hidden"
            ),
            cls="absolute top-3 right-4 z-20 flex gap-x-2"
        ),
        cls="relative" # Needed for absolute positioning of toggles
    )


    # Use the main base_layout to get all the necessary headers and scripts
    return base_layout(
        page_title,
        navbar_with_toggles,
        main_content,
        # Semi-transparent overlay for mobile view when a panel is open
        Div(id="ev-overlay", onclick="closeAllEvaluatorPanels()"),
    )