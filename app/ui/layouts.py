# ui/layouts.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Dict, Any, Tuple # Import Tuple for type hint
from starlette.requests import Request # Import Request for type hint

# Import the appropriate navbar functions needed
# If evaluator_layout uses evaluator_navbar, import it here too
from .nav_components import render_sticky_header, app_navbar, evaluator_navbar # Import all used navbars

# AG Grid CDN links (keep as they were)
ag_grid_js_cdn = "https://cdn.jsdelivr.net/npm/ag-grid-community/dist/ag-grid-community.min.js"
ag_grid_css_cdn = "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-grid.css"
ag_theme_css_cdn = "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-quartz.css" # Or another theme

# --- Flatpickr CDN Links ---
flatpickr_css_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"
flatpickr_js_cdn = "https://cdn.jsdelivr.net/npm/flatpickr"
flatpickr_month_plugin_css_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/style.css" # Verify path
flatpickr_month_plugin_js_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/index.js" # Verify path
flatpickr_locale_et_js_cdn = "https://npmcdn.com/flatpickr/dist/l10n/et.js" # Estonian locale


# --- ToastAlert Component (keep as is) ---
def ToastAlert(message: str, alert_type: str = 'info', icon_name: Optional[str] = None) -> FT:
    # ... (ToastAlert code remains unchanged) ...
    base_classes = "fixed bottom-4 right-4 z-50 p-3 rounded-md shadow-lg flex items-center"
    type_classes = {
        'info': "bg-blue-100 border border-blue-300 text-blue-800",
        'success': "bg-green-100 border border-green-300 text-green-800",
        'warning': "bg-orange-100 border border-orange-300 text-orange-800",
        'error': "bg-red-100 border border-red-300 text-red-800",
    }
    specific_classes = type_classes.get(alert_type, type_classes['info'])
    if icon_name is None:
        icon_map = {'info': 'info', 'success': 'check-circle', 'warning': 'alert-triangle', 'error': 'alert-circle'}
        icon_name = icon_map.get(alert_type, 'info')
    content_items = []
    if icon_name: content_items.append(UkIcon(icon_name, cls="inline-block w-5 h-5"))
    content_items.append(Span(message, cls="ml-2 align-middle" if icon_name else "align-middle"))
    return Div(
        *content_items, cls=f"{base_classes} {specific_classes}", id="error-toast",
        style="display: none;", data_toast_message=message, data_toast_status=alert_type
    )


# --- base_layout function (MODIFIED to include Flatpickr) ---
def base_layout(title: str, *content: Any, theme_headers: tuple = Theme.blue.headers()) -> FT:
    # Combine theme headers with other necessary global assets
    all_hdrs = list(theme_headers) # Start with theme
    all_hdrs.extend([
        # AG Grid (keep existing)
        # Link(rel="stylesheet", href=ag_grid_css_cdn), # Base grid CSS if needed
        Link(rel="stylesheet", href=ag_theme_css_cdn), # Theme CSS
        # Flatpickr CSS
        Link(rel="stylesheet", href=flatpickr_css_cdn),
        Link(rel="stylesheet", href=flatpickr_month_plugin_css_cdn),
        # Core JS Libraries
        Script(src="https://unpkg.com/htmx.org@1.9.10"), # HTMX
        Script(src=ag_grid_js_cdn, defer=True),         # AG Grid JS
        # Flatpickr JS Libraries
        Script(src=flatpickr_js_cdn),                   # Flatpickr Core
        Script(src=flatpickr_locale_et_js_cdn),         # Flatpickr Estonian Locale
        Script(src=flatpickr_month_plugin_js_cdn),      # Flatpickr Month Plugin
        # Custom JS (ensure these come AFTER libraries they depend on)
        Script(src="/static/js/tab_scroll.js"),         # Your tab scroll
        Script(src="/static/js/input_tag.js", defer=True),  # Your input tag
        Script(src="/static/js/education_form.js"),     # Your education form specific JS (if still needed)
        # +++ ADD FLATICKR INITIALIZER +++
        Script(src="/static/js/flatpickr_init.js", defer=True), Style("""
                    .ag-header-cell-filter-button { display: none !important; }
                        """), # Your new Flatpickr initializer
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.2/dist/vis-timeline-graph2d.min.css"),
        Script(src="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.2/standalone/umd/vis-timeline-graph2d.min.js"),
        Script(src="/static/js/vis_timeline_init.js", defer=True),
    ])

    return Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title(title, id="page-title"),
            # Include all combined headers
            *all_hdrs
        ),
        Body(
            *content,
            Div(id="toast-container"), # For potential toasts
            cls="bg-background text-foreground"
        ),
        lang="et" # Keep Estonian language attribute
    )


# --- public_layout function (keep as is) ---
def public_layout(title: str, *content: Any) -> FT:
    # ... (public_layout code remains unchanged) ...
    return base_layout(title, Container( *content, cls="flex flex-col items-center justify-center min-h-screen py-12" ) )


# --- app_layout (keep as is, uses render_sticky_header) ---
def app_layout(request: Request, title: str, content: Any, active_tab: str, badge_counts: Dict = {}) -> FT:
    """
    Main layout using a single combined sticky header.
    Centers content container on medium screens and up.
    """
    print(f"--- DEBUG: app_layout rendering with title: '{title}' ---")
    sticky_header = render_sticky_header(
        request=request, active_tab=active_tab, badge_counts=badge_counts
    )
    main_content_container = Container(
        Div(content, id="tab-content-container"),
        cls=f"{ContainerT.xl} pt-8 md:max-w-screen-lg md:mx-auto" # Centering classes
    )
    return base_layout(title, sticky_header, main_content_container)

# --- evaluator_layout (MODIFIED) ---
def evaluator_layout(request: Request, title: str, content: Any) -> FT:
    """
    Layout for evaluator views, using a WIDER (2xl) centered container.
    """
    page_title = f"{title} | Hindamiskeskkond"

    # --- Use a wider max-width class ---
    MAX_WIDTH_CLASS = "md:max-w-screen-xl" # Changed from xl to 2xl

    navbar_container = Div(
        evaluator_navbar(request),
        cls=f"w-full {MAX_WIDTH_CLASS} md:mx-auto" # Apply wider class
    )
    main_content_container = Container(
        content,
        cls=f"{ContainerT.xl} pt-8 {MAX_WIDTH_CLASS} md:mx-auto" # Apply wider class
    )
    return base_layout(page_title, navbar_container, main_content_container)