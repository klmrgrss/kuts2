#ui/checkbox_group.py
from fasthtml.common import *
from monsterui.all import *

def render_checkbox_group(section_id, items, section_info, checked_state):
    level = section_info.get("level", "")
    category = section_info.get("category", "")
    return Div(
        *[LabelCheckboxX(
            item, id=f"qual_{section_id}_{i}", name=f"qual_{section_id}_{i}",
            value="on", checked=checked_state.get(f"qual_{section_id}_{i}", False), cls="mb-2"
        ) for i, item in enumerate(items)],
        id=f"checkbox-group-{section_id}" # This ID is targeted by HTMX swap
    )