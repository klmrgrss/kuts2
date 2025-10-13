# app/ui/landing/features_section.py
from fasthtml.common import *
from monsterui.all import *

def render_features_section():
    """Renders the features/benefits section of the landing page."""
    return Container(
         Section(
             H2("Üks keskkond, kõik vajalik", cls="text-3xl font-bold mb-12 text-center"),
             Grid(
                 Card(CardHeader(UkIcon("archive", cls="w-8 h-8 text-primary")), CardBody(H3("Tsentraliseeritud haldus"), P("Hoia kõiki oma taotlusi, dokumente ja töökogemusi ühes kohas."))),
                 Card(CardHeader(UkIcon("compass", cls="w-8 h-8 text-primary")), CardBody(H3("Juhendatud protsess"), P("Süsteem juhendab sind läbi andmete sisestamise, tagades korrektse tulemuse."))),
                 Card(CardHeader(UkIcon("lock", cls="w-8 h-8 text-primary")), CardBody(H3("Turvaline ja usaldusväärne"), P("Kasutame sisselogimiseks turvalist Smart-ID lahendust ja Sinu andmeid hoitakse turvaliselt."))),
                 cols=1, md_cols=3,
                 cls="gap-8"
             ),
             cls="py-12"
         )
     )