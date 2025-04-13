# app/ui/evaluator/applicant_summary.py

from fasthtml.common import *
from monsterui.all import * # Import components like Card, Grid, Strong, Span etc.
from typing import Optional, Dict, List

# Placeholder for the download base URL
FILE_DOWNLOAD_BASE_URL = "/files/download"

# Helper function to format YYYY-MM-DD to DD.MM.YYYY (keep from previous version)
def format_iso_to_estonian_date(iso_date_str: Optional[str]) -> str:
    """Converts 'YYYY-MM-DD' to 'DD.MM.YYYY'. Returns original or 'N/A' on error."""
    if not iso_date_str or len(iso_date_str) != 10:
        return iso_date_str or 'N/A'
    try:
        year, month, day = iso_date_str.split('-')
        if not (year.isdigit() and month.isdigit() and day.isdigit()):
            return iso_date_str
        return f"{day}.{month}.{year}"
    except ValueError:
        return iso_date_str


def render_applicant_summary(
    user_data: Optional[Dict],
    education_data: Optional[Dict],
    training_files: Optional[List[Dict]],
    emp_proof_data: Optional[Dict]
) -> FT:
    """
    Renders the applicant summary section WITHOUT card styling.
    """
    # Handle potentially missing data gracefully
    user_data = user_data or {}
    education_data = education_data or {}
    training_files = training_files or []
    emp_proof_data = emp_proof_data or {}

    # Line 1: Applicant Name and Placeholder Date (remains the same)
    line1_container = Div(
        H3(user_data.get('full_name', 'N/A'), cls="text-xl md:text-2xl font-bold"),
        Span("Taotluse esitamise kuupäev: ", cls="text-xs font-light text-muted-foreground"),
        cls="flex items-baseline justify-between"
    )

    # Prepare Line 2 Items (remains the same)
    line2_items = []
    email = user_data.get('email')
    if email: line2_items.append(Span(email, cls="text-sm text-muted-foreground"))
    birthday_iso = user_data.get('birthday')
    if birthday_iso:
        formatted_birthday = format_iso_to_estonian_date(birthday_iso)
        line2_items.append(Span(formatted_birthday, cls="text-sm text-muted-foreground"))
    edu_level = education_data.get('education_detail', 'Haridus puudub')
    line2_items.append(Span(edu_level, cls="text-sm"))
    edu_doc_id = education_data.get('document_storage_identifier')
    if edu_doc_id: edu_doc_el = A("Hariduse dokument", href=f"{FILE_DOWNLOAD_BASE_URL}/{edu_doc_id}", target="_blank", cls="link text-sm")
    else: edu_doc_el = Span("Hariduse dokument", cls="text-red-500 cursor-not-allowed text-sm")
    line2_items.append(edu_doc_el)
    has_training_docs = bool(training_files and any(f.get('storage_identifier') for f in training_files))
    if has_training_docs: training_el = Span("Täiendkoolitus", cls="text-primary text-sm")
    else: training_el = Span("Täiendkoolitus", cls="text-red-500 cursor-not-allowed text-sm")
    line2_items.append(training_el)
    emp_proof_id = emp_proof_data.get('storage_identifier')
    if emp_proof_id: emp_proof_el = A("Töötamise tõend", href=f"{FILE_DOWNLOAD_BASE_URL}/{emp_proof_id}", target="_blank", cls="link text-sm")
    else: emp_proof_el = Span("Töötamise tõend", cls="text-red-500 cursor-not-allowed text-sm")
    line2_items.append(emp_proof_el)

    # Line 2: Container Div (remains the same)
    line2_container = Div(
        *line2_items,
        cls="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1"
    )

    # --- Return content wrapped in a simple Div with margin ---
    # Remove Card() and CardBody() wrappers
    return Div(
        line1_container,  # Line 1
        line2_container,  # Line 2
        cls="mb-4" # Apply bottom margin to this outer Div instead of the Card
    )