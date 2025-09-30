# app/ui/evaluator_v2/test_search_page.py
from fasthtml.common import *
from monsterui.all import *
from typing import List, Dict

def render_test_search_page(applications: List[Dict]):
    """Renders a simple, single-page active search for applications."""

    def show_contacts(apps: list[dict]):
        """Helper to render table rows for a list of applications."""
        if not apps:
            return Tr(Td("No matching applications found.", colspan="3", cls="text-center"))
        return [
            Tr(
                Td(app.get('applicant_name', 'N/A')),
                Td(app.get('qualification_name', 'N/A')),
                Td(app.get('submission_date', 'N/A'))
            ) for app in apps
        ]

    return Titled("Evaluator Search Test",
        Container(
            H3("Search Applications"),
            Input(
                type="search",
                name="search",
                placeholder="Begin Typing To Search...",
                hx_post="/evaluator/test/search",
                hx_trigger="keyup changed delay:300ms, search",
                hx_target="#search-results",
                hx_swap="innerHTML"
            ),
            Table(
                Thead(
                    Tr(
                        Th("Applicant Name"),
                        Th("Qualification"),
                        Th("Submission Date")
                    )
                ),
                Tbody(
                    *show_contacts(applications),
                    id="search-results"
                ),
                cls="table-auto w-full mt-4"
            ),
            cls="mt-8"
        )
    )