# app/ui/evaluator_v2/ev_layout.py
from fasthtml.common import *
from monsterui.all import *
from starlette.requests import Request
from ui.layouts import base_layout
from ui.nav_components import evaluator_navbar
from typing import Any

def ev_layout(
    request: Request,
    title: str,
    left_panel_content: Any,
    center_panel_content: Any,
    right_panel_content: Any,
    db: Any,
    # Add parameters for the drawer's version of panels
    drawer_left_panel_content: Any,
    drawer_right_panel_content: Any = None # Optional for backward compat if needed, but we will pass it
) -> FT:
    """
    Renders the evaluator layout using a responsive approach.
    """
    page_title = f"{title} | Hindamiskeskkond"

    layout = Div(
        Input(id="left-drawer-toggle", type="checkbox", cls="drawer-toggle"),

        # --- DRAWER CONTENT (Main Viewport Area) ---
        Div(
            Div(
                evaluator_navbar(request, db),
                cls="sticky top-0 z-30 flex-shrink-0"
            ),

            Div(
                # Left Panel (Desktop)
                Div(
                    left_panel_content, # This is the original for desktop
                    cls="hidden lg:block h-full"
                ),

                # Center Panel
                center_panel_content,

                # Right Panel
                Div(
                    right_panel_content,
                    cls="hidden lg:block h-full"
                ),

                cls=("grid w-full max-w-full min-h-0 flex-grow overflow-x-hidden "
                     "grid-cols-[minmax(0,1fr)] "
                     "lg:grid-cols-[minmax(280px,1.2fr)_3fr_minmax(280px,1.2fr)] "
                     "[&>*]:min-w-0")
            ),
            cls="drawer-content flex flex-col h-screen overflow-hidden"
        ),

        # --- DRAWER SIDE (Slide-out mobile menu) ---
        Div(
            Label(fr="left-drawer-toggle", aria_label="close sidebar", cls="drawer-overlay"),
            Div(
                # Use the new, uniquely-suffixed content for the drawer
                Div(
                    drawer_left_panel_content,
                    cls="flex-1 overflow-y-auto" 
                ),
                Div(
                    drawer_right_panel_content or right_panel_content,
                    cls="flex-1 overflow-y-auto border-t" 
                ),
                cls="lg:hidden flex flex-col h-full w-80 shadow-xl bg-gray-50 dark:bg-gray-900" # Main wrapper
            ),
            cls="drawer-side z-40"
        ),
        cls="drawer"
    )

    return base_layout(page_title, layout)