# gem/ui/nav_components.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Dict, Any
from starlette.requests import Request
from fastlite import NotFoundError

# --- TABS Dictionary ---
TABS = { 
    "kutsed": "Taotletavad kutsed", 
    "workex": "Töökogemus",
    "dokumendid": "Dokumentide lisamine",
    "ulevaatamine": "Taotluse ülevaatamine", 
    }

# --- public_navbar ---
def public_navbar() -> FT:
    return Div( Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500" ), H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"), href="/", cls="flex items-center" ), cls="flex items-center" ), Div( A(Button("Logi sisse", cls=ButtonT.ghost), href="/login"), A(Button("Registreeru", cls=ButtonT.secondary), href="/register"), cls="flex items-center space-x-2" ), cls="flex justify-between items-center p-4 bg-background border-b border-border shadow-sm" )


# --- app_navbar (MODIFIED to show name and remove logout) ---
def app_navbar(request: Request, db: Any) -> FT:
    """
    Creates the main application navbar (top bar) with responsive layout.
    Displays user's full name and removes the logout button.
    """
    user_email = request.session.get("user_email", "")
    is_authenticated = request.session.get("authenticated", False)

    # --- Fetch user's full name from DB ---
    display_name = user_email # Fallback to email
    if is_authenticated and db:
        try:
            user_data = db.t.users[user_email]
            display_name = user_data.get('full_name') or user_email
        except NotFoundError:
            print(f"--- WARN [app_navbar]: User '{user_email}' not found in DB. Using email as display name. ---")
        except Exception as e:
            print(f"--- ERROR [app_navbar]: DB lookup failed for '{user_email}'. Error: {e} ---")


    # --- Wide Screen Elements ---
    wide_screen_left = Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500" ), H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"), href="/app", cls="flex items-center" ), cls="flex items-center" )
    
    # MODIFIED: Use name, remove logout button
    wide_screen_right = Div(
        A(
            UkIcon("user", cls="inline-block mr-2 align-middle"),
            Span(display_name, cls="text-sm"),
            href="/app/taotleja",
            cls="flex items-center mr-4 p-2 rounded hover:bg-muted transition-colors"
        ) if is_authenticated else Span(),
        cls="flex items-center"
    )

    # --- Narrow Screen Elements ---
    MAX_NAME_LEN = 15
    truncated_name = (display_name[:MAX_NAME_LEN] + '…') if len(display_name) > MAX_NAME_LEN else display_name

    narrow_screen_content = Div(
        # Left Third: MODIFIED to use name
        Div(
            A(
                UkIcon("user", cls="inline-block mr-1 align-middle"),
                Span(truncated_name, cls="text-sm"),
                href="/app/taotleja",
                cls="flex items-center"
            ),
            cls="flex-1 text-left"
        ),

        Div( A(UkIcon("brick-wall", width=28, height=28, cls="text-pink-500"), href="/app"), cls="flex-none text-center" ),
        Div( Button(UkIcon("ellipsis-vertical", width=20, height=20), cls=ButtonT.ghost), cls="flex-1 text-right" ),
        cls="flex items-center justify-between w-full space-x-2"
    )

    # --- Main Navbar Structure ---
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
    nav_container = Div( tab_list, cls="flex justify-center border-b border-border overflow-x-auto overflow-y-hidden" )
    return Nav(nav_container, aria_label="Application Tabs", cls="bg-background")


# --- Combined Sticky Header Function (MODIFIED to accept db) ---
def render_sticky_header(request: Request, active_tab: str, db: Any, badge_counts: Dict = None, container_class: str = "md:max-w-screen-lg") -> FT:
    """Renders the combined sticky header, passing db to the app_navbar."""
    top_nav_content = app_navbar(request, db) # Pass db to app_navbar
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

# --- evaluator_navbar (remains the same) ---
def evaluator_navbar(request: Request) -> FT:
    user_email = request.session.get("user_email", "evaluator@example.com")
    is_authenticated = request.session.get("authenticated", False)
    evaluator_title = "Ehitamise valdkonna kutsete taotluste HINDAMISKESKKOND"
    wide_screen_left = Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-blue-500" ), H4(evaluator_title, cls="inline-block align-middle"), href="/evaluator/dashboard", cls="flex items-center" ), cls="flex items-center" )
    wide_screen_right = Div( Span(f"Logged in as: {user_email}", cls="text-sm mr-4") if is_authenticated else Span(), A(Button("Logout", cls=ButtonT.ghost), href="/logout") if is_authenticated else Span(), cls="flex items-center" )
    MAX_EMAIL_LEN = 15
    display_email = (user_email[:MAX_EMAIL_LEN] + '…') if len(user_email) > MAX_EMAIL_LEN else user_email
    narrow_screen_content = Div( Div(Span(display_email, cls="text-sm"), cls="flex-1 text-left"), Div(A(UkIcon("brick-wall", width=28, height=28, cls="text-blue-500"), href="/evaluator/dashboard"), cls="flex-none text-center"), Div(Button(UkIcon("ellipsis-vertical", width=20, height=20), cls=ButtonT.ghost), cls="flex-1 text-right"), cls="flex items-center justify-between w-full space-x-2" )
    return Div( Div( wide_screen_left, wide_screen_right, cls="hidden md:flex justify-between items-center w-full" ), Div( narrow_screen_content, cls="flex md:hidden items-center w-full" ), cls="flex items-center p-4 bg-background border-b border-border shadow-sm" )