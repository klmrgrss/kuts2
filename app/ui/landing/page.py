# app/ui/landing/page.py
from fasthtml.common import *
from ..nav_components import landing_page_navbar 
from .hero_section import render_hero_section
from .features_section import render_features_section
from .info_section import render_info_section
from .footer import render_footer

def render_landing_page():
    """Assembles the complete landing page from its components."""
    return Div(
        landing_page_navbar(),
        render_hero_section(),
        render_features_section(),
        render_info_section(),
        render_footer()
    )