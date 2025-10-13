# app/ui/landing/info_section.py
from fasthtml.common import *
from monsterui.all import *

def render_info_section():
    """
    Renders the informational section with FAQs and links to important documents.
    Designed for future expansion with more content.
    """
    # Placeholder for FAQ items. We can build this out later.
    faq_items = Div(
        Details(
            Summary(H4("Mida ma vajan taotluse esitamiseks?", cls="font-semibold cursor-pointer"), cls="py-2"),
            P("Taotlemiseks on vajalik kehtiv Smart-ID, digitaalsed koopiad haridust ja täiendkoolitusi tõendavatest dokumentidest ning ülevaade oma varasemast töökogemusest.", cls="text-muted-foreground pb-2")
        ),
        Details(
            Summary(H4("Kui kaua menetlus aega võtab?", cls="font-semibold cursor-pointer"), cls="py-2"),
            P("Menetlusprotsessi kestus sõltub taotluse keerukusest ja esitatud andmete korrektsusest. Täpsemat infot näed peale sisselogimist oma töölaualt.", cls="text-muted-foreground pb-2")
        )
    )

    # Links to important rules and documents
    docs_card = Card(
        CardHeader(H3("Olulised viited ja reeglid")),
        CardBody(
            Ul(
                Li(A("Ehitusjuht, tase 6 - Nõuded", href="#", target="_blank", cls="link")),
                Li(A("Ehituse tööjuht, tase 5 - Nõuded", href="#", target="_blank", cls="link")),
                Li(A("Oskustöölise kutse - Nõuded", href="#", target="_blank", cls="link")),
                cls="list-disc list-inside space-y-2"
            )
        ),
        cls="border-primary"
    )

    return Container(
        Section(
            H2("Juhendid ja Abimaterjalid", cls="text-3xl font-bold mb-12 text-center"),
            Grid(
                Div(faq_items),  # Left column for FAQs
                Div(docs_card),  # Right column for documents
                cols=1, lg_cols=2, cls="gap-8 lg:gap-12 items-start"
            ),
            cls="py-12"
        )
    )