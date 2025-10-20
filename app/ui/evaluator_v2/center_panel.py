# app/ui/evaluator_v2/center_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import Dict, Optional, List
from ui.shared_components import LevelPill
from logic.models import ComplianceDashboardState, ComplianceCheck

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
    
    button_type = "submit" if icon_name == "send" else "button"
    
    return Button(
        UkIcon(icon_name, cls="w-4 h-4"),
        Span(label_text, cls="hidden sm:inline"),
        cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')}",
        type=button_type,
        **kwargs
    )

def DropdownContextButton(
    icon_name: str,
    label_text: str,
    dropdown_options: dict, 
    name: str, # NEW: Added name parameter
    color: Optional[str] = None,
    **kwargs
) -> FT:
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

    # --- THE FIX: Use the dynamic 'name' parameter for the hidden input ---
    hidden_input = Input(type="hidden", id=f"hidden-{button_id}", name=name, value="")

    return Div(
        hidden_input,
        Button(
            UkIcon(icon_name, cls="w-4 h-4"),
            Span(label_text, cls="hidden sm:inline"),
            id=button_id,
            data_original_text=label_text,
            type="button",
            cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')} border-r border-gray-300",
            style="border-radius: 9999px 0 0 9999px; border-right: 1px solid #d1d5db;"
        ),
        Button(
            UkIcon("chevron-down", cls="w-3 h-3"),
            onclick=f"toggleDropdown('{dropdown_id}')",
            type="button",
            cls=f"{base_classes} {style_classes} px-2",
            style="border-radius: 0 9999px 9999px 0; margin-left: -1px;"
        ),
        Div(
            *[Button(
                text,
                onclick=f"selectDropdownOption('{button_id}', '{text}', '{value}')",
                type="button",
                cls="block w-full text-left px-3 py-2 text-sm hover:bg-base-300",
                style="border: none; background: none;"
            ) for value, text in dropdown_options.items()],
            id=dropdown_id,
            cls=("absolute bottom-full left-0 mb-1 bg-base-200 border border-base-300 "
                 "rounded-xl shadow-lg z-50 w-auto whitespace-nowrap overflow-hidden"),
            style="display: none;"
        ),
        cls="relative inline-flex",
        **kwargs
    )

def render_compliance_section(title: str, icon_name: str, check: ComplianceCheck):
    """Renders a single compliance section based on the ComplianceCheck state."""
    
    if not check.is_relevant:
        style_cls = "border-gray-300 opacity-50"
        status_icon = UkIcon("minus", cls="w-5 h-5 text-gray-500")
        status_text = "Ei ole selle paketi puhul asjakohane"
    else:
        style_cls = "border-green-500" if check.is_met else "border-red-500"
        status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if check.is_met else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
        status_text = f"Nõue: {check.required}, Esitatud: {check.provided}"

    return Details(
        Summary(
            Div(
                Div(cls=f"w-1.5 h-full absolute left-0 top-0 bg-{style_cls.split('-')[1]}-500"),
                UkIcon(icon_name, cls="w-5 h-5"),
                H5(title, cls="font-semibold"),
                status_icon,
                Span(status_text, cls="text-sm text-gray-500 truncate"),
                UkIcon("chevron-down", cls="accordion-marker ml-auto"),
                cls="flex items-center gap-x-3 w-full cursor-pointer p-3 relative"
            )
        ),
        Div(
            P(check.evaluator_comment or "Hindaja kommentaarid...", cls="text-sm p-4 border-t italic text-gray-600"),
        ),
        open=not check.is_met and check.is_relevant,
        cls=f"border {style_cls} rounded-lg"
    )

def render_compliance_dashboard(state: ComplianceDashboardState) -> FT:
    """Renders only the compliance dashboard part of the UI."""
    if state.overall_met:
        header = H3(f"Vastab tingimustele (Variant: {state.package_id})", cls="text-lg font-semibold text-green-700 p-2 bg-green-50 rounded-md text-center")
    else:
        header = H3(f"Tingimused ei ole täidetud (Variant: {state.package_id})", cls="text-lg font-semibold text-red-700 p-2 bg-red-50 rounded-md text-center")

    return Div(
        header,
        render_compliance_section("Haridus", "book-open", state.education),
        render_compliance_section("Töökogemus kokku", "briefcase", state.total_experience),
        render_compliance_section("Vastav töökogemus", "target", state.matching_experience),
        render_compliance_section("Baaskoolitus", "award", state.base_training),
        render_compliance_section("Tingimuslik baaskoolitus", "alert-triangle", state.conditional_training),
        render_compliance_section("Ehitusjuhi baaskoolitus", "award", state.manager_training),
        render_compliance_section("Täiendkoolitus", "award", state.cpd_training),
        cls="p-4 space-y-4"
    )

def render_center_panel(qual_data: Dict, user_data: Dict, state: ComplianceDashboardState) -> FT:
    applicant_name = user_data.get('full_name', 'N/A')
    qual_level = qual_data.get('level', '')
    qual_name = qual_data.get('qualification_name', '')
    specialisations = qual_data.get('specialisations', [])
    selected_count = qual_data.get('selected_specialisations_count', len(specialisations))
    total_count = qual_data.get('total_specialisations', len(specialisations))
    qual_id = qual_data.get('qual_id', '') 

    header = Details(
        Summary( Div(
            LevelPill(qual_level),
            Div( H2(applicant_name, cls="text-xl font-bold overflow-hidden text-ellipsis whitespace-nowrap"),
                P("·", cls="text-gray-400 whitespace-nowrap mx-1"),
                P(f"{qual_name}", cls="text-sm text-gray-700 flex-auto min-w-0 break-words whitespace-normal"),
                cls="flex flex-wrap items-baseline gap-y-0 min-w-0" ),
            DivHStacked(
                P("Spetsialiseerumised", cls="text-xs"),
                P(f"({selected_count}/{total_count})", cls="text-xs font-bold text-gray-600 whitespace-nowrap ml-1"),
                UkIcon("chevron-down", cls="accordion-marker"),
                cls="justify-self-end flex items-center" ),
            cls="grid grid-cols-[auto,1fr,auto] items-center gap-x-3" ),
            cls="list-none cursor-pointer col-span-3" ),
        Div( Ul(*[Li(s) for s in specialisations], cls="list-disc list-inside text-xs text-gray-700"),
            cls="col-start-2 ml-4 mt-2" ),
        open=False,
        cls="border-b bg-gray-50 sticky top-0 z-10 grid grid-cols-[auto,1fr,auto] gap-x-3"
    )

    compliance_dashboard = render_compliance_dashboard(state)

    education_dropdown_options = {
        "": "Tühista valik", "keskharidus": "Keskharidus",
        "ehitustehniline_keskeriharidus": "Ehitustehniline keskeriharidus",
        "vastav_kõrgharidus_180_eap": "Vastav Bakalaureus (180 EAP)",
        "vastav_kõrgharidus_240_eap": "Vastav Rakenduskõrgharidus (240 EAP)",
        "vastav_kõrgharidus_300_eap": "Vastav Magister (300 EAP)",
        "mittevastav_kõrgharidus_180_eap": "Mittevastav Bakalaureus (180 EAP)",
        "tehniline_kõrgharidus_300_eap": "Tehniline Magister (300 EAP)",
    }
    
    final_decision_area = Form(
        Div(
            Div(
                Textarea(
                    placeholder="Vali kontekst ja sisesta kommentaar või põhjendus...",
                    rows=3,
                    cls="textarea w-full resize-none border-0 focus:outline-none focus:ring-0"
                ),
                Div(
                    Div(
                        DropdownContextButton(
                            icon_name="book-open",
                            label_text="Haridus",
                            dropdown_options=education_dropdown_options,
                            name="education_level" # Assign the correct name
                        ),
                        Label(
                            CheckboxX(id="education_old_or_foreign", name="education_old_or_foreign"),
                            Span(">10a / välisriik", cls="text-xs ml-1"),
                            cls="flex items-center p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer"
                        ),
                        ContextButton(icon_name="briefcase", label_text="Töökogemus"),
                        ContextButton(icon_name="award", label_text="Täiendkoolitus"),
                        DropdownContextButton(
                            icon_name="list-checks",
                            label_text="Otsus",
                            dropdown_options={"Anda": "Anda", "Mitte anda": "Mitte anda"},
                            name="final_decision" # Assign the correct name
                        ),
                        cls="flex flex-wrap items-center gap-x-2"
                    ),
                    ContextButton(icon_name="send", label_text=""),
                    cls="flex flex-wrap items-center justify-between gap-x-2 p-2 bg-base-100 rounded-b-lg"
                ),
                cls="border-2 rounded-lg shadow-lg"
            ),
            cls="px-4 "
        ),
        hx_post=f"/evaluator/d/re-evaluate/{qual_id}",
        hx_trigger="change delay:500ms",
        hx_target="#compliance-dashboard-container",
        hx_swap="innerHTML",
        cls="pb-4 pt-2 bg-white"
    )

    return Div(
        header,
        Div(compliance_dashboard, id="compliance-dashboard-container", cls="flex-grow overflow-y-auto [scrollbar-width:none]"),
        final_decision_area,
        Script("""
            let buttonStates = {};

            function toggleButton(buttonId) {
                const button = document.getElementById(buttonId);
                if (!button) return;
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
                if (!dropdown) return;
                const isVisible = dropdown.style.display !== 'none';
                document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
                    if (d.id !== dropdownId) d.style.display = 'none';
                });
                dropdown.style.display = isVisible ? 'none' : 'block';
            }

            function selectDropdownOption(buttonId, optionText, optionValue) {
                const button = document.getElementById(buttonId);
                const span = button.querySelector('span');
                const hiddenInput = document.getElementById(`hidden-${buttonId}`);
                if (!button || !span || !hiddenInput) return;

                hiddenInput.value = optionValue;

                button.classList.remove('bg-transparent', 'bg-red-100', 'text-red-800', 'bg-green-100', 'text-green-800', 'bg-blue-100', 'text-blue-800');

                if (optionValue === "") {
                    span.textContent = button.dataset.originalText; 
                    button.classList.add('bg-transparent'); 
                    buttonStates[buttonId] = false;
                } else {
                    span.textContent = optionText;

                    if (buttonId === 'btn-otsus') {
                        if (optionText === 'Anda') {
                            button.classList.add('bg-green-100', 'text-green-800');
                        } else if (optionText === 'Mitte anda') {
                            button.classList.add('bg-red-100', 'text-red-800');
                        }
                    } else {
                        button.classList.add('bg-blue-100', 'text-blue-800');
                    }
                    buttonStates[buttonId] = true;
                }

                const dropdownId = buttonId.replace('btn-', 'dropdown-');
                const dropdown = document.getElementById(dropdownId);
                if(dropdown) dropdown.style.display = 'none';
                
                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
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
        id="ev-center-panel",
        cls="flex flex-col h-full bg-white"
    )