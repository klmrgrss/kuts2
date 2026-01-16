# app/ui/evaluator_v2/center_panel.py
from fasthtml.common import *
from monsterui.all import *
from typing import Dict, Optional, List
from ui.shared_components import LevelPill
from logic.models import ComplianceDashboardState, ComplianceCheck
from ui.evaluator_v2.application_list import get_safe_dom_id

# --- Reusable Components ---

def render_compliance_subsection(title: str, check: ComplianceCheck, show_title: bool = True):
    if not check.is_relevant: return None
    icon = UkIcon("check-circle", cls="w-5 h-5 text-green-500") if check.is_met else UkIcon("x-circle", cls="w-5 h-5 text-red-500")
    
    content = Div(P(f"Nõue: {check.required}, Esitatud: {check.provided}", cls="text-xs text-gray-500 dark:text-gray-400"))
    if show_title:
        content = Div(P(title, cls="font-semibold text-sm"), content)
        
    return Div(icon, content, cls="flex items-center gap-x-3 px-3 py-2")

def render_compliance_section(title: str, icon_name: str, subsections: List[FT], all_checks: List[ComplianceCheck], context_name: str, comment: Optional[str], decision: Optional[str] = None, inline_details: Optional[str] = None):
    relevant = [c for c in all_checks if c.is_relevant]
    if not relevant and context_name != "otsus":
         border, accent, icon, text = "border-gray-300 dark:border-gray-700 opacity-50", "bg-gray-300", UkIcon("minus", cls="text-gray-500"), "Ei ole asjakohane"
    else:
        all_met = all(c.is_met for c in relevant) if relevant else True
        if context_name == "otsus" and decision:
            if decision == "Anda": border, accent, icon, text = "border-green-500", "bg-green-500", UkIcon("check-circle", cls="text-green-500"), f"Otsus: {decision}"
            elif decision == "Mitte anda": border, accent, icon, text = "border-red-500", "bg-red-500", UkIcon("shield-off", cls="text-red-500"), f"Otsus: {decision}"
            else: border, accent, icon, text = "border-blue-500", "bg-blue-500", UkIcon("shield-check", cls="text-blue-500"), f"Otsus: {decision}"
        else:
            border = "border-green-500" if all_met else "border-red-500"
            accent = "bg-green-500" if all_met else "bg-red-500"
            icon = UkIcon("check-circle", cls="text-green-500") if all_met else UkIcon("x-circle", cls="text-red-500")
            text = f"{len([c for c in relevant if c.is_met])}/{len(relevant)} täidetud" if context_name!="otsus" else "Otsus"

    header_content = [
        Div(cls=f"w-1.5 h-full absolute left-0 top-0 {accent}"), UkIcon(icon_name, cls="w-5 h-5"), H5(title, cls="font-semibold")
    ]
    
    if inline_details:
        header_content.append(Span(inline_details, cls="text-xs text-gray-500 dark:text-gray-400 truncate flex-1 ml-2"))
    else:
        # If no inline details, add a spacer to push status to right if desired, or keep packed
        header_content.append(Div(cls="flex-1"))

    header_content.extend([icon, Span(text, cls="text-sm text-gray-500 dark:text-gray-400 truncate")])

    return Div(
        Div(
            *header_content,
            cls="flex items-center gap-x-3 w-full p-3 relative bg-white dark:bg-gray-800 rounded-t-lg"
        ),
        Div(
            *subsections,
            P(comment or "Kommentaarid...", id=f"comment-display-{context_name}", data_comment=comment or "", cls="text-sm p-4 border-t italic text-gray-600 dark:text-gray-300 dark:border-gray-700 min-h-[4rem]"),
            cls="p-3 border-t bg-gray-50 dark:bg-gray-900 dark:border-gray-700 space-y-2"
        ),
        cls=f"border {border} rounded-lg overflow-hidden bg-white dark:bg-gray-800 dark:border-gray-700 cursor-pointer transition-shadow hover:shadow-md", 
        data_context=context_name,
        onclick=f"window.evDashboard.setActiveContext('{context_name}')"
    )

def render_compliance_dashboard(state: ComplianceDashboardState):
    # Header moved to main panel
    
    sections = [
        render_compliance_subsection("Haridustase", state.education, show_title=False),
        render_compliance_subsection("Töökogemus kokku", state.total_experience),
        render_compliance_subsection("Vastav töökogemus", state.matching_experience),
        render_compliance_subsection("Baaskoolitus", state.base_training),
        render_compliance_subsection("Tingimuslik baaskoolitus", state.conditional_training),
        render_compliance_subsection("Ehitusjuhi baaskoolitus", state.manager_training),
        render_compliance_subsection("Täiendkoolitus", state.cpd_training)
    ]
    
    edu_details = f"Nõue: {state.education.required}, Esitatud: {state.education.provided}" if state.education.is_relevant else None
    
    exp_parts = []
    if state.total_experience.is_relevant: 
        exp_parts.append(f"Kokku: {state.total_experience.provided} (Nõue {state.total_experience.required})")
    if state.matching_experience.is_relevant:
        exp_parts.append(f"Vastav: {state.matching_experience.provided} (Nõue {state.matching_experience.required})")
    exp_details = " | ".join(exp_parts) if exp_parts else None

    return Div(
        # header removed
        render_compliance_section("Haridus", "book-open", [], [state.education], "haridus", state.haridus_comment, inline_details=edu_details),
        render_compliance_section("Töökogemus", "briefcase", [], [state.total_experience, state.matching_experience], "tookogemus", state.tookogemus_comment, inline_details=exp_details),
        render_compliance_section("Koolitus", "award", [s for s in sections[3:] if s], [state.base_training, state.conditional_training, state.manager_training, state.cpd_training], "koolitus", state.koolitus_comment),
        render_compliance_section("Otsus", "list-checks", [], [], "otsus", state.otsus_comment, state.final_decision),
        id="compliance-dashboard-container",
        cls="p-4 space-y-4 pb-32"
    )

def render_center_panel(qual_data: Dict, user_data: Dict, state: ComplianceDashboardState) -> FT:
    aname, qlevel, qname = user_data.get('full_name','N/A'), qual_data.get('level',''), qual_data.get('qualification_name','')
    specs = qual_data.get('specialisations', [])
    qual_id = qual_data.get('qual_id', '')

    status_txt = f"{'Vastab tingimustele' if state.overall_met else 'Tingimused ei ole täidetud'} (Variant: {state.package_id})"
    status_cls = "text-xs font-bold uppercase tracking-wider mb-0.5 " + ("text-green-600" if state.overall_met else "text-red-600")

    header = Details(
        Summary(Div(
            P(status_txt, cls=status_cls + " w-full mb-1"),
            Div(
                LevelPill(qlevel),
                Div(H2(aname, cls="text-xl font-bold truncate"), P("·", cls="mx-1"), P(f"{qname}", cls="text-sm truncate"), cls="flex items-center min-w-0"),
                DivHStacked(P("Spetsialiseerumised", cls="text-xs"), P(f"({qual_data.get('selected_specialisations_count',len(specs))}/{len(specs)})", cls="text-xs font-bold"), UkIcon("chevron-down", cls="w-4 h-4"), cls="justify-self-end flex items-center"),
                cls="grid grid-cols-[auto,1fr,auto] items-center gap-x-3 w-full"
            ),
            cls="flex flex-col w-full"), cls="list-none cursor-pointer w-full"),
        Div(Ul(*[Li(s) for s in specs], cls="list-disc list-inside text-xs"), cls="ml-12 mt-2 text-gray-600 dark:text-gray-400"),
        open=False, cls="border-b bg-gray-50 dark:bg-gray-900 dark:border-gray-700 sticky top-0 z-10 p-3 shadow-sm w-full"
    )

    # --- Footer Construction ---
    
    # 1. Context Menu
    ctx_opts = {'haridus': 'Haridus', 'tookogemus': 'Töökogemus', 'koolitus': 'Täiendkoolitus'} 
    ctx_id = "ctx-menu"
    ctx_menu = Div(
        Div("Vali kontekst", cls="px-3 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700"),
        *[Button(label, onclick=f"window.evDashboard.setActiveContext('{key}'); toggleDropdown('{ctx_id}')", cls="block w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700") for key, label in ctx_opts.items()],
        id=ctx_id, cls="absolute bottom-full left-0 mb-2 w-48 bg-white dark:bg-gray-900 border dark:border-gray-700 rounded-lg shadow-xl overflow-hidden z-50", style="display: none;"
    )

    # 2. Haridus Controls (Inline)
    edu_opts = {"": "Haridus: -", "keskharidus": "Keskharidus", "vastav_kõrgharidus_180_eap": "Bakalaureus (180)", "vastav_kõrgharidus_240_eap": "Rakenduskõrg (240)", "vastav_kõrgharidus_300_eap": "Magister (300)", "mittevastav_kõrgharidus_180_eap": "Muu Baka (180)", "tehniline_kõrgharidus_300_eap": "Tehniline Mag (300)"}
    edu_curr = state.education.provided or ""
    edu_disp = edu_opts.get(edu_curr, "Vali")
    
    foreign_opts = {"": ">10/F: Ei", "on": ">10/F: Jah"}
    foreign_curr = "on" if getattr(state, "education_old_or_foreign", False) else ""
    foreign_disp = foreign_opts.get(foreign_curr, "Ei")

    def InlineDropdown(btn_id, label, opts, name, current, width_cls="w-32"):
        dd_id = btn_id.replace('btn-', 'dropdown-')
        return Div(
            Input(type="hidden", name=name, value=current, id=f"hidden-{btn_id}"),
            Button(Span(label, cls="truncate max-w-[100px]"), UkIcon("chevron-down", cls="w-3 h-3 ml-1 flex-none"), 
                   id=btn_id, onclick=f"toggleDropdown('{dd_id}')", type="button",
                   cls="inline-flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-full bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors h-8 whitespace-nowrap"),
            Div(*[Button(txt, onclick=f"window.selectInlineOption('{btn_id}', '{val}', '{txt}')", type="button", cls="block w-full text-left px-3 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700") for val, txt in opts.items()],
                id=dd_id, cls=f"absolute bottom-full left-0 mb-1 {width_cls} bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-lg overflow-hidden z-50", style="display: none;"),
            cls="relative"
        )

    haridus_area = Div(
        InlineDropdown("btn-edu-lvl", edu_disp, edu_opts, "education_level", edu_curr, "w-48"),
        InlineDropdown("btn-foreign", foreign_disp, foreign_opts, "education_old_or_foreign", foreign_curr, "w-32"),
        id="haridus-inline-controls", cls="hidden flex items-center gap-1.5 transition-all duration-300 ease-in-out origin-left"
    )

    # 3. Decision Button (Inline)
    dec_opts = {"Anda": "green", "Mitte anda": "red", "Täiendav tegevus": "blue"}
    dec_curr = state.final_decision or ""
    dec_label = dec_curr if dec_curr in dec_opts else "Vali otsus"
    dec_cls = "bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300" # Default
    if dec_curr == "Anda": dec_cls = "bg-green-100 text-green-800 border-green-500"
    elif dec_curr == "Mitte anda": dec_cls = "bg-red-100 text-red-800 border-red-500"
    elif dec_curr: dec_cls = "bg-blue-100 text-blue-800 border-blue-500"

    decision_dropdown_id = "decision-dropdown"
    decision_btn = Div(
        Input(type="hidden", name="final_decision", value=dec_curr, id="hidden-final_decision"),
        Button(UkIcon("chevron-up", cls="w-3 h-3 mr-1"), Span(dec_label, id="decision-btn-label"), 
               onclick=f"window.evDashboard.setActiveContext('otsus'); toggleDropdown('{decision_dropdown_id}')", type="button",
               id="decision-main-btn",
               cls=f"inline-flex items-center px-3 py-1.5 text-xs font-bold rounded-full border transition-colors h-8 shadow-sm hover:shadow-md whitespace-nowrap {dec_cls}"),
        Div(*[Button(val, onclick=f"window.setDecision('{val}', '{col}')", type="button", cls="block w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 font-semibold") for val, col in dec_opts.items()],
            id=decision_dropdown_id, cls="absolute bottom-full left-0 mb-2 w-40 bg-white dark:bg-gray-900 border dark:border-gray-700 rounded-lg shadow-xl overflow-hidden z-50", style="display: none;"),
        cls="relative"
    )

    # --- Main Input Wrapper (Flex Column: Textarea Top, Buttons Bottom) ---
    input_container = Div(
        # Row 1: Textarea
        Textarea(name="main_comment", id="main-comment-textarea", placeholder="Sisesta kommentaar...", rows=2, 
                 # _ = "on keydown[ctrlKey and key is 'Enter'] closest <form/>.requestSubmit()", removed in favor of HTMX trigger
                 cls="block w-full bg-transparent border-0 focus:ring-0 text-sm px-1 py-1 resize-none leading-normal text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none mb-1",
                 style="min-height: 48px; max-height: 150px;"),
                 
        # Row 2: Toolbar (Buttons)
        Div(
             # Left Group
             Div(
                 # Plus
                 Div(Button(UkIcon("plus", cls="w-5 h-5"), onclick=f"toggleDropdown('{ctx_id}')", type="button", 
                            cls="btn btn-circle btn-sm btn-ghost hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400"),
                     ctx_menu, cls="relative flex-none"),
                 # Haridus
                 haridus_area,
                 # Otsus
                 decision_btn,
                 cls="flex items-center gap-1.5"
             ),
             
             # Right Group (Send)
             Button(UkIcon("send", cls="w-4 h-4 text-white"), type="submit", 
                    cls="btn btn-circle btn-sm bg-blue-600 hover:bg-blue-700 border-0 flex-none shadow-md"),
                    
             cls="flex items-center justify-between w-full"
        ),
        
        cls="w-full flex flex-col p-2.5 rounded-2xl bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 transition-all shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 overflow-visible"
    )

    footer = Form(
        Input(type="hidden", name="active_context", id="active-context-input"),
        Div(input_container, cls="p-2 overflow-visible"), # ensured overflow-visible
        id="final-decision-area", hx_post=f"/evaluator/d/re-evaluate/{qual_id}", hx_trigger="submit, keydown[ctrlKey&&key=='Enter']", 
        hx_target="#compliance-dashboard-container", hx_swap="outerHTML", hx_select="#compliance-dashboard-container",
        cls="sticky bottom-0 z-30 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md border-t dark:border-gray-700 shadow-negative transition-all duration-300 pb-4 overflow-visible"
    )

    js_script = Script("""
        (function() {
             console.log('EvDashboard Init');
             window.evDashboard = {
                currentContext: null,
                setActiveContext(ctx) {
                    console.log('Set Context', ctx);
                    this.currentContext = ctx;
                    const aci = document.getElementById('active-context-input');
                    if(aci) aci.value = ctx || '';
                    
                    // Toggle Haridus Inline Area
                    const haridusArea = document.getElementById('haridus-inline-controls');
                    if(haridusArea) {
                        if (ctx === 'haridus') {
                            haridusArea.classList.remove('hidden');
                        } else {
                            haridusArea.classList.add('hidden');
                        }
                    }
                    
                    // Highlights
                     document.querySelectorAll('[data-context]').forEach(el => {
                        const active = el.dataset.context === ctx;
                        el.classList.toggle('ring-2', active);
                        el.classList.toggle('ring-blue-500', active);
                    });
                    
                    // Load comment
                    const store = document.getElementById(`comment-display-${ctx}`);
                    const ta = document.getElementById('main-comment-textarea');
                    if(ta) {
                        ta.value = store ? (store.dataset.comment || '') : '';
                        const map = {'haridus': 'Kommentaar hariduse kohta...', 'otsus': 'Põhjendus otsusele...', 'tookogemus': 'Märkmed töökogemusest...', 'koolitus': 'Märkmed koolitusest...'};
                        ta.placeholder = map[ctx] || 'Sisesta kommentaar...';
                        ta.focus();
                    }
                }
            };
            
            window.toggleDropdown = (id) => { 
                console.log('Toggle Dropdown', id);
                const d=document.getElementById(id); 
                // Close others
                document.querySelectorAll('[id^="dropdown-"], [id^="decision-dropdown"], [id="ctx-menu"]').forEach(el => { if(el.id!==id) el.style.display='none'; });
                if(d) {
                    d.style.display = d.style.display==='none'?'block':'none'; 
                    console.log('Dropdown display:', d.style.display);
                }
            };
            
            window.selectInlineOption = (btnId, val, txt) => {
                document.getElementById('hidden-'+btnId).value = val;
                document.querySelector(`#${btnId} span`).innerText = txt;
                document.getElementById(btnId.replace('btn-','dropdown-')).style.display='none';
            };
            
            window.setDecision = (val, color) => {
                const inp = document.getElementById('hidden-final_decision');
                if(inp) inp.value = val;
                const btn = document.getElementById('decision-main-btn');
                const label = document.getElementById('decision-btn-label');
                if(label) label.innerText = val;
                
                // Color mapping
                if(btn) {
                    btn.className = "inline-flex items-center px-3 py-1.5 text-xs font-bold rounded-full border transition-colors h-8 shadow-sm hover:shadow-md ";
                    if (color === 'green') btn.className += "bg-green-100 text-green-800 border-green-500";
                    else if (color === 'red') btn.className += "bg-red-100 text-red-800 border-red-500";
                    else if (color === 'blue') btn.className += "bg-blue-100 text-blue-800 border-blue-500";
                }
                
                const dd = document.getElementById('decision-dropdown');
                if(dd) dd.style.display='none';
            };
            
            // Auto-expand
            const ta = document.getElementById('main-comment-textarea');
            if(ta) ta.addEventListener('input', function() { this.style.height='auto'; this.style.height=this.scrollHeight+'px'; });
            
        })();
    """)

    return Div(header, render_compliance_dashboard(state), footer, js_script, id="ev-center-panel", cls="flex flex-col h-full bg-white dark:bg-gray-900 overflow-y-auto relative [scrollbar-width:thin] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-gray-300 dark:[&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb]:rounded-full")