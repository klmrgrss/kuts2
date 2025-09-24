# app/ui/documents_page.py
from fasthtml.common import *
from monsterui.all import *

def SectionContainer(legend_text: str, *children, **kwargs):
    """A reusable component for creating the 'text-on-border' style."""
    return Div(
        Span(legend_text, cls="absolute -top-3 left-4 bg-background px-2 text-lg font-semibold text-gray-600"),
        *children,
        # Matching margins and border style from other tabs
        cls=f"relative mt-8 mb-10 p-4 md:p-6 rounded-lg space-y-4 border-2"
    )

def StatusStrip(docs: list, doc_type: str, title: str):
    """Renders a colored status strip indicating if documents are present."""
    
    # Filter for documents of the specified type
    relevant_docs = [doc for doc in docs if doc.get('document_type') == doc_type]
    
    if not relevant_docs:
        # Red/Pink strip for missing documents
        return Div(
            UkIcon("info", cls="flex-shrink-0"),
            P(f"Ühtegi '{title}' dokumenti pole veel lisatud."),
            cls="p-4 bg-red-100 text-red-800 rounded-lg my-2 flex items-center gap-x-3"
        )
    else:
        # Green strip for added documents
        doc_links = [
            A(doc.get('original_filename'), href=f"/files/download/{doc.get('storage_identifier')}", target="_blank", cls="link font-semibold underline")
            for doc in relevant_docs
        ]
        # Join links with a comma
        items = [doc_links[0]]
        for link in doc_links[1:]:
            items.append(", ")
            items.append(link)

        return Div(
            UkIcon("check-circle", cls="flex-shrink-0"),
            Div(
                Span(f"{title}: ", cls="font-bold"),
                *items
            ),
            cls="p-4 bg-green-100 text-green-800 rounded-lg my-2 flex items-center gap-x-3"
        )


def render_documents_page(existing_documents: list):
    """Renders the main page for the 'Dokumentide lisamine' tab with consistent layout."""
    
    # --- Section 1: Haridus (Education) ---
    education_form = Form(
        P("Palun lae üles oma haridust tõendav(ad) dokument(id).", cls="text-sm text-muted-foreground mb-4"),
        LabelInput(label="Õppeasutus", name="institution", required=True),
        LabelInput(label="Eriala", name="specialty", required=True),
        LabelInput(
            label="Lõpetamise aeg (kuu ja aasta)", name="graduation_date", type="text",
            placeholder="Vali kuu ja aasta...", input_cls="flatpickr-month-input", required=True
        ),
        Div(Upload("Upload Button!", id='upload1'),
               UploadZone(DivCentered(Span("Upload Zone"), UkIcon("upload")), id='upload2'),
               cls='space-y-4'),

        LabelInput(
            label="Vali fail (PDF, JPG, PNG)", name="document_file", type="file",
            accept=".pdf,.jpg,.jpeg,.png", required=True
        ),
        Div(Button("Lisa hariduse dokument", type="submit", cls="btn btn-primary"), cls="flex justify-start mt-6 pt-4 border-t"),
        hx_post="/app/dokumendid/upload?document_type=education",
        hx_target="#tab-content-container", hx_swap="innerHTML", enctype="multipart/form-data",
        cls="space-y-4"
    )

    # --- Section 2: Täiendkoolitus (Training) ---
    training_form = Form(
        P("Palun laadige üles oma täiendkoolituste tunnistused PDF formaadis. Maksimaalne failisuurus on 10MB.", cls="text-sm text-muted-foreground mb-4"),
        LabelInput(label="Koolituse või tunnistuse kirjeldus", name="description", required=True),
        LabelInput(label="Vali fail (PDF)", name="document_file", type="file", accept=".pdf", required=True),
        Div(Button("Lisa koolituse dokument", type="submit", cls="btn btn-primary"), cls="flex justify-start mt-6 pt-4 border-t"),
        hx_post="/app/dokumendid/upload?document_type=training",
        hx_target="#tab-content-container", hx_swap="innerHTML", enctype="multipart/form-data",
        cls="space-y-4"
    )

    # --- Section 3: Töötamise tõend (Employment Proof) ---
    employment_form = Form(
        P("Palun laadige üles digitaalselt allkirjastatud dokumendikonteiner (nt. ASiC-E). Maksimaalne failisuurus on 10MB.", cls="text-sm text-muted-foreground mb-4"),
        LabelInput(label="Faili kirjeldus (vabatahtlik)", name="description"),
        LabelInput(label="Vali fail", name="document_file", type="file", accept=".asice,.sce", required=True),
        Div(Button("Lisa töötamise tõend", type="submit", cls="btn btn-primary"), cls="flex justify-start mt-6 pt-4 border-t"),
        hx_post="/app/dokumendid/upload?document_type=employment_proof",
        hx_target="#tab-content-container", hx_swap="innerHTML", enctype="multipart/form-data",
        cls="space-y-4"
    )

    # --- FIX: Wrap content in a div with consistent max-width and margin ---
    return Div(
        Div(
            StatusStrip(existing_documents, 'education', "Haridus"),
            StatusStrip(existing_documents, 'training', "Täiendkoolitus"),
            StatusStrip(existing_documents, 'employment_proof', "Töötamise tõend"),
            
            SectionContainer("1. Haridus", education_form),
            SectionContainer("2. Täiendkoolitus", training_form),
            SectionContainer("3. Töötamise tõend", employment_form),
        ),
        cls="max-w-5xl mx-auto" # This brings it in line with other tabs
    )