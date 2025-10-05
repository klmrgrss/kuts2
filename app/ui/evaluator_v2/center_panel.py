# app/ui/evaluator_v2/center_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import Dict, Optional, List
from ui.shared_components import LevelPill # Import LevelPill

def ContextButton(
    icon_name: str,
    label_text: str,
    color: Optional[str] = None,
    **kwargs
) -> FT:
    """
    Creates a contemporary, minimalistic button with precise vertical alignment.
    The text label is hidden on extra-small screens.
    """
    color_map = {
        'green': "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800",
        'red': "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800",
    }
    base_classes = (
        "inline-flex items-center justify-center "
        "h-8 px-3 "
        "gap-x-2 "
        "rounded-full "
        "text-sm font-bold normal-case "
        "transition-colors duration-150"
    )
    if color in color_map:
        style_classes = color_map[color]
    else:
        style_classes = "bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700"
    return Button(
        UkIcon(icon_name, cls="w-4 h-4"),
        Span(label_text, cls="hidden sm:inline"),
        cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')}",
        **kwargs
    )

def DropdownContextButton(
    icon_name: str,
    label_text: str,
    dropdown_options: list,
    color: Optional[str] = None,
    **kwargs
) -> FT:
    """
    Creates a context button with dropdown functionality.
    The text label is hidden on extra-small screens.
    """
    button_id = f"btn-{label_text.lower().replace(' ', '-')}"
    dropdown_id = f"dropdown-{label_text.lower().replace(' ', '-')}"

    color_map = {
        'green': "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800",
        'red': "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800",
    }
    base_classes = (
        "inline-flex items-center justify-center "
        "h-8 px-3 "
        "gap-x-2 "
        "rounded-full "
        "text-sm font-bold normal-case "
        "transition-colors duration-150"
    )
    if color in color_map:
        style_classes = color_map[color]
    else:
        style_classes = "bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700"

    return Div(
        Button(
            UkIcon(icon_name, cls="w-4 h-4"),
            Span(label_text, cls="hidden sm:inline"),
            id=button_id,
            onclick=f"toggleButton('{button_id}')",
            cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')} border-r border-gray-300",
            style="border-radius: 9999px 0 0 9999px; border-right: 1px solid #d1d5db;"
        ),
        Button(
            UkIcon("chevron-down", cls="w-3 h-3"),
            onclick=f"toggleDropdown('{dropdown_id}')",
            cls=f"{base_classes} {style_classes} px-2",
            style="border-radius: 0 9999px 9999px 0; margin-left: -1px;"
        ),
        Div(
            *[Button(
                option,
                onclick=f"selectDropdownOption('{button_id}', '{option}')",
                cls="block w-full text-left px-3 py-2 text-sm hover:bg-base-300",
                style="border: none; background: none;"
            ) for option in dropdown_options],
            id=dropdown_id,
            cls=("absolute bottom-full left-0 mb-1 bg-base-200 border border-base-300 "
                 "rounded-xl shadow-lg z-50 w-auto whitespace-nowrap overflow-hidden"),
            style="display: none;"
        ),
        cls="relative inline-flex",
        **kwargs
    )

def render_compliance_section_from_data(title: str, icon_name: str, result_details: Dict):
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
        Div(P("Details about the rule and analysis can be added here.", cls="text-sm p-4 border-t")),
        open=not is_compliant,
        cls=f"border {status_color_class} rounded-lg "
    )

def render_center_panel(qual_data: Dict, user_data: Dict, validation_results: Dict) -> FT:
    applicant_name = user_data.get('full_name', 'N/A')
    qual_level = qual_data.get('level', '')
    qual_name = qual_data.get('qualification_name', '')
    specialisations = qual_data.get('specialisations', [])
    selected_count = qual_data.get('selected_specialisations_count', len(specialisations))
    total_count = qual_data.get('total_specialisations', len(specialisations))

    header = Details(
        Summary(
            Div(
                LevelPill(qual_level),
                Div(
                    H2(applicant_name, cls="text-xl font-bold overflow-hidden text-ellipsis whitespace-nowrap"),
                    P("·", cls="text-gray-400 whitespace-nowrap mx-1"),
                    P(f"{qual_name}", cls="text-sm text-gray-700 flex-auto min-w-0 break-words whitespace-normal"),
                    cls="flex flex-wrap items-baseline gap-y-0 min-w-0"
                ),
                DivHStacked(
                    P("Spetsialiseerumised", cls="text-xs"),
                    P(f"({selected_count}/{total_count})", cls="text-xs font-bold text-gray-600 whitespace-nowrap ml-1"),
                    UkIcon("chevron-down", cls="accordion-marker"),
                    cls="justify-self-end flex items-center"
                ),
                cls="grid grid-cols-[auto,1fr,auto] items-center gap-x-3"
            ),
            cls="list-none cursor-pointer col-span-3"
        ),
        Div(
            Ul(*[Li(s) for s in specialisations], cls="list-disc list-inside text-xs text-gray-700"),
            cls="col-start-2 ml-4 mt-2"
        ),
        open=False,
        cls="border-b bg-gray-50 sticky top-0 z-10 grid grid-cols-[auto,1fr,auto] gap-x-3"
    )

    compliance_sections = []
    met_package = next((res for res in validation_results.get("results", []) if res["is_met"]), None)
    if met_package:
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
        Div(
            Div(
                Textarea(
                    placeholder="Vali kontekst ja sisesta kommentaar või põhjendus...",
                    rows=3,
                    cls="textarea w-full resize-none border-0 focus:outline-none focus:ring-0"
                ),
                Div(
                    # --- THE FIX: Group left-side buttons and use justify-between ---
                    Div(
                        DropdownContextButton(
                            icon_name="book-open",
                            label_text="Haridus",
                            dropdown_options=[
                                "Keskharidus", "Keskeriharidus", "180 Bak",
                                "240 RakendusKH", "300 Mag", "Muu kõrgh"
                            ]
                        ),
                        ContextButton(icon_name="briefcase", label_text="Töökogemus"),
                        ContextButton(icon_name="award", label_text="Täiendkoolitus"),
                        DropdownContextButton(
                            icon_name="list-checks",
                            label_text="Otsus",
                            dropdown_options=["Anda", "Mitte anda"]
                        ),
                        cls="flex flex-wrap items-center gap-x-2" # Group for the left side
                    ),
                    ContextButton(icon_name="send", label_text=""),
                    cls="flex flex-wrap items-center justify-between gap-x-2 p-2 bg-base-100 rounded-b-lg"
                ),
                cls="border-2 rounded-lg shadow-xl"
            ),
            cls="px-4 "
        ),
        Script("""
            let buttonStates = {};

            function toggleButton(buttonId) {
                const button = document.getElementById(buttonId);
                const isActive = buttonStates[buttonId] || false;
                if (isActive) {
                    button.classList.remove('bg-blue-100', 'text-blue-800');
                    button.classList.add('bg-transparent');
                    buttonStates[buttonId] = false;
                } else {
                    button.classList.remove('bg-transparent');
                    button.classList.add('bg-blue-100', 'text-blue-800');
                    buttonStates[buttonId] = true;
                }
            }

            function toggleDropdown(dropdownId) {
                const dropdown = document.getElementById(dropdownId);
                const isVisible = dropdown.style.display !== 'none';
                document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
                    if (d.id !== dropdownId) d.style.display = 'none';
                });
                dropdown.style.display = isVisible ? 'none' : 'block';
            }

            function selectDropdownOption(buttonId, option) {
                const button = document.getElementById(buttonId);
                const span = button.querySelector('span');
                span.textContent = option;

                button.classList.remove('bg-transparent', 'bg-red-100', 'text-red-800', 'bg-green-100', 'text-green-800', 'bg-blue-100', 'text-blue-800');

                if (buttonId === 'btn-otsus') {
                    if (option === 'Anda') {
                        button.classList.add('bg-green-100', 'text-green-800');
                    } else if (option === 'Mitte anda') {
                        button.classList.add('bg-red-100', 'text-red-800');
                    }
                } else {
                    button.classList.add('bg-blue-100', 'text-blue-800');
                }
                buttonStates[buttonId] = true;

                const dropdownId = buttonId.replace('btn-', 'dropdown-');
                document.getElementById(dropdownId).style.display = 'none';
            }

            document.addEventListener('click', function(event) {
                const isDropdownButton = event.target.closest('button') &&
                                         event.target.closest('button').onclick &&
                                         event.target.closest('button').onclick.toString().includes('toggleDropdown');

                if (!isDropdownButton && !event.target.closest('[id^="dropdown-"]')) {
                    document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
                        d.style.display = 'none';
                    });
                }
            });
        """),
        cls="pb-4 pt-2 bg-white"
    )

    return Div(
        header,
        Div(compliance_dashboard, cls="flex-grow overflow-y-auto [scrollbar-width:none]"),
        final_decision_area,
        id="ev-center-panel",
        cls="flex flex-col h-full bg-white"
    )