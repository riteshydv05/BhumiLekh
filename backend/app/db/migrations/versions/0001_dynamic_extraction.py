"""Dynamic extraction architecture migration.

Adds:
  - documents.document_type
  - document_results.data_type
  - document_results.page_number
  - document_results.bounding_box (JSONB)
  - document_results.extraction_method
  - document_results.canonical_key
  - document_results.validation_status
  - document_pages table (raw OCR storage)

Revision: 0001
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

revision = "0001_dynamic_extraction"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. documents — add document_type column
    # ------------------------------------------------------------------
    op.add_column(
        "documents",
        sa.Column(
            "document_type",
            sa.String(100),
            nullable=True,
            server_default="Unknown",
            comment="Classified document type: Sale Deed, RoR, Mutation, etc.",
        ),
    )

    # ------------------------------------------------------------------
    # 2. document_results — add dynamic extraction metadata columns
    # ------------------------------------------------------------------

    # data_type: string, integer, decimal, date, person, identifier, etc.
    op.add_column(
        "document_results",
        sa.Column(
            "data_type",
            sa.String(50),
            nullable=True,
            server_default="string",
            comment="Detected data type of the extracted value",
        ),
    )

    # page_number: which page the field was found on
    op.add_column(
        "document_results",
        sa.Column(
            "page_number",
            sa.Integer,
            nullable=True,
            comment="1-indexed page from which field was extracted",
        ),
    )

    # bounding_box: [x1, y1, x2, y2] coordinates from OCR
    op.add_column(
        "document_results",
        sa.Column(
            "bounding_box",
            JSONB,
            nullable=True,
            comment="OCR bounding box [x1, y1, x2, y2] or polygon",
        ),
    )

    # extraction_method: how the field was discovered
    op.add_column(
        "document_results",
        sa.Column(
            "extraction_method",
            sa.String(50),
            nullable=True,
            server_default="key_value_extraction",
            comment="Extraction method: key_value_extraction, ner, table_extraction, handwriting_ocr, vlm, manual",
        ),
    )

    # canonical_key: optional standard land-record identifier (nullable)
    op.add_column(
        "document_results",
        sa.Column(
            "canonical_key",
            sa.String(100),
            nullable=True,
            comment="Standard canonical key e.g. SURVEY_NUMBER (NULL for unknown fields)",
        ),
    )

    # validation_status: pending, valid, invalid, warning
    op.add_column(
        "document_results",
        sa.Column(
            "validation_status",
            sa.String(20),
            nullable=True,
            server_default="pending",
            comment="Field validation state: pending, valid, invalid, warning",
        ),
    )

    # ------------------------------------------------------------------
    # 3. document_pages — new table for raw OCR storage
    # ------------------------------------------------------------------
    op.create_table(
        "document_pages",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
        ),
        sa.Column(
            "document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("page_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("ocr_confidence", sa.Float, nullable=True),
        sa.Column("ocr_engine", sa.String(100), nullable=True),
        sa.Column("blocks_json", JSONB, nullable=True),
        sa.Column("preprocessing_info", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_document_pages_document_id",
        "document_pages",
        ["document_id"],
    )


def downgrade() -> None:
    # document_pages
    op.drop_index("ix_document_pages_document_id", table_name="document_pages")
    op.drop_table("document_pages")

    # document_results columns
    for col in [
        "validation_status", "canonical_key", "extraction_method",
        "bounding_box", "page_number", "data_type",
    ]:
        op.drop_column("document_results", col)

    # documents column
    op.drop_column("documents", "document_type")
