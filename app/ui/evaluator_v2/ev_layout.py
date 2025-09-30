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

    # --- THE FIX: Use a single drawer that CONTAINS the grid ---
    # This structure allows for responsive layout changes.

    layout = Div(
        # The checkbox to control the drawer on mobile
        Input(id="left-drawer-toggle", type="checkbox", cls="drawer-toggle"),

        # --- DRAWER CONTENT ---
        # This area contains the navbar and the main grid layout.
        Div(
            # 1. Navbar: It is sticky and contains the mobile toggle.
            Div(
                evaluator_navbar(request, db),
                cls="sticky top-0 z-30"
            ),

            # 2. Main Grid: This defines the 3-column desktop layout.
            #    On mobile, this grid collapses, and the panels are handled by the drawer.
            Div(
                # Left Panel (visible on desktop, part of drawer on mobile)
                Div(
                    left_panel_content,
                    cls="hidden lg:block h-full"
                ),

                # Center Panel
                center_panel_content,

                # Right Panel (visible on desktop, part of drawer on mobile)
                Div(
                    right_panel_content,
                    cls="hidden lg:block h-full"
                ),

                cls="grid lg:grid-cols-[minmax(280px,1.2fr)_3fr_minmax(280px,1.2fr)] h-[calc(100vh-68px)]"
            ),
            cls="drawer-content"
        ),

        # --- DRAWER SIDE ---
        # This holds the content for the slide-out panels on mobile.
        Div(
            Label(fr="left-drawer-toggle", aria_label="close sidebar", cls="drawer-overlay"),
            # On mobile, we show BOTH panels in the drawer, stacked.
            Div(
                left_panel_content,
                right_panel_content,
                cls="lg:hidden flex flex-col divide-y h-full" # Only show on mobile
            ),
            cls="drawer-side z-40"
        ),
        cls="drawer"
    )

    # Note: We are now using a single drawer. The right-side panel on mobile
    # will appear in the same drawer as the left, which is a common mobile pattern.
    return base_layout(page_title, layout)