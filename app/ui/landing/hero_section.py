# app/ui/landing/hero_section.py
from fasthtml.common import *
from monsterui.all import *

def render_hero_section():
    """Renders the main hero section with an HTMX-powered Smart-ID login CTA."""
    return Div(
        Container(
            H1("Ehitamise valdkonna kutsete taotlemise keskkond", cls="text-4xl md:text-5xl font-bold mb-4 text-center"),
            #P("Esita ja halda oma kutsetaotlusi turvaliselt, kiirelt ja mugavalt.", cls="text-lg md:text-xl text-muted-foreground mb-8 text-center max-w-3xl mx-auto"),
            
            # This container will be the target for the HTMX swap
            Div(
                Button(
                    UkIcon("smartphone", cls="mr-2"),
                    "Logi sisse Smart-ID'ga",
                    cls=(ButtonT.primary, ButtonT.lg),
                    hx_get="/auth/smart-id/form",
                    hx_target="#hero-cta-container",
                    hx_swap="innerHTML"
                ),
            P("Teenusesse sisselogimiseks vajate kehtivat Smart-ID kontot.", cls="text-xs text-muted-foreground mt-4") ,               id="hero-cta-container" # The target ID for the swap
            ),
            
            cls="py-16 md:py-24 text-center"
        ),
        cls="bg-gradient-to-b from-background to-muted/50"
    )