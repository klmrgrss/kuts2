# ui/qualification_form.py
from fasthtml.common import *
from monsterui.all import *
from .checkbox_group import render_checkbox_group

def FormSection(*children, **kwargs):
    """A simple helper component that creates a Div and passes along any keyword arguments."""
    return Div(*children, **kwargs)

def Pill(text: str, bg_color: str):
    """A helper component to create a styled 'pill' or 'badge'."""
    return Span(text, cls=f"px-2.5 py-1 rounded-full text-xs font-semibold {bg_color}")

def render_qualification_form(sections: dict, app_id: str):
    """
    Renders the qualification selection form with a clear, responsive,
    label-value aligned layout for wide screens.
    """

    level_colors = {
        "Ehitusjuht, TASE 6": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
        "Ehituse tööjuht, TASE 5": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        "Oskustööline, TASE 4": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
    }
    default_color = "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"

    # --- Main Form Structure ---
    form_content = Form(
        H3("Taotletavad kutsed", cls="text-xl font-semibold mb-2"),
        P("Vali tegevusalad ja spetsialiseerumised, millele soovid kutset taotleda.", cls="text-sm text-muted-foreground mb-6"),

        *[
            FormSection(
                # --- FIX: Replaced Grid component with Div and explicit Tailwind classes ---

                # --- Row 1: KUTSETASE ---
                Div(
                    # Left Column (Label)
                    Div(
                        Small("KUTSETASE", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    # Right Column (Value)
                    Div(
                        Pill(section["level"], bg_color=level_colors.get(section["level"], default_color)),
                        cls="md:col-span-2"
                    ),
                    # Added responsive grid classes directly
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center"
                ),

                # --- Row 2: TEGEVUSALA ---
                Div(
                    # Left Column (Label)
                    Div(
                        Small("TEGEVUSALA", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    # Right Column (Value)
                    Div(
                        H5(section["category"], cls="text-base md:ml-1 md:text-lg font-bold text-foreground/90"),
                        cls="md:col-span-4"
                    ),
                    # Added responsive grid classes directly
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center mt-3"
                ),

                # --- Row 3: SPETSIALISEERUMINE ---
                Div(
                    # Left Column (Label)
                    Div(
                        Small("SPETSIALISEERUMINE", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    # Right Column (Value - contains checkboxes and toggle)
                    Div(
                        render_checkbox_group(
                            section_id=section["id"],
                            items=section["items"],
                            section_info={"level": section["level"], "category": section["category"]},
                            checked_state=section["preselected"]
                        ),
                        # Toggle switch is placed below the checkboxes within the same column
                        Div(
                            LabelSwitch(
                                "Tervikspetsialiseerumine",
                                id=f"toggle-{section['id']}", name=f"toggle-{section['id']}", value="on",
                                checked=section.get("toggle_on", False),
                                hx_post=f"/app/kutsed/toggle?section_id={section['id']}&app_id={app_id}",
                                hx_target=f"#checkbox-group-{section['id']}", hx_swap="outerHTML",
                                hx_include="this", hx_trigger="change",
                                cls="flex items-center gap-2 mt-4 text-sm text-gray-600"
                            ),
                            cls="flex justify-start md:justify-end" # Aligns toggle
                        ),
                        cls="md:col-span-4"
                    ),
                    # Added responsive grid classes directly
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 mt-3"
                ),

                id=f"qual-section-{section['id']}",
                cls="mb-6 border rounded-lg p-4 space-y-2" # space-y for mobile stacking
            )
            for section in sections.values()
        ],

        Div(id="qual-form-error", cls="text-red-500 mt-2 mb-2"),
        # --- Submit Button ---
        Div(
            Button("Kinnita valikud ja jätka", type="submit", cls="btn btn-primary"),
            cls="flex justify-end mt-6 pt-4 border-t"
        ),

        # --- HTMX Form Attributes ---
        method="post",
        hx_post="/app/kutsed/submit",
        hx_target="#qual-form-error",
        hx_swap="innerHTML",
        id="qualification-form",
        cls="space-y-4"
    )

    # --- Final Component Assembly ---
    return Div(
        Card(
            CardBody(form_content)
        ),
        # JavaScript for syncing the "Select All" toggle with checkboxes
        Script("""
        function setupSyncForSection(sectionId) {
            const checkboxes = document.querySelectorAll(`#checkbox-group-${sectionId} input[type="checkbox"]`);
            const toggle = document.querySelector(`#toggle-${sectionId}`);
            if (!toggle || checkboxes.length === 0) return;

            function updateToggleState() {
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                toggle.checked = allChecked;
            }

            checkboxes.forEach(checkbox => checkbox.addEventListener('change', updateToggleState));
        }

        function initializeQualificationSync() {
            const sections = document.querySelectorAll('[id^="qual-section-"]');
            sections.forEach(section => {
                const sectionId = section.id.replace('qual-section-', '');
                setupSyncForSection(sectionId);
            });
        }
        
        document.addEventListener('DOMContentLoaded', initializeQualificationSync);
        
        document.body.addEventListener('htmx:afterSwap', function(event) {
            const target = event.detail.target;
            if (target.id && target.id.startsWith('checkbox-group-')) {
                const sectionId = target.id.replace('checkbox-group-', '');
                setupSyncForSection(sectionId);
            } else if (target.querySelector && target.querySelector('[id^="checkbox-group-"]')) {
                initializeQualificationSync();
            }
        });
        """)
    )
