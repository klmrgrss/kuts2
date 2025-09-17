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
    is_task_active = is_edit or selected_activity is not None
    is_form_disabled = not is_task_active

    form_wrapper_class = 'form-disabled' if is_form_disabled else ''
    initial_section_class = 'state-in-progress' if is_task_active else 'state-unfocused'

    exp_id = experience.get('id') if is_edit else None
    experience = experience or {}
    experiences = experiences or []

    form_action = "/app/workex/save"
    cancel_action = "/app/workex"
    button_text = "Salvesta muudatused" if is_edit else "Kinnita ja lisa taotlusele"

    def val(key, default=''): return experience.get(key, default)

    activity_strips = []
    for i, activity in enumerate(available_activities):
        is_activity_in_focus = (activity == selected_activity) or (is_edit and activity == experience.get('associated_activity'))
        
        activity_experiences = [exp for exp in experiences if exp.get('associated_activity') == activity]
        has_experiences = len(activity_experiences) > 0
        
        experience_chips = []
        # --- MODIFICATION: Added enumerate to the loop for numbering ---
        for i, exp in enumerate(activity_experiences, 1):
            is_being_edited = is_edit and exp.get('id') == experience.get('id')
            
            link_classes = "px-1 text-sm rounded-none no-animation" 
            if is_being_edited:
                link_classes += " bg-blue-500 text-white"
            else:
                link_classes += " bg-gray-200 dark:bg-gray-700"

            experience_chips.append(
                A(
                    # Added "f'{i}. '" to the beginning of the string for the number
                    f"{i}. {exp.get('start_date', '')} - {exp.get('object_address', 'Aadress puudub')}",
                    hx_get=f"/app/workex/{exp.get('id')}/edit",
                    hx_target="#tab-content-container",
                    hx_swap="innerHTML",
                    cls=link_classes
                )
            )
        # --- END MODIFICATION ---

        is_adding_new_in_this_activity = (activity == selected_activity) and not is_edit
        
        add_chip_classes = "btn btn-xs btn-secondary rounded-full no-animation"
        if is_adding_new_in_this_activity:
            add_chip_classes += " activity-selected"

        add_new_chip = A(
            UkIcon("plus", cls="w-4 h-4"),
            hx_get=f"/app/workex?activity={activity}",
            hx_target="#tab-content-container",
            hx_swap="innerHTML",
            cls=add_chip_classes
        )
        
        experience_chips.append(add_new_chip)

        chips_container = Div(
            Div(*experience_chips, cls="flex flex-row flex-wrap items-center gap-2"),
            cls="p-4"
        )

        if has_experiences:
            icon = UkIcon("check-circle", cls="flex-shrink-0")
            text = P(f"Salvestatud '{activity}' töökogemused")
            strip_classes = "p-4 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 rounded-t-lg flex items-center gap-x-3"
        else:
            icon = UkIcon("info", cls="flex-shrink-0")
            text = P(f"Ühtegi '{activity}' töökogemust pole lisatud")
            strip_classes = "p-4 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100 rounded-t-lg flex items-center gap-x-3"

        header_strip = Div(
            icon,
            text,
            cls=strip_classes
        )

        border_class = 'border-blue-500' if is_activity_in_focus else 'border-gray-200 dark:border-gray-700'
        
        visual_group_wrapper = Div(
            header_strip,
            chips_container,
            cls=f"border-2 rounded-lg {border_class}" 
        )

        activity_strips.append(visual_group_wrapper)

    activity_selection_box = Div(
        Div(id="form-guidance-message"),
        Div(*activity_strips, cls="space-y-4"), 
        cls="mb-6"
    )

    form_intro_text = None
    if is_task_active:
        intro_title = f"MUUDA töökogemust: {val('start_date')} - {val('object_address')}" if is_edit else f"LISA UUS töökogemus tegevusalale: {selected_activity}"
        form_intro_text = Div(
            Div(
                P(intro_title, cls="font-semibold"),
                Div(UkIcon("chevron-down", cls="w-6 h-6"), cls="flex justify-center"),
                cls="p-2 bg-blue-100 text-blue-800 rounded-lg my-2 text-center"
            )
        )
    
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

    form_content = Form(
        Fieldset(
            form_intro_text if form_intro_text else "",
            Div(id="form-error-message", cls="text-red-500 mb-2 md:mb-4"),
            Hidden(name="experience_id", value=str(exp_id)) if is_edit else None,
            Hidden(name="associated_activity", value=val('associated_activity') if is_edit else selected_activity, required=True),

            SectionContainer("1. Üldinfo",
                StyledLabelInput(label="Taotleja roll objektil", placeholder="objektijuht, projektijuht vms", id="role", name="role", value=val('role'), required=True),
                Div(
                    P("Töövõtuvorm", cls=LABEL_CLASS + " mb-1"),
                    Div(
                        *[Div(Radio(id=f"contract_type_{v}", name="contract_type", value=v, checked=(val('contract_type') == v)), FormLabel(l, fr=f"contract_type_{v}", cls="ml-2 text-sm"), cls="flex items-center") for v, l in [("PTV", "Peatöövõtt"), ("PTVO", "Peatöövõtt omajõududega"), ("ATV", "Alltöövõtt")]],
                        cls="flex flex-row flex-wrap gap-x-4 gap-y-2 mt-1"
                    )
                ),
                DivHStacked(
                    Div(
                        P("Alguskuu/aasta", fr="start_date", cls="mb-1 " + LABEL_CLASS),
                        Div(
                            Input(
                                id="start_date", name="start_date", type="text", placeholder="Vali kuu & aasta...",
                                value=val('start_date'), cls=f"{INPUT_CLASS} flatpickr-month-input pr-8"
                            ),
                            UkIcon("calendar", cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"),
                            cls="relative"
                        ),
                        cls="w-48"
                    ),
                    Div(
                        P("Lõppkuu/aasta", fr="end_date", cls="mb-1 " + LABEL_CLASS),
                        Div(
                            Input(
                                id="end_date", name="end_date", type="text", placeholder="Vali kuu & aasta...",
                                value=val('end_date'), cls=f"{INPUT_CLASS} flatpickr-month-input pr-8"
                            ),
                            UkIcon("calendar", cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"),
                            cls="relative"
                        ),
                        cls="w-48"
                    ),
                    cls="mb-4 space-x-4"
                ),
            ),

            SectionContainer("2. Teostatud ehitustööd",
                InputTag(name="work_keywords", value=val('work_keywords', "Vundamenditööd, Müüritööd"), placeholder="Lisa ehitustöö ja vajuta Enter...", max_length=30),
                StyledLabelTextArea(label="Ehitustegevuse liigi kirjeldus", id="work_description", name="work_description", value=val('work_description'), rows=3)
            ),

            SectionContainer("3. Ehitusobjekti andmed",
                StyledLabelInput(label="Objekti aadress", id="object_address", name="object_address", value=val('object_address')),
                StyledLabelInput(label="Objekti otstarve", id="object_purpose", name="object_purpose", value=val('object_purpose')),
                StyledLabelInput(label="EHR kood", id="ehr_code", name="ehr_code", value=val('ehr_code')),
                LabelCheckboxX(label="Kas ehitusluba oli nõutav?", id="permit_required", name="permit_required", checked=bool(val('permit_required', 0)), label_cls=LABEL_CLASS, cls="mt-2")
            ),

            Div(
                SectionContainer("4. Ettevõtte andmed",
                    StyledLabelInput(label="Ettevõtte nimi", id="company_name", name="company_name", value=val('company_name')),
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
                cls="grid md:grid-cols-2 md:gap-6"
            ),

            disabled=is_form_disabled
        ),
        hx_post=form_action,
        hx_target="#tab-content-container",
        hx_swap="innerHTML",
        id="work-experience-form-v2",
        cls="space-y-4 md:space-y-6 validated-form"
    )

    page_content = Div(
        activity_selection_box,
        Div(
            form_content,
            _=("on click if I match '.form-disabled' then "
               "call alert('Palun vali ülevalt tegevusala uue kogemuse lisamiseks või klõpsa olemasoleval kogemusel, et seda muuta.')"),
            cls=f"{form_wrapper_class}"
        ),
        cls="max-w-5xl mx-auto",
        id="work-experience-form-v2-container"
    )

    delete_url = f"/app/workex/{exp_id}/delete" if is_edit else None
    action_bar = StickyActionBar(
        form_id="work-experience-form-v2",
        save_text=button_text,
        cancel_url=cancel_action,
        delete_url=delete_url
    ) if is_task_active else None

    return page_content, action_bar