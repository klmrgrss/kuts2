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

def render_checkbox_cell(is_checked: bool):
    return Td(
        Input(type="checkbox", checked=is_checked, disabled=True, cls="checkbox checkbox-xs"),
        cls="text-center"
    )

def render_work_experience_table(experiences: list) -> FT:
    if not experiences:
        return Div("Töökogemus puudub.", cls="text-sm text-gray-500 italic p-3")

    rows = []
    for idx, exp in enumerate(experiences, 1):
        # Duration
        duration_str = calculate_duration_str(exp.get('start_date'), exp.get('end_date'))
        
        # Determining PTV/ATV/PTVO
        # Just simple string matching for now based on user request mapping
        c_type = (exp.get('contract_type') or "").strip()
        is_ptv = c_type == "PTV"
        is_atv = c_type == "ATV"
        is_ptvo = c_type == "PTVO"

        rows.append(Tr(
            Td(str(idx), cls="text-center text-gray-400"),
            Td(exp.get('role', '-'), cls="font-medium"),
            Td(
                Div(exp.get('start_date', '-'), cls="text-xs"),
                Div(exp.get('end_date', '...'), cls="text-xs text-gray-400"),
            ),
            Td(duration_str, cls="font-mono text-xs whitespace-nowrap"),
            render_checkbox_cell(is_ptv),
            render_checkbox_cell(is_atv),
            render_checkbox_cell(is_ptvo),
            Td(exp.get('object_address', '-'), cls="text-xs max-w-[150px] truncate", title=exp.get('object_address', '')),
            Td(exp.get('ehr_code', '-'), cls="font-mono text-xs"),
            render_checkbox_cell(bool(exp.get('permit_required'))), # Ehitusluba field mapping? mapped permit_required to int 0/1 in controller
            Td(
                render_info_card("Ettevõte", exp.get('company_name'), exp.get('company_code'), exp.get('company_contact'), exp.get('company_email'), exp.get('company_phone'))
            ),
            Td(
                render_info_card("Tellija", exp.get('client_name'), exp.get('client_code'), exp.get('client_contact'), exp.get('client_email'), exp.get('client_phone'))
            ),
            cls="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        ))

    headers = ["#", "Roll", "Periood", "Kokku", "PTV", "ATV", "PTVO", "Asukoht", "EHR kood", "Ehitusluba", "Ettevõte", "Tellija"]
    
    return Div(
        Table(
            Thead(Tr(*[Th(h, cls="whitespace-nowrap") for h in headers])),
            Tbody(*rows),
            cls="table table-xs w-full"
        ),
        cls="overflow-x-auto border-t dark:border-gray-700 mt-2"
    )
