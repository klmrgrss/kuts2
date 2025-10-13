# app/ui/landing/footer.py
from fasthtml.common import *
from monsterui.all import *
import datetime

def render_footer():
    """Renders the application-wide public footer."""
    return Footer(
        Container(
            Div(
                Img(src="/static/logo_EEEL.png", cls="h-8 mr-2 bg-blue-800"),
                P(f"© {datetime.date.today().year} Eesti Ehitusettevõtjate Liit. Kõik õigused kaitstud."),
                # A("Privaatsuspoliitika", href="#", cls="link"), # Uncomment when you have a privacy policy
                cls="flex justify-between items-center text-sm text-muted-foreground"
            )
        ),
        cls="py-6 border-t mt-12"
    )