"""Documents API — v1

Endpoints:
  POST   /api/v1/documents/upload          Upload a document (triggers AI pipeline)
  GET    /api/v1/documents                 List all documents
  GET    /api/v1/documents/{id}            Get document detail (extended)
  GET    /api/v1/documents/{id}/file       Stream the raw file
  GET    /api/v1/documents/{id}/status     Lightweight status check
  GET    /api/v1/documents/{id}/results    Get extracted field results

Backward compatibility:
  - POST /upload and GET / responses retain original field names and types
  - All new fields are optional / additive
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a document and enqueue it for AI processing.

    Returns the same 6-field response as before (backward compatible).
    The document will be asynchronously processed through the AI pipeline.
    """
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
        # Pipeline enqueue failure must not break upload
        import logging
        logging.getLogger(__name__).warning(
            "Failed to enqueue processing task for %s: %s", document.id, exc
        )

    # Backward-compatible response (same 6 fields as before)
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
        "created_at": document.created_at,
        # Extended fields (new, always present — may be None)
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

    return {
        "document_id": str(document.id),
        "status": document.status,
        "field_count": len(results),
        "fields": [
            {
                "id": str(r.id),
                "field_name": r.field_name,
                "field_value": r.field_value,
                "confidence": r.confidence,
                "validated": r.validated,
                "anomaly_flag": r.anomaly_flag,
                "anomaly_reason": r.anomaly_reason,
            }
            for r in results
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
