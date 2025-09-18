# gem/ui/custom_components.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional

# InputTag function remains unchanged...
def InputTag(name: str, value: str = "", placeholder: str = "", max_length: int = 24, disabled: bool = False, cls: str = ""):
    """
    Renders an interactive tag input component.
    Follows Fasthtml convention by using PascalCase name.
    """
    container_id = f"input-tag-{name}"
    hidden_input_id = f"hidden-input-{name}"
    text_input_id = f"text-input-{name}"
    tag_container_id = f"tag-container-{name}" # Div holding the visible tags + input

    initial_tags = []
    processed_value = ""
    if value:
        tag_list = [tag.strip() for tag in value.split(',') if tag.strip()]
        valid_tags = []
        for tag_text in tag_list:
            if len(tag_text) <= max_length:
                 valid_tags.append(tag_text)
                 initial_tags.append(
                     Span(
                         tag_text,
                         Button(
                             "✕",
                             type="button",
                             aria_label=f"Remove tag {tag_text}",
                             data_value=tag_text,
                             cls="input-tag-remove ml-1 text-red-500 hover:text-red-700 font-bold text-xs align-middle cursor-pointer"
                         ),
                         cls="input-tag-item inline-flex items-center bg-gray-200 text-gray-800 rounded px-2 py-0.5 text-sm mr-1 mb-1"
                     )
                 )
        processed_value = ",".join(valid_tags)

    container_classes = "input input-bordered w-full input-sm flex flex-wrap items-center gap-1 min-h-[2.5rem] h-auto"

    return Div(
        Div(
            Input(type="hidden", id=hidden_input_id, name=name, value=processed_value),
            Div(
                *initial_tags,
                Input(
                    type="text",
                    id=text_input_id,
                    placeholder=placeholder,
                    maxlength=str(max_length),
                    disabled=disabled,
                    cls="input-tag-input border-none outline-none focus:ring-0 p-1 flex-grow text-sm bg-transparent disabled:bg-gray-100",
                    data_input_tag_container=container_id
                ),
                id=tag_container_id,
                cls=container_classes,
            ),
            Div(aria_live="polite", aria_atomic="true", cls="sr-only", id=f"sr-{container_id}"),
        ),
        id=container_id,
        cls=f"custom-input-tag-container {cls}"
    )

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
    
    # --- FIX: Make Cancel button an HTMX-powered link ---
    cancel_button = ""
    if cancel_url:
        cancel_button = A(
            cancel_text,
            href=cancel_url, # Keep href for right-click/new-tab functionality
            hx_get=cancel_url,
            hx_target="#tab-content-container", # Target the main content area
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