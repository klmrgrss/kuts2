# app/ui/nav_components.py

from fasthtml.common import *
from typing import Any, Dict

from fastlite import NotFoundError
from monsterui.all import *
from starlette.requests import Request

from auth.roles import ROLE_LABELS, is_admin, is_evaluator, normalize_role

# --- TABS Dictionary ---
TABS = {
    "kutsed": "Taotletavad kutsed",
    "workex": "Töökogemus",
    "dokumendid": "Dokumentide lisamine",
    "ulevaatamine": "Taotluse ülevaatamine",
    }

# --- NEW: landing_page_navbar ---
def landing_page_navbar() -> FT:
    """A simplified navbar for the public landing page without login/register buttons."""
    return Div(
        Container(
            A(
                UkIcon("brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500"),
                H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"),
                href="/",
                cls="flex items-center"
            ),
            cls="flex items-center"
        ),
        cls="flex justify-start items-center p-4 bg-background border-b border-border shadow-sm"
    )

# --- public_navbar ---
def public_navbar() -> FT:
    return Div( Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500" ), H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"), href="/", cls="flex items-center" ), cls="flex items-center" ), Div( A(Button("Logi sisse", cls=ButtonT.ghost), href="/login"), A(Button("Registreeru", cls=ButtonT.secondary), href="/register"), cls="flex items-center space-x-2" ), cls="flex justify-between items-center p-4 bg-background border-b border-border shadow-sm" )


# --- app_navbar ---
def app_navbar(request: Request, db: Any) -> FT:
    """
    Creates the main application navbar (top bar) with responsive layout.
    Displays user's full name and removes the logout button.
    """
    user_email = request.session.get("user_email", "")
    is_authenticated = request.session.get("authenticated", False)
    user_role = normalize_role(request.session.get("role"))

    # Fetch user's full name from DB
    display_name = user_email # Fallback to email
    if is_authenticated and db:
        try:
            user_data = db.t.users[user_email]
            display_name = user_data.get('full_name') or user_email
        except NotFoundError:
            print(f"--- WARN [app_navbar]: User '{user_email}' not found in DB. Using email as display name. ---")
        except Exception as e:
            print(f"--- ERROR [app_navbar]: DB lookup failed for '{user_email}'. Error: {e} ---")

    evaluator_chip = ""
    if is_evaluator(user_role):
        evaluator_chip = A(
            Label("Ava hindaja vaade", cls=LabelT.primary),
            href="/evaluator/d",
            cls="mr-4 no-underline hover:opacity-80 transition-opacity"
        )


    if is_admin(user_role):
        badge_text = ROLE_LABELS.admin
    elif is_evaluator(user_role):
        badge_text = ROLE_LABELS.evaluator
    else:
        badge_text = ROLE_LABELS.applicant

    wide_screen_left = Div(
        A(
            UkIcon("brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500"),
            H4("Kutsekeskkond", cls="inline-block align-middle"),
            Span(badge_text, cls="ml-2 px-2 py-0.5 text-sm font-semibold rounded-full bg-blue-100 text-blue-800"),
            href="/dashboard",
            cls="flex items-center"
        ),
        cls="flex items-center"
    )

    wide_screen_right = Div(
        evaluator_chip,
        A(
            UkIcon("user", cls="inline-block mr-2 align-middle"),
            Span(display_name, cls="text-sm"),
            href="/dashboard",
            cls="flex items-center mr-4 p-2 rounded hover:bg-muted transition-colors"
        ) if is_authenticated else Span(),
        cls="flex items-center"
    )

    MAX_NAME_LEN = 15
    truncated_name = (display_name[:MAX_NAME_LEN] + '…') if len(display_name) > MAX_NAME_LEN else display_name

    narrow_screen_content = Div(
        Div(
            Button(UkIcon("ellipsis-vertical", width=20, height=20), cls=ButtonT.ghost),
            cls="flex-1"
        ),
        Div(
            A(UkIcon("brick-wall", width=28, height=28, cls="text-pink-500"), href="/dashboard"),
            cls="flex-none"
        ),
        Div(
            A(
                UkIcon("user", cls="inline-block mr-1 align-middle"),
                Span(truncated_name, cls="text-sm"),
                href="/dashboard",
                cls="flex items-center"
            ),
            cls="flex-1 flex justify-end"
        ),
        cls="flex items-center w-full"
    )

    return Div(
        Div( wide_screen_left, wide_screen_right, cls="hidden md:flex justify-between items-center w-full" ),
        Div( narrow_screen_content, cls="flex md:hidden items-center w-full" ),
        cls="flex items-center p-4 bg-background border-b border-border"
    )


def tab_nav(active_tab: str, request: Request, badge_counts: Dict = None) -> FT:
    badge_counts = badge_counts or {}
    nav_items = []
    active_tab_classes = 'border-primary text-primary'
    inactive_tab_classes = 'border-transparent hover:text-muted-foreground hover:border-border'

    for tab_id, tab_name in TABS.items():
        is_active = (tab_id == active_tab)
        badge = None
        count = badge_counts.get(tab_id)
        if count is not None and count > 0:
            badge = Span(str(count), cls="uk-badge text-green-500 ml-2")

        link_classes = f"inline-block p-4 border-b-2 rounded-t-lg {active_tab_classes if is_active else inactive_tab_classes} {'tab-active' if is_active else ''}"

        link = A(
            tab_name,
            badge if badge else '',
            hx_get=f'/app/{tab_id}',
            hx_target='#tab-content-container',
            hx_swap='innerHTML',
            hx_push_url="true",
            cls=link_classes
        )
        nav_items.append(Li(link, role='presentation', cls="flex-shrink-0"))

    tab_list = Ul( *nav_items, id="tab-list-container", cls="flex flex-nowrap -mb-px text-sm font-medium text-center text-muted-foreground" )
    nav_container = Div( tab_list, cls="flex justify-center md:justify-s border-b border-border overflow-x-auto overflow-y-hidden" )
    return Nav(nav_container, aria_label="Application Tabs", cls="bg-background")


def render_sticky_header(request: Request, active_tab: str, db: Any, badge_counts: Dict = None, container_class: str = "md:max-w-screen-lg") -> FT:
    """Renders the combined sticky header, passing db to the app_navbar."""
    top_nav_content = app_navbar(request, db)
    tab_nav_content = tab_nav(active_tab, request, badge_counts)
    tab_nav_wrapper = Div(tab_nav_content, id="tab-navigation-container")

    return Div(
        Div(
            top_nav_content,
            tab_nav_wrapper,
            cls=f"w-full {container_class} md:mx-auto"
        ),
        cls="sticky top-0 z-50 bg-background shadow-md"
    )

def evaluator_navbar(request: Request, db: Any) -> FT:
    """ Renders the evaluator navbar with a consistent and responsive UI. """
    user_email = request.session.get("user_email", "")
    is_authenticated = request.session.get("authenticated", False)
    user_role = normalize_role(request.session.get("role"))

    display_name = user_email
    if is_authenticated and db:
        try:
            user_data = db.t.users[user_email]
            display_name = user_data.get('full_name') or user_email
        except NotFoundError:
            print(f"--- WARN [evaluator_navbar]: User '{user_email}' not found. ---")
        except Exception as e:
            print(f"--- ERROR [evaluator_navbar]: DB lookup failed for '{user_email}'. Error: {e} ---")

    role_label = ROLE_LABELS.evaluator if not is_admin(user_role) else ROLE_LABELS.admin

    # --- Wide Screen (Desktop) View ---
    wide_screen_view = Div(
        Div(
            A(
                UkIcon("brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-blue-500"),
                H4("Kutsekeskkond", cls="inline-block align-middle"),
                Span(
                    role_label,
                    cls="ml-2 px-2 py-0.5 text-sm font-semibold rounded-full bg-gray-200 text-gray-800"
                ),
                href="/dashboard",
                cls="flex items-center"
            ),
            cls="flex items-center"
        ),
        Div(
            A(
                UkIcon("user", cls="inline-block mr-2 align-middle"),
                Span(display_name, cls="text-sm"),
                href="/dashboard",
                cls="flex items-center mr-4 p-2 rounded hover:bg-muted transition-colors"
            ),
            cls="flex items-center"
        ),
        cls="hidden lg:flex justify-between items-center w-full"
    )

    MAX_NAME_LEN = 15
    truncated_name = (display_name[:MAX_NAME_LEN] + '…') if len(display_name) > MAX_NAME_LEN else display_name

    # --- Narrow Screen (Mobile) View ---
    narrow_screen_view = Div(
        Div(
            Label(
                UkIcon("menu", cls="w-6 h-6"),
                fr="left-drawer-toggle",
                cls="btn btn-ghost btn-square drawer-button"
            ),
            cls="flex-1"
        ),
        Div(
            A(UkIcon("brick-wall", width=28, height=28, cls="text-blue-500"), href="/dashboard"),
            cls="flex-none"
        ),
        Div(
             A(
                UkIcon("user", width=24, height=24, cls="inline-block mr-1 align-middle"),
                Span(truncated_name, cls="text-sm"),
                href="/dashboard",
                cls="flex items-center"
            ),
             cls="flex-1 flex justify-end"
        ),
        cls="flex lg:hidden items-center w-full"
    )

    return Div(
        wide_screen_view,
        narrow_screen_view,
        cls="navbar bg-base-100 border-b px-2"
    )