"""Duplicate Detection Service — file-level and field-level content deduplication.

File-level:
  SHA-256 hash of the raw file bytes. Detects identical file re-uploads.

Field-level:
  Compares canonical field values across documents to detect content duplicates
  (e.g., same survey number + village + owner appearing in two different uploads).
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DuplicateCandidate:
    """A potentially duplicate document."""
    document_id: str
    filename: str
    match_type: str  # "file_hash" | "content_match"
    matched_fields: list[str] = field(default_factory=list)
    similarity_score: float = 1.0


@dataclass
class DuplicateReport:
    """Duplicate detection results for a document."""
    document_id: str
    file_hash: str = ""
    has_file_duplicate: bool = False
    has_content_duplicate: bool = False
    duplicates: list[DuplicateCandidate] = field(default_factory=list)
    checked_documents: int = 0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "file_hash": self.file_hash,
            "has_file_duplicate": self.has_file_duplicate,
            "has_content_duplicate": self.has_content_duplicate,
            "duplicate_count": len(self.duplicates),
            "checked_documents": self.checked_documents,
            "duplicates": [
                {
                    "document_id": d.document_id,
                    "filename": d.filename,
                    "match_type": d.match_type,
                    "matched_fields": d.matched_fields,
                    "similarity_score": d.similarity_score,
                }
                for d in self.duplicates
            ],
        }


# ---------------------------------------------------------------------------
# File-Level Duplicate Detection (SHA-256)
# ---------------------------------------------------------------------------

def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def check_file_duplicates(
    document_id: str,
    file_hash: str,
    db_session: Any = None,
) -> list[DuplicateCandidate]:
    """Check if any existing document has the same file hash."""
    from app.models.document import Document

    if db_session is None:
        from app.db.session import SessionLocal
        db_session = SessionLocal()
        should_close = True
    else:
        should_close = False

    duplicates: list[DuplicateCandidate] = []
    try:
        target_uuid = uuid.UUID(str(document_id))

        # Query documents with matching file_hash (excluding self)
        existing = (
            db_session.query(Document)
            .filter(Document.id != target_uuid)
            .filter(Document.file_hash == file_hash)
            .all()
        )

        for doc in existing:
            duplicates.append(DuplicateCandidate(
                document_id=str(doc.id),
                filename=doc.original_filename,
                match_type="file_hash",
                matched_fields=["file_content"],
                similarity_score=1.0,
            ))

        if duplicates:
            logger.warning(
                "[%s] File-level duplicate detected: %d matching documents",
                document_id, len(duplicates),
            )
    except Exception as exc:
        logger.warning("[%s] File duplicate check failed: %s", document_id, exc)
    finally:
        if should_close:
            db_session.close()

    return duplicates


# ---------------------------------------------------------------------------
# Field-Level Content Duplicate Detection
# ---------------------------------------------------------------------------

# Key canonical fields for content matching
_CONTENT_MATCH_KEYS = {
    "SURVEY_NUMBER", "KHASRA_NUMBER", "KHATA_NUMBER", "PLOT_NUMBER",
    "OWNER_NAME", "VILLAGE", "DISTRICT",
}

# Minimum number of matching fields to consider content duplicate
_MIN_FIELD_MATCHES = 3


def check_content_duplicates(
    document_id: str,
    fields: list[Any],
    db_session: Any = None,
) -> list[DuplicateCandidate]:
    """Check if another document has the same canonical field values."""
    from app.models.document import Document
    from app.models.document_result import DocumentResult

    # Build canonical field map for the current document
    current_canonical: dict[str, str] = {}
    for f in fields:
        if isinstance(f, dict):
            ck = f.get("canonical_key")
            fv = f.get("field_value") or ""
        else:
            ck = getattr(f, "canonical_key", None)
            fv = getattr(f, "field_value", getattr(f, "extracted_value", "")) or ""

        if ck and ck in _CONTENT_MATCH_KEYS and fv.strip():
            current_canonical[ck] = fv.strip().lower()

    if len(current_canonical) < 2:
        logger.info("[%s] Insufficient canonical fields for content duplicate check", document_id)
        return []

    if db_session is None:
        from app.db.session import SessionLocal
        db_session = SessionLocal()
        should_close = True
    else:
        should_close = False

    duplicates: list[DuplicateCandidate] = []
    try:
        target_uuid = uuid.UUID(str(document_id))

        # Get all other document IDs
        other_doc_ids = [
            row[0] for row in
            db_session.query(Document.id)
            .filter(Document.id != target_uuid)
            .all()
        ]

        for other_id in other_doc_ids:
            # Get canonical fields for this other document
            other_results = (
                db_session.query(DocumentResult)
                .filter(DocumentResult.document_id == other_id)
                .filter(DocumentResult.canonical_key.in_(list(_CONTENT_MATCH_KEYS)))
                .all()
            )

            other_canonical: dict[str, str] = {}
            for r in other_results:
                if r.canonical_key and r.field_value:
                    other_canonical[r.canonical_key] = r.field_value.strip().lower()

            # Count matching fields
            matched_fields = []
            for ck, val in current_canonical.items():
                if ck in other_canonical and other_canonical[ck] == val:
                    matched_fields.append(ck)

            if len(matched_fields) >= _MIN_FIELD_MATCHES:
                other_doc = db_session.query(Document).filter(Document.id == other_id).first()
                similarity = len(matched_fields) / max(len(current_canonical), 1)
                duplicates.append(DuplicateCandidate(
                    document_id=str(other_id),
                    filename=other_doc.original_filename if other_doc else "unknown",
                    match_type="content_match",
                    matched_fields=matched_fields,
                    similarity_score=round(similarity, 3),
                ))

        if duplicates:
            logger.warning(
                "[%s] Content-level duplicates detected: %d matching documents",
                document_id, len(duplicates),
            )
    except Exception as exc:
        logger.warning("[%s] Content duplicate check failed: %s", document_id, exc)
    finally:
        if should_close:
            db_session.close()

    return duplicates


# ---------------------------------------------------------------------------
# Combined duplicate detection
# ---------------------------------------------------------------------------

def detect_duplicates(
    document_id: str,
    file_bytes: bytes | None = None,
    fields: list[Any] | None = None,
    db_session: Any = None,
) -> DuplicateReport:
    """Run both file-level and content-level duplicate detection.

    Returns a unified DuplicateReport.
    """
    report = DuplicateReport(document_id=document_id)

    # File-level check
    if file_bytes:
        report.file_hash = compute_file_hash(file_bytes)

        # Save hash to document for future lookups
        _save_file_hash(document_id, report.file_hash, db_session)

        file_dupes = check_file_duplicates(document_id, report.file_hash, db_session)
        if file_dupes:
            report.has_file_duplicate = True
            report.duplicates.extend(file_dupes)

    # Content-level check
    if fields:
        content_dupes = check_content_duplicates(document_id, fields, db_session)
        if content_dupes:
            report.has_content_duplicate = True
            # Add only non-duplicate entries (avoid double-counting same doc)
            seen_ids = {d.document_id for d in report.duplicates}
            for cd in content_dupes:
                if cd.document_id not in seen_ids:
                    report.duplicates.append(cd)

    logger.info(
        "[%s] Duplicate detection complete: file_dup=%s, content_dup=%s, total=%d",
        document_id, report.has_file_duplicate, report.has_content_duplicate,
        len(report.duplicates),
    )
    return report


def _save_file_hash(document_id: str, file_hash: str, db_session: Any = None) -> None:
    """Persist file_hash to the document record for future lookups."""
    from app.models.document import Document

    if db_session is None:
        from app.db.session import SessionLocal
        db_session = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        target_uuid = uuid.UUID(str(document_id))
        doc = db_session.query(Document).filter(Document.id == target_uuid).first()
        if doc and hasattr(doc, "file_hash"):
            doc.file_hash = file_hash
            db_session.commit()
    except Exception as exc:
        logger.warning("[%s] Failed to save file_hash: %s", document_id, exc)
        db_session.rollback()
    finally:
        if should_close:
            db_session.close()
