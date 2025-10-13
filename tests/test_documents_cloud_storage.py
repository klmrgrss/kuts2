# tests/test_documents_cloud_storage.py
import io
import json
import base64
from itsdangerous import Signer

from main import db, documents_controller, SESSION_SECRET_KEY
from auth.roles import EVALUATOR


class FakeBlob:
    def __init__(self, name: str, storage: dict[str, tuple[bytes, str | None]]):
        self._name = name
        self._storage = storage

    def upload_from_string(self, data: bytes, content_type: str | None = None) -> None:
        self._storage[self._name] = (data, content_type)

    def exists(self) -> bool:
        return self._name in self._storage

    def generate_signed_url(self, *_, **__) -> str:
        return f"https://fake.storage/{self._name}"


class FakeBucket:
    def __init__(self) -> None:
        self.storage: dict[str, tuple[bytes, str | None]] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(name, self.storage)


def test_document_upload_requires_cloud_storage(authenticated_client):
    controller = documents_controller

    original_bucket = controller.bucket
    original_local_dir = controller.local_storage_dir
    original_fallback = controller._local_fallback_enabled

    controller.bucket = None
    controller.local_storage_dir = None
    controller._local_fallback_enabled = False

    try:
        response = authenticated_client.post(
            "/app/dokumendid/upload?document_type=other",
            data={"description": "Should fail"},
            files={"document_file": ("f.txt", io.BytesIO(b"test"), "text/plain")},
        )
        assert response.status_code == 503
    finally:
        controller.bucket = original_bucket
        controller.local_storage_dir = original_local_dir
        controller._local_fallback_enabled = original_fallback


def test_document_upload_and_view_uses_signed_url(authenticated_client):
    controller = documents_controller

    fake_bucket = FakeBucket()
    original_bucket = controller.bucket
    controller.bucket = fake_bucket

    try:
        existing_ids = {doc.get("id") for doc in controller.documents_table(order_by="id")}

        file_bytes = b"Signed URL document"
        upload_response = authenticated_client.post(
            "/app/dokumendid/upload?document_type=education",
            data={"description": "Cloud doc", "institution": "", "specialty": "", "graduation_date": ""},
            files={"document_file": ("doc.pdf", io.BytesIO(file_bytes), "application/pdf")},
        )

        assert upload_response.status_code == 200
        assert upload_response.headers.get("HX-Redirect") == "/app/dokumendid"

        new_docs = [doc for doc in controller.documents_table(order_by="id") if doc.get("id") not in existing_ids]
        assert new_docs, "Expected document to be stored"
        document = new_docs[-1]

        storage_identifier = document.get("storage_identifier")
        assert storage_identifier in fake_bucket.storage

        view_response = authenticated_client.get(f"/files/view/{document['id']}", follow_redirects=False)
        assert view_response.status_code == 307
        assert view_response.headers.get("location") == f"https://fake.storage/{storage_identifier}"

    finally:
        controller.bucket = original_bucket


def test_localised_evaluator_can_view_other_users_document(authenticated_client):
    controller = documents_controller

    original_bucket = controller.bucket
    original_local_dir = controller.local_storage_dir
    original_fallback = controller._local_fallback_enabled

    fake_bucket = FakeBucket()
    controller.bucket = fake_bucket
    controller.local_storage_dir = None
    controller._local_fallback_enabled = False

    storage_identifier = "other.user/doc.pdf"
    fake_bucket.storage[storage_identifier] = (b"data", "application/pdf")

    doc_record = controller.documents_table.insert({
        "user_email": "other.user@example.com", "document_type": "other", "description": "Other user document",
        "metadata": "{}", "original_filename": "doc.pdf", "storage_identifier": storage_identifier,
        "upload_timestamp": "2024-01-01T00:00:00",
    })
    document_id = doc_record.get('id')

    users_table = db.t.users
    test_user_email = "test_user@example.com"
    original_role = users_table[test_user_email].get("role")

    try:
        users_table.update({"role": "Hindaja"}, pk_values=test_user_email)

        # Re-authenticate the client with the new 'evaluator' role
        session_data = {"authenticated": True, "user_email": test_user_email, "role": EVALUATOR}
        signer = Signer(SESSION_SECRET_KEY)
        signed_data = signer.sign(base64.b64encode(json.dumps(session_data).encode("utf-8")))
        authenticated_client.cookies.set("session", signed_data.decode("utf-8"))

        view_response = authenticated_client.get(f"/files/view/{document_id}", follow_redirects=False)

        assert view_response.status_code == 307
        assert view_response.headers.get("location") == f"https://fake.storage/{storage_identifier}"
    finally:
        users_table.update({"role": original_role}, pk_values=test_user_email)
        controller.bucket = original_bucket
        controller.local_storage_dir = original_local_dir
        controller._local_fallback_enabled = original_fallback
        controller.documents_table.delete(document_id)