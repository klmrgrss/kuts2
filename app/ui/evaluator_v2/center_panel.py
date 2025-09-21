# app/ui/evaluator_v2/center_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import Dict

def render_center_panel(qual_data: Dict, user_data: Dict) -> FT:
    """
    Renders the center panel with the details of the selected qualification
    and the argumentation/decision components.
    """
    applicant_name = user_data.get('full_name', 'N/A')
    qual_name = f"{qual_data.get('level', '')} - {qual_data.get('qualification_name', '')}"
    specialisation = qual_data.get('specialisation', 'N/A')

    header = Div(
        H2(applicant_name, cls="text-2xl font-bold"),
        P(qual_name, cls="text-lg text-gray-600"),
        P(f"Spetsialiseerumine: {specialisation}", cls="text-sm text-gray-500"),
        cls="p-4 border-b bg-gray-50"
    )

    # Placeholder for argumentation and decision form
    decision_area = Div(
        H3("Otsus ja kommentaarid", cls="text-xl font-semibold mb-4"),
        TextArea(
            name="eval_comment",
            placeholder="Sisesta siia oma kommentaarid ja põhjendused...",
            rows=8,
            cls="textarea textarea-bordered w-full"
        ),
        Select(
            Options("Otsus tegemata", "Vastab", "Ei vasta", "Vajab lisainfot"),
            name="eval_decision",
            cls="select select-bordered w-full mt-4"
        ),
        cls="p-4"
    )

    # Chat/Action area at the bottom
    chat_input_area = Div(
        TextArea(
            placeholder="Sisesta kiirmärge või alusta arutelu...",
            rows=2,
            cls="textarea textarea-bordered w-full"
        ),
        Button("Salvesta märge", cls="btn btn-secondary mt-2"),
        cls="p-4 border-t sticky bottom-0 bg-white"
    )

    return Div(
        header,
        decision_area,
        chat_input_area,
        # The ID and hx_swap_oob attribute are crucial for HTMX
        id="ev-center-panel",
        hx_swap_oob="true",
        cls="flex flex-col h-full" # Ensure it fills the vertical space
    )