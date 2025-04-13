# ui/employment_proof_form.py
from fasthtml.common import *
from monsterui.all import *

def render_employment_proof_form():
    """Renders the employment proof upload form within a Card."""

    # Define the standard title style
    TITLE_CLASS = "text-xl font-semibold mb-4" # Example standard title class

    return Card( # Wrap in Card
        CardBody( # Use CardBody
            Form(
                H3("Töötamise tõendi esitamine", cls=TITLE_CLASS), # Standardized Title
                P(
                    "Palun laadige üles digitaalselt allkirjastatud dokumendikonteiner (nt. ASiC-E). "
                    "Maksimaalne failisuurus on 10MB.",
                    cls="mb-4 text-sm text-muted-foreground", # Adjusted text style
                ),
                Div(id="form-error-message", cls="text-red-500 mb-4"),  # For error messages
                # LabelTextArea(
                #     label="Faili kirjeldus",
                #     id="file_description",
                #     name="file_description",
                #     placeholder="Kirjeldage faili sisu",
                #     rows=4,
                #     cls="mb-4",
                # ),
                LabelInput(
                    label="Vali fail",
                    id="employment_proof",
                    name="employment_proof",
                    type="file",
                    accept="application/octet-stream",  # Adjust as needed for ASiC-E
                    required=True,
                    cls="mb-4",
                ),
                Div(
                    Button("Laadi üles", type="submit", cls="btn btn-primary"),  # Adjusted button class
                    cls="flex justify-start mt-6 pt-4 border-t" # Adjusted spacing and added border-t
                ),
                # --- HTMX Attributes for Form Submission ---
                method="post",
                hx_post="/app/tootamise_toend/upload",  # Route for file upload
                hx_target="#form-error-message",  # Target the error div
                hx_swap="innerHTML",
                enctype="multipart/form-data",  # Important for file uploads
                # Remove card-like classes from Form tag itself
                # cls="p-6 border rounded bg-white shadow" # REMOVED
                cls="space-y-4" # Add basic spacing if needed
            )
        )
        # Add any Card specific classes if needed
    )