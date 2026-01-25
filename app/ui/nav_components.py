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
                H4("Kutsekeskkond", cls="inline-block align-middle"),
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

# --- Theme Toggle ---
def ThemeToggle() -> FT:
    return Button(
        UkIcon("moon", cls="dark:hidden w-5 h-5"),
        UkIcon("sun", cls="hidden dark:block w-5 h-5 text-yellow-400"),
        onclick="toggleTheme()",
        cls=ButtonT.ghost + " rounded-full p-2 ml-2"
    )

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
            UkIcon("user", cls="w-6 h-6"),
            href="/dashboard",
            cls="flex items-center mr-4 p-2 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
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
                UkIcon("user", cls="w-6 h-6"),
                href="/dashboard",
                cls="flex items-center text-muted-foreground"
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
    
    # Define ordered steps with custom label splitting for mobile
    # Tuple: (id, full_text_for_desktop, [list_of_parts_for_mobile])
    ORDERED_TABS_DATA = [
        ("kutsed", "Taotletavad kutsed", ["Taotletavad", " kutsed"]),
        ("workex", "Töökogemus", ["Töökogemus"]),
        ("dokumendid", "Dokumentide lisamine", ["Dokumentide", " lisamine"]),
        ("ulevaatamine", "Taotluse ülevaatamine", ["Taotluse", " ülevaatamine"])
    ]
    
    # Find active index
    active_idx = -1
    for i, (tid, _, _) in enumerate(ORDERED_TABS_DATA):
        if tid == active_tab:
            active_idx = i
            break
            
    steps = []
    for i, (tab_id, full_name, parts) in enumerate(ORDERED_TABS_DATA):
        is_completed_or_active = i <= active_idx
        is_active = i == active_idx
        
        step_classes = "step cursor-pointer min-w-fit px-2"
        if is_completed_or_active:
            step_classes += " step-primary"
            
        # Link content styling
        # Removed whitespace-nowrap to allow multiline on mobile if needed, 
        # though we controle it via Br() mostly.
        link_text_cls = "text-sm leading-tight md:leading-normal"
        if is_active:
             link_text_cls += " font-bold text-primary"
        else:
             link_text_cls += " text-muted-foreground hover:text-foreground"
        
        # Build Label
        # If parts > 1, insert Br(cls="md:hidden") between them. 
        # On desktop (md:), the text flows naturally or we force nowrap.
        # Actually simplest: Join with space, and insert Br(cls="md:hidden")
        
        label_content = []
        for idx, part in enumerate(parts):
            if idx > 0:
                label_content.append(Br(cls="md:hidden"))
            label_content.append(part)

        # Determine badge
        count = badge_counts.get(tab_id)
        badge = Span(str(count), cls="badge badge-sm badge-secondary ml-1 align-middle") if count and count > 0 else ""

        link_content = Span(*label_content, badge, cls=link_text_cls)
        
        link = A(
            link_content,
            hx_get=f'/app/{tab_id}',
            hx_target='#tab-content-container',
            hx_swap='innerHTML',
            hx_push_url="true",
            cls="block py-2 focus:outline-none text-center"
        )
        
        steps.append(Li(link, cls=step_classes, data_content=str(i + 1)))

    return Div(
        Ul(*steps, cls="steps steps-horizontal steps-sm w-full"),
        cls="w-full overflow-x-auto py-4 bg-background border-b border-border px-4"
    )


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
        cls="sticky top-0 z-50 bg-background shadow-md min-w-full"
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
            ThemeToggle(),
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