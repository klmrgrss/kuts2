# app/ui/dashboard_page.py
from fasthtml.common import *
from monsterui.all import *


def render_applicant_dashboard(data: dict, applicant_name: str) -> FT:
    """
    Renders the applicant's view of the dashboard.

    Args:
        data (dict): A dictionary containing the applicant's data to be displayed.
        applicant_name (str): The name of the applicant.

    Returns:
        FT: A FastHTML component representing the applicant's dashboard.
    """
    
    return Div(
        # Applicant's name, styled as a floating label on the top border of the container.
        Span(applicant_name, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300"),
        Div(
            # Main content area of the dashboard.
            Div(
                # Iterates through the data dictionary and displays key-value pairs.
                *[Div(P(key, cls="font-semibold text-muted-foreground w-1/3"), P(value, cls="w-2/3")) for key, value in data.items()],
                cls="space-y-3"
            ),
            # A horizontal rule to separate content sections.
            Hr(cls="my-6 border-border"),
            # Bottom section with action buttons.
            Div(
                # A button linking to the main application page.
                A(Button("Taotluse juurde", cls=ButtonT.primary), href="/app/kutsed"),
                # A link to log out.
                A("Logi välja", href="/logout", cls="text-sm text-muted-foreground hover:underline"),
                cls="flex justify-between items-center"
            ),
            cls="p-6"
        ),
        # The main container with a border and rounded corners.
        cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
    )


def render_evaluator_dashboard(data: dict) -> FT:
    """
    Renders the evaluator's view of the dashboard.

    Args:
        data (dict): A dictionary containing data for the evaluator, including the number of applications to review.

    Returns:
        FT: A FastHTML component representing the evaluator's dashboard.
    """
    
    # Retrieves the number of applications to review from the data dictionary.
    review_count = data.get("applications_to_review", 0)
    
    return Div(
        # Dashboard title, styled as a floating label on the top border of the container.
        Span("Hindaja Töölaud", cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600 dark:text-gray-300"),
        Div(
            # Main content area of the dashboard.
            Div(
                Div(
                    # Displays the number of applications waiting for review.
                    P("Ülevaatamist ootavad taotlused:", cls="font-semibold text-muted-foreground"),
                    P(str(review_count), cls="text-2xl font-bold"),
                    cls="text-center"
                ),
                cls="space-y-3"
            ),
            # A horizontal rule to separate content sections.
            Hr(cls="my-6 border-border"),
            # Bottom section with action buttons.
            Div(
                # A button linking to the evaluator's environment.
                A(Button("Ava hindamiskeskkond", cls=ButtonT.primary), href="/evaluator/d"),
                # A link to log out.
                A("Logi välja", href="/logout", cls="text-sm text-muted-foreground hover:underline"),
                cls="flex justify-between items-center"
            ),
            cls="p-6"
        ),
        # The main container with a border and rounded corners.
        cls="relative mt-8 rounded-lg border-2 border-border dark:border-gray-600"
    )
