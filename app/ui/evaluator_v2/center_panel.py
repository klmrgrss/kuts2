# app/ui/evaluator_v2/center_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import Dict, Optional
from ui.shared_components import LevelPill # Import LevelPill

def ContextButton(
    icon_name: str,
    label_text: str,
    color: Optional[str] = None,
    **kwargs
) -> FT:
    """
    Creates a contemporary, minimalistic button with precise vertical alignment.
    Can be colored green or red, otherwise defaults to a ghost style.

    Args:
        icon_name: The name of the icon from the UkIcon set.
        label_text: The text to display next to the icon.
        color: Optional color for the button ('green' or 'red').
        **kwargs: Additional HTML/HTMX attributes for the button.
    """
    # Color schemes for different states
    color_map = {
        'green': "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800",
        'red': "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800",
    }

    # Base classes for consistent styling and alignment
    base_classes = (
        "inline-flex items-center justify-center "
        "h-8 px-3 "
        "gap-x-2 "
        "rounded-full "
        "text-sm font-normal normal-case "
        "transition-colors duration-150"
    )

    # Select the appropriate classes based on the color parameter
    if color in color_map:
        style_classes = color_map[color]
    else:
        # Default "ghost" button style
        style_classes = "bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700"

    return Button(
        UkIcon(icon_name, cls="w-4 h-4"),
        Span(label_text),
        cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')}",
        **kwargs
    )

def render_compliance_section_from_data(title: str, icon_name: str, result_details: Dict):
    """Dynamically renders a compliance section based on validation results."""
    is_compliant = result_details.get("met", False)
    status_text = f"Nõutud: {result_details.get('required')}, Esitatud: {result_details.get('provided')}"
    
    status_color_class = "border-green-500" if is_compliant else "border-red-500"
    status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if is_compliant else UkIcon("x-circle", cls="w-5 h-5 text-red-500")

    return Details(
        Summary(
            Div(
                Div(cls=f"w-1.5 h-full absolute left-0 top-0 bg-{status_color_class.split('-')[1]}-500"),
                UkIcon(icon_name, cls="w-5 h-5"),
                H3(title, cls="font-semibold"),
                status_icon,
                Span(status_text, cls="text-sm text-gray-500 truncate"),
                UkIcon("chevron-down", cls="accordion-marker ml-auto"),
                cls="flex items-center gap-x-3 w-full cursor-pointer p-3 relative"
            )
        ),
        # Content can be expanded later with more rule details
        Div(P("Details about the rule and analysis can be added here.", cls="text-sm p-4 border-t")),
        open=not is_compliant, # Open the section if it failed
        cls=f"border {status_color_class} rounded-lg "
    )
# ^ --- END NEW HELPER FUNCTION --- ^

def render_center_panel(qual_data: Dict, user_data: Dict, validation_results: Dict) -> FT:
    """
    Renders the center panel with the details of the selected qualification
    and the argumentation/decision components, based on the Compliance Dashboard UI.
    """
    applicant_name = user_data.get('full_name', 'N/A')
    qual_level = qual_data.get('level', '')
    qual_name = qual_data.get('qualification_name', '')
    specialisations = qual_data.get('specialisations', [])
    selected_count = qual_data.get('selected_specialisations_count', len(specialisations))
    total_count = qual_data.get('total_specialisations', len(specialisations))

    # --- Header ---
    header = Details(
        # This part is the clickable accordion title
    Summary(
        # Header row
        Div(
            # 1) Pill (fixed width)
            LevelPill(qual_level),

            # 2) Name + (count · level) — single row; only level may wrap
            Div(
                # Make this a flex row that can wrap, but only the level is allowed to wrap
                H2(applicant_name,
                cls="text-xl font-bold overflow-hidden text-ellipsis whitespace-nowrap"),
                
                P("·", cls="text-gray-400 whitespace-nowrap mx-1"),
                # Level text is the ONLY thing allowed to wrap to the next line
                P(f"{qual_name}",
                cls="text-sm text-gray-700 flex-auto min-w-0 break-words whitespace-normal"),
                cls="flex flex-wrap items-baseline gap-y-0 min-w-0"
            ),

            # 3) Chevron (right)
            DivHStacked(
                P("Spetsialiseerumised", cls="text-xs"),
                P(f"({selected_count}/{total_count})",
                cls="text-xs  font-bold text-gray-600 whitespace-nowrap ml-1"),
                UkIcon("chevron-down", cls="accordion-marker"),
                cls="justify-self-end flex items-center"
            ),

            # Shared 3-col grid for header
            cls="grid grid-cols-[auto,1fr,auto] items-center gap-x-3"
        ),
        cls="list-none cursor-pointer col-span-3"
    ),

    # Collapsible content — aligned under level/name (middle column)
    Div(
        Ul(
            *[Li(s) for s in specialisations],
            cls="list-disc list-inside text-xs text-gray-700"
        ),
        cls="col-start-2 ml-4 mt-2"
    ),

    # Accordion props + shared grid so row 2 aligns with column 2
    open=False,
    cls="border-b bg-gray-50 sticky top-0 z-10 grid grid-cols-[auto,1fr,auto] gap-x-3"
    )



    # --- Helper Component for Accordion Sections (Unchanged) ---
    def ComplianceSection(
        title: str,
        icon_name: str,
        status_text: str,
        is_compliant: bool,
        rule_text: str,
        analysis_items: list,
        is_open: bool = True,
        pdf_path: Optional[str] = None,
        doc_filename: str = "Document"
    ):
        status_color_class = "border-green-500" if is_compliant else "border-red-500"
        status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if is_compliant else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
        modal_id = f"pdf-modal-{title.replace(' ', '-').lower()}"

        pdf_modal = None
        if pdf_path:
            pdf_modal = Modal(
                Embed(src=pdf_path, type='application/pdf', width='100%', height='500px'),
                id=modal_id,
                header=ModalTitle(doc_filename),
                footer=ModalCloseButton("Sule", cls="btn-secondary"),
                dialog_cls="w-11/12 max-w-7xl"
            )

        return Details(
            Summary(
                Div(
                    Div(cls=f"w-1.5 h-full absolute left-0 top-0 bg-{status_color_class.split('-')[1]}-500"),
                    UkIcon(icon_name, cls="w-5 h-5"),
                    H3(title, cls="font-semibold"),
                    status_icon,
                    Span(status_text, cls="text-sm text-gray-500 truncate"),
                    UkIcon("chevron-down", cls="accordion-marker ml-auto"),
                    cls="flex items-center gap-x-3 w-full cursor-pointer p-3 relative"
                )
            ),
            Div(
                Div(
                    P("Kohaldatav Reegel", cls="font-semibold text-xs text-gray-500 uppercase mb-1"),
                    P(rule_text, cls="p-2 bg-blue-50 text-blue-800 rounded text-sm italic"),
                    cls="mb-4"
                ),
                Div(
                    P("Süsteemi Analüüs", cls="font-semibold text-xs text-gray-500 uppercase mb-1"),
                    Div(*[P(item) for item in analysis_items], cls="p-2 bg-gray-50 rounded text-sm space-y-1"),
                    cls="mb-4"
                ),
                Div(
                    P("Tõendusmaterjal", cls="font-semibold text-xs text-gray-500 uppercase mb-1"),
                    Button(UkIcon("file-text", cls="w-4 h-4 mr-2"), f"Vaata dokumenti: {doc_filename}", cls="btn btn-sm btn-outline", **{"uk-toggle": f"target: #{modal_id}"}) if pdf_path else P("Dokument puudub.", cls="text-sm text-gray-500"),
                    pdf_modal if pdf_modal else Div()
                ),
                cls="p-4 border-t"
            ),
            open=is_open,
            cls=f"border {status_color_class} rounded-lg "
        )

     # --- Dynamic Compliance Dashboard ---
    compliance_sections = []
    # Find the first package the applicant meets
    met_package = next((res for res in validation_results.get("results", []) if res["is_met"]), None)

    if met_package:
        # If a package is met, show its details
        compliance_sections.append(
            Div(
                H3(f"Vastab tingimustele (Variant: {met_package['package_id']})", cls="text-lg font-semibold text-green-700 p-2 bg-green-50 rounded-md text-center"),
                render_compliance_section_from_data("Haridus", "book-open", met_package['details']['education']),
                render_compliance_section_from_data("Töökogemus (kokku)", "briefcase", met_package['details']['total_experience']),
                render_compliance_section_from_data("Vastav töökogemus", "briefcase", met_package['details']['matching_experience']),
                render_compliance_section_from_data("Baaskoolitus", "award", met_package['details']['base_training']),
            )
        )
    else:
        # If no package is met, show the details of the first (or best-fit) one that failed
        first_package = validation_results.get("results", [{}])[0]
        compliance_sections.append(
             Div(
                H3(f"Tingimused ei ole täidetud (Variant: {first_package['package_id']})", cls="text-lg font-semibold text-red-700 p-2 bg-red-50 rounded-md text-center"),
                render_compliance_section_from_data("Haridus", "book-open", first_package['details']['education']),
                render_compliance_section_from_data("Töökogemus (kokku)", "briefcase", first_package['details']['total_experience']),
                render_compliance_section_from_data("Vastav töökogemus", "briefcase", first_package['details']['matching_experience']),
                render_compliance_section_from_data("Baaskoolitus", "award", first_package['details']['base_training']),
            )
        )

    compliance_dashboard = Div(*compliance_sections, cls="p-4 space-y-4")

    # --- Final Decision & Chat Area ---
    final_decision_area = Div(
    # This is the wrapper for the composite "chat input" component.
    # We apply padding here to give it space within the final_decision_area.
    Div(
        # This new inner Div will have the continuous border.
        # `overflow-hidden` is important to make the child corner rounding work correctly.
        Div(
            # Main Text Input
            Textarea(
                placeholder="Vali kontekst ja sisesta kommentaar või põhjendus...",
                rows=3,
                # Remove all border and rounding classes from the textarea itself.
                # Add focus styling to prevent the default browser outline on click.
                cls="textarea w-full resize-none border-0 focus:outline-none focus:ring-0 overflow-hidden"
            ),
            # Toolbar with Context Buttons
            Div(
                ContextButton(icon_name="book-open", label_text="Haridus"),
                ContextButton(icon_name="briefcase", label_text="Töökogemus"),
                ContextButton(icon_name="award", label_text="Täiendkoolitus"),
                ContextButton(icon_name="ban", label_text="Mitte anda", cls="ml-auto ", color="red"),
                ContextButton(icon_name="list-checks", label_text="Anda", color="green"),
                ContextButton(icon_name="sparkles", label_text=""),
                # This toolbar now only needs a top border to separate it from the textarea.
                cls="flex items-center gap-x-2 p-2 bg-base-100"
            ),
            # The continuous border and rounding are applied to this single wrapper.
            cls="border-2 rounded-lg overflow-hidden"
        ),
        cls="px-4 "
    ), cls="pb-4 pt-2 shadow-xl")

    return Div(
        header,
        Div(compliance_dashboard, cls="flex-grow overflow-y-auto [scrollbar-width:none]"),
        final_decision_area,
        id="ev-center-panel",
        cls="flex flex-col h-full bg-white"
    )