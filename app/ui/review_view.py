# gem/ui/review_view.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional

# --- render_data_dl helper (REVISED based on user's flexbox model) ---
def render_data_dl(data_dict: dict, fields: list[tuple[str, str]]) -> Optional[Div]:
    """
    Renders data using Divs based on user-provided flexbox model
    with data-uk-leader on the expanding label div.
    """
    if data_dict is None: return None
    items = []
    for key, label in fields:
        value = data_dict.get(key)
        # Only render if there's a value
        if value:
            # Create row div based on model: <div class="flex gap-x-2 items-center">
            row_div = Div(
                # Label Div: <div class="flex-1" data-uk-leader="fill: .">Label</div>
                Div(
                    label,
                    # Apply flex-1 (Tailwind grow) and data-uk-leader attribute
                    cls="flex-initial font-bold",
                    # Use correct syntax for data attributes with hyphens
                    # Added 'fill: .' to specify dots. Use data-uk-leader for non-boolean.
                    #**{'data-uk-leader': 'fill: . ' }
                ),
                # Value Div: <div>Value</div> (No special classes from model)
                Div(str(value)),

                # Apply flex and gap to the outer row container
                cls="flex gap-x-2 items-center" # Added items-center for vertical alignment
            )
            items.append(row_div)

    if not items: return None
    # Return a container Div for all rows
    return Div(*items, cls="space-y-1") # Keep vertical spacing

 #--- Helper for consistent Section Header ---
def render_section_header(title: str, edit_url: str, count: Optional[int] = None) -> FT: #<<< Check this line carefully
    """Creates the CardHeader with H3 title (optionally with count) and underlined 'Muuda' link."""
    display_title = title
    if count is not None and count > 0:
        display_title = f"{title} ({count})"
    return CardHeader(
        DivHStacked(
            H5(display_title), # Section Title
            A("Muuda", href=edit_url, cls="text-primary underline hover:no-underline text-sm")
        ),
        cls="pb-2" # Reduced bottom padding for tighter spacing
    )

def render_review_page(data: dict) -> FT:
    """
    Renders the application review page with consistent styling and compact layout.
    """
    user_data = data.get('user', {})
    profile_data = data.get('profile', {})
    qualifications = data.get('qualifications', [])
    experiences = data.get('experience', [])
    experience_count = data.get('experience_count', 0) # Get the count
    education = data.get('education', {})
    training_files = data.get('training_files', [])
    employment_proof = data.get('employment_proof', {})

    TITLE_CLASS = "text-xl font-semibold"
    CARD_BODY_CLS = "pt-0"
    content_sections = []

   # --- Applicant Section Card ---
    applicant_fields = [('full_name', 'Nimi'), ('email', 'E-post'), ('birthday', 'Sünniaeg'), ('address', 'Aadress'), ('phone', 'Telefon')]
    combined_profile = {**user_data, **profile_data}
    if 'hashed_password' in combined_profile: del combined_profile['hashed_password']
    applicant_dl = render_data_dl(combined_profile, applicant_fields)
    content_sections.append( Card( render_section_header("Taotleja andmed", "/app/taotleja"), CardBody(applicant_dl if applicant_dl else P("Taotleja andmed puuduvad.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS), cls="mb-3" ) )


    # --- Qualifications Section Card ---
    qual_items = []
    if qualifications:
        for q in qualifications:
            # Reduced font size slightly
            qual_items.append(Li(Div(Span(f"{q.get('level', '')} - {q.get('qualification_name', '')}", cls="font-medium text-sm"), Span(f": {q.get('specialisation', '')}", cls="text-sm text-muted-foreground"))))
    content_sections.append(
        Card(
            render_section_header("Taotletavad kutsed", "/app/kutsed"), # Use helper
            CardBody(Ul(*qual_items, cls="list-disc list-inside space-y-1") if qual_items else P("Valitud kutsed puuduvad.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS),
            cls="mb-3" # Reduced margin between cards
        )
    )

   # --- Work Experience Section Card (MODIFIED: Display ALL Fields) ---
    exp_items = []
    if experiences:
        # Define labels for clarity
        labels = {
            "keywords": "Teostatud ehitustööd:","object": "Objekt:", "keywords": "Teostatud ehitustööd:", "competency": "Seos kutsega:",
            "contract_type": "Lepingu tüüp:", "permit_required": "Luba nõutav:",
            "other_work": "Muu töö:", "activity": "Ehitustegevus:", "other_activity": "Muu tegevus:",
            "description": "Ehitustegevuse liik:", "company_details": "Ehitustööde teostaja:", "client_details": "Tellija:"
        }
        for i, exp in enumerate(experiences):
            details = []

            # --- Line 1: Role @ Company | Date Range ---
            date_range = f"{exp.get('start_month', '')}/{exp.get('start_year', '')} - {exp.get('end_month', '')}/{exp.get('end_year', '')}"
            line1 = Div(
                Div( Strong(exp.get('role', 'N/A'), cls="text-sm"), Span(f" @ {exp.get('company_name', 'N/A')}", cls="text-xs text-muted-foreground ml-1") ),
                Div( Span(date_range, cls="text-xs text-muted-foreground whitespace-nowrap"), cls="text-right flex-shrink-0 ml-2" ),
                cls="flex justify-between items-center"
            )
            details.append(line1)

            # --- Helper to add a labeled line if value exists ---
            def add_detail_line(label_key, value, prefix=""):
                if value:
                    # Simple formatting for keywords: replace comma with comma+space
                    display_value = value.replace(',', ', ') if label_key == "keywords" else value
                    details.append(Div(Strong(labels.get(label_key, ""), cls="text-muted-foreground mr-1"), f"{prefix}{display_value}", cls="text-xs mt-1"))

            # --- Object Info ---
            obj_parts = []
            if exp.get('object_address'): obj_parts.append(exp['object_address'])
            if exp.get('object_purpose'): obj_parts.append(f"({exp['object_purpose']})")
            if exp.get('ehr_code'): obj_parts.append(f"[EHR: {exp['ehr_code']}]")
            add_detail_line("object", " ".join(obj_parts))

            # --- Keywords ---
            add_detail_line("keywords", exp.get('work_keywords'))

            # --- Competency / Activities ---
            add_detail_line("competency", exp.get('competency'))
            add_detail_line("activity", exp.get('construction_activity'))
            add_detail_line("other_activity", exp.get('other_activity'))
            #add_detail_line("other_work", exp.get('other_work')) # Add other_work

            # --- Contract Type & Permit ---
            add_detail_line("contract_type", exp.get('contract_type'))
            add_detail_line("permit_required", "Jah" if exp.get('permit_required') == 1 else "Ei")

            # --- Description ---
            desc = exp.get('work_description', '')
            add_detail_line("description", desc[:150] + ("..." if len(desc) > 150 else "")) # Slightly longer snippet

            # --- Company Details (Code, Contact, Email, Phone) ---
            company_details_list = []
            company_name = exp.get('company_name')
            if company_name: # Only proceed if there is a company name
                # Start the list with the company name
                company_details_list.append(f"{company_name}")
                # Now add other details if they exist
                if exp.get('company_code'): company_details_list.append(f"Reg.kood: {exp['company_code']}")
                if exp.get('company_contact'): company_details_list.append(f"Kontakt: {exp['company_contact']}")
                if exp.get('company_email'): company_details_list.append(f"E-post: {exp['company_email']}")
                if exp.get('company_phone'): company_details_list.append(f"Tel: {exp['company_phone']}")

                # Only add the Div if we have details (which we will if name exists)
                details.append(Div(
                        Strong(labels.get("company_details", "Ehitustööde teostaja:"), cls="text-muted-foreground mr-1"), # Use .get for safety
                        "; ".join(company_details_list), # Join the complete list
                        cls="text-xs mt-1"
                    ))
            # --- Client Details (Name, Code, Contact, Email, Phone) ---
            if exp.get('client_name'): # Only show if client name exists
                client_details_list = [f"{exp['client_name']}"]
                if exp.get('client_code'): client_details_list.append(f"Reg.kood: {exp['client_code']}")
                if exp.get('client_contact'): client_details_list.append(f"Kontakt: {exp['client_contact']}")
                if exp.get('client_email'): client_details_list.append(f"E-post: {exp['client_email']}")
                if exp.get('client_phone'): client_details_list.append(f"Tel: {exp['client_phone']}")
                details.append(Div(Strong(labels["client_details"], cls="text-muted-foreground mr-1"), "; ".join(client_details_list), cls="text-xs mt-1"))


            # --- Combine details for this item with separator ---
            separator_cls = "border-t border-gray-200 pt-2 mt-2" if i > 0 else ""
            exp_items.append(Div(*details, cls=separator_cls))

    content_sections.append(
        Card(
            render_section_header("Töökogemused", "/app/tookogemus", count=experience_count),
            CardBody(Div(*exp_items) if exp_items else P("Töökogemusi pole lisatud.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS),
            cls="mb-3"
        )
    )
    # --- End Work Experience Section ---

    # --- Education Section Card ---
    education_fields = [('education_detail', 'Hariduse tase/nimetus'), ('institution', 'Õppeasutus'), ('specialty', 'Eriala'), ('graduation_date', 'Lõpetamise kuupäev')]
    education_dl = render_data_dl(education, education_fields) # render_data_dl already made tighter
    content_sections.append(
        Card(
            render_section_header("Haridus", "/app/haridus"), # Use helper
            CardBody(education_dl if education_dl else P("Hariduse andmed puuduvad.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS),
            cls="mb-3" # Reduced margin between cards
        )
    )

    # --- Training Files Section Card ---
    training_items = []
    if training_files:
        for tf in training_files:
            # Reduced font size
             training_items.append(Li(Div(Span(tf.get('original_filename', 'Nimetu fail'), cls="font-medium text-sm"), Span(f" ({tf.get('file_description', 'Kirjeldus puudub')})", cls="text-xs text-muted-foreground"))))
    content_sections.append(
        Card(
            render_section_header("Täiendkoolitused", "/app/taiendkoolitus"), # Use helper
            CardBody(Ul(*training_items, cls="list-disc list-inside space-y-1") if training_items else P("Täiendkoolituse tunnistusi ei ole lisatud.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS),
            cls="mb-3" # Reduced margin between cards
        )
    )

    # --- Employment Proof Section Card ---
    emp_proof_dl = None
    if employment_proof and employment_proof.get('original_filename'):
        emp_proof_fields = [('original_filename', 'Faili nimi'), ('file_description', 'Faili kirjeldus'), ('upload_timestamp', 'Üleslaadimise aeg')]
        emp_proof_dl = render_data_dl(employment_proof, emp_proof_fields) # render_data_dl already made tighter
    content_sections.append(
        Card(
            render_section_header("Töötamise tõendamine", "/app/tootamise_toend"), # Use helper
            CardBody(emp_proof_dl if emp_proof_dl else P("Töötamise tõendit ei ole lisatud.", cls="text-sm text-muted-foreground"), cls=CARD_BODY_CLS),
            cls="mb-3" # Reduced margin between cards
        )
    )

    # --- Submission Section (Inside the outer card body) ---
    submission_section = Section(
        P("Palun vaata taotluse andmed hoolikalt üle. Esitamisel saadetakse taotlus menetlemiseks EEELi kutsekomisjonile ning koopia sinu e-postile.", cls="mt-4 mb-3 text-center text-sm text-muted-foreground"), # Reduced margins
        Form(
             Div(Button("Esita taotlus", type="submit", cls="btn btn-primary text-xl mt-4 mb-8"), cls="flex justify-center"),
             method="post",
             hx_post="/app/ulevaatamine/submit",
             hx_confirm="Oled kindel, et soovid taotluse esitada?",
             hx_target="#tab-content-container",
             hx_swap="innerHTML"
        ),
        cls="my-6 pt-4 border-t" # Reduced margins/padding
    )

    # --- Assemble Inner Content for the Outer Container ---
    # Using Div with responsive styles instead of Card for outer container
    inner_content = Div(
        H3("Taotluse ülevaatamine ja esitamine", cls=TITLE_CLASS),
        # Add spacing between inner content sections using space-y
        Div(
            *content_sections,
            cls="space-y-3" # Add vertical space between the inner cards/sections
        ),
        submission_section,
        cls="space-y-4" # Space between main content list and submission section
    )

    # --- Return outer Div with responsive styling ---
    # Similar to forms: no padding/card on mobile, padding/card on desktop
    return Div(
        inner_content,
        cls="p-0 md:p-6 shadow-none border-0 rounded-none bg-transparent md:border md:rounded-lg md:shadow md:bg-card"
    )