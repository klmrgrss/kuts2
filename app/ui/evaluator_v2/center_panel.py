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
    icon_name: Optional[str],
    label_text: str,
    dropdown_options: dict,
    name: str,
    color: Optional[str] = None,
    current_value: Optional[str] = None,
    **kwargs
) -> FT:
    button_id = f"btn-{name}"
    dropdown_id = f"dropdown-{name}"

    color_map = {
        'green': "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800",
        'red': "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800",
        'blue': "bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800",
    }
    base_classes = (
        "inline-flex items-center justify-center "
        "h-8 px-3 "
        "gap-x-2 "
        "rounded-full "
        "text-sm font-bold normal-case "
        "transition-colors duration-150"
    )
    default_style_classes = color_map[color] if color in color_map else "bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700"

    resolved_value = current_value or ""
    if resolved_value and resolved_value not in dropdown_options:
        resolved_value = ""

    selected_label = None
    if resolved_value in dropdown_options:
        selected_label = dropdown_options[resolved_value]
        if resolved_value == "" and selected_label and selected_label.casefold() in {"tühista valik"}:
            selected_label = None

    highlight_color = None
    if resolved_value:
        if name == "final_decision":
            if resolved_value == "Anda":
                highlight_color = 'green'
            elif resolved_value == "Mitte anda":
                highlight_color = 'red'
        else:
            highlight_color = 'blue'

    style_classes = color_map.get(highlight_color, default_style_classes)

    hidden_input = Input(
        type="hidden",
        id=f"hidden-{button_id}",
        name=name,
        value=resolved_value
    )

    button_children = []
    if icon_name:
        button_children.append(UkIcon(icon_name, cls="w-4 h-4"))
    button_children.append(Span(selected_label or label_text, cls="hidden sm:inline"))
    button_children.append(UkIcon("chevron-down", cls="w-3 h-3 ml-1"))

    return Div(
        hidden_input,
        Button(
            *button_children,
            id=button_id,
            data_original_text=label_text,
            onclick=f"toggleDropdown('{dropdown_id}')",
            type="button",
            cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')}"
        ),
        Div(
            *[Button(
                text,
                onclick=f"selectDropdownOption('{button_id}', '{text}', '{value}')",
                type="button",
                cls=(
                    "block w-full text-left px-3 py-2 text-sm hover:bg-base-300 "
                    "{}".format(
                        "font-semibold bg-base-300 dark:bg-base-200" if resolved_value == value else ""
                    )
                ).strip(),
                style="border: none; background: none;",
                data_value=value,
            ) for value, text in dropdown_options.items()],
            id=dropdown_id,
            cls=("absolute bottom-full left-0 mb-1 bg-base-200 border border-base-300 "
                 "rounded-xl shadow-lg z-50 w-auto whitespace-nowrap overflow-hidden"),
            style="display: none;"
        ),
        cls="relative inline-flex",
        **kwargs
    )

def render_compliance_subsection(title: str, check: ComplianceCheck):
    """Renders a subsection within a main compliance category."""
    if not check.is_relevant:
        return None  # Don't render irrelevant subsections

    status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if check.is_met else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
    status_text = f"Nõue: {check.required}, Esitatud: {check.provided}"

    return Div(
        status_icon,
        Div(
            P(title, cls="font-semibold text-sm"),
            P(status_text, cls="text-xs text-gray-500")
        ),
        cls="flex items-center gap-x-3 px-3 py-2"
    )

def render_compliance_section(title: str, icon_name: str, subsections: List[FT], all_checks: List[ComplianceCheck], context_name: str, comment: Optional[str]):
    """
    Renders a main compliance category with its subsections and a read-only comment area.
    """
    relevant_checks = [c for c in all_checks if c.is_relevant]
    if not relevant_checks and context_name != "otsus": # "Otsus" is always relevant
        style_cls = "border-gray-300 opacity-50"
        status_icon = UkIcon("minus", cls="w-5 h-5 text-gray-500")
        status_text = "Ei ole selle paketi puhul asjakohane"
        is_open = False
    else:
        all_met = all(c.is_met for c in relevant_checks) if relevant_checks else True
        style_cls = "border-green-500" if all_met else "border-red-500"
        status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if all_met else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
        status_text = f"{len([c for c in relevant_checks if c.is_met])}/{len(relevant_checks)} alapunkti täidetud" if relevant_checks else "Otsus"
        is_open = not all_met

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
            *subsections,
            P(
                comment or "Kommentaarid...", 
                id=f"comment-display-{context_name}",
                data_comment=comment or "", # Store comment for JS
                cls="text-sm p-4 border-t italic text-gray-600 min-h-[4rem]"
            ),
            cls="p-3 border-t bg-gray-50"
        ),
        open=is_open,
        cls=f"border {style_cls} rounded-lg",
        data_context=context_name
    )

def render_compliance_dashboard(state: ComplianceDashboardState) -> FT:
    """Renders the compliance dashboard with four main, grouped sections."""
    if state.overall_met:
        header = H3(f"Vastab tingimustele (Variant: {state.package_id})", cls="text-lg font-semibold text-green-700 p-2 bg-green-50 rounded-md text-center")
    else:
        header = H3(f"Tingimused ei ole täidetud (Variant: {state.package_id})", cls="text-lg font-semibold text-red-700 p-2 bg-red-50 rounded-md text-center")

    education_subsections = [s for s in [render_compliance_subsection("Haridustase", state.education)] if s]
    experience_subsections = [s for s in [
        render_compliance_subsection("Töökogemus kokku", state.total_experience),
        render_compliance_subsection("Vastav töökogemus", state.matching_experience)
    ] if s]
    training_subsections = [s for s in [
        render_compliance_subsection("Baaskoolitus", state.base_training),
        render_compliance_subsection("Tingimuslik baaskoolitus", state.conditional_training),
        render_compliance_subsection("Ehitusjuhi baaskoolitus", state.manager_training),
        render_compliance_subsection("Täiendkoolitus (taastõendamisel)", state.cpd_training)
    ] if s]

    return Div(
        header,
        render_compliance_section("Haridus", "book-open", education_subsections, [state.education], "haridus", state.haridus_comment),
        render_compliance_section("Töökogemus", "briefcase", experience_subsections, [state.total_experience, state.matching_experience], "tookogemus", state.tookogemus_comment),
        render_compliance_section("Koolitus", "award", training_subsections, [state.base_training, state.conditional_training, state.manager_training, state.cpd_training], "koolitus", state.koolitus_comment),
        render_compliance_section("Otsus", "list-checks", [], [], "otsus", state.otsus_comment),
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

    education_current_value = state.education.provided or ""
    education_old_or_foreign_value = ""
    if hasattr(state, "education_old_or_foreign"):
        education_old_or_foreign_value = "on" if getattr(state, "education_old_or_foreign") else ""
    elif state.conditional_training.is_relevant:
        education_old_or_foreign_value = "on"

    final_decision_value = getattr(state, "final_decision", "")
    
    final_decision_area = Form(
        Input(type="hidden", name="active_context", id="active-context-input"),
        Div(
            Div(
                Textarea(
                    name="main_comment",
                    id="main-comment-textarea",
                    placeholder="Vali kontekst ja sisesta kommentaar või põhjendus...",
                    rows=3,
                    cls="textarea w-full resize-none border-0 focus:outline-none focus:ring-0"
                ),
                Div(
                    Div(
                        # Redesigned Haridus Button
                        Div(
                            DropdownContextButton(
                                icon_name=None, label_text=">10a / välis",
                                dropdown_options={"on": "Jah", "": "Ei"}, name="education_old_or_foreign",
                                data_context="haridus",
                                current_value=education_old_or_foreign_value
                            ),
                            DropdownContextButton(
                                icon_name="book-open", label_text="Haridus",
                                dropdown_options=education_dropdown_options, name="education_level",
                                data_context="haridus",
                                current_value=education_current_value
                            ),
                            cls="flex items-center"
                        ),
                        ContextButton(icon_name="briefcase", label_text="Töökogemus", data_context="tookogemus"),
                        ContextButton(icon_name="award", label_text="Täiendkoolitus", data_context="koolitus"),
                        DropdownContextButton(
                            icon_name="list-checks", label_text="Otsus",
                            dropdown_options={"Anda": "Anda", "Mitte anda": "Mitte anda"}, name="final_decision",
                            data_context="otsus",
                            current_value=final_decision_value
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
        id="final-decision-area",
        hx_post=f"/evaluator/d/re-evaluate/{qual_id}",
        hx_trigger="change delay:500ms, keyup delay:500ms from:#main-comment-textarea",
        hx_target="#compliance-dashboard-container",
        hx_swap="innerHTML",
        cls="pb-4 pt-2 bg-white"
    )

    return Div(
        header,
        Div(compliance_dashboard, id="compliance-dashboard-container", cls="flex-grow overflow-y-auto [scrollbar-width:none]"),
        final_decision_area,
        Script("""
            let activeContext = { current: null };
            const mainCommentBox = document.getElementById('main-comment-textarea');
            const activeContextInput = document.getElementById('active-context-input');

            function loadCommentForActiveContext() {
                if (!mainCommentBox) return;
                if (activeContext.current) {
                    const commentDisplay = document.getElementById(`comment-display-${activeContext.current}`);
                    mainCommentBox.value = commentDisplay ? commentDisplay.dataset.comment : '';
                } else {
                    mainCommentBox.value = '';
                }
            }

            function setActiveContext(contextName) {
                if (activeContext.current === contextName) contextName = null;
                activeContext.current = contextName;
                if (activeContextInput) activeContextInput.value = contextName || '';
                console.log('Active context:', activeContext.current);

                document.querySelectorAll('#compliance-dashboard-container [data-context]').forEach(el => {
                    el.classList.toggle('ring-2', el.dataset.context === contextName);
                    el.classList.toggle('ring-blue-500', el.dataset.context === contextName);
                    el.classList.toggle('shadow-lg', el.dataset.context === contextName);
                });

                document.querySelectorAll('#final-decision-area [data-context]').forEach(el => {
                    const interactiveEl = el.closest('div.relative') || el.closest('button');
                    interactiveEl.classList.toggle('bg-blue-100', el.dataset.context === contextName);
                    interactiveEl.classList.toggle('dark:bg-blue-900', el.dataset.context === contextName);
                });
                loadCommentForActiveContext();
            }
            
            function initContextHighlighting() {
                const container = document.getElementById('compliance-dashboard-container');
                if (container) container.addEventListener('click', e => {
                    const section = e.target.closest('[data-context]');
                    if (section) setActiveContext(section.dataset.context);
                });
                
                const toolbox = document.getElementById('final-decision-area');
                if (toolbox) toolbox.addEventListener('click', e => {
                    const button = e.target.closest('[data-context]');
                    if (button) setActiveContext(button.dataset.context);
                });
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
                const span = button ? button.querySelector('span') : null;
                const hiddenInput = document.getElementById(`hidden-${buttonId}`);
                if (!button || !span || !hiddenInput) return;

                hiddenInput.value = optionValue;

                const defaultClasses = ['bg-transparent', 'hover:bg-gray-200', 'dark:hover:bg-gray-700'];
                const blueClasses = ['bg-blue-100', 'text-blue-800', 'hover:bg-blue-200', 'dark:bg-blue-900', 'dark:text-blue-200', 'dark:hover:bg-blue-800'];
                const greenClasses = ['bg-green-100', 'text-green-800', 'hover:bg-green-200', 'dark:bg-green-900', 'dark:text-green-200', 'dark:hover:bg-green-800'];
                const redClasses = ['bg-red-100', 'text-red-800', 'hover:bg-red-200', 'dark:bg-red-900', 'dark:text-red-200', 'dark:hover:bg-red-800'];

                button.classList.remove(
                    ...defaultClasses,
                    ...blueClasses,
                    ...greenClasses,
                    ...redClasses
                );

                let appliedClasses = [];

                if (!optionValue) {
                    span.textContent = button.dataset.originalText;
                    appliedClasses = defaultClasses;
                } else {
                    span.textContent = optionText;
                    if (buttonId.includes('final_decision')) {
                        appliedClasses = optionValue === 'Anda' ? greenClasses : redClasses;
                    } else {
                        appliedClasses = blueClasses;
                    }
                }

                if (appliedClasses.length) {
                    button.classList.add(...appliedClasses);
                }

                const dropdownId = buttonId.replace('btn-', 'dropdown-');
                const dropdown = document.getElementById(dropdownId);
                if (dropdown) {
                    dropdown.querySelectorAll('button[data-value]').forEach(optionButton => {
                        const isSelected = optionButton.dataset.value === optionValue;
                        optionButton.classList.toggle('bg-base-300', isSelected);
                        optionButton.classList.toggle('dark:bg-base-200', isSelected);
                        optionButton.classList.toggle('font-semibold', isSelected);
                    });
                    dropdown.style.display = 'none';
                }

                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            }

            document.addEventListener('click', function(event) {
                const isDropdownButton = event.target.closest('button[onclick*="toggleDropdown"]');
                if (!isDropdownButton && !event.target.closest('[id^="dropdown-"]')) {
                    document.querySelectorAll('[id^="dropdown-"]').forEach(d => d.style.display = 'none');
                }
            });

            initContextHighlighting();
        """),
        id="ev-center-panel",
        cls="flex flex-col h-full bg-white"
    )