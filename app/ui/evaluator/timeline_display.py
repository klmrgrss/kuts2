# app/ui/evaluator/timeline_display.py

from fasthtml.common import *
# No need for monsterui unless you add Card/etc. back later
# import json # json is used in controller, not needed here usually

def render_timeline_display(timeline_items_json: str) -> FT:
    """
    Renders the container Div for the Vis.js timeline.

    Args:
        timeline_items_json: A JSON string containing the prepared timeline items data
                             (list of dicts with id, group, content, start, end, title).
    """

    # Heading for the timeline section
    timeline_heading = H4(
        "Töökogemuse ajajoon", # "Work Experience Timeline"
        cls="text-lg font-medium mb-2" # Standard heading style
    )

    # The Div container that Vis.js will target
    timeline_container = Div(
        # The ID for the JavaScript initializer to find
        id="vis-timeline-container",
        # Embed the JSON data directly into the data-* attribute
        data_timeline_items=timeline_items_json,
        # Basic styling for the container (can be adjusted or moved to CSS)
        # Ensure height is sufficient for the timeline to render initially
        style="height: 300px; width: 100%; border: 1px solid #e2e8f0; background-color: #f8fafc; border-radius: 0.375rem;", # Example style: height, border, bg, rounded corners
        # Add a placeholder message if needed, though JS will overwrite it
        # P("Laen ajajoont...", cls="text-center text-gray-500 p-4")
    )

    # Return the heading and the container, wrapped in a Div for layout spacing
    return Div(
        timeline_heading,
        timeline_container,
        cls="mt-6 mb-4" # Add margin top/bottom for spacing from surrounding elements
    )