# app/ui/work_experience_view_v2.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Optional
from .custom_components import InputTag, StickyActionBar

def render_work_experience_form_v2(
    available_activities: List[str],
    experiences: List[dict] = None,
    experience: Optional[dict] = None,
    activity_counts: List[dict] = None,
    selected_activity: Optional[str] = None
):
    is_edit = experience is not None
    # A task is active if we are editing OR a new activity has been selected.
    is_task_active = is_edit or selected_activity is not None
    # The form is disabled if no task is active.
    is_form_disabled = not is_task_active

    form_wrapper_class = 'form-disabled' if is_form_disabled else ''
    initial_section_class = 'state-in-progress' if is_task_active else 'state-unfocused'

    exp_id = experience.get('id') if is_edit else None
    experience = experience or {}
    experiences = experiences or []

    # Use new v2 routes
    form_action = "/app/workex/save"
    cancel_action = "/app/workex" # Reloads the tab to reset state
    button_text = "Salvesta muudatused" if is_edit else "Kinnita ja lisa taotlusele"

    def val(key, default=''): return experience.get(key, default)

    # --- Activity Selection Box ---
    # This section is now for displaying activities and their existing experiences
    activity_strips = []
    for i, activity in enumerate(available_activities):
        # An activity is "in focus" if it's selected for a new item OR if we are editing an item belonging to it.
        is_activity_in_focus = (activity == selected_activity) or (is_edit and activity == experience.get('associated_activity'))

        activity_experiences = [exp for exp in experiences if exp.get('associated_activity') == activity]

        experience_chips = []
        for exp in activity_experiences:
            # Determine state for existing experiences
            exp_state = 'state-complete' if exp.get('work_description') and exp.get('object_address') else 'state-in-progress'

            # Check if the current link's experience is the one being edited
            is_being_edited = is_edit and exp.get('id') == experience.get('id')

            # Start with base classes
            link_classes = f"btn btn-sm {exp_state} border no-animation"
            # Conditionally add the 'activity-selected' class to the link itself for a double highlight effect
            if is_being_edited:
                link_classes += " activity-selected"

            experience_chips.append(
                A(
                    # Descriptive name as requested
                    f"{exp.get('start_date', '')} - {exp.get('object_address', 'Aadress puudub')}",
                    # This link now uses hx-get to reload the tab content, preventing scroll jumps
                    hx_get=f"/app/workex/{exp.get('id')}/edit",
                    hx_target="#tab-content-container",
                    hx_swap="innerHTML",
                    # Apply the combined classes
                    cls=link_classes
                )
            )

        # Add the "+ Lisa uus töökogemus" chip
        is_adding_new_in_this_activity = (activity == selected_activity) and not is_edit
        add_chip_classes = "btn btn-sm btn-outline border-dashed no-animation"
        if is_adding_new_in_this_activity:
            add_chip_classes += " activity-selected" # Sub-highlight for the add chip

        add_new_chip = A(
            "+ Lisa töökogemus",
            hx_get=f"/app/workex?activity={activity}",
            hx_target="#tab-content-container",
            hx_swap="innerHTML",
            cls=add_chip_classes
        )
        experience_chips.append(add_new_chip)


        # Apply the 'activity-selected' class to the container if it's active
        container_classes = f"p-2 rounded-lg bg-gray-50 dark:bg-gray-900 border-2 {'activity-selected' if is_activity_in_focus else 'border-transparent'}"

        activity_strips.append(
            Div(
                # The activity title
                H4(activity, cls="font-semibold text-md mb-1"),
                # List of existing experiences for this activity plus the add new chip
                Div(*experience_chips, cls="flex flex-row flex-wrap gap-2 mt-1 ml-2") if experience_chips else P("Selle tegevusala kohta pole töökogemusi lisatud.", cls="text-xs text-gray-500 mt-1"),
                cls=container_classes
            )
        )

    activity_selection_box = Div(
        #H3("1. Vali tegevusala või muuda olemasolevat kogemust", cls="text-xl font-semibold mb-4"),
        #P("Uue kogemuse lisamiseks vali tegevusala. Olemasoleva muutmiseks klõpsa selle kirjel.", cls="text-sm text-muted-foreground mb-6"),
        Div(id="form-guidance-message"), # Placeholder for the guidance message
        Div(*activity_strips, cls="space-y-2"),
        cls="mb-6"
    )

    # --- Explanatory text for the form ---
    form_intro_text = None
    if is_task_active:
        intro_title = f"MUUDA töökogemust: {val('start_date')} - {val('object_address')}" if is_edit else f"LISA UUS töökogemus tegevusalale: {selected_activity}"
        form_intro_text = Div(
            #H3("2. Sisesta andmed", cls="text-xl font-semibold mb-2"),
            Div(
                P(intro_title, cls="font-semibold"),
                Div(
                    UkIcon("chevron-down", cls="w-6 h-6"),
                    cls="flex justify-center"
                ),
                cls="p-2 bg-blue-100 text-blue-800 rounded-lg my-2 text-center"
            )
        )

    # --- Reusable Component Functions ---
    # Modified to accept the state class
    def SectionContainer(legend_text: str, *children, **kwargs):
        current_class = kwargs.pop('cls', '')
        return Div(
            Span(legend_text, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600"),
            *children,
            cls=f"relative mt-8 p-4 md:p-6 rounded-lg space-y-4 md:space-y-6 {initial_section_class} {current_class}",
            **kwargs
        )

    LABEL_CLASS = "font-semibold"
    INPUT_CLASS = "input input-bordered w-full input-sm"

    def StyledLabelInput(label, id, name, value, required=False, type="text", **kwargs):
        return LabelInput(label=label, id=id, name=name, value=value, required=required, type=type, label_cls=LABEL_CLASS, input_cls=INPUT_CLASS, **kwargs)

    def StyledLabelTextArea(label, id, name, value, required=False, rows=4):
        return LabelTextArea(label=label, id=id, name=name, value=value, required=required, rows=rows, label_cls=LABEL_CLASS, input_cls=INPUT_CLASS)

    # --- The main form content ---
    form_content = Form(
        Fieldset(
            form_intro_text if form_intro_text else "",
            Div(id="form-error-message", cls="text-red-500 mb-2 md:mb-4"),
            Hidden(name="experience_id", value=str(exp_id)) if is_edit else None,
            # The associated activity is now set based on edit or new selection
            Hidden(name="associated_activity", value=val('associated_activity') if is_edit else selected_activity),

            SectionContainer("1. Üldinfo",
                StyledLabelInput(label="Taotleja roll objektil", placeholder="objektijuht, projektijuht vms", id="role", name="role", value=val('role'), required=True),
                Div(
                    P("Töövõtuvorm", cls=LABEL_CLASS + " mb-1"),
                    Div(
                        *[Div(Radio(id=f"contract_type_{v}", name="contract_type", value=v, checked=(val('contract_type') == v), required=True), FormLabel(l, fr=f"contract_type_{v}", cls="ml-2 text-sm"), cls="flex items-center") for v, l in [("PTV", "Peatöövõtt"), ("PTVO", "Peatöövõtt omajõududega"), ("ATV", "Alltöövõtt")]],
                        cls="flex flex-row flex-wrap gap-x-4 gap-y-2 mt-1"
                    )
                ),
                DivHStacked(
                    Div(P("Alguskuu/aasta", fr="start_date", cls="mb-1 " + LABEL_CLASS), Div(Input(id="start_date", name="start_date", type="text", placeholder="Vali kuu & aasta...", value=val('start_date'), cls=f"{INPUT_CLASS} flatpickr-month-input pr-8"), UkIcon("calendar", cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"), cls="relative"), cls="w-48"),
                    Div(P("Lõppkuu/aasta", fr="end_date", cls="mb-1 " + LABEL_CLASS), Div(Input(id="end_date", name="end_date", type="text", placeholder="Vali kuu & aasta...", value=val('end_date'), cls=f"{INPUT_CLASS} flatpickr-month-input pr-8"), UkIcon("calendar", cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"), cls="relative"), cls="w-48"),
                    cls="mb-4 space-x-4"
                ),
            ),

            SectionContainer("2. Teostatud ehitustööd",
                InputTag(name="work_keywords", value=val('work_keywords', "Vundamenditööd, Müüritööd"), placeholder="Lisa ehitustöö ja vajuta Enter...", max_length=30),
                StyledLabelTextArea(label="Ehitustegevuse liigi kirjeldus", id="work_description", name="work_description", value=val('work_description'), rows=3, required=True)
            ),

            SectionContainer("3. Ehitusobjekti andmed",
                StyledLabelInput(label="Objekti aadress", id="object_address", name="object_address", value=val('object_address'), required=True),
                StyledLabelInput(label="Objekti otstarve", id="object_purpose", name="object_purpose", value=val('object_purpose')),
                StyledLabelInput(label="EHR kood", id="ehr_code", name="ehr_code", value=val('ehr_code')),
                LabelCheckboxX(label="Kas ehitusluba oli nõutav?", id="permit_required", name="permit_required", checked=bool(val('permit_required', 0)), label_cls=LABEL_CLASS, cls="mt-2")
            ),

            # The two-column layout for company/client data
            Div(
                SectionContainer("4. Ettevõtte andmed",
                    StyledLabelInput(label="Ettevõtte nimi", id="company_name", name="company_name", value=val('company_name'), required=True),
                    StyledLabelInput(label="Registrikood", id="company_code", name="company_code", value=val('company_code')),
                    StyledLabelInput(label="Kontaktisik", id="company_contact", name="company_contact", value=val('company_contact')),
                    StyledLabelInput(label="E-post", id="company_email", name="company_email", value=val('company_email'), type="email"),
                    StyledLabelInput(label="Telefon", id="company_phone", name="company_phone", value=val('company_phone'), type="tel"),
                ),
                SectionContainer("5. Tellija andmed",
                    StyledLabelInput(label="Tellija nimi", id="client_name", name="client_name", value=val('client_name')),
                    StyledLabelInput(label="Registrikood", id="client_code", name="client_code", value=val('client_code')),
                    StyledLabelInput(label="Kontaktisik", id="client_contact", name="client_contact", value=val('client_contact')),
                    StyledLabelInput(label="E-post", id="client_email", name="client_email", value=val('client_email'), type="email"),
                    StyledLabelInput(label="Telefon", id="client_phone", name="client_phone", value=val('client_phone'), type="tel"),
                ),
                cls="grid md:grid-cols-2 md:gap-6" # Grid layout for desktop
            ),

            # The fieldset is disabled as a whole if no task is active
            disabled=is_form_disabled
        ),
        hx_post=form_action,
        # On success, we want to reload the whole tab to show the new state
        hx_target="#tab-content-container",
        hx_swap="innerHTML",
        id="work-experience-form-v2",
        cls="space-y-4 md:space-y-6 validated-form" # Add .validated-form class
    )

    # This is now wrapped in a Div that handles the disabled state click
    page_content = Div(
        activity_selection_box if activity_selection_box else "",

        # This Div will intercept clicks and trigger animations
        Div(
            form_content,
            # Add the animation class here
            _=("on click if I match '.form-disabled' then "
               "call alert('Palun vali ülevalt tegevusala uue kogemuse lisamiseks või klõpsa olemasoleval kogemusel, et seda muuta.')"),
            cls=f"{form_wrapper_class}"
        ),
        cls="max-w-5xl mx-auto",
        id="work-experience-form-v2-container"
    )

    # Wrap the form and add the action bar
    action_bar = StickyActionBar(
        form_id="work-experience-form-v2",
        save_text=button_text,
        cancel_url=cancel_action
    ) if is_task_active else None

    return page_content, action_bar
