# ui/education_form.py
from fasthtml.common import *
from monsterui.all import * # Assuming LabelInput, Button, etc. are here

def render_education_form(sections_data: dict, existing_data: dict = None):
    """
    Renders the education form UI using standard components within a Card,
    using Flatpickr for the graduation date month/year input.
    """
    existing_data = existing_data or {}
    selected_level = existing_data.get('selected_level', None)
    other_text = existing_data.get('other_text', '')
    institution = existing_data.get('institution', '')
    specialty = existing_data.get('specialty', '')
    # Get the graduation date directly (should be YYYY-MM format)
    graduation_date_value = existing_data.get('graduation_date', '')

    # --- Remove old month formatting logic ---
    # graduation_month_value = graduation_date[:7] if graduation_date and len(graduation_date) >= 7 else "" # No longer needed

    # --- Define standard input/label classes ---
    INPUT_CLASS = "input input-bordered w-full"
    LABEL_CLASS = "label label-text pb-1"
    RADIO_LABEL_CLASS = "ml-2 text-sm font-medium text-foreground"
    TITLE_CLASS = "text-xl font-semibold mb-4"

    radio_groups = []
    # --- Radio Group Loop (remains the same) ---
    for idx, section_info in sections_data.items():
        items_in_group = []
        section_tooltip = section_info.get("tooltip", "Tooltip puudub")
        try:
            for item_value, item_label in section_info["items"]:
                radio_id = f"edu_level_{idx}_{item_value.replace(' ', '_').replace('.', '')}"
                is_checked = (selected_level == item_value)
                is_other_radio = item_value == "Muu haridus"
                radio_button = Radio(id=radio_id, name="education_level", value=item_value, checked=is_checked, data_is_other=str(is_other_radio).lower())
                label_comp = FormLabel(item_label, fr=radio_id, cls=RADIO_LABEL_CLASS)
                radio_item_div = Div(radio_button, label_comp, cls="flex items-center mb-2")
                if is_other_radio:
                    other_input = Input(
                        type="text", id="other_education_text_input", name="other_education_text",
                        placeholder="Täpsusta muu haridus", value=other_text if is_checked else '',
                        cls=INPUT_CLASS + " ml-6 mt-1",
                        style="display: none;" if not is_checked else "display: block;"
                    )
                    items_in_group.append(Div(radio_item_div, other_input))
                else:
                    items_in_group.append(radio_item_div)
            group_title = Div(
                P(section_info["title"], cls="text-base font-medium text-foreground"),
                UkIcon("info", height=16, width=16, cls="text-muted-foreground flex-shrink-0 ml-2", **{"uk-tooltip": f"title: {section_tooltip}; pos: right"}),
                cls="flex items-center mb-3 mt-4"
            )
            radio_groups.append(Div(group_title, *items_in_group, cls="border-b pb-4 mb-4"))
        except Exception as e: print(f"--- ERROR processing items in section {idx}: {e} ---")
    # --- End Radio Group Loop ---

    # --- Form structure ---
    form_content = Form(
        H3("Haridus", cls=TITLE_CLASS),
        # Div( # Submit Button moved to bottom for consistency
        #     Button("Kinnita valikud", type="submit", cls="btn btn-primary mt-4"),
        #     cls="flex justify-start"
        # ),
        P("Märgi oma hariduslik taust", cls="text-sm text-muted-foreground mb-6"),
        *radio_groups,
        Section(
            LabelInput(label="Õppeasutus", name="institution", id="institution", value=institution, label_cls=LABEL_CLASS, input_cls=INPUT_CLASS),
            LabelInput(label="Eriala", name="specialty", id="specialty", value=specialty, label_cls=LABEL_CLASS, input_cls=INPUT_CLASS),

            # +++ MODIFIED Graduation Date Input for Flatpickr +++
            LabelInput(
                label="Lõpetamise aeg (kuu ja aasta)",
                name="graduation_date",
                id="graduation_date",
                type="text", # CHANGED type to "text"
                value=graduation_date_value, # Use the direct YYYY-MM value
                placeholder="Vali kuu ja aasta...", # Add placeholder
                # Add the class for the JS initializer and standard input class
                input_cls=f"{INPUT_CLASS} flatpickr-month-input", # ADDED class
                label_cls=LABEL_CLASS
            ),
            # +++ END MODIFICATION +++

            cls="space-y-4 mt-6"
        ),
        Div( # File Upload Section
            LabelInput(
                label="Vali fail (pdf, doc, docx, jpg, png | MAX 10M)",
                type="file",
                id='education_document',
                name='education_document',
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png",
                cls="mb-4",
                input_cls=INPUT_CLASS, # Apply standard input class
                label_cls=LABEL_CLASS,
            ),
            cls="border-t pt-4 mt-6" # Added border-top and margin-top
        ),
        Div( # Submit Button (now at the bottom)
            Button("Kinnita valikud", type="submit", cls="btn btn-primary mt-4"),
            cls="flex justify-start mt-6 pt-4 border-t" # Adjusted spacing
        ),
        # Form attributes remain the same
        method="post",
        hx_post="/app/haridus/submit",
        hx_encoding="multipart/form-data",
        id="education-form",
        cls="space-y-4" # Overall spacing for form elements
    )

    # Wrap form in Card and CardBody (structure remains)
    # Note: The Script tag for education_form.js might only be needed now
    # if it handles the 'Other' radio button logic. If not, it could be removed.
    return Div(
        Card(
            CardBody(
                form_content
            )
        ),
        Script(src="/static/js/education_form.js"), # Keep if needed for 'Other' logic
    )