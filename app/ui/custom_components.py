# app/ui/custom_components.py
from fasthtml.common import *
from monsterui.all import *
from typing import Optional

def StickyActionBar(
    form_id: str,
    save_text: str = "Salvesta valikud",
    cancel_url: Optional[str] = None,
    cancel_text: str = "Tühista",
    delete_url: Optional[str] = None,
    delete_text: str = "Kustuta töökogemus",
    **kwargs
):
    """
    Creates a sticky bar at the bottom of the viewport for form actions.
    The cancel button now uses HTMX to reload the main tab content.
    """
    save_button = Button(save_text, type="submit", form=form_id, cls="btn btn-primary", disabled=True)

    # --- FIX: Changed Cancel from a link (A) to a button (Button) ---
    cancel_button = ""
    if cancel_url:
        cancel_button = Button(
            cancel_text,
            type="button", # Ensure it doesn't submit the form
            hx_get=cancel_url,
            hx_target="#tab-content-container",
            hx_swap="innerHTML",
            cls="btn btn-secondary disabled" # Still controlled by form_validator.js
        )

    delete_button = ""
    if delete_url:
        delete_button = Button(
            delete_text,
            type="button",
            cls="btn btn-error",
            hx_delete=delete_url,
            hx_confirm="Oled kindel, et soovid selle töökogemuse kustutada?",
            hx_target="#tab-content-container",
            hx_swap="innerHTML"
        )

    attrs = {
        "cls": "sticky-action-bar",
        "data-form-id": form_id
    }
    attrs.update(kwargs)

    return Div(
        Div(
            Div(
                Div(delete_button, cls="mr-auto"),
                Div(cancel_button, save_button, cls="flex space-x-2"),
                cls="flex justify-between items-center w-full"
            ),
            cls="max-w-5xl mx-auto px-4"
        ),
        **attrs
    )