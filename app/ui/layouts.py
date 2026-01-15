# app/ui/layouts.py
from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Dict, Any, Tuple
from starlette.requests import Request

from .nav_components import render_sticky_header, app_navbar, evaluator_navbar

# --- CDN Links ---
ag_grid_js_cdn = "https://cdn.jsdelivr.net/npm/ag-grid-community/dist/ag-grid-community.min.js"
ag_theme_css_cdn = "https://cdn.jsdelivr.net/npm/ag-grid-community/styles/ag-theme-quartz.css"
flatpickr_css_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"
flatpickr_js_cdn = "https://cdn.jsdelivr.net/npm/flatpickr"
flatpickr_month_plugin_css_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/style.css"
flatpickr_month_plugin_js_cdn = "https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/monthSelect/index.js"
flatpickr_locale_et_js_cdn = "https://npmcdn.com/flatpickr/dist/l10n/et.js"


# --- ToastAlert Component ---
def ToastAlert(message: str, alert_type: str = 'info', icon_name: Optional[str] = None) -> FT:
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


# --- base_layout function (MODIFIED) ---
def base_layout(title: str, *content: Any, theme_headers: tuple = Theme.blue.headers()) -> FT:
    all_hdrs = list(theme_headers)
    all_hdrs.extend([
        Link(rel="icon",href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🇪🇪</text></svg>"),
        #Link(rel="stylesheet", href=ag_theme_css_cdn),
        Link(rel="manifest", href="/static/manifest.json"),
        Link(rel="stylesheet", href=flatpickr_css_cdn),
        Link(rel="stylesheet", href=flatpickr_month_plugin_css_cdn),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src=ag_grid_js_cdn, defer=True),
        Script(src=flatpickr_js_cdn),
        Script(src=flatpickr_locale_et_js_cdn),
        Script(src=flatpickr_month_plugin_js_cdn),
        Script(src="/static/js/tab_scroll.js", defer=True),
        Script(src="/static/js/form_validator.js", defer=True),
        Script(src="/static/js/flatpickr_init.js", defer=True),
        Script(src="/static/js/qualification_scroll.js", defer=True),
        Script(src="/static/js/qualification_form.js", defer=True),
        Style("""
                    .no-animation, .no-animation:hover { animation: none !important; transition: none !important; }
                    div.activity-selected { border-color: #3b82f6; }
                    a.activity-selected { border-color: #3b82f6 !important; background-color: #dbeafe !important; transform: scale(0.95); }
                    .ag-header-cell-filter-button { display: none !important; }
                    .state-unfocused { border-width: 2px; border-color: #e5e7eb; }
                    .state-in-progress { border-width: 2px; border-color: #3b82f6; }
                    .state-complete { border-width: 2px; border-color: #22c55e; }
                    .form-disabled { opacity: 0.6; pointer-events: none; }
                    .sticky-action-bar { position: fixed; bottom: 0; left: 0; right: 0; z-index: 10; background-color: rgba(255, 255, 255, 0.8); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); padding: 0.75rem; border-top: 1px solid #e5e7eb; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05); }
                    .dark .sticky-action-bar { background-color: rgba(31, 41, 55, 0.8); border-top-color: #4b5563; }
                    #tab-content-container { padding-bottom: 100px; }
                    summary { list-style: none; } /* For Firefox */
                    summary::-webkit-details-marker { display: none; } /* For Chrome, Safari */
                    """),
        Script("""
        // Immediate theme application to prevent FOUC
        (function() {
            var isDark = localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
            if (isDark) document.documentElement.classList.add('dark');
            else document.documentElement.classList.remove('dark');
        })();
        
        function toggleTheme() {
            var isDark = document.documentElement.classList.toggle('dark');
            localStorage.theme = isDark ? 'dark' : 'light';
        }
        """)
    ])
    return Html( Head( Meta(charset="UTF-8"), Meta(name="viewport", content="width=device-width, initial-scale=1.0"), Title(title, id="page-title"), *all_hdrs ), Body( *content, Div(id="toast-container"), cls="bg-background text-foreground" ), lang="et" )


# --- public_layout function ---
def public_layout(title: str, *content: Any) -> FT:
    return base_layout(title, Container( *content, cls="flex flex-col items-center justify-center min-h-screen py-12" ) )


# --- app_layout (MODIFIED to accept and pass db) ---
def app_layout(request: Request, title: str, content: Any, active_tab: str, db: Any, badge_counts: Dict = {}, container_class: str = "md:max-w-screen-lg", footer: Optional[Any] = None) -> FT:
    """
    Main layout that now accepts a 'db' object to pass to the sticky header.
    """
    print(f"--- DEBUG: app_layout rendering with title: '{title}' ---")
    sticky_header = render_sticky_header(
        request=request, active_tab=active_tab, db=db, badge_counts=badge_counts, container_class=container_class
    )
    main_content_container = Container(
        Div(content, id="tab-content-container"),
        cls=f"{ContainerT.xl} pt-8 w-full {container_class} md:mx-auto"
    )

    footer_container = Div(footer, id="footer-container") if footer else Div(id="footer-container")

    return base_layout(title, sticky_header, main_content_container, footer_container)

# --- dashboard_layout (NEW) ---
def dashboard_layout(request: Request, title: str, content: Any, db: Any) -> FT:
    """
    Renders a simpler layout for the main dashboard, including the top navbar
    but excluding the application-specific tab navigation.
    """
    # Determine which navbar to show based on role
    user_role = request.session.get("role")
    if user_role == 'evaluator':
        top_nav_content = evaluator_navbar(request, db)
    else:
        top_nav_content = app_navbar(request, db)

    top_nav = Div(
        top_nav_content,
        cls="sticky top-0 z-50 bg-background shadow-md"
    )

    main_content_container = Container(
        Div(content, id="dashboard-content-container"),
        cls=f"{ContainerT.xl} pt-8 md:max-w-screen-md md:mx-auto"
    )

    return base_layout(title, top_nav, main_content_container)

# --- evaluator_layout (MODIFIED) ---
def evaluator_layout(request: Request, title: str, content: Any, db: Any) -> FT:
    """ Renders the V1 evaluator layout, now accepting and passing the db object. """
    page_title = f"{title} | Hindamiskeskkond"
    MAX_WIDTH_CLASS = "md:max-w-screen-xl"
    # --- MODIFIED: Pass db to the navbar ---
    navbar_container = Div( evaluator_navbar(request, db), cls=f"w-full {MAX_WIDTH_CLASS} md:mx-auto" )
    main_content_container = Container( content, cls=f"{ContainerT.xl} pt-8 {MAX_WIDTH_CLASS} md:mx-auto" )
    return base_layout(page_title, navbar_container, main_content_container)