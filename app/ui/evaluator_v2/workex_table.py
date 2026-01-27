from fasthtml.common import *
from typing import Optional
from datetime import datetime

def calculate_duration_str(start_str: Optional[str], end_str: Optional[str]) -> str:
    if not start_str: return "-"
    try:
        start = datetime.strptime(start_str, "%Y-%m").date()
        end = datetime.strptime(end_str, "%Y-%m").date() if end_str else datetime.today().date()
        
        # Approximate months
        diff_months = (end.year - start.year) * 12 + (end.month - start.month) + 1 # inclusive
        
        years = diff_months // 12
        months = diff_months % 12
        
        parts = []
        if years > 0: parts.append(f"{years}a")
        if months > 0: parts.append(f"{months}k")
        return " ".join(parts) if parts else "0k"
    except:
        return "?"

def render_info_card(label: str, name: Optional[str], code: Optional[str], contact: Optional[str], email: Optional[str], phone: Optional[str]):
    """Renders a dropdown card for Company/Client info"""
    if not name: return Span("-")
    
    return Details(
        Summary(
            Span(name, cls="border-b border-dotted border-gray-400 hover:text-blue-600 cursor-pointer truncate max-w-[150px] block"),
            cls="list-none"
        ),
        Div(
            P(Strong(label), cls="text-xs text-gray-400 uppercase tracking-widest mb-1"),
            Div(
                P(name, cls="font-bold"),
                P(f"Reg: {code}") if code else None,
                Div(cls="border-t my-1 dark:border-gray-600"),
                P(UkIcon("user", cls="w-3 h-3 mr-1 inline") + f"{contact}") if contact else None,
                P(UkIcon("mail", cls="w-3 h-3 mr-1 inline") + f"{email}") if email else None,
                P(UkIcon("phone", cls="w-3 h-3 mr-1 inline") + f"{phone}") if phone else None,
                cls="text-xs space-y-0.5"
            ),
            cls="absolute z-50 bg-white dark:bg-gray-800 border dark:border-gray-700 shadow-xl rounded-lg p-3 w-64 mt-1"
        ),
        cls="relative"
    )

def render_checkbox_cell(is_checked: bool, qual_id: str, exp_id: int):
    # Using hx-post to toggle state independently. 
    # Must stop propagation to prevent row clicks if any.
    return Td(
        Input(type="checkbox", checked=is_checked, 
              hx_post=f"/evaluator/d/toggle-exp/{qual_id}/{exp_id}",
              hx_target="#compliance-dashboard-container",
              hx_swap="outerHTML",
              cls="checkbox checkbox-xs"),
        cls="text-center",
        onclick="event.stopPropagation()" # Prevent row click if any
    )

def render_work_experience_table(experiences: list, qual_id: str = None, accepted_ids: list = None) -> FT:
    if not experiences:
        return Div("Töökogemus puudub.", cls="text-sm text-gray-500 italic p-3")

    accepted_ids = accepted_ids or []
    rows = []
    for idx, exp in enumerate(experiences, 1):
        # Duration
        duration_str = calculate_duration_str(exp.get('start_date'), exp.get('end_date'))
        exp_id = exp.get('id')
        
        # Check if accepted by evaluator
        is_accepted = exp_id in accepted_ids

        # Determining PTV/ATV/PTVO (Informational columns)
        c_type = (exp.get('contract_type') or "").strip()
        is_ptv = c_type == "PTV"
        is_atv = c_type == "ATV"
        is_ptvo = c_type == "PTVO"

        # Checkbox Column (First)
        # We need qual_id to form the URL. If not provided, disable?
        if qual_id and exp_id:
            check_col = render_checkbox_cell(is_accepted, qual_id, exp_id)
        else:
            check_col = Td(Input(type="checkbox", disabled=True, cls="checkbox checkbox-xs"), cls="text-center")

        rows.append(Tr(
            check_col,
            Td(str(idx), cls="text-center text-gray-400"),
            Td(exp.get('role', '-'), cls="font-medium"),
            Td(
                Div(exp.get('start_date', '-'), cls="text-xs"),
                Div(exp.get('end_date', '...'), cls="text-xs text-gray-400"),
            ),
            Td(duration_str, cls="font-mono text-xs whitespace-nowrap"),
            # Removed redundant logic contract type checkboxes (visual only)
            # Keeping them as "visual indicators" as per original code? 
            # Original code used render_checkbox_cell which was just disabled input.
            # I'll keep them as simple disabled checks.
            Td(Input(type="checkbox", checked=is_ptv, disabled=True, cls="checkbox checkbox-xs"), cls="text-center"),
            Td(Input(type="checkbox", checked=is_atv, disabled=True, cls="checkbox checkbox-xs"), cls="text-center"),
            Td(Input(type="checkbox", checked=is_ptvo, disabled=True, cls="checkbox checkbox-xs"), cls="text-center"),
            
            Td(exp.get('object_address', '-'), cls="text-xs max-w-[150px] truncate", title=exp.get('object_address', '')),
            Td(exp.get('ehr_code', '-'), cls="font-mono text-xs"),
            Td(Input(type="checkbox", checked=bool(exp.get('permit_required')), disabled=True, cls="checkbox checkbox-xs"), cls="text-center"),
            Td(
                render_info_card("Ettevõte", exp.get('company_name'), exp.get('company_code'), exp.get('company_contact'), exp.get('company_email'), exp.get('company_phone'))
            ),
            Td(
                render_info_card("Tellija", exp.get('client_name'), exp.get('client_code'), exp.get('client_contact'), exp.get('client_email'), exp.get('client_phone'))
            ),
            cls=f"hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors {'bg-green-50/50' if is_accepted else ''}"
        ))

    headers = ["OK", "#", "Roll", "Periood", "Kokku", "PTV", "ATV", "PTVO", "Asukoht", "EHR kood", "Ehitusluba", "Ettevõte", "Tellija"]
    
    return Div(
        Table(
            Thead(Tr(*[Th(h, cls="whitespace-nowrap") for h in headers])),
            Tbody(*rows),
            cls="table table-xs w-full"
        ),
        cls="overflow-x-auto border-t dark:border-gray-700 mt-2"
    )
