# gem/ui/nav_components.py

from fasthtml.common import *
from monsterui.all import *
from typing import Optional, Dict, Any

# --- TABS Dictionary (remains the same) ---
TABS = { # ... TABS content ...
    #"taotleja": "Taotleja", 
    "kutsed": "Taotletavad kutsed", 
    #"tookogemus": "Töökogemus",
    "workex": "Töökogemus",
    "dokumendid": "Dokumentide lisamine",
    #"haridus": "Haridus", 
    #"taiendkoolitus": "Täiendkoolitus", 
    #"tootamise_toend": "Töötamise tõend", 
    "ulevaatamine": "Taotluse ülevaatamine", 
    }

# --- public_navbar (remains the same) ---
def public_navbar() -> FT:
    # ... (code unchanged) ...
    return Div( Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500" ), H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"), href="/", cls="flex items-center" ), cls="flex items-center" ), Div( A(Button("Logi sisse", cls=ButtonT.ghost), href="/login"), A(Button("Registreeru", cls=ButtonT.secondary), href="/register"), cls="flex items-center space-x-2" ), cls="flex justify-between items-center p-4 bg-background border-b border-border shadow-sm" )


# --- app_navbar (Make responsive - CENTER icon, TRUNCATE email) ---
def app_navbar(request: Request) -> FT:
    """
    Creates the main application navbar (top bar) with responsive layout.
    Narrow: [Truncated Email] | [CENTERED Larger Brick] | [Ellipsis]
    Wide:   [Logo+Text]       | [Logged in as email + Logout]
    """
    user_email = request.session.get("user_email", "user@example.com")
    is_authenticated = request.session.get("authenticated", False)

    # --- Wide Screen Elements (Unchanged) ---
    wide_screen_left = Div( A( UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-pink-500" ), H4("Ehitamise valdkonna kutsete taotlemine", cls="inline-block align-middle"), href="/app", cls="flex items-center" ), cls="flex items-center" )
    wide_screen_right = Div( Span(f"Logged in as: {user_email}", cls="text-sm mr-4") if is_authenticated else Span(), A(Button("Logout", cls=ButtonT.ghost), href="/logout") if is_authenticated else Span(), cls="flex items-center" )

    # --- Narrow Screen Elements (Revised Structure) ---

    # Truncate email in Python
    MAX_EMAIL_LEN = 15 # Max characters before truncating
    display_email = (user_email[:MAX_EMAIL_LEN] + '…') if len(user_email) > MAX_EMAIL_LEN else user_email

    narrow_screen_content = Div(
        # Left Third: Truncated Email (Aligned Left)
        Div(
            Span(display_email, cls="text-sm"),
            cls="flex-1 text-left" # Use flex-1 to take up space, align text left
        ),

        # Center Third: Larger Brick Icon (Centered)
        Div(
            A(UkIcon("brick-wall", width=28, height=28, cls="text-pink-500"), href="/app"), # Increased size
            cls="flex-none text-center" # flex-none prevents growing/shrinking, center icon
        ),

        # Right Third: Ellipsis Icon (Aligned Right)
        Div(
            Button(UkIcon("ellipsis-vertical", width=20, height=20), cls=ButtonT.ghost),
             cls="flex-1 text-right" # Use flex-1, align content right
        )

        # Layout for narrow screen: Use flex, items-center for vertical alignment
        ,cls="flex items-center justify-between w-full space-x-2" # Added space-x-2 for minor spacing
    )


    # --- Main Navbar Structure (Unchanged) ---
    return Div(
        # Wide screen layout (hidden below md)
        Div( wide_screen_left, wide_screen_right, cls="hidden md:flex justify-between items-center w-full" ),
        # Narrow screen layout (shown below md)
        Div( narrow_screen_content, cls="flex md:hidden items-center w-full" ),
         # Base styles (padding, background, border)
         cls="flex items-center p-4 bg-background border-b border-border"
         # Sticky positioning is handled by the parent `render_sticky_header`
    )


def tab_nav(active_tab: str, request: Request, badge_counts: Dict = None) -> FT:
    badge_counts = badge_counts or {}
    nav_items = []
    active_tab_classes = 'border-primary text-primary' # Define active classes
    inactive_tab_classes = 'border-transparent hover:text-muted-foreground hover:border-border' # Define inactive classes

    for tab_id, tab_name in TABS.items():
        is_active = (tab_id == active_tab)
        badge = None
        count = badge_counts.get(tab_id)
        if count is not None and count > 0:
            badge = Span(str(count), cls="uk-badge text-green-500 ml-2") # Add badge with margin

        # Add a specific class to the active link for easier selection, e.g., 'tab-active'
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
        nav_items.append(Li(link, role='presentation', cls="flex-shrink-0")) # flex-shrink-0 prevents tabs from shrinking

    # The Ul holds the list of tabs
    tab_list = Ul(
        *nav_items,
        id="tab-list-container",
        cls="flex flex-nowrap -mb-px text-sm font-medium text-center text-muted-foreground"
    )

    # A parent Div that centers the Ul and handles horizontal scrolling
    nav_container = Div(
        tab_list,
        cls="flex justify-center border-b border-border overflow-x-auto overflow-y-hidden"
    )

    return Nav(nav_container, aria_label="Application Tabs", cls="bg-background")


# --- Combined Sticky Header Function (MODIFIED for centering on wide screens) ---
def render_sticky_header(request: Request, active_tab: str, badge_counts: Dict = None, container_class: str = "md:max-w-screen-lg") -> FT:
    """Renders the combined sticky header with content centered on wide screens."""
    top_nav_content = app_navbar(request)
    tab_nav_content = tab_nav(active_tab, request, badge_counts)
    # We still need the wrapper for the tab nav content itself for scrolling/styling
    tab_nav_wrapper = Div(tab_nav_content, id="tab-navigation-container")

    # Outer sticky container (maintains full width background/shadow)
    return Div(
        # *** ADDED: Inner centering container ***
        Div(
            # Place the actual navigation components inside this inner container
            top_nav_content,
            tab_nav_wrapper,

            # *** CORRECTED classes ***
            cls=f"w-full {container_class} md:mx-auto"
        ),
        # Original classes for the outer sticky container remain
        cls="sticky top-0 z-50 bg-background shadow-md"
    )

# +++ ADD NEW FUNCTION +++
def evaluator_navbar(request: Request) -> FT:
    """
    Creates the main application navbar specifically for the EVALUATOR view.
    """
    user_email = request.session.get("user_email", "evaluator@example.com") # Default if needed
    is_authenticated = request.session.get("authenticated", False)

    # --- Evaluator Specific Title ---
    evaluator_title = "Ehitamise valdkonna kutsete taotluste HINDAMISKESKKOND" # New Title

    # --- Wide Screen Elements ---
    # Use the new title here
    wide_screen_left = Div(
        A(
            UkIcon( "brick-wall", width=24, height=24, cls="inline-block mr-2 align-middle text-blue-500" ), # Maybe change icon color?
            H4(evaluator_title, cls="inline-block align-middle"), # USE NEW TITLE
            href="/evaluator/dashboard", # Link to evaluator dashboard
            cls="flex items-center"
        ),
        cls="flex items-center"
    )
    # Right side remains the same (Logout button, etc.)
    wide_screen_right = Div(
        Span(f"Logged in as: {user_email}", cls="text-sm mr-4") if is_authenticated else Span(),
        A(Button("Logout", cls=ButtonT.ghost), href="/logout") if is_authenticated else Span(),
        cls="flex items-center"
    )

    # --- Narrow Screen Elements (Can be simplified or kept similar to app_navbar) ---
    # Option: Keep the simplified narrow view from app_navbar for consistency
    MAX_EMAIL_LEN = 15
    display_email = (user_email[:MAX_EMAIL_LEN] + '…') if len(user_email) > MAX_EMAIL_LEN else user_email
    narrow_screen_content = Div(
        Div(Span(display_email, cls="text-sm"), cls="flex-1 text-left"),
        Div(A(UkIcon("brick-wall", width=28, height=28, cls="text-blue-500"), href="/evaluator/dashboard"), cls="flex-none text-center"), # Link to evaluator dashboard
        Div(Button(UkIcon("ellipsis-vertical", width=20, height=20), cls=ButtonT.ghost), cls="flex-1 text-right") # Placeholder for potential dropdown
        ,cls="flex items-center justify-between w-full space-x-2"
    )

    # --- Main Navbar Structure ---
    return Div(
        Div( wide_screen_left, wide_screen_right, cls="hidden md:flex justify-between items-center w-full" ),
        Div( narrow_screen_content, cls="flex md:hidden items-center w-full" ),
        cls="flex items-center p-4 bg-background border-b border-border shadow-sm" # Added shadow-sm
    )
# +++ END NEW FUNCTION +++