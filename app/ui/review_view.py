# app/ui/review_view.py
# gem/ui/review_view.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional
import json

def render_data_dl(data_dict: dict, fields: list[tuple[str, str]]) -> Optional[Div]:
    """Renders data in a simple two-column flex layout."""
    if data_dict is None: return None
    items = []
    for key, label in fields:
        value = data_dict.get(key)
        if value:
            row_div = Div(
                Div(label, cls="font-bold w-1/3 flex-shrink-0"),
                Div(str(value), cls="w-2/3"),
                cls="flex gap-x-2 items-baseline"
            )
            items.append(row_div)
    if not items: return None
    return Div(*items, cls="space-y-1")

def ReviewSection(title: str, edit_url: str, *content, count: Optional[int] = None) -> FT:
    """Creates a section with the 'title-on-border' style."""
    display_title = f"{title} ({count})" if count is not None and count > 0 else title
    
    return Div(
        # Flex container for title and edit link
        Div(
            Span(
                display_title,
                cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300"
            ),
            A(
                "Muuda",
                href=edit_url,
                # MODIFIED: Adjusted position to be slightly lower
                cls="absolute top-0 right-4 text-primary underline hover:no-underline text-sm"
            ),
        ),
        # Inner content with padding
        Div(*content, cls="p-4 md:p-6"),
        # Main container styling
        cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
    )

def render_review_page(data: dict) -> FT:
    """
    Renders the application review page with consistent section styling.
    """
    user_data = data.get('user', {})
    profile_data = data.get('profile', {})
    qualifications = data.get('qualifications', [])
    experiences = data.get('experience', [])
    experience_count = data.get('experience_count', 0)
    education_doc = data.get('education', {})
    training_files = data.get('training_files', [])
    employment_proof = data.get('employment_proof', {})

    content_sections = []

    # --- Applicant Section ---
    applicant_fields = [('full_name', 'Nimi'), ('email', 'E-post'), ('birthday', 'Sünniaeg'), ('address', 'Aadress'), ('phone', 'Telefon')]
    combined_profile = {**user_data, **profile_data}
    if 'hashed_password' in combined_profile: del combined_profile['hashed_password']
    applicant_dl = render_data_dl(combined_profile, applicant_fields)
    content_sections.append(
        ReviewSection(
            "Taotleja andmed", "/app/taotleja",
            applicant_dl if applicant_dl else P("Taotleja andmed puuduvad.", cls="text-sm text-muted-foreground")
        )
    )

    # --- Qualifications Section ---
    qual_items = []
    if qualifications:
        for q in qualifications:
            item_content = Span(
                f"{q.get('level', '')} - {q.get('qualification_name', '')}: ",
                I(q.get('specialisation')), 
                cls="font-medium text-sm"
            )
            qual_items.append(Li(item_content))

    content_sections.append(
        ReviewSection(
            "Taotletavad kutsed", "/app/kutsed",
            Ul(*qual_items, cls="list-disc list-inside space-y-1") if qual_items else P("Valitud kutsed puuduvad.", cls="text-sm text-muted-foreground")
        )
    )

    # --- Work Experience Section ---
    exp_items = []
    if experiences:
        labels = {"object": "Objekt:", "work_keywords": "Teostatud tööd:", "permit_required": "Luba nõutav:"}
        for i, exp in enumerate(experiences):
            details = []
            date_range = f"{exp.get('start_date', '')} - {exp.get('end_date', '...')}"
            line1 = Div( Div( Strong(exp.get('role', 'N/A'), cls="text-sm"), Span(f" @ {exp.get('company_name', 'N/A')}", cls="text-xs text-muted-foreground ml-1") ), Div( Span(date_range, cls="text-xs text-muted-foreground whitespace-nowrap"), cls="text-right flex-shrink-0 ml-2" ), cls="flex justify-between items-center" )
            details.append(line1)
            def add_detail_line(label_key, value):
                if value: details.append(Div(Strong(labels.get(label_key, ""), cls="text-muted-foreground mr-1"), value.replace(',', ', '), cls="text-xs mt-1"))
            obj_parts = [p for p in [exp.get('object_address'), f"({exp.get('object_purpose')})" if exp.get('object_purpose') else '', f"[EHR: {exp.get('ehr_code')}]" if exp.get('ehr_code') else ''] if p]
            add_detail_line("object", " ".join(obj_parts))
            add_detail_line("work_keywords", exp.get('work_keywords'))
            add_detail_line("permit_required", "Jah" if exp.get('permit_required') == 1 else "Ei")
            separator_cls = "border-t border-gray-200 pt-2 mt-2" if i > 0 else ""
            exp_items.append(Div(*details, cls=separator_cls))
    content_sections.append(
        ReviewSection(
            "Töökogemused", "/app/workex",
            Div(*exp_items, cls="space-y-2") if exp_items else P("Töökogemusi pole lisatud.", cls="text-sm text-muted-foreground"),
            count=experience_count
        )
    )

    # --- Documents Section (Combined) ---
    doc_items = []
    if education_doc and education_doc.get('original_filename'):
        # Metadata for education is a JSON string, so we need to load it
        edu_meta = json.loads(education_doc.get('metadata', '{}'))
        edu_desc = f"{edu_meta.get('institution')} ({edu_meta.get('specialty')})"
        doc_items.append(Li(Span("Haridus: ", cls="font-semibold"), A(edu_desc, href=f"/files/view/{education_doc.get('storage_identifier')}", target="_blank", cls="link text-sm")))
    
    if training_files:
        for tf in training_files:
            doc_items.append(Li(Span("Täiendkoolitus: ", cls="font-semibold"), A(tf.get('description', 'Nimetu fail'), href=f"/files/view/{tf.get('storage_identifier')}", target="_blank", cls="link text-sm")))
    
    if employment_proof and employment_proof.get('original_filename'):
        doc_items.append(Li(Span("Töötamise tõend: ", cls="font-semibold"), A(employment_proof['original_filename'], href=f"/files/view/{employment_proof.get('storage_identifier')}", target="_blank", cls="link text-sm")))

    content_sections.append(
        ReviewSection(
            "Lisatud dokumendid", "/app/dokumendid",
            Ul(*doc_items, cls="list-disc list-inside space-y-1") if doc_items else P("Ühtegi dokumenti pole lisatud.", cls="text-sm text-muted-foreground")
        )
    )

    # --- Submission Section ---
    submission_section = Section(
        P("Palun vaata taotluse andmed hoolikalt üle. Esitamisel saadetakse taotlus menetlemiseks EEELi kutsekomisjonile ning koopia sinu e-postile.", cls="mt-4 mb-3 text-center text-sm text-muted-foreground"),
        Form(
             Div(Button("Esita taotlus", type="submit", cls="btn btn-primary text-xl mt-4 mb-8"), cls="flex justify-center"),
             method="post",
             hx_post="/app/ulevaatamine/submit",
             hx_confirm="Oled kindel, et soovid taotluse esitada?",
             hx_target="#tab-content-container",
             hx_swap="innerHTML"
        ),
        cls="my-6 pt-4 border-t"
    )

    # --- Assemble final page content ---
    return Div(
        # H3("Taotluse ülevaatamine ja esitamine", cls="text-xl font-semibold mb-4"), # <-- REMOVED/COMMENTED OUT
        *content_sections,
        submission_section,
        cls="p-0 md:p-4"
    )