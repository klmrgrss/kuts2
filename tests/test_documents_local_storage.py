import io
from pathlib import Path

from main import documents_controller


def test_document_upload_falls_back_to_local_storage(authenticated_client):
    controller = documents_controller

    assert controller.bucket is None
    assert controller.local_storage_dir is not None

    existing_ids = {
        doc.get("id")
        for doc in controller.documents_table(order_by="id")
    }

    file_bytes = b"Local storage upload test"
    response = authenticated_client.post(
        "/app/dokumendid/upload?document_type=other",
        data={"description": "Local fallback"},
        files={"document_file": ("local_test.txt", io.BytesIO(file_bytes), "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/app/dokumendid"

    new_docs = [
        doc
        for doc in controller.documents_table(order_by="id")
        if doc.get("id") not in existing_ids
    ]

    assert new_docs, "Expected a new document record to be created."
    doc_record = new_docs[-1]

    storage_identifier = doc_record.get("storage_identifier")
    assert storage_identifier and storage_identifier.startswith("local:")

    relative_path = storage_identifier.split("local:", 1)[1]
    local_base = controller.local_storage_dir.resolve()
    local_path = (local_base / Path(relative_path)).resolve()
    assert local_path.exists()

    with open(local_path, "rb") as stored_file:
        assert stored_file.read() == file_bytes

    view_response = authenticated_client.get(f"/files/view/{doc_record['id']}")
    assert view_response.status_code == 200
    assert view_response.content == file_bytes
    assert "attachment" in view_response.headers.get("content-disposition", "")
