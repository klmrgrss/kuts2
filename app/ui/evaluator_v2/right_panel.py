# app/ui/evaluator_v2/right_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict

def render_right_panel(documents: List[Dict], work_experience: List[Dict], bg_class: str = "bg-white dark:bg-gray-900", id_suffix: str = "") -> FT:
    """
    Renders the right panel with applicant's documents and work history
    in collapsible accordion sections. Accepts optional bg_class and id_suffix.
    """
    panel_id = f"ev-right-panel{id_suffix}"

    # --- Education Section ---
    education_docs = [doc for doc in documents if doc.get('document_type') == 'education']
    education_section = Details(
        Summary(
            UkIcon("book-open", cls="w-5 h-5"),
            "Haridus",
            Span(f"({len(education_docs)})", cls="ml-1 text-gray-500 dark:text-gray-400"),
            cls="flex items-center gap-x-2 font-semibold cursor-pointer p-3 border-b dark:border-gray-700"
        ),
        Div(
            *[
                A(doc.get('original_filename'),
                  href=f"/files/view/{doc.get('id')}",
                  target="_blank",
                  # --- THE FIX: Added truncate ---
                  cls="block p-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm link truncate")
                for doc in education_docs
            ] if education_docs else [P("Hariduse dokumente ei leitud.", cls="p-3 text-sm text-gray-500")],
        ),
        open=True
    )

    # --- Training Section ---
    training_docs = [doc for doc in documents if doc.get('document_type') == 'training']
    training_section = Details(
        Summary(
            UkIcon("award", cls="w-5 h-5"),
            "Täiendkoolitus",
            Span(f"({len(training_docs)})", cls="ml-1 text-gray-500 dark:text-gray-400"),
            cls="flex items-center gap-x-2 font-semibold cursor-pointer p-3 border-b dark:border-gray-700"
        ),
        Div(
            *[
                A(doc.get('description') or doc.get('original_filename'),
                  href=f"/files/view/{doc.get('id')}",
                  target="_blank",
                  # --- THE FIX: Added truncate ---
                  cls="block p-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm link truncate")
                for doc in training_docs
            ] if training_docs else [P("Täiendkoolituse dokumente ei leitud.", cls="p-3 text-sm text-gray-500")],
        ),
        open=True
    )

    # --- Work Experience Section ---
    work_exp_section = Details(
        Summary(
            UkIcon("briefcase", cls="w-5 h-5"),
            "Töökogemus",
            Span(f"({len(work_experience)})", cls="ml-1 text-gray-500 dark:text-gray-400"),
            cls="flex items-center gap-x-2 font-semibold cursor-pointer p-3 border-b dark:border-gray-700"
        ),
        Div(
            *[
                Div(
                    P(exp.get('object_address', 'Aadress puudub'), cls="italic font-medium text-sm truncate"),
                    P(f"{exp.get('role', '')} | {exp.get('start_date', '')} - {exp.get('end_date', '...')}", cls="italic text-xs text-gray-500"),
                    cls="p-2 border-b"
                )
                for exp in work_experience
            ] if work_experience else [P("Töökogemusi ei leitud.", cls="p-3 text-sm text-gray-500")],
        ),
        open=True
    )

    return Div(
        education_section,
        training_section,
        work_exp_section,
        id=panel_id,
        hx_swap_oob="true",
        cls=f"h-full border-l dark:border-gray-700 divide-y dark:divide-gray-700 {bg_class}"
    )