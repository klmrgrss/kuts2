# app/ui/dashboard_page.py
from fasthtml.common import *
from monsterui.all import *

def render_applicant_dashboard(data: dict, applicant_name: str) -> FT:
    """Renders the applicant's view of the dashboard."""
    
    return Div(
        Span(applicant_name, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300"),
        Div(
            Div(
                *[Div(P(key, cls="font-semibold text-muted-foreground w-1/3"), P(value, cls="w-2/3")) for key, value in data.items()],
                cls="space-y-3"
            ),
            Hr(cls="my-6 border-border"),
            Div(
                A(Button("Jätka taotluse täitmist", cls=ButtonT.primary), href="/app/kutsed"),
                A("Logi välja", href="/logout", cls="text-sm text-muted-foreground hover:underline"),
                cls="flex justify-between items-center"
            ),
            cls="p-6"
        ),
        cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
    )

def render_evaluator_dashboard(data: dict) -> FT:
    """Renders the evaluator's view of the dashboard."""
    
    review_count = data.get("applications_to_review", 0)
    
    return Div(
        Span("Hindaja Töölaud", cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300"),
        Div(
            Div(
                Div(
                    P("Ülevaatamist ootavad taotlused:", cls="font-semibold text-muted-foreground"),
                    P(str(review_count), cls="text-2xl font-bold"),
                    cls="text-center"
                ),
                cls="space-y-3"
            ),
            Hr(cls="my-6 border-border"),
            Div(
                A(Button("Ava hindamiskeskkond", cls=ButtonT.primary), href="/evaluator/d"),
                A("Logi välja", href="/logout", cls="text-sm text-muted-foreground hover:underline"),
                cls="flex justify-between items-center"
            ),
            cls="p-6"
        ),
        cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
    )