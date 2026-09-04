"""API integration tests using FastAPI TestClient with SQLite."""
import io

import pytest


class TestHealthEndpoints:

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDocumentListEndpoint:

    def test_list_empty(self, client):
        response = client.get("/api/v1/documents")
        assert response.status_code == 200
        assert response.json() == []


class TestDocumentUploadEndpoint:

    def _pdf_bytes(self) -> bytes:
        """Return a tiny but valid PDF for testing."""
        return (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF\n"
        )

    def test_upload_pdf(self, client, monkeypatch):
        """Upload endpoint: should persist document and return 6 fields."""
        # Monkeypatch MinIO and Celery to avoid real connections in tests
        import app.services.storage_service as ss
        import app.workers.pipeline_tasks as pt

        monkeypatch.setattr(ss, "upload_file", lambda **kwargs: None)

        class FakeTask:
            id = "fake-task-id"

        def fake_delay(doc_id):
            return FakeTask()

        class FakePT:
            @staticmethod
            def delay(doc_id):
                return FakeTask()

        monkeypatch.setattr(pt, "process_document", FakePT)

        pdf_bytes = self._pdf_bytes()
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test_land.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify backward-compatible 6-field contract
        assert "id" in data
        assert "filename" in data
        assert data["filename"] == "test_land.pdf"
        assert "status" in data
        assert data["status"] == "UPLOADED"
        assert "file_size" in data
        assert data["file_size"] == len(pdf_bytes)
        assert "content_type" in data
        assert data["content_type"] == "application/pdf"
        assert "created_at" in data

    def test_upload_unsupported_type(self, client):
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_empty_file(self, client, monkeypatch):
        import app.services.storage_service as ss
        monkeypatch.setattr(ss, "upload_file", lambda **kwargs: None)

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400

    def test_get_document_not_found(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documents/{fake_id}")
        assert response.status_code == 404

    def test_get_document_status_not_found(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documents/{fake_id}/status")
        assert response.status_code == 404

    def test_get_document_results_not_found(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/documents/{fake_id}/results")
        assert response.status_code == 404
