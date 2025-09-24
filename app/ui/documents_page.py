# app/ui/documents_page.py
from fasthtml.common import *
from monsterui.all import *

def SectionContainer(legend_text: str, *children, **kwargs):
    """A reusable component for creating the 'text-on-border' style."""
    return Div(
        Span(legend_text, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600"),
        *children,
        cls=f"relative mt-8 mb-10 p-4 md:p-6 rounded-lg space-y-4 border-2"
    )

def StatusStrip(docs: list, doc_type: str, title: str):
    """Renders a colored status strip indicating if documents are present."""
    relevant_docs = [doc for doc in docs if doc.get('document_type') == doc_type]
    
    if not relevant_docs:
        return Div(
            UkIcon("info", cls="flex-shrink-0"),
            P(f"Ühtegi '{title}' dokumenti pole veel lisatud."),
            cls="p-4 bg-red-100 text-red-800 rounded-lg my-2 flex items-center gap-x-3"
        )
    else:
        doc_links = [
            A(doc.get('original_filename'), href=f"/files/download/{doc.get('storage_identifier')}", target="_blank", cls="link font-semibold underline")
            for doc in relevant_docs
        ]
        items = [doc_links[0]]
        for link in doc_links[1:]:
            items.extend([", ", link])

        return Div(
            UkIcon("check-circle", cls="flex-shrink-0"),
            Div(Span(f"{title}: ", cls="font-bold"), *items),
            cls="p-4 bg-green-100 text-green-800 rounded-lg my-2 flex items-center gap-x-3"
        )

def create_upload_form(doc_type: str, description: str, accept: str, button_text: str):
    """Helper function to create a standardized document upload form."""
    file_input_id = f'{doc_type}-document-file'
    
    return Form(
        P(description, cls="text-sm text-muted-foreground mb-4"),
        UploadZone(
            DivCentered(UkIcon("upload", cls="w-6 h-6 mr-2"), Span(f"Lohista siia või klõpsa, et valida")),
            id=f'{doc_type}-upload-zone',
            **{'for': file_input_id}
        ),
        # This Upload component now acts as the submit trigger
        Upload(
            button_text,
            id=file_input_id,
            name='document_file',
            accept=accept,
            required=True,
            # HTMX attributes are now on the Upload component itself
            hx_post=f"/app/dokumendid/upload?document_type={doc_type}",
            hx_target="#tab-content-container",
            hx_swap="innerHTML",
            hx_encoding="multipart/form-data",
            cls="" # Styled as a button
        ),
        # The separate Form button is no longer needed
        cls="space-y-4"
    )

def render_documents_page(existing_documents: list):
    """Renders the main page for the 'Dokumentide lisamine' tab with consistent layout."""
    
    # --- Section 1: Haridus (Education) ---
    education_form = create_upload_form(
        doc_type="haridus",
        description="Palun lae üles oma haridust tõendav(ad) dokument(id) (PDF, JPG, PNG).",
        accept=".pdf,.jpg,.jpeg,.png",
        button_text="Lisa hariduse dokument"
    )

    # --- Section 2: Täiendkoolitus (Training) ---
    training_form = create_upload_form(
        doc_type="koolitus",
        description="Palun laadige üles oma täiendkoolituste tunnistused (PDF, max 10MB).",
        accept=".pdf",
        button_text="Lisa koolituse dokument"
    )

    # --- Section 3: Töötamise tõend (Employment Proof) ---
    employment_form = create_upload_form(
        doc_type="tootamine",
        description="Palun laadige üles digitaalselt allkirjastatud dokumendikonteiner (nt. ASiC-E, max 10MB).",
        accept=".asice,.sce",
        button_text="Lisa töötamise tõend"
    )

    return Div(
        Div(
            StatusStrip(existing_documents, 'education', "Haridus"),
            StatusStrip(existing_documents, 'training', "Täiendkoolitus"),
            StatusStrip(existing_documents, 'employment_proof', "Töötamise tõend"),
            
            SectionContainer("1. Haridus", education_form),
            SectionContainer("2. Täiendkoolitus", training_form),
            SectionContainer("3. Töötamise tõend", employment_form),
        ),
        cls="max-w-5xl mx-auto"
    )