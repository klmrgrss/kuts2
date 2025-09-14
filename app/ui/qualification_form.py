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

def QualificationStatusStrip(sections: dict):
    """Renders a status strip indicating how many activity areas have selections."""
    
    # Count the number of sections (tegevusalad) with at least one preselected item.
    sections_with_selections = sum(1 for section in sections.values() if section.get("preselected"))

    if sections_with_selections == 0:
        # Red/Pink strip for no selections
        return Div(
            UkIcon("info", cls="flex-shrink-0"),
            P("Ühtegi tegevusala pole valitud."),
            cls="p-4 bg-red-100 text-red-800 rounded-lg my-4 flex items-center gap-x-3"
        )
    else:
        # Green strip showing the count
        plural_text = "tegevusala" if sections_with_selections == 1 else "tegevusala"
        return Div(
            UkIcon("check-circle", cls="flex-shrink-0"),
            P(f"Valitud on {sections_with_selections} {plural_text}."),
            cls="p-4 bg-green-100 text-green-800 rounded-lg my-4 flex items-center gap-x-3"
        )

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

    border_colors = {
        "Ehitusjuht, TASE 6": "border-blue-300 dark:border-blue-700",
        "Ehituse tööjuht, TASE 5": "border-green-300 dark:border-green-700",
        "Oskustööline, TASE 4": "border-yellow-300 dark:border-yellow-700"
    }
    default_border_color = "border-gray-300 dark:border-gray-600"

    # --- Main Form Structure ---
    form_content = Form(
        #H3("Märgi taotletav spetsialiseerumine", cls="text-xl font-semibold mb-2"),
        #P("Vali soovitud kutsetaseme ja tegevusala alt taotletav spetsialiseerumine.", cls="text-sm text-muted-foreground mb-6"),
        QualificationStatusStrip(sections), # Add the status strip here

        *[
            Div(
                # --- Row 1: KUTSETASE (Legend) ---
                Div(
                    Small("KUTSETASE", cls="text-xs font-semibold text-muted-foreground"),
                    Pill(section["level"], bg_color=level_colors.get(section["level"], default_color)),
                    cls="absolute -top-3 left-4 bg-background px-2 flex items-center gap-x-2"
                ),

                # --- Row 2: TEGEVUSALA ---
                Div(
                    Div(
                        Small("TEGEVUSALA", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    Div(
                        P(section["category"], cls="text-2xl md:ml-1 md:text-2xl font-bold text-foreground"),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center"
                ),

                DividerSplit(P("SPETSIALISEERUMINE", cls="text-xs font-semibold  text-muted-foreground")),

                # --- NEW: Centered Toggle Switch Row ---
                # This Div is now outside the main grid for specializations
                Div(
                    (LabelSwitch(
                        "Tervik",
                        id=f"toggle-{section['id']}", name=f"toggle-{section['id']}", value="on",
                        checked=section.get("toggle_on", False),
                        hx_post=f"/app/kutsed/toggle?section_id={section['id']}&app_id={app_id}",
                        hx_target=f"#checkbox-group-{section['id']}", hx_swap="outerHTML",
                        hx_include="this", hx_trigger="change",
                        cls="flex items-center gap-2 mb-3 text-sm italic font-semibold text-muted-foreground"
                    ) if len(section["items"]) > 1 else Div()), # Conditionally render
                    cls="flex justify-center" # Center the toggle
                ),

                # --- Row 3: SPETSIALISEERUMINE (Checkboxes only) ---
                Div(
                    # Left Column (Label)
                    Div(
                        # The label is now optional as the Divider serves as the main title
                        # Small("SPETSIALISEERUMINE", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    # Right Column (Value - contains only checkboxes now)
                    Div(
                        render_checkbox_group(
                            section_id=section["id"],
                            items=section["items"],
                            section_info={"level": section["level"], "category": section["category"]},
                            checked_state=section["preselected"]
                        ),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4"
                ),

                id=f"qual-section-{section['id']}",
                cls=f"relative mt-8 mb-10 border-4 rounded-lg p-4 space-y-4 {border_colors.get(section['level'], default_border_color)}"
            )
            for section in sections.values()
        ],


        Div(id="qual-form-error", cls="text-red-500 mt-2 mb-2"),
        # --- Submit Button ---
        Div(
            Button("Salvesta valikud", type="submit", cls="btn btn-primary"),
            cls="flex justify-end mt-6 pt-4 border-t"
        ),

        # --- HTMX Form Attributes ---
        method="post",
        hx_post="/app/kutsed/submit",
        hx_target="#tab-content-container",
        hx_swap="innerHTML",
        id="qualification-form",
        cls="space-y-8"
    )

    # --- Final Component Assembly ---
    return Div(
        form_content,
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