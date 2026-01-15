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

    data_context = kwargs.pop('data_context', None)
    data_attributes = {'data-context': data_context} if data_context else {}

    return Button(
        UkIcon(icon_name, cls="w-4 h-4"),
        Span(label_text, cls="hidden sm:inline"),
        cls=f"{base_classes} {style_classes} {kwargs.pop('cls', '')}",
        type=button_type,
        **data_attributes,
        **kwargs
    )

def DropdownContextButton(
    icon_name: Optional[str],
    label_text: str,
    dropdown_options: dict,
    name: str,
    color: Optional[str] = None,
    current_value: Optional[str] = None,
    display_mode: str = "default",
    title_text: Optional[str] = None,
    placeholder_text: Optional[str] = None,
    rounded: bool = True,
    button_cls: str = "",
    wrapper_cls: str = "",
    **kwargs
) -> FT:
    button_id = f"btn-{name}"
    dropdown_id = f"dropdown-{name}"

    color_map = {
        'green': "bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800",
        'red': "bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800",
        'blue': "bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800",
    }

    base_classes = [
        "inline-flex",
        "gap-x-2",
        "transition-colors",
        "duration-150",
        "text-sm",
        "font-bold",
        "normal-case",
    ]

    if display_mode == "stacked":
        base_classes.extend([
            "items-start",
            "justify-between",
            "px-4",
            "py-2",
            "w-full",
            "text-left",
            "min-h-[3.25rem]",
            "leading-tight",
        ])
    else:
        base_classes.extend([
            "items-center",
            "justify-center",
            "h-8",
            "px-3",
        ])

    if rounded:
        base_classes.append("rounded-full")

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
            elif resolved_value == "Täiendav tegevus":
                highlight_color = 'blue'
        else:
            highlight_color = 'blue'

    style_classes = color_map.get(highlight_color, default_style_classes)

    hidden_input = Input(
        type="hidden",
        id=f"hidden-{button_id}",
        name=name,
        value=resolved_value
    )

    placeholder = placeholder_text or label_text
    display_value = selected_label or placeholder

    button_children: List[FT] = []

    if display_mode == "stacked":
        title_content = title_text or label_text
        button_children.append(
            Div(
                Span(
                    title_content,
                    cls="text-[11px] font-semibold uppercase text-gray-500 tracking-wide"
                ),
                Span(
                    display_value,
                    cls="text-sm font-semibold text-gray-900",
                    data_role="dropdown-value"
                ),
                cls="flex flex-col items-start gap-y-0.5"
            )
        )
        button_children.append(UkIcon("chevron-down", cls="w-3 h-3 ml-2 mt-0.5"))
    else:
        if icon_name:
            button_children.append(UkIcon(icon_name, cls="w-4 h-4"))
        button_children.append(
            Span(display_value, cls="hidden sm:inline", data_role="dropdown-value")
        )
        button_children.append(UkIcon("chevron-down", cls="w-3 h-3 ml-1"))

    data_context = kwargs.pop('data_context', None)
    data_attributes = {'data-context': data_context} if data_context else {}

    button_class = " ".join(base_classes + [style_classes, button_cls]).strip()

    wrapper_base_cls = "relative flex" if display_mode == "stacked" else "relative inline-flex"
    if wrapper_cls:
        wrapper_base_cls = f"{wrapper_base_cls} {wrapper_cls}".strip()

    return Div(
        hidden_input,
        Button(
            *button_children,
            id=button_id,
            data_original_text=label_text,
            data_placeholder_text=placeholder,
            onclick=f"toggleDropdown('{dropdown_id}')",
            type="button",
            cls=button_class
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
            style="display: none;",
        ),
        cls=wrapper_base_cls,
        **data_attributes,
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

def render_compliance_section(title: str, icon_name: str, subsections: List[FT], all_checks: List[ComplianceCheck], context_name: str, comment: Optional[str], decision: Optional[str] = None):
    """Renders a main compliance category with its subsections and a read-only comment area."""

    relevant_checks = [c for c in all_checks if c.is_relevant]
    if not relevant_checks and context_name != "otsus":  # "Otsus" is always relevant
        border_cls = "border-gray-300 opacity-50"
        accent_bar_cls = "bg-gray-300"
        status_icon = UkIcon("minus", cls="w-5 h-5 text-gray-500")
        status_text = "Ei ole selle paketi puhul asjakohane"
    else:
        all_met = all(c.is_met for c in relevant_checks) if relevant_checks else True
        border_cls = "border-green-500" if all_met else "border-red-500"
        accent_bar_cls = "bg-green-500" if all_met else "bg-red-500"
        status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if all_met else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
        status_text = (
            f"{len([c for c in relevant_checks if c.is_met])}/{len(relevant_checks)} alapunkti täidetud"
            if relevant_checks else "Otsus"
        )

    if context_name == "otsus":
        decision_display = decision or "Otsus valimata"
        if decision:
            decision_display = f"Otsus: {decision}"
        status_text = decision_display
        if decision == "Anda":
            border_cls = "border-green-500"
            accent_bar_cls = "bg-green-500"
            status_icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500")
        elif decision == "Mitte anda":
            border_cls = "border-red-500"
            accent_bar_cls = "bg-red-500"
            status_icon = UkIcon("shield-off", cls="w-5 h-5 text-red-500")
        elif decision == "Täiendav tegevus":
            border_cls = "border-blue-500"
            accent_bar_cls = "bg-blue-500"
            status_icon = UkIcon("shield-check", cls="w-5 h-5 text-blue-500")
        else:
            border_cls = "border-gray-300"
            accent_bar_cls = "bg-gray-300"
            status_icon = UkIcon("minus", cls="w-5 h-5 text-gray-500")

    header = Div(
        Div(cls=f"w-1.5 h-full absolute left-0 top-0 {accent_bar_cls}"),
        UkIcon(icon_name, cls="w-5 h-5"),
        H5(title, cls="font-semibold"),
        status_icon,
        Span(status_text, cls="text-sm text-gray-500 truncate"),
        cls="flex items-center gap-x-3 w-full p-3 relative bg-white rounded-t-lg"
    )

    body = Div(
        *subsections,
        P(
            comment or "Kommentaarid...",
            id=f"comment-display-{context_name}",
            data_comment=comment or "",  # Store comment for JS
            cls="text-sm p-4 border-t italic text-gray-600 min-h-[4rem]"
        ),
        cls="p-3 border-t bg-gray-50 space-y-2"
    )

    return Div(
        header,
        body,
        cls=f"border {border_cls} rounded-lg overflow-hidden bg-white",
        data_context=context_name
    )

from ui.evaluator_v2.application_list import get_safe_dom_id

def render_compliance_dashboard(state: ComplianceDashboardState, qual_id: str = "") -> FT:
    """Renders the main compliance dashboard. qual_id is used for client-side script targeting."""
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
        render_compliance_section("Otsus", "list-checks", [], [], "otsus", state.otsus_comment, state.final_decision),
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
                UkIcon("chevron-down", cls="w-4 h-4 text-gray-500"),
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

    haridus_split_control = Div(
        DropdownContextButton(
            icon_name=None,
            label_text="Vali",
            dropdown_options=education_dropdown_options,
            name="education_level",
            current_value=education_current_value,
            display_mode="stacked",
            title_text="Haridus",
            placeholder_text="Vali",
            rounded=False,
            button_cls="items-start",
            wrapper_cls="flex-1"
        ),
        Div(cls="w-px bg-base-300 self-stretch"),
        DropdownContextButton(
            icon_name=None,
            label_text="Ei",
            dropdown_options={"on": "Jah", "": "Ei"},
            name="education_old_or_foreign",
            current_value=education_old_or_foreign_value,
            display_mode="stacked",
            title_text=">10/F",
            placeholder_text="Ei",
            rounded=False,
            button_cls="items-start",
            wrapper_cls="flex min-w-[7rem]"
        ),
        data_context="haridus",
        cls="flex items-stretch rounded-full border border-base-300 bg-white shadow-sm"
    )

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
                        haridus_split_control,
                        ContextButton(icon_name="briefcase", label_text="Töökogemus", data_context="tookogemus"),
                        ContextButton(icon_name="award", label_text="Täiendkoolitus", data_context="koolitus"),
                        DropdownContextButton(
                            icon_name="list-checks", label_text="Otsus",
                            dropdown_options={"Anda": "Anda", "Mitte anda": "Mitte anda", "Täiendav tegevus": "Täiendav tegevus"}, name="final_decision",
                            data_context="otsus",
                            current_value=final_decision_value,
                            placeholder_text="Vali otsus"
                        ),
                        cls="flex flex-wrap items-center gap-2"
                    ),
                    # --- Client-Side Icon Updater Script ---
                    # Uses the qual_id to find the safe DOM ID and updates the icon class immediately
                    Script(f"""
                        document.addEventListener('submit', function(e) {{
                            if (e.target && e.target.matches('form[hx-post$="/re-evaluate"]')) {{
                                const formData = new FormData(e.target);
                                const decision = formData.get('final_decision');
                                const safeId = "{get_safe_dom_id(qual_id) if qual_id else ''}";
                                if (!safeId) return;

                                const listItem = document.getElementById(safeId);
                                if (!listItem) return;

                                const iconContainer = listItem.querySelector('div.flex.items-center.justify-center');
                                if (!iconContainer) return;
                                
                                // Reset classes
                                iconContainer.innerHTML = '';
                                let newIcon = '';
                                let newClass = 'w-5 h-5 ';

                                if (decision === 'Anda') {{
                                    newIcon = 'shield-check';
                                    newClass += 'text-green-500';
                                }} else if (decision === 'Mitte anda') {{
                                    newIcon = 'shield-off';
                                    newClass += 'text-red-500';
                                }} else if (decision === 'Täiendav tegevus') {{
                                    newIcon = 'shield-check';
                                    newClass += 'text-blue-500';
                                }} else {{
                                    newIcon = 'shield';
                                    newClass += 'text-gray-200';
                                }}
                                
                                // Create new icon (using UIkit or SVG structure directly if needed, but innerHTML is easiest for mock)
                                // Since UkIcon renders an svg/img/span, we interpret it roughly. 
                                // For UkIcon to work dynamically we might need to trigger UIKit update, 
                                // but swapping the innerHTML with a known SVG or just text class is faster.
                                // We will rely on OOB for perfect SVG, this is "optimistic" and "post-submit" feedback.
                                // Actually, let's just update the class of the existing SVG if it exists, or wait for OOB.
                                // But OOB is failing. 
                                // Let's try to set the generic UK-icon attribute and let UIkit re-parse if possible, 
                                // OR manually inject the SVG roughly. All shields look similar, color is key.
                                
                                // Simple approach: Change color class of the existing element
                                const existingIcon = iconContainer.querySelector('[uk-icon], svg, span');
                                
                                if (existingIcon) {{
                                    existingIcon.classList.remove('text-gray-200', 'text-gray-400', 'text-green-500', 'text-red-500', 'text-blue-500');
                                    // Extract color from newClass
                                    const colorCls = newClass.split(' ').pop(); 
                                    existingIcon.classList.add(colorCls);
                                    
                                    // Force icon shape change
                                    existingIcon.setAttribute('uk-icon', newIcon);
                                    
                                    // Manually clear and reinject SVG for immediate feedback if UIkit doesn't observe attributes
                                    // This is a robust fallback for "optimistic" UI
                                    if (window.UIkit && window.UIkit.icon) {{
                                       window.UIkit.icon(existingIcon, {{icon: newIcon}});
                                    }}
                                }}
                            }}
                        }});
                    """),
                    ContextButton(icon_name="send", label_text=""),
                    cls="flex flex-wrap items-center justify-between gap-x-2 p-2 bg-base-100 rounded-b-lg"
                ),
                cls="border-2 rounded-lg shadow-lg"
            ),
            cls="px-4 "
        ),
        id="final-decision-area",
        hx_post=f"/evaluator/d/re-evaluate/{qual_id}",
        hx_trigger="submit, change",
        hx_target="#compliance-dashboard-container",
        hx_swap="innerHTML",
        cls="pb-4 pt-2 bg-white"
    )

    return Div(
        header,
        Div(compliance_dashboard, id="compliance-dashboard-container", cls="flex-grow overflow-y-auto [scrollbar-width:none]"),
        final_decision_area,
        Script("""
            (function() {
                window.toggleDropdown = function(dropdownId) {
                    const dropdown = document.getElementById(dropdownId);
                    if (!dropdown) return;
                    const isVisible = dropdown.style.display !== 'none';
                    document.querySelectorAll('[id^="dropdown-"]').forEach(d => {
                        if (d.id !== dropdownId) d.style.display = 'none';
                    });
                    dropdown.style.display = isVisible ? 'none' : 'block';
                };

                window.selectDropdownOption = function(buttonId, optionText, optionValue) {
                    const button = document.getElementById(buttonId);
                    const valueSpan = button ? button.querySelector('[data-role="dropdown-value"]') : null;
                    const hiddenInput = document.getElementById(`hidden-${buttonId}`);
                    if (!button || !valueSpan || !hiddenInput) return;

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
                    const placeholderText = button.dataset.placeholderText || button.dataset.originalText || '';

                    if (!optionValue) {
                        valueSpan.textContent = placeholderText;
                        appliedClasses = defaultClasses;
                    } else {
                        valueSpan.textContent = optionText;
                        if (buttonId.includes('final_decision')) {
                            if (optionValue === 'Anda') appliedClasses = greenClasses;
                            else if (optionValue === 'Mitte anda') appliedClasses = redClasses;
                            else if (optionValue === 'Täiendav tegevus') appliedClasses = blueClasses;
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
                };

                const dashboard = window.evDashboard || {
                    currentContext: null,
                    getMainCommentBox() {
                        return document.getElementById('main-comment-textarea');
                    },
                    getActiveContextInput() {
                        return document.getElementById('active-context-input');
                    },
                    setActiveContext(contextName) {
                        const input = this.getActiveContextInput();
                        if (this.currentContext === contextName) {
                            this.currentContext = null;
                            if (input) input.value = '';
                        } else {
                            this.currentContext = contextName;
                            if (input) input.value = contextName || '';
                        }
                        console.debug('Active context:', this.currentContext);
                        this.applyHighlights();
                        this.loadCommentForActiveContext();
                    },
                    applyHighlights() {
                        const contextName = this.currentContext;
                        document.querySelectorAll('#compliance-dashboard-container [data-context]').forEach(el => {
                            const isActive = !!contextName && el.dataset.context === contextName;
                            el.classList.toggle('ring-2', isActive);
                            el.classList.toggle('ring-blue-500', isActive);
                            el.classList.toggle('shadow-lg', isActive);
                        });

                        document.querySelectorAll('#final-decision-area [data-context]').forEach(el => {
                            const isActive = !!contextName && el.dataset.context === contextName;
                            if (el.matches('button')) {
                                ['bg-blue-100', 'dark:bg-blue-900', 'ring-2', 'ring-blue-500'].forEach(cls => {
                                    el.classList.toggle(cls, isActive);
                                });
                            } else {
                                ['ring-2', 'ring-blue-500', 'ring-offset-1', 'ring-offset-white', 'dark:ring-offset-slate-900', 'shadow-md'].forEach(cls => {
                                    el.classList.toggle(cls, isActive);
                                });
                            }
                        });
                    },
                    loadCommentForActiveContext() {
                        const textarea = this.getMainCommentBox();
                        if (!textarea) return;
                        if (!this.currentContext) {
                            textarea.value = '';
                            return;
                        }
                        const commentDisplay = document.getElementById(`comment-display-${this.currentContext}`);
                        textarea.value = commentDisplay ? (commentDisplay.dataset.comment || '') : '';
                    },
                    syncFromDom() {
                        const input = this.getActiveContextInput();
                        const initial = input && input.value ? input.value : null;
                        this.currentContext = initial;
                    }
                };

                dashboard.syncFromDom();
                dashboard.applyHighlights();
                dashboard.loadCommentForActiveContext();
                window.evDashboard = dashboard;

                const textarea = dashboard.getMainCommentBox();
                if (textarea && !textarea.dataset.contextBindingAttached) {
                    const ensureDecisionContext = () => {
                        if (!window.evDashboard.currentContext) {
                            window.evDashboard.setActiveContext('otsus');
                        }
                    };
                    textarea.addEventListener('focus', ensureDecisionContext);
                    textarea.addEventListener('input', ensureDecisionContext);
                    textarea.dataset.contextBindingAttached = 'true';
                }

                if (!window.evDashboardListenersAttached) {
                    document.addEventListener('click', function(event) {
                        const dashboardArea = document.getElementById('compliance-dashboard-container');
                        if (dashboardArea && dashboardArea.contains(event.target)) {
                            const section = event.target.closest('[data-context]');
                            if (section) {
                                window.evDashboard.setActiveContext(section.dataset.context);
                                return;
                            }
                        }

                        const toolbox = document.getElementById('final-decision-area');
                        if (toolbox && toolbox.contains(event.target)) {
                            const button = event.target.closest('[data-context]');
                            if (button) {
                                window.evDashboard.setActiveContext(button.dataset.context);
                            }
                        }
                    });

                    document.addEventListener('htmx:afterSwap', function(event) {
                        if (event.detail && event.detail.target && event.detail.target.id === 'compliance-dashboard-container') {
                            window.evDashboard.applyHighlights();
                            window.evDashboard.loadCommentForActiveContext();
                        }
                    });

                    document.addEventListener('click', function(event) {
                        const isDropdownButton = event.target.closest('button[onclick*="toggleDropdown"]');
                        if (!isDropdownButton && !event.target.closest('[id^="dropdown-"]')) {
                            document.querySelectorAll('[id^="dropdown-"]').forEach(d => d.style.display = 'none');
                        }
                    });

                    window.evDashboardListenersAttached = true;
                }
            })();
        """),
        id="ev-center-panel",
        cls="flex flex-col h-full bg-white"
    )