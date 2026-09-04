"""Database migration script.

Runs SQLAlchemy's create_all for new tables, then applies ALTER TABLE
statements for columns added to existing tables.

Safe to run multiple times (idempotent: uses IF NOT EXISTS).

Usage:
    cd backend
    python -m app.db.migrate
"""
import logging

logger = logging.getLogger(__name__)

# Columns to add to the existing `documents` table (all nullable).
# Use IF NOT EXISTS so this script is safe to re-run.
_DOCUMENT_COLUMN_MIGRATIONS = [
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS task_id VARCHAR(255)",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS ocr_confidence FLOAT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_metadata JSONB",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type VARCHAR(100)",
]

_DOCUMENT_RESULTS_COLUMN_MIGRATIONS = [
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS original_text TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS normalized_text TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS transliteration TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS translation TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS data_type VARCHAR(50) DEFAULT 'string'",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS page_number INTEGER",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS bounding_box JSONB",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50)",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS canonical_key VARCHAR(100)",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS source_text TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS normalized_value TEXT",
    "ALTER TABLE document_results ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) DEFAULT 'unverified'",
]


def run_migrations() -> None:
    # Import all models to ensure they are registered in Base.metadata
    import app.models  # noqa: F401

    from sqlalchemy import inspect, text

    from app.db.session import Base, engine

    logger.info("Running database migrations...")

    # Step 1: Create new tables (documents, document_results)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created/verified via create_all")

    # Step 2: Add new columns to existing tables (idempotent)
    with engine.begin() as conn:
        for stmt in _DOCUMENT_COLUMN_MIGRATIONS + _DOCUMENT_RESULTS_COLUMN_MIGRATIONS:
            try:
                conn.execute(text(stmt))
                logger.info("Migration applied: %s", stmt)
            except Exception as exc:
                logger.warning("Migration skipped/failed (%s): %s", stmt, exc)

    # List all tables for confirmation
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info("DB tables: %s", [t for t in tables if not t.startswith("spatial")])

    # Verify new document columns
    cols = [c["name"] for c in inspector.get_columns("documents")]
    logger.info("documents columns: %s", cols)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    run_migrations()
