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
    db: Any
) -> FT:
    """
    Renders the evaluator layout using a responsive approach:
    - A three-column grid on large screens (desktop).
    - A DaisyUI Drawer component for slide-out panels on smaller screens (mobile).
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

            # --- THE FIX: Applying the advanced overflow prevention classes ---
            Div(
                # Left Panel
                Div(
                    left_panel_content,
                    cls="hidden lg:block h-full"
                ),

                # Center Panel
                center_panel_content,

                # Right Panel
                Div(
                    right_panel_content,
                    cls="hidden lg:block h-full"
                ),

                # This class list now contains the robust solution from your notes.
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
                left_panel_content,
                Div(
                    right_panel_content,
                    cls="border-t"
                ),
                cls="lg:hidden flex flex-col h-full bg-base-100 w-80"
            ),
            cls="drawer-side z-40"
        ),
        cls="drawer"
    )

    return base_layout(page_title, layout)