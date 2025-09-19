# klmrgrss/kuts2/kuts2-sticky-bar/app/ui/qualification_form.py
from fasthtml.common import *
from monsterui.all import *
from .custom_components import StickyActionBar
from .checkbox_group import render_checkbox_group

def FormSection(*children, **kwargs):
    """A simple helper component that creates a Div and passes along any keyword arguments."""
    return Div(*children, **kwargs)

def Pill(text: str, bg_color: str):
    """A helper component to create a styled 'pill' or 'badge'."""
    return Span(text, cls=f"px-2.5 py-1 rounded-full text-xs font-semibold {bg_color}")

def QualificationStatusStrip(sections: dict):
    """Renders a status strip indicating how many activity areas have selections."""
    
    sections_with_selections = sum(1 for section in sections.values() if section.get("preselected"))

    if sections_with_selections == 0:
        return Div(
            UkIcon("info", cls="flex-shrink-0"),
            P("Ühtegi tegevusala pole valitud."),
            cls="p-4 bg-red-100 text-red-800 rounded-lg my-4 flex items-center gap-x-3"
        )
    else:
        plural_text = "tegevusala" if sections_with_selections == 1 else "tegevusala"
        return Div(
            UkIcon("check-circle", cls="flex-shrink-0"),
            P(f"Valitud on {sections_with_selections} {plural_text}."),
            cls="p-4 bg-green-100 text-green-800 rounded-lg my-4 flex items-center gap-x-3"
        )

def render_qualification_form(sections: dict, app_id: str):
    """
    Renders the qualification selection form with a clear, responsive,
    label-value aligned layout for wide screens.
    """

    level_colors = {
        "Ehitusjuht, TASE 6": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
        "Ehituse tööjuht, TASE 5": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        "Oskustööline, TASE 4": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
    }
    default_color = "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"

    border_colors = {
        "Ehitusjuht, TASE 6": "border-blue-300 dark:border-blue-700",
        "Ehituse tööjuht, TASE 5": "border-green-300 dark:border-green-700",
        "Oskustööline, TASE 4": "border-yellow-300 dark:border-yellow-700"
    }
    default_border_color = "border-gray-300 dark:border-gray-600"

    form_content = Form(
        QualificationStatusStrip(sections),

        *[
            Div(
                Div(
                    Small("KUTSETASE", cls="text-xs font-semibold text-muted-foreground"),
                    Pill(section["level"], bg_color=level_colors.get(section["level"], default_color)),
                    cls="absolute -top-3 left-4 bg-background px-2 flex items-center gap-x-2"
                ),
                Div(
                    Div(
                        Small("TEGEVUSALA", cls="text-xs font-semibold text-muted-foreground"),
                        cls="md:col-span-1"
                    ),
                    Div(
                        P(section["category"], cls="text-2xl md:ml-1 md:text-2xl font-bold text-foreground"),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4 items-center"
                ),
                DividerSplit(P("SPETSIALISEERUMINE", cls="text-xs font-semibold  text-muted-foreground")),
                Div(
                    (LabelSwitch(
                        "Tervik",
                        id=f"toggle-{section['id']}", name=f"toggle-{section['id']}", value="on",
                        checked=section.get("toggle_on", False),
                        hx_post=f"/app/kutsed/toggle?section_id={section['id']}&app_id={app_id}",
                        hx_target=f"#checkbox-group-{section['id']}", hx_swap="outerHTML",
                        hx_include="this", hx_trigger="change",
                        cls="flex items-center gap-2 mb-3 text-sm italic font-semibold text-muted-foreground"
                    ) if len(section["items"]) > 1 else Div()),
                    cls="flex justify-center"
                ),
                Div(
                    Div(cls="md:col-span-1"),
                    Div(
                        render_checkbox_group(
                            section_id=section["id"],
                            items=section["items"],
                            section_info={"level": section["level"], "category": section["category"]},
                            checked_state=section["preselected"]
                        ),
                        cls="md:col-span-4"
                    ),
                    cls="grid grid-cols-1 md:grid-cols-5 gap-y-1 md:gap-x-4"
                ),

                id=f"qual-section-{section['id']}",
                cls=f"relative mt-8 mb-10 border-4 rounded-lg p-4 space-y-4 {border_colors.get(section['level'], default_border_color)}"
            )
            for section in sections.values()
        ],
        method="post",
        hx_post="/app/kutsed/submit",
        hx_target="#tab-content-container",
        hx_swap="innerHTML",
        id="qualification-form",
        cls="space-y-8 validated-form",
        data_validation_mode="dirty"
    )

    action_bar = StickyActionBar(form_id="qualification-form")
    
    # The inline <script> has been completely removed from this component.
    page_content = Div(
        form_content
    )

    return page_content, action_bar