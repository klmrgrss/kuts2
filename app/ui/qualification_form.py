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
                # --- Row 1: KUTSETASE ---
                Div(
                    Div(
                        Small("KUTSETASE", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    Div(
                        Pill(section["level"], bg_color=level_colors.get(section["level"], default_color)),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center"
                ),

                # --- Row 2: TEGEVUSALA ---
                Div(
                    Div(
                        Small("TEGEVUSALA", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    Div(
                        H5(section["category"], cls="text-base md:ml-1 md:text-lg font-extrabold text-foreground"),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center mt-3"
                ),

                DividerSplit(P("Valitav spetsialiseerumine", cls="text-sm text-gray-400")),

                # --- FIX: Corrected the structure of the Div components in this row ---
                # --- Row 3: SPETSIALISEERUMINE ---
                Div(
                    # Left Column (Label)
                    Div(
                        #Small("SPETSIALISEERUMINE", cls="text-xs font-semibold text-muted-foreground"),
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
                        # Wrapper Div for the toggle switch
                        Div(
                            (LabelSwitch(
                                "Tervikspetsialiseerumine",
                                id=f"toggle-{section['id']}", name=f"toggle-{section['id']}", value="on",
                                checked=section.get("toggle_on", False),
                                hx_post=f"/app/kutsed/toggle?section_id={section['id']}&app_id={app_id}",
                                hx_target=f"#checkbox-group-{section['id']}", hx_swap="outerHTML",
                                hx_include="this", hx_trigger="change",
                                cls="flex items-center gap-2 mt-4 text-sm "
                            ) if len(section["items"]) > 1 else Div()), # Conditionally render
                            cls="flex justify-start md:justify-start"
                        ),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 mt-8"
                ),

                id=f"qual-section-{section['id']}",
                cls="mb-6 border-4 rounded-lg p-4 space-y-2"
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
        # --- JavaScript for toggle sync ---
        Script("""
        function setupSyncForSection(sectionId) {
            const container = document.getElementById(`qual-section-${sectionId}`);
            if (!container) return;

            const checkboxes = container.querySelectorAll(`#checkbox-group-${sectionId} input[type="checkbox"]`);
            const toggle = container.querySelector(`#toggle-${sectionId}`);
            
            if (!toggle || checkboxes.length === 0) return;

            function updateToggleState() {
                const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                toggle.checked = allChecked;
            }

            checkboxes.forEach(checkbox => {
                checkbox.removeEventListener('change', updateToggleState); // Prevent duplicate listeners
                checkbox.addEventListener('change', updateToggleState);
            });
            
            // Initial sync on setup
            updateToggleState();
        }

        function initializeQualificationSync() {
            const sections = document.querySelectorAll('[id^="qual-section-"]');
            sections.forEach(section => {
                const sectionId = section.id.replace('qual-section-', '');
                setupSyncForSection(sectionId);
            });
        }
        
        // Run on initial page load
        document.addEventListener('DOMContentLoaded', initializeQualificationSync);
        
        // Re-run after any HTMX swap to catch newly added or replaced content
        document.body.addEventListener('htmx:afterSwap', function(event) {
            // A simple, robust way is to just re-scan the whole document for sections
            initializeQualificationSync();
        });
        """)
    )
