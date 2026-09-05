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
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)",
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

# Index on file_hash for duplicate detection
_INDEX_MIGRATIONS = [
    "CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents (file_hash)",
    # Learning system indexes
    "CREATE INDEX IF NOT EXISTS idx_training_samples_document_id ON training_samples (document_id)",
    "CREATE INDEX IF NOT EXISTS idx_training_samples_used ON training_samples (used_in_training)",
    "CREATE INDEX IF NOT EXISTS idx_training_samples_correction_type ON training_samples (correction_type)",
    "CREATE INDEX IF NOT EXISTS idx_learning_snapshots_deployed ON learning_snapshots (deployed)",
    "CREATE INDEX IF NOT EXISTS idx_learning_snapshots_version ON learning_snapshots (version)",
]

# GIS / Integration columns added to land_records_reference
_REFERENCE_COLUMN_MIGRATIONS = [
    "ALTER TABLE land_records_reference ADD COLUMN IF NOT EXISTS centroid_lat DOUBLE PRECISION",
    "ALTER TABLE land_records_reference ADD COLUMN IF NOT EXISTS centroid_lng DOUBLE PRECISION",
    "ALTER TABLE land_records_reference ADD COLUMN IF NOT EXISTS lrms_id VARCHAR(100)",
    "ALTER TABLE land_records_reference ADD COLUMN IF NOT EXISTS dilrmp_id VARCHAR(100)",
]

_GIS_MIGRATIONS = [
    # Add geometry column if not exists (PostGIS)
    """DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'land_records_reference' AND column_name = 'parcel_geometry'
        ) THEN
            ALTER TABLE land_records_reference
                ADD COLUMN parcel_geometry geometry(Polygon, 4326);
        END IF;
    END $$;""",
    # Spatial index
    "CREATE INDEX IF NOT EXISTS idx_land_records_parcel_gist ON land_records_reference USING GIST (parcel_geometry)",
]

# Document ownership + Audit log indexes
_AUTH_MIGRATIONS = [
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by UUID",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs (resource_type, resource_id)",
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)",
]


def seed_reference_data() -> None:
    """Populate the land_records_reference table with synthetic data for the prototype."""
    from app.models.land_record_reference import LandRecordReference
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        existing_count = db.query(LandRecordReference).count()
        if existing_count > 0:
            logger.info("Reference data already seeded (%d records), skipping", existing_count)
            return

        # Synthetic reference records with PostGIS parcel geometries
        # Using WKT (Well-Known Text) for polygon boundaries
        records = [
            LandRecordReference(
                survey_number="123/4",
                khasra_number="456",
                khata_number="78",
                plot_number="12A",
                owner_name="Rajesh Kumar",
                father_name="Mohan Lal",
                village="Chandpur",
                tehsil="Sadar",
                district="Lucknow",
                state="Uttar Pradesh",
                area="2.5 hectares",
                land_classification="Agricultural",
                registration_number="REG-2020-001234",
                mutation_number="MUT-2019-5678",
                source_database="synthetic_prototype",
                lrms_id="LRMS-UP-LKO-001",
                dilrmp_id="DILRMP-UP-001234",
                centroid_lat=26.8567,
                centroid_lng=80.9462,
                parcel_geometry="SRID=4326;POLYGON((80.943 26.854, 80.949 26.854, 80.949 26.859, 80.943 26.859, 80.943 26.854))",
            ),
            LandRecordReference(
                survey_number="567/8",
                khasra_number="890",
                khata_number="34",
                plot_number="5B",
                owner_name="Sunita Devi",
                father_name="Ram Prasad",
                village="Barabanki",
                tehsil="Nawabganj",
                district="Barabanki",
                state="Uttar Pradesh",
                area="1.2 acres",
                land_classification="Residential",
                registration_number="REG-2021-005678",
                mutation_number="MUT-2020-1234",
                source_database="synthetic_prototype",
                lrms_id="LRMS-UP-BBK-002",
                dilrmp_id="DILRMP-UP-005678",
                centroid_lat=26.9320,
                centroid_lng=81.1870,
                parcel_geometry="SRID=4326;POLYGON((81.184 26.929, 81.190 26.929, 81.190 26.935, 81.184 26.935, 81.184 26.929))",
            ),
            LandRecordReference(
                survey_number="234/1",
                khasra_number="111",
                khata_number="22",
                plot_number="3C",
                owner_name="Ramesh Sharma",
                father_name="Devendra Sharma",
                village="Kanpur Dehat",
                tehsil="Akbarpur",
                district="Kanpur",
                state="Uttar Pradesh",
                area="5.0 bigha",
                land_classification="Agricultural",
                registration_number="REG-2019-009012",
                mutation_number="MUT-2018-3456",
                source_database="synthetic_prototype",
                lrms_id="LRMS-UP-KNP-003",
                dilrmp_id="DILRMP-UP-009012",
                centroid_lat=26.4499,
                centroid_lng=80.3319,
                parcel_geometry="SRID=4326;POLYGON((80.328 26.447, 80.336 26.447, 80.336 26.453, 80.328 26.453, 80.328 26.447))",
            ),
            LandRecordReference(
                survey_number="789/2",
                khasra_number="222",
                khata_number="55",
                plot_number="7D",
                owner_name="Priya Singh",
                father_name="Vikram Singh",
                village="Varanasi",
                tehsil="Varanasi Sadar",
                district="Varanasi",
                state="Uttar Pradesh",
                area="0.8 hectares",
                land_classification="Commercial",
                registration_number="REG-2022-003456",
                source_database="synthetic_prototype",
                lrms_id="LRMS-UP-VNS-004",
                dilrmp_id="DILRMP-UP-003456",
                centroid_lat=25.3176,
                centroid_lng=82.9739,
                parcel_geometry="SRID=4326;POLYGON((82.971 25.315, 82.977 25.315, 82.977 25.320, 82.971 25.320, 82.971 25.315))",
            ),
            LandRecordReference(
                survey_number="345/6",
                khasra_number="333",
                khata_number="99",
                plot_number="1E",
                owner_name="Amit Verma",
                father_name="Suresh Verma",
                village="Allahabad",
                tehsil="Allahabad Sadar",
                district="Prayagraj",
                state="Uttar Pradesh",
                area="3.0 hectares",
                land_classification="Agricultural",
                registration_number="REG-2018-007890",
                mutation_number="MUT-2017-9012",
                source_database="synthetic_prototype",
                lrms_id="LRMS-UP-PRG-005",
                dilrmp_id="DILRMP-UP-007890",
                centroid_lat=25.4358,
                centroid_lng=81.8463,
                parcel_geometry="SRID=4326;POLYGON((81.842 25.432, 81.850 25.432, 81.850 25.439, 81.842 25.439, 81.842 25.432))",
            ),
            # Maharashtra demo parcels (matching the GIS map view)
            LandRecordReference(
                survey_number="142/1",
                khasra_number="451",
                khata_number="201",
                plot_number="W-1",
                owner_name="Rameshwar Dnyaneshwar Patil",
                father_name="Dnyaneshwar Patil",
                village="Wagholi",
                tehsil="Haveli",
                district="Pune",
                state="Maharashtra",
                area="0.85 hectares",
                land_classification="Jirayat (Agricultural)",
                registration_number="REG-MH-2021-14201",
                source_database="synthetic_prototype",
                lrms_id="LRMS-MH-PUN-006",
                dilrmp_id="DILRMP-MH-014201",
                centroid_lat=18.5790,
                centroid_lng=73.9805,
                parcel_geometry="SRID=4326;POLYGON((73.978 18.577, 73.979 18.581, 73.983 18.580, 73.981 18.577, 73.978 18.577))",
            ),
            LandRecordReference(
                survey_number="142/2",
                khasra_number="452",
                khata_number="202",
                plot_number="W-2",
                owner_name="Suresh Baburao Deshmukh",
                father_name="Baburao Deshmukh",
                village="Wagholi",
                tehsil="Haveli",
                district="Pune",
                state="Maharashtra",
                area="1.20 hectares",
                land_classification="Bagayat (Irrigated)",
                registration_number="REG-MH-2021-14202",
                source_database="synthetic_prototype",
                lrms_id="LRMS-MH-PUN-007",
                dilrmp_id="DILRMP-MH-014202",
                centroid_lat=18.5825,
                centroid_lng=73.9815,
                parcel_geometry="SRID=4326;POLYGON((73.979 18.581, 73.980 18.584, 73.984 18.583, 73.983 18.580, 73.979 18.581))",
            ),
            LandRecordReference(
                survey_number="143/A",
                khasra_number="453",
                khata_number="203",
                plot_number="W-3",
                owner_name="Chandrakant Keshav Jadhav",
                father_name="Keshav Jadhav",
                village="Wagholi",
                tehsil="Haveli",
                district="Pune",
                state="Maharashtra",
                area="0.45 hectares",
                land_classification="Non-Agricultural (Commercial)",
                registration_number="REG-MH-2022-14301",
                source_database="synthetic_prototype",
                lrms_id="LRMS-MH-PUN-008",
                dilrmp_id="DILRMP-MH-014301",
                centroid_lat=18.5775,
                centroid_lng=73.9838,
                parcel_geometry="SRID=4326;POLYGON((73.981 18.577, 73.983 18.580, 73.987 18.579, 73.984 18.575, 73.981 18.577))",
            ),
        ]

        for rec in records:
            db.add(rec)
        db.commit()
        logger.info("Seeded %d synthetic reference records", len(records))
    except Exception as exc:
        logger.warning("Failed to seed reference data: %s", exc)
        db.rollback()
    finally:
        db.close()


def run_migrations() -> None:
    # Import all models to ensure they are registered in Base.metadata
    import app.models  # noqa: F401

    from sqlalchemy import inspect, text

    from app.db.session import Base, engine

    logger.info("Running database migrations...")

    # Step 1: Create new tables (documents, document_results, land_records_reference, validation_results)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created/verified via create_all")

    # Step 2: Add new columns to existing tables (idempotent)
    with engine.begin() as conn:
        all_stmts = (
            _DOCUMENT_COLUMN_MIGRATIONS
            + _DOCUMENT_RESULTS_COLUMN_MIGRATIONS
            + _INDEX_MIGRATIONS
            + _REFERENCE_COLUMN_MIGRATIONS
            + _GIS_MIGRATIONS
            + _AUTH_MIGRATIONS
        )
        for stmt in all_stmts:
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

    # Step 3: Seed reference data
    seed_reference_data()

    # Step 4: Seed default admin user
    seed_admin_user()


def seed_admin_user() -> None:
    """Create a default admin user if none exists."""
    from app.models.user import User
    from app.db.session import SessionLocal
    from app.core.security import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == "ADMIN").first()
        if existing:
            logger.info("Admin user already exists (%s), skipping", existing.username)
            return

        admin = User(
            username="admin",
            email="admin@bhumilekh.gov.in",
            full_name="System Administrator",
            hashed_password=hash_password("admin123"),
            role="ADMIN",
            is_active=True,
        )
        db.add(admin)

        # Also seed demo users for each role
        demo_users = [
            User(
                username="officer1",
                email="officer@bhumilekh.gov.in",
                full_name="Revenue Officer",
                hashed_password=hash_password("officer123"),
                role="OFFICER",
            ),
            User(
                username="verifier1",
                email="verifier@bhumilekh.gov.in",
                full_name="Document Verifier",
                hashed_password=hash_password("verifier123"),
                role="VERIFIER",
            ),
            User(
                username="user1",
                email="user@bhumilekh.gov.in",
                full_name="Public User",
                hashed_password=hash_password("user123"),
                role="USER",
            ),
        ]
        for u in demo_users:
            db.add(u)

        db.commit()
        logger.info("Seeded default admin + 3 demo users")
    except Exception as exc:
        logger.warning("Failed to seed admin user: %s", exc)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    run_migrations()
