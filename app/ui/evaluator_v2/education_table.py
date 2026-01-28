from fasthtml.common import *

from logic.models import ComplianceDashboardState

def render_education_input_table(state: ComplianceDashboardState, qual_id: str):
    """
    Renders the Education compliance table.
    Styled to match work_experience_table (table-xs, hover, border-t).
    """
    edu_opts = {
        "": "Vali haridustase...",
        "keskharidus": "Keskharidus",
        "vastav_kõrgharidus_180_eap": "Kõrgharidus (õppekava täidetud)",
        "vastav_kõrgharidus_240_eap": "Rakenduskõrgharidus (240 EAP)",
        "vastav_kõrgharidus_300_eap": "Magistrikraad (300 EAP)",
        "mittevastav_kõrgharidus_180_eap": "Muu kõrgharidus",
        "tehniline_kõrgharidus_300_eap": "Tehniline magister"
    }
    curr_edu = state.education.provided or ""
    
    # Helper for auto-saving inputs
    def _auto_save(name):
        return {
            "hx_post": f"/evaluator/d/re-evaluate/{qual_id}",
            "hx_trigger": "change",
            "hx_include": "#compliance-dashboard-container, #final-decision-area",
            "hx_target": "#compliance-dashboard-container",
            "hx_swap": "outerHTML",
            "name": name
        }

    # Column Headers matching workex flair
    headers = ["Haridustase", "Omandamisest 10a+", "Välisriigis omandatud"]
    
    return Div(
        Table(
            Thead(Tr(
                Th("Haridustase", cls="whitespace-nowrap text-left px-3 py-2 min-w-[250px]"),
                Th("Omandamisest 10a+", cls="whitespace-nowrap text-center px-3 py-2"),
                Th("Välisriigis omandatud", cls="whitespace-nowrap text-center px-3 py-2")
            )),
            Tbody(Tr(
                Td(
                    Select(
                        *[Option(lbl, value=k, selected=(k==curr_edu)) for k,lbl in edu_opts.items()],
                        cls="select select-bordered select-sm w-full text-xs h-8 min-h-0 py-0",
                        **_auto_save("education_level")
                    ),
                    cls="align-middle px-2"
                ),
                Td(
                    Input(type="checkbox", checked=state.education_10y_plus, 
                          cls="checkbox checkbox-sm checkbox-primary mx-auto block",
                          **_auto_save("education_10y_plus")),
                    cls="text-center align-middle px-2"
                ),
                Td(
                    Input(type="checkbox", checked=state.education_foreign, 
                          cls="checkbox checkbox-sm checkbox-primary mx-auto block",
                          **_auto_save("education_foreign")),
                    cls="text-center align-middle px-2"
                )
            ), cls="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"),
            cls="table table-xs w-auto"
        ),
        cls="overflow-x-auto border-t dark:border-gray-700 mt-2 rounded-b-lg"
    )
