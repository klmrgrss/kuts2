# gem/ui/custom_components.py

from fasthtml.common import *

# Function definition renamed to InputTag to match convention and user preference
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

    # *** CORRECTED RETURN STATEMENT ***
    # Return the outermost Div containing the component structure
    return Div(
        # This inner Div holds the hidden input and the visible part
        Div(
            Input(type="hidden", id=hidden_input_id, name=name, value=processed_value),
            Div( # This is the visible container styled like an input
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
            # Accessibility live region
            Div(aria_live="polite", aria_atomic="true", cls="sr-only", id=f"sr-{container_id}"),
        ),
        # Attributes for the outermost container Div
        id=container_id,
        cls=f"custom-input-tag-container {cls}" # Hook class + any passed classes
    )