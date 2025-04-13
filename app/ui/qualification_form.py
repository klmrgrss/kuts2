# ui/components/qualification_form.py
from fasthtml.common import *
from monsterui.all import *

# Imports and helper definitions (Pill, FormSection, render_checkbox_group, etc.) remain the same...

# Temporary color definitions if not imported
COLORS = {
    'blue_light': 'blue-100',   # Example Tailwind class
    'green_light': 'green-100', # Example Tailwind class
    'yellow_light': 'yellow-100' # Example Tailwind class
}

level_colors = {
    "Ehitusjuht, TASE 6": f"bg-{COLORS['blue_light']}",
    "Ehituse tööjuht, TASE 5": f"bg-{COLORS['green_light']}",
    "Oskustööline, TASE 4": f"bg-{COLORS['yellow_light']}"
}

# Example FormSection if not imported
def FormSection(*children, section_id): return Div(*children, id=section_id, cls="mb-6 border-b pb-4")
# Example Pill if not imported
def Pill(text, bg_color): return Span(text, cls=f"px-2 py-1 rounded text-xs {bg_color}")
# Example LabelSwitch if not imported
# def LabelSwitch(label, **kwargs): return Div(Label(label), Switch(**kwargs), cls="flex items-center")

# You might need checkbox_group here too, or import it
from .checkbox_group import render_checkbox_group # Assuming it's importable

def render_qualification_form(sections: dict, app_id: str):
    """Renders the qualification selection form UI within a Card."""

    # Define the standard title style
    TITLE_CLASS = "text-xl font-semibold mb-4" # Example standard title class

    # Form content logic remains largely the same...
    form_content = Form(
            H3("Taotletavad kutsed", cls=TITLE_CLASS), # Standardized Title
                        Div( # Wrap button in Div for alignment/spacing
                Button("Kinnita valikud", type="submit", cls="btn btn-primary mt-4"), # Adjusted margin
                 cls="" # Added border-t
            ),
            P("Vali tegevusalad, mille kutsekvalifikatsiooni soovid tõendada", cls="text-sm text-muted-foreground mb-6"), # Subtitle/Instruction
            # Loop through sections data passed from controller
            *[FormSection(
                *(
                    Div( # Level Pill
                        Small("KUTSETASE", cls="text-xs text-gray-500"), Br(),
                        Pill(section["level"], bg_color=level_colors.get(section["level"], "bg-gray-100"))
                    ),
                    Div( # Category
                        Small("TEGEVUSALA", cls="text-xs text-gray-500"),
                        P(section["category"], cls="text-sm md:text-base font-bold text-gray-700"),
                        cls="mt-2"
                    ),
                    Div( # Toggle Switch
                        LabelSwitch(
                            "Tervikspetsialiseerumine",
                            id=f"toggle-{section['id']}", name=f"toggle-{section['id']}", value="on",
                            checked=section.get("toggle_on", False),
                            # Use controller route for HTMX post
                            hx_post=f"/app/kutsed/toggle?section_id={section['id']}&app_id={app_id}",
                            hx_target=f"#checkbox-group-{section['id']}", hx_swap="outerHTML",
                            hx_include="this", hx_trigger="change",
                            cls="flex items-center gap-2 mt-1 mb-1 text-sm text-gray-600"
                        ),
                        cls="text-right" # Align right
                    ),
                    Div( # Checkboxes
                        Small("SPETSIALISEERUMINE", cls="text-xs text-gray-500"),
                        render_checkbox_group(section["id"], section["items"],
                                    {"level": section["level"], "category": section["category"]},
                                    section["preselected"])
                    )
                ),
                section_id=f"qual-section-{section['id']}",
            ) for section in sections.values()],

            Hidden(app_id, id="application_id", name="application_id") if app_id else None,
            # Use controller route for form action
            Div(id="qual-form-error", cls="text-red-500 mt-2 mb-2"),
            Div( # Wrap button in Div for alignment/spacing
                Button("Kinnita valikud", type="submit", cls="btn btn-primary mt-4"), # Adjusted margin
                 cls="" # Added border-t
            ),
            # Use controller route for form action
            method="post",
            hx_post="/app/kutsed/submit", # Use hx-post for HTMX submission
            hx_target="#qual-form-error", # Target the error div for validation messages
            hx_swap="innerHTML",          # Replace error div content on validation failure
            id="qualification-form",
            # Remove card styling from Form tag
            # cls=CLASSES.get("card_wide", "bg-white p-6 rounded shadow") # REMOVED
            cls="space-y-4" # Basic spacing
        )

    # Wrap the form content in Card and CardBody
    content = Div( # Outer container for Card and Script
        Card(
            CardBody(
                form_content
            )
        ),
        # JavaScript remains the same
        Script("""
        // --- JS from qs.txt---
        // ... (keep existing JS) ...
        function setupSyncForSection(sectionId) {
            const checkboxes = document.querySelectorAll(`#checkbox-group-${sectionId} input[type="checkbox"]`);
            const toggle = document.querySelector(`#toggle-${sectionId}`);
            if (!toggle || checkboxes.length === 0) return;
            function updateToggleState() {
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                toggle.checked = allChecked;
            }
            function updateCheckboxesState() {
                checkboxes.forEach(cb => { cb.checked = toggle.checked; });
            }
            checkboxes.forEach(checkbox => checkbox.addEventListener('change', updateToggleState));
            toggle.addEventListener('change', updateCheckboxesState);
            // updateToggleState(); // Initial sync might conflict with HTMX load, check if needed
        }
        function initializeQualificationSync() {
            const sections = document.querySelectorAll('[id^="qual-section-"]');
            sections.forEach(section => {
                const sectionId = section.id.replace('qual-section-', '');
                setupSyncForSection(sectionId);
            });
        }
        // Initial load
        document.addEventListener('DOMContentLoaded', initializeQualificationSync);
        // After HTMX swap targeting a checkbox group or the whole container
        document.body.addEventListener('htmx:afterSwap', function(event) {
            const target = event.detail.target;
            // Check if target IS a checkbox group or CONTAINS one
             if (target.id && target.id.startsWith('checkbox-group-')) {
                const sectionId = target.id.replace('checkbox-group-', '');
                setupSyncForSection(sectionId); // Re-apply sync logic to swapped group
            } else if (target.querySelector && target.querySelector('[id^="checkbox-group-"]')) {
                // If the swapped content contains checkbox groups (e.g., full tab swap)
                initializeQualificationSync();
            }
        });
        """)
    )

    return content