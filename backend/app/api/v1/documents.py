"""Documents API — v1

Endpoints:
  POST   /api/v1/documents/upload          Upload a document (triggers AI pipeline)
  GET    /api/v1/documents                 List all documents
  GET    /api/v1/documents/{id}            Get document detail (extended)
  GET    /api/v1/documents/{id}/file       Stream the raw file
  GET    /api/v1/documents/{id}/status     Lightweight status check
  GET    /api/v1/documents/{id}/results    Get extracted field results
  GET    /api/v1/documents/{id}/fields     Get dynamic fields (alias for results)
  GET    /api/v1/documents/{id}/ocr        Get raw OCR pages
  POST   /api/v1/documents/{id}/fields     Add a manual field
  PATCH  /api/v1/documents/{id}/fields/{field_id}  Edit a field
  DELETE /api/v1/documents/{id}/fields/{field_id}  Remove a field
"""
import uuid
from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.document_result import DocumentResult
from app.services.storage_service import get_file, upload_file

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def _serialize_field(r: DocumentResult) -> dict:
    """Serialize a DocumentResult row to JSON."""
    return {
        "id": str(r.id),
        "document_id": str(r.document_id),
        "field_name": r.field_name,
        "field_value": r.field_value,
        "normalized_value": getattr(r, "normalized_value", None),
        "data_type": getattr(r, "data_type", "string"),
        "confidence": r.confidence,
        "page_number": getattr(r, "page_number", None),
        "bounding_box": getattr(r, "bounding_box", None),
        "source_text": getattr(r, "source_text", None),
        "extraction_method": getattr(r, "extraction_method", None),
        "canonical_key": getattr(r, "canonical_key", None),
        "original_text": r.original_text,
        "normalized_text": r.normalized_text,
        "transliteration": r.transliteration,
        "translation": r.translation,
        "validated": r.validated,
        "validation_status": getattr(r, "validation_status", "pending"),
        "anomaly_flag": r.anomaly_flag,
        "anomaly_reason": r.anomaly_reason,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a document and enqueue it for AI processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_data = await file.read()

    if not file_data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    document_id = uuid.uuid4()
    storage_key = f"{document_id}/{file.filename}"

    upload_file(
        file_data=file_data,
        storage_key=storage_key,
        content_type=file.content_type,
    )

    document = Document(
        id=document_id,
        original_filename=file.filename,
        storage_key=storage_key,
        content_type=file.content_type,
        file_size=len(file_data),
        status="UPLOADED",
        detected_language=language if language and language != "auto" else "unknown",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Enqueue the AI processing pipeline (non-blocking)
    try:
        from app.workers.pipeline_tasks import process_document

        task = process_document.delay(str(document.id))
        document.task_id = task.id
        db.commit()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "Failed to enqueue processing task for %s: %s", document.id, exc
        )

    return {
        "id": str(document.id),
        "filename": document.original_filename,
        "status": document.status,
        "file_size": document.file_size,
        "content_type": document.content_type,
        "created_at": document.created_at,
    }


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("")
def list_documents(
    db: Session = Depends(get_db),
):
    """List all documents ordered by most recent first."""
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": str(document.id),
            "filename": document.original_filename,
            "status": document.status,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "detected_language": document.detected_language,
            "document_type": getattr(document, "document_type", None),
            "created_at": document.created_at,
        }
        for document in documents
    ]


# ---------------------------------------------------------------------------
# Get document detail
# ---------------------------------------------------------------------------

@router.get("/{document_id}")
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get document metadata including AI processing results."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(document.id),
        "filename": document.original_filename,
        "status": document.status,
        "file_size": document.file_size,
        "content_type": document.content_type,
        "detected_language": document.detected_language,
        "document_type": getattr(document, "document_type", None),
        "created_at": document.created_at,
        "task_id": document.task_id,
        "error_message": document.error_message,
        "page_count": document.page_count,
        "ocr_confidence": document.ocr_confidence,
        "processing_metadata": document.processing_metadata,
    }


# ---------------------------------------------------------------------------
# Lightweight status check
# ---------------------------------------------------------------------------

@router.get("/{document_id}/status")
def get_document_status(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Return a lightweight status object for polling."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": str(document.id),
        "status": document.status,
        "task_id": document.task_id,
        "error_message": document.error_message,
    }


# ---------------------------------------------------------------------------
# Get extracted field results
# ---------------------------------------------------------------------------

@router.get("/{document_id}/results")
def get_document_results(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Return extracted field results for a processed document."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    results = (
        db.query(DocumentResult)
        .filter(DocumentResult.document_id == document_id)
        .all()
    )

    field_items = [_serialize_field(r) for r in results]

    return {
        "document_id": str(document.id),
        "status": document.status,
        "document_type": getattr(document, "document_type", None),
        "count": len(results),
        "field_count": len(results),
        "results": field_items,
        "fields": field_items,
    }


# ---------------------------------------------------------------------------
# Dynamic fields CRUD — alias + add/edit/delete
# ---------------------------------------------------------------------------

@router.get("/{document_id}/fields")
def get_fields(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get dynamic extracted fields (same as /results, cleaner name)."""
    return get_document_results(document_id, db)


@router.post("/{document_id}/fields")
def add_field(
    document_id: uuid.UUID,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Manually add a new field to a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    field_name = body.get("field_name")
    if not field_name:
        raise HTTPException(status_code=400, detail="field_name is required")

    new_field = DocumentResult(
        document_id=document_id,
        field_name=field_name,
        field_value=body.get("field_value"),
        data_type=body.get("data_type", "string"),
        confidence=body.get("confidence", 1.0),
        page_number=body.get("page_number"),
        extraction_method="manual",
        canonical_key=body.get("canonical_key"),
        source_text=body.get("source_text"),
        validated=True,
        validation_status="valid",
    )
    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    return _serialize_field(new_field)


@router.patch("/{document_id}/fields/{field_id}")
def update_field(
    document_id: uuid.UUID,
    field_id: uuid.UUID,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Edit an existing field (value, name, etc.)."""
    field = (
        db.query(DocumentResult)
        .filter(
            DocumentResult.id == field_id,
            DocumentResult.document_id == document_id,
        )
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Updatable attributes
    for attr in (
        "field_name", "field_value", "data_type", "confidence",
        "canonical_key", "validation_status", "anomaly_flag", "anomaly_reason",
    ):
        if attr in body:
            setattr(field, attr, body[attr])

    field.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(field)

    return _serialize_field(field)


@router.delete("/{document_id}/fields/{field_id}")
def delete_field(
    document_id: uuid.UUID,
    field_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Remove an extracted field."""
    field = (
        db.query(DocumentResult)
        .filter(
            DocumentResult.id == field_id,
            DocumentResult.document_id == document_id,
        )
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    db.delete(field)
    db.commit()
    return {"status": "deleted", "field_id": str(field_id)}


# ---------------------------------------------------------------------------
# Raw OCR pages
# ---------------------------------------------------------------------------

@router.get("/{document_id}/ocr")
def get_ocr_pages(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Return raw OCR output for debugging and verification."""
    from app.models.document_page import DocumentPage

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = (
        db.query(DocumentPage)
        .filter(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
        .all()
    )

    return {
        "document_id": str(document_id),
        "page_count": len(pages),
        "pages": [
            {
                "id": str(p.id),
                "page_number": p.page_number,
                "raw_text": p.raw_text,
                "language": p.language,
                "ocr_confidence": p.ocr_confidence,
                "ocr_engine": p.ocr_engine,
                "blocks_json": p.blocks_json,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pages
        ],
    }


# ---------------------------------------------------------------------------
# Stream raw file
# ---------------------------------------------------------------------------

@router.get("/{document_id}/file")
def view_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Stream the original uploaded document file."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        response = get_file(document.storage_key)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Document file not found in storage",
        )

    return StreamingResponse(
        response.stream(32 * 1024),
        media_type=document.content_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{document.original_filename}"'
            )
        },
    )


# ---------------------------------------------------------------------------
# Reprocess with target language
# ---------------------------------------------------------------------------

@router.post("/{document_id}/reprocess")
def reprocess_document(
    document_id: uuid.UUID,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Re-run AI OCR and extraction pipeline with a target OCR language."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    target_lang = payload.get("language", "auto")
    doc.detected_language = target_lang
    doc.status = "PROCESSING"
    doc.error_message = None
    db.commit()

    # Clear previous results
    db.query(DocumentResult).filter(DocumentResult.document_id == document_id).delete()
    db.commit()

    # Trigger processing task
    try:
        from app.workers.pipeline_tasks import process_document
        task = process_document.delay(str(document_id))
        doc.task_id = task.id
        db.commit()
    except Exception as exc:
        # Fallback to direct synchronous execution if Celery unavailable
        from app.workers.pipeline_tasks import process_document_sync
        process_document_sync(str(document_id))

    return {
        "document_id": str(document_id),
        "status": "PROCESSING",
        "language": target_lang,
        "message": f"Reprocessing document with OCR language '{target_lang}'",
    }


# ---------------------------------------------------------------------------
# Translate Extracted Fields
# ---------------------------------------------------------------------------

@router.post("/{document_id}/translate")
def translate_document(
    document_id: uuid.UUID,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """Translate extracted fields for a document into target_language (e.g. 'en', 'hi', 'mr', 'ta')."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    target_lang = payload.get("target_language", "en")
    from app.services.translation_service import translate_document_results
    updated_results = translate_document_results(str(document_id), target_lang=target_lang, db=db)

    return {
        "document_id": str(document_id),
        "target_language": target_lang,
        "fields_translated": len(updated_results),
        "fields": [_serialize_field(r) for r in updated_results],
    }
