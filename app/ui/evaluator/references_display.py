# app/ui/evaluator/references_display.py

from fasthtml.common import *
# Removed MonsterUI import as Card/etc are not used here
# from monsterui.all import *
from typing import Any # Added for FT type hint clarity

def render_references_grid() -> FT:
    """
    Renders the container Div for the AG Grid that will display
    implementer (TEOSTAJA) and client (TELLIJA) details.
    The grid itself is initialized and populated by JavaScript.
    """
    # Container Div for the AG Grid
    # - Use a specific ID for the JavaScript to target
    # - Apply AG Grid theme
    # - Set a height (can be adjusted)
    # - No data attributes needed here, data is set dynamically
    references_grid_container = Div(
        id="ag-grid-references", # ID for JS to target
        #cls="ag-theme-quartz",   # Apply AG Grid theme
        style="height: 150px; width: 100%;" # Adjust height as needed (enough for 2 rows + header)
    )

    # Return only the grid container, wrapped in a Div with spacing
    # Add a heading if desired
    return Div(
        # Optional Heading:
        H4("Kontaktid / Viited", cls="text-lg font-medium mb-2"),
        references_grid_container,
        # Apply margin if needed, although parent grid gap might handle spacing
        # cls="mb-4"
    )

# Remove the old render_references_display function if it exists