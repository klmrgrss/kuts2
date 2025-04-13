# ui/work_experience_view.py
# --- Keep imports ---
from fasthtml.common import *
from monsterui.all import *
from typing import List, Optional # Ensure List and Optional are imported

from ui.custom_components import InputTag

# --- Helper Function to Format YYYY-MM Date for Display ---
def format_yyyy_mm(date_str: Optional[str]) -> str:
    """Formats 'YYYY-MM' string to 'MM/YYYY' for display. Returns empty if invalid."""
    if not date_str or len(date_str) != 7 or date_str[4] != '-':
        return ""
    try:
        year, month = date_str.split('-')
        # Basic validation
        if not (year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
             return "" # Invalid format/value
        return f"{month}/{year}"
    except ValueError:
        return "" # Handle potential split errors


# --- RENDER SINGLE EXPERIENCE ITEM (MODIFIED: Display start_date/end_date) ---
def render_experience_item(experience: dict):
    exp_id = experience.get('id', 'N/A')
    role = experience.get('role', 'N/A')
    company = experience.get('company_name', 'N/A')
    object_address = experience.get('object_address', 'N/A')

    # --- MODIFIED: Use new date fields and formatter ---
    start_date_str = format_yyyy_mm(experience.get('start_date'))
    end_date_str = format_yyyy_mm(experience.get('end_date'))
    date_range = f"{start_date_str} - {end_date_str}" if start_date_str else ""
    if not end_date_str and start_date_str: # Handle case with only start date
        date_range = start_date_str
    # --- END MODIFICATION ---

    associated_activity = experience.get('associated_activity')
    delete_confirmation = "Oled kindel, et soovid selle töökogemuse taotlusest kustutada?"
    keywords_string = experience.get('work_keywords', '')
    formatted_keywords = keywords_string.replace(',', ', ') if keywords_string else ''

    # --- Label/Value classes remain the same ---
    LABEL_COLOR_CLS = "text-muted-foreground"
    VALUE_COLOR_CLS = "text-foreground"
    LABEL_WIDTH_CLS = "w-40"
    LABEL_CLS = f"{LABEL_COLOR_CLS} font-medium {LABEL_WIDTH_CLS} flex-shrink-0"

    # --- Div structure remains largely the same, just uses the new date_range ---
    return Div(
        Div(
            P(f"Ehitusobjekt: {object_address}", cls="text-lg font-semibold mb-2"),
            Div( # Container for details
                (Div(Span("Tegevusala:", cls=LABEL_CLS), Span(associated_activity, cls=VALUE_COLOR_CLS), cls="flex items-baseline gap-x-2") if associated_activity else None),
                Div(Span("Roll:", cls=LABEL_CLS), Span(f"{role} ettevõttes {company}", cls=VALUE_COLOR_CLS), cls="flex items-baseline gap-x-2"),
                # Display the new date range format
                Div(Span("Periood:", cls=LABEL_CLS), Span(date_range, cls=f"{VALUE_COLOR_CLS} text-sm"), cls="flex items-baseline gap-x-2"),
                (Div(Span("Teostatud ehitustööd:", cls=LABEL_CLS), Span(formatted_keywords, cls=f"{VALUE_COLOR_CLS} text-sm"), cls="flex items-baseline gap-x-2") if formatted_keywords else None),
                P("...", cls="text-center text-muted-foreground text-xl my-1"),
                cls="space-y-1"
            ),
            cls="mb-2"
        ),
        Div( # Footer (buttons)
            DivRAligned(
                Button("Muuda", hx_get=f"/app/tookogemus/{exp_id}/edit", hx_target="#add-experience-form-container", hx_swap="innerHTML", cls="btn btn-secondary mt-4 border-2 border-solid border-gray-400"),
                Button("Kustuta", hx_delete=f"/app/tookogemus/{exp_id}", hx_target=f"#experience-{exp_id}", hx_swap="outerHTML", hx_confirm=delete_confirmation, cls="btn mt-4 bg-red-50 text-red-700 border-2 border-solid border-red-400"),
                cls="flex space-x-2"
            ),
            cls="mt-2 border-t pt-2"
        ),
        id=f"experience-{exp_id}",
        cls="mb-4 border bg-gray-50 border-gray-200 rounded-lg p-3 shadow-none md:p-4 md:shadow md:bg-card"
    )


# --- RENDER LIST OF EXPERIENCES (No changes needed here) ---
def render_work_experience_list(experiences: list, warning_message: Optional[FT] = None):
    # ... (This function remains unchanged from your provided version) ...
    TITLE_CLASS = "text-xl font-semibold mb-4"
    if warning_message:
        return Div( H3("Töökogemuse kirjeldamine", cls=TITLE_CLASS), warning_message, cls="p-0 md:p-6 shadow-none border-0 rounded-none bg-transparent md:border md:rounded-lg md:shadow md:bg-card")
    list_items = [render_experience_item(exp) for exp in experiences] if experiences else [P("Töökogemusi pole veel lisatud.", cls="text-center text-muted-foreground p-4")]
    add_button = Button("+ Lisa töökogemus", hx_get="/app/tookogemus/add_form", hx_target="#add-experience-form-container", hx_swap="innerHTML", cls="btn btn-primary mt-4")
    add_button_container = Div(add_button, id="add-button-container")
    add_form_container = Div(id="add-experience-form-container", cls="mt-4")
    add_form_section = Div(add_button_container, add_form_container)
    experience_list_section = Div(H4("Salvestatud töökogemused", cls="text-lg italic font-medium mt-6 mb-3") if experiences else None, *list_items, id="work-experience-list")
    return Div(H3("Töökogemuse kirjeldamine", cls=TITLE_CLASS), add_form_section, experience_list_section, cls="p-0 md:p-6 shadow-none border-0 rounded-none bg-transparent md:border md:rounded-lg md:shadow md:bg-card")


# --- RENDER ADD/EDIT FORM (MODIFIED: Use Flatpickr for dates) ---
def render_work_experience_form(available_activities: List[str], experience: Optional[dict] = None): # Use Optional[dict]
    is_edit = experience is not None
    exp_id = experience.get('id') if is_edit else None
    # Ensure experience is a dict even if None was passed
    experience = experience or {}

    form_action = "/app/tookogemus/save"
    button_text = "Salvesta muudatused" if is_edit else "Kinnita ja lisa taotlusele"
    cancel_button_text = "Tühista"
    form_title = f"{'Muuda töökogemuse andmeid' if is_edit else 'Sisesta töökogemuse andmed'}"

    # Helper to get value, using the guaranteed dict 'experience'
    def val(key, default=''): return experience.get(key, default)

    LABEL_CLASS = "font-semibold" # Use default label styling or define as needed
    INPUT_CLASS = "input input-bordered w-full input-sm" # Standard input class

    # Removed the old StyledLabelInput helpers as they are not used for dates anymore
    # Keep others if used elsewhere in the form
    def StyledLabelTextArea(label, id, name, value, required=False, rows=4):
        return LabelTextArea(label=label, id=id, name=name, value=value, required=required, rows=rows, label_cls=LABEL_CLASS, input_cls=INPUT_CLASS)
    def StyledLabelCheckboxX(label, id, name, checked=False):
        return LabelCheckboxX(label=label, id=id, name=name, checked=checked, label_cls=LABEL_CLASS, cls="mt-2")

    # Prepare options for the Select dropdown (remains the same)
    select_options = [Option(act, value=act, selected=(act == val('associated_activity'))) for act in available_activities]

    return Form(
        H3(form_title, cls="text-xl font-semibold mb-3 md:mb-4"),
        Div(id="form-error-message", cls="text-red-500 mb-2 md:mb-4"),
        Hidden(name="experience_id", value=str(exp_id)) if is_edit else None,

        # Associated Activity Selection (remains the same)
        Section(
            #H4("Seosta see töökogemus järgmise tegevusalaga:", fr="associated_activity", ),
            Select(Option("--- Seosta töökogemus tegevusalaga ---", value="", disabled=True, selected=(not val('associated_activity'))), *select_options, id="associated_activity", name="associated_activity", required=True, cls="font-semibold text-xl"), # Apply input class
            cls="space-y-1 md:space-y-2 mb-3 md:mb-4", 
        ),
                Section( # Competency/Activity Info
             H5("Ehitustöö lühikirjeldus. Lisa uus / kustuta ebavajalik", cls="text-base font-medium mb-2"),
             InputTag(name="work_keywords", value=val('work_keywords', "Vundamenditööd, Müüritööd, Ehituse ettevalmistus"), placeholder="Lisa ehitustöö ja vajuta Enter...", max_length=24, cls="mb-3"),
             cls="space-y-2 md:space-y-4 mt-3 md:mt-6 border-t pt-2 md:pt-4"
        ),

        # --- MODIFIED General Info Section ---
        Section(
            LabelInput(label="Taotleja roll objektil", placeholder="objektijuht, projektijuht vms", id="role", name="role", value=val('role'), required=True, input_cls=INPUT_CLASS, cls="mb-3 md:mb-4"),

            # +++ REPLACED Month/Year Grid with Flatpickr Inputs +++
            DivHStacked(
            Div(
                P("Alguskuu/aasta", fr="start_date", cls="mb-1 " + LABEL_CLASS), # Label for the input

                # --- Wrapper Div for Input + Icon ---
                
                Div(
                    # --- The Flatpickr Input ---
                    Input(
                        id="start_date",
                        name="start_date",
                        type="text", # Input type is text for Flatpickr
                        placeholder="Vali kuu & aasta...",
                        value=val('start_date'), # Pre-populates with existing value
                        # Input classes: Standard styling + Flatpickr hook + Right padding for icon
                        cls=f"{INPUT_CLASS} flatpickr-month-input pr-8"
                    ),

                    # --- The Calendar Icon ---
                    UkIcon(
                        "calendar", # Icon name (from UIkit icons via MonsterUI)
                        # Absolute positioning classes:
                        # - absolute: Takes icon out of normal flow
                        # - right-2: Positions 2 units from the right edge of the wrapper
                        # - top-1/2: Positions top edge at 50% height of the wrapper
                        # - -translate-y-1/2: Shifts icon up by 50% of its own height for vertical centering
                        # - pointer-events-none: Allows clicking "through" the icon onto the input
                        cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                    ),

                    # --- Wrapper Div styling ---
                    # - relative: Establishes positioning context for the absolute icon
                    cls="relative"
                ),
                # --- Width applied to the group containing Label and Input-Wrapper ---
                cls="w-48" # Adjust width as needed
            ),

            # --- Group for End Date Input + Label (Apply similar structure) ---
            Div(
                P("Lõppkuu/aasta", fr="end_date", cls="mb-1 " + LABEL_CLASS),
                Div( # Wrapper Div for Input + Icon
                    Input(
                        id="end_date",
                        name="end_date",
                        type="text",
                        placeholder="Vali kuu & aasta...",
                        value=val('end_date'),
                        cls=f"{INPUT_CLASS} flatpickr-month-input pr-8" # Add padding for icon
                    ),
                    UkIcon("calendar", cls="h-5 w-5 text-muted-foreground absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"),
                    cls="relative" # Wrapper is relative
                ),
                cls="w-48" # Width for the group
            ), cls="mb-4 space-x-4"), # Space between the two groups,
            # +++ END REPLACEMENT +++

            LabelInput(label="Ehitustegevuse liik", id="work_description", Placeholder="uusehitis, rekonstrueerimine, remont või muu" , name="work_description", value=val('work_description'), rows=4, required=False, cls="mb-3 md:mb-4", input_cls=INPUT_CLASS),
# --- Radio Button Group for Töövõtuvorm ---
            Div( # Main container for the radio group section
                # Use Label component for the group title, associate with first radio for accessibility?
                # Or just use a P/H5 tag. Adding required marker visually if needed.
                P("Töövõtuvorm", cls=LABEL_CLASS + " mb-1"), # Group label, added * visually

                Div( # Inner container for horizontal stacking of radio buttons
                    # Loop through the options
                    *[
                        Div( # Wrapper for each radio + label pair
                            Radio(
                                id=f"contract_type_{value}",
                                name="contract_type", # Same name binds them as a group
                                value=value,
                                # Check if the current experience's contract_type matches this radio's value
                                checked=(val('contract_type') == value),
                                required=True # HTML5 required attribute
                            ),
                            FormLabel(
                                label_text, # Display text e.g., "Peatöövõtt (PTV)"
                                fr=f"contract_type_{value}", # Associates label with radio button
                                cls="ml-2 text-sm" # Styling for the label text
                            ),
                            cls="flex items-center" # Aligns radio and label horizontally
                        )
                        # Define the options as (value, label_text) tuples
                        for value, label_text in [
                            ("PTV", "Peatöövõtt (PTV)"),
                            ("PTVO", "Peatöövõtt omajõududega (PTVO)"),
                            ("ATV", "Alltöövõtt (ATV)")
                        ]
                    ],
                    # Apply flex classes for layout
                    # - flex-row: Arrange items horizontally
                    # - flex-wrap: Allow items to wrap onto next line if needed
                    # - gap-x-4: Horizontal space between items
                    # - gap-y-2: Vertical space if items wrap
                    # - mt-1: Small margin top
                    cls="flex flex-row flex-wrap gap-x-4 gap-y-2 mt-1"
                )
            ),
            # --- End Radio Button Group ---
        ),
        # --- END MODIFIED General Info Section ---

        # Other Sections (Competency, Object, Company, Client) remain the same...

        Section( # Object Info
             H4("Ehitusobjekti andmed", cls="text-lg font-medium mb-2 md:mb-3"),
             StyledLabelCheckboxX(label="Kas ehitusluba oli nõutav?", id="permit_required", name="permit_required", checked=bool(val('permit_required', 0))),
             LabelInput(label="Objekti aadress", id="object_address", name="object_address", value=val('object_address'), input_cls=INPUT_CLASS),
             LabelInput(label="Objekti otstarve", id="object_purpose", name="object_purpose", value=val('object_purpose'), input_cls=INPUT_CLASS),
             LabelInput(label="EHR kood", id="ehr_code", name="ehr_code", value=val('ehr_code'), input_cls=INPUT_CLASS),
             cls="space-y-2 md:space-y-4 mt-3 md:mt-6 border-t pt-2 md:pt-4"
        ),
        # --- Container for Company and Client Info using CSS Grid ---
# --- Container for Company and Client Info using CSS Grid ---
        Div(
            # --- Company Info Section ---
            # No changes needed in the first section
            Section(
                H4("Ehitustöid teostanud ettevõtte andmed", cls="text-lg font-medium mb-2 md:mb-3"),
                Grid(
                    LabelInput(label="Töid teostanud ettevõtte nimi", id="company_name", name="company_name", value=val('company_name'), required=True, input_cls=INPUT_CLASS),
                    LabelInput(label="Ettevõtte registrikood", id="company_code", name="company_code", value=val('company_code'), input_cls=INPUT_CLASS),
                    cols=1, cls="gap-2 md:gap-4"
                ),
                Grid(
                    LabelInput(label="Kontaktisik ehitustööd teostanud ettevõttes", id="company_contact", name="company_contact", value=val('company_contact'), input_cls=INPUT_CLASS),
                    LabelInput(label="E-post", id="company_email", name="company_email", value=val('company_email'), type="email", input_cls=INPUT_CLASS),
                    LabelInput(label="Telefon", id="company_phone", name="company_phone", value=val('company_phone'), type="tel", input_cls=INPUT_CLASS),
                    cols=1, cls="gap-2 md:gap-4"
                ),
                cls="space-y-2 md:space-y-4" # Keep internal spacing
            ),

            # --- Client Info Section (MODIFIED) ---
            Section(
                H4("Tellija andmed", cls="text-lg font-medium mb-2 md:mb-3"),
                Grid(
                    LabelInput(label="Tellija nimi", id="client_name", name="client_name", value=val('client_name'), input_cls=INPUT_CLASS),
                    LabelInput(label="Tellija registrikood / ID", id="client_code", name="client_code", value=val('client_code'), input_cls=INPUT_CLASS),
                    cols=1, cls="gap-2 md:gap-4"
                ),
                Grid(
                    LabelInput(label="Tellijapoolne kontaktisik", id="client_contact", name="client_contact", value=val('client_contact'), input_cls=INPUT_CLASS),
                    LabelInput(label="E-post", id="client_email", name="client_email", value=val('client_email'), type="email", input_cls=INPUT_CLASS),
                    LabelInput(label="Telefon", id="client_phone", name="client_phone", value=val('client_phone'), type="tel", input_cls=INPUT_CLASS),
                    cols=1, cls="gap-2 md:gap-4"
                ),
                # +++ Added border and padding classes +++
                # md:border-l: Add left border only on md+ screens
                # md:border-gray-300: Set border color (adjust if needed)
                # md:pl-6: Add left padding only on md+ screens (adjust value like pl-4, pl-8 if needed)
                cls="space-y-2 md:space-y-4 md:border-l md:border-gray-300 md:pl-6"
            ),

            # --- Parent Div classes remain the same ---
            cls="grid grid-cols-1 md:grid-cols-2 gap-6 mt-3 md:mt-6 border-t pt-2 md:pt-4"
        ),
        # --- End of Company/Client Info Container ---

        # Buttons (remain the same)
        Div(
             Button(button_text, type="submit", cls="btn btn-primary mt-4"),
             Button(cancel_button_text, type="button", cls="btn btn-secondary mt-4", hx_get="/app/tookogemus/cancel_form", hx_target="#add-experience-form-container", hx_swap="innerHTML"),
             cls="flex justify-end space-x-2 md:space-x-4 mt-4 md:mt-6 pt-4 md:pt-6 border-t"
        ),

        # Form Attributes (remain the same)
        hx_post=form_action,
        hx_target=f"#experience-{exp_id}" if is_edit else "#work-experience-list",
        hx_swap="outerHTML" if is_edit else "beforeend",
        id="work-experience-form",
        cls="space-y-3 md:space-y-6 p-4 md:p-6 border rounded-lg shadow-lg bg-card bg-pink-50/20" # Added background color for the form
    )