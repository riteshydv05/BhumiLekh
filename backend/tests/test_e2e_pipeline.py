"""End-to-End Pipeline Integration Test.

Target Flow Tested:
  POST /documents/upload
        ↓
  MinIO Storage & PostgreSQL Document Record
        ↓
  Celery process_document(document_id)
        ↓
  PREPROCESSING → PaddleOCR → Language Detection → TrOCR Handwriting → LayoutLMv3
        ↓
  IndicNER Entity Extraction → Multilingual Normalization/Transliteration → Validation
        ↓
  scikit-learn IsolationForest Anomaly Detection
        ↓
  PostgreSQL Result Persistence & Status Update (COMPLETED / VERIFICATION_REQUIRED)
"""

import io
import json
import uuid
import pytest
from PIL import Image, ImageDraw

from tests.conftest import TestSessionLocal as SessionLocal, test_engine as engine
from app.db.session import Base
from app.models.document import Document
from app.models.document_result import DocumentResult
from app.workers.pipeline_tasks import process_document
from app.services.storage_service import upload_file


def create_sample_land_record_image() -> bytes:
    """Generate a clean synthetic land record image (7/12 document)."""
    img = Image.new("RGB", (1000, 1200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    lines = [
        "7/12 LAND RECORD / अधिकार अभिलेख पत्रक",
        "Village: Wagholi | Taluka: Haveli | District: Pune",
        "Survey Number: 245A",
        "Area Hectares: 2.5",
        "Owner Name: Ramesh Kumar and Suresh Kumar",
        "Co-Owner Name: Suresh Kumar",
        "Registration Date: 15-08-2022",
        "Mutation Number: MUT-2024-009",
        "Stamp Duty: 50000",
        "Market Value: 1200000",
    ]
    
    y = 50
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 60

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(scope="module")
def setup_database():
    """Ensure test database tables are present."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield


def test_end_to_end_document_processing_pipeline(setup_database, monkeypatch):
    """Full End-to-End Test for Document Upload and AI Pipeline Orchestration."""

    monkeypatch.setattr("app.workers.pipeline_tasks._get_db_session", lambda: SessionLocal())

    db = SessionLocal()
    doc_id = uuid.uuid4()
    storage_key = f"e2e_test/{doc_id}/sample_land_record.png"
    
    file_bytes = create_sample_land_record_image()
    content_type = "image/png"

    # 1. Upload to storage (or mock for offline runner)
    try:
        upload_file(file_bytes, storage_key, content_type)
    except Exception:
        monkeypatch.setattr(
            "app.workers.pipeline_tasks._stage_download",
            lambda d_id: (file_bytes, content_type)
        )

    # 2. Insert Document record into PostgreSQL (status=UPLOADED)
    document = Document(
        id=doc_id,
        original_filename="sample_land_record.png",
        storage_key=storage_key,
        content_type=content_type,
        file_size=len(file_bytes),
        status="UPLOADED",
    )
    db.add(document)
    db.commit()

    # 3. Execute Celery pipeline task
    result = process_document(str(doc_id))

    # 4. Assert task status
    assert result["status"] in ("COMPLETED", "VERIFICATION_REQUIRED")

    # 5. Fetch updated Document from DB
    updated_doc = db.query(Document).filter(Document.id == doc_id).first()
    assert updated_doc is not None
    assert updated_doc.status in ("COMPLETED", "VERIFICATION_REQUIRED")
    assert updated_doc.processing_metadata is not None

    # Verify stage execution metadata
    stages = updated_doc.processing_metadata.get("stages", {})
    assert "preprocessing" in stages
    assert "ocr" in stages
    assert "language" in stages
    assert "layout" in stages
    assert "extraction" in stages
    assert "multilingual" in stages
    assert "validation" in stages
    assert "isolation_forest_anomaly_detection" in stages

    # Check IsolationForest anomaly result
    ml_meta = stages.get("isolation_forest_anomaly_detection", {})
    assert "anomaly_score" in ml_meta
    assert "risk_classification" in ml_meta

    # 6. Fetch DocumentResult rows from DB
    results = (
        db.query(DocumentResult)
        .filter(DocumentResult.document_id == doc_id)
        .all()
    )

    # Construct final structured output JSON
    final_output = {
        "document_id": str(updated_doc.id),
        "filename": updated_doc.original_filename,
        "status": updated_doc.status,
        "page_count": updated_doc.page_count,
        "detected_language": updated_doc.detected_language,
        "ocr_confidence": updated_doc.ocr_confidence,
        "pipeline_stages": {
            k: {v_k: v_v for v_k, v_v in v.items() if v_k != "ocr_pages"}
            for k, v in stages.items()
        },
        "extracted_fields": [
            {
                "field_name": r.field_name,
                "field_value": r.field_value,
                "original_text": r.original_text,
                "normalized_text": r.normalized_text,
                "transliteration": r.transliteration,
                "translation": r.translation,
                "confidence": r.confidence,
                "validated": r.validated,
                "anomaly_flag": r.anomaly_flag,
                "anomaly_reason": r.anomaly_reason,
            }
            for r in results
        ],
    }

    # Print final stored structured JSON
    print("\n========================================================")
    print("FINAL STORED STRUCTURED DOCUMENT PROCESSING JSON:")
    print("========================================================")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
    print("========================================================\n")

    # Clean up DB records
    db.query(DocumentResult).filter(DocumentResult.document_id == doc_id).delete()
    db.query(Document).filter(Document.id == doc_id).delete()
    db.commit()
    db.close()
