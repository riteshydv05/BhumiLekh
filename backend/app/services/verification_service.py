"""Cross-Database Verification Service.

Compares extracted canonical fields against a reference `land_records` table.
Returns MATCH / MISMATCH / NOT_FOUND / NOT_VERIFIABLE per field.

For the prototype, the reference table is synthetic (seeded in PostgreSQL).
The design is ready for future integration with authorized government
LRMS / DILRMP databases.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

VERIFICATION_MATCH = "MATCH"
VERIFICATION_MISMATCH = "MISMATCH"
VERIFICATION_NOT_FOUND = "NOT_FOUND"
VERIFICATION_NOT_VERIFIABLE = "NOT_VERIFIABLE"


@dataclass
class FieldVerification:
    """Verification result for a single canonical field."""
    field_name: str
    canonical_key: str | None
    extracted_value: str | None
    reference_value: str | None
    status: str  # MATCH | MISMATCH | NOT_FOUND | NOT_VERIFIABLE
    source: str = "land_records_reference"


@dataclass
class VerificationReport:
    """Full verification report for a document."""
    document_id: str = ""
    field_verifications: list[FieldVerification] = field(default_factory=list)
    match_count: int = 0
    mismatch_count: int = 0
    not_found_count: int = 0
    not_verifiable_count: int = 0
    reference_record_id: str | None = None
    overall_status: str = "UNVERIFIED"

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "overall_status": self.overall_status,
            "match_count": self.match_count,
            "mismatch_count": self.mismatch_count,
            "not_found_count": self.not_found_count,
            "not_verifiable_count": self.not_verifiable_count,
            "reference_record_id": self.reference_record_id,
            "field_verifications": [
                {
                    "field_name": fv.field_name,
                    "canonical_key": fv.canonical_key,
                    "extracted_value": fv.extracted_value,
                    "reference_value": fv.reference_value,
                    "status": fv.status,
                    "source": fv.source,
                }
                for fv in self.field_verifications
            ],
        }


# ---------------------------------------------------------------------------
# Verifiable canonical keys — only these can be cross-referenced
# ---------------------------------------------------------------------------
_VERIFIABLE_KEYS = {
    "SURVEY_NUMBER", "KHASRA_NUMBER", "KHATA_NUMBER", "PLOT_NUMBER",
    "OWNER_NAME", "FATHER_NAME",
    "VILLAGE", "TEHSIL", "DISTRICT",
    "AREA", "LAND_CLASSIFICATION",
    "REGISTRATION_NUMBER", "MUTATION_NUMBER",
}

# ---------------------------------------------------------------------------
# Lookup keys for matching reference records
# ---------------------------------------------------------------------------
_MATCH_KEYS = {"SURVEY_NUMBER", "KHASRA_NUMBER", "KHATA_NUMBER", "PLOT_NUMBER", "REGISTRATION_NUMBER"}


def _normalize_value(val: str | None) -> str:
    """Normalize a value for comparison (lowercase, strip whitespace/punctuation)."""
    if not val:
        return ""
    import re
    return re.sub(r"[\s\-/.,;:]+", " ", val.strip().lower()).strip()


def verify_against_reference(
    document_id: str,
    fields: list[Any],
    db_session: Any = None,
) -> VerificationReport:
    """Compare extracted fields against the reference land_records table.

    `fields` is a list of objects/dicts with `field_name`, `field_value`,
    `canonical_key` attributes.
    """
    report = VerificationReport(document_id=document_id)

    # Build map of canonical_key → extracted value
    canonical_map: dict[str, tuple[str, str | None]] = {}
    for f in fields:
        if isinstance(f, dict):
            ck = f.get("canonical_key")
            fn = f.get("field_name", "")
            fv = f.get("field_value")
        else:
            ck = getattr(f, "canonical_key", None)
            fn = getattr(f, "field_name", "")
            fv = getattr(f, "field_value", getattr(f, "extracted_value", None))

        if ck and ck in _VERIFIABLE_KEYS:
            canonical_map[ck] = (fn, fv)

    if not canonical_map:
        # No verifiable canonical fields found — all NOT_VERIFIABLE
        for f in fields:
            fn = f.get("field_name", "") if isinstance(f, dict) else getattr(f, "field_name", "")
            ck = f.get("canonical_key") if isinstance(f, dict) else getattr(f, "canonical_key", None)
            report.field_verifications.append(FieldVerification(
                field_name=fn,
                canonical_key=ck,
                extracted_value=None,
                reference_value=None,
                status=VERIFICATION_NOT_VERIFIABLE,
            ))
            report.not_verifiable_count += 1
        report.overall_status = "NOT_VERIFIABLE"
        return report

    # Try to find a matching reference record
    reference_record = _lookup_reference_record(canonical_map, db_session)

    if reference_record is None:
        # No reference record found
        for ck, (fn, fv) in canonical_map.items():
            report.field_verifications.append(FieldVerification(
                field_name=fn,
                canonical_key=ck,
                extracted_value=fv,
                reference_value=None,
                status=VERIFICATION_NOT_FOUND,
            ))
            report.not_found_count += 1
        # Non-verifiable fields
        for f in fields:
            fn = f.get("field_name", "") if isinstance(f, dict) else getattr(f, "field_name", "")
            ck = f.get("canonical_key") if isinstance(f, dict) else getattr(f, "canonical_key", None)
            if ck not in canonical_map:
                report.field_verifications.append(FieldVerification(
                    field_name=fn, canonical_key=ck,
                    extracted_value=None, reference_value=None,
                    status=VERIFICATION_NOT_VERIFIABLE,
                ))
                report.not_verifiable_count += 1
        report.overall_status = "NOT_FOUND"
        return report

    report.reference_record_id = str(reference_record.get("id", ""))

    # Compare each verifiable field
    for ck, (fn, fv) in canonical_map.items():
        ref_col = _canonical_to_column(ck)
        ref_val = reference_record.get(ref_col)

        if ref_val is None:
            report.field_verifications.append(FieldVerification(
                field_name=fn, canonical_key=ck,
                extracted_value=fv, reference_value=None,
                status=VERIFICATION_NOT_FOUND,
            ))
            report.not_found_count += 1
        elif _normalize_value(str(fv)) == _normalize_value(str(ref_val)):
            report.field_verifications.append(FieldVerification(
                field_name=fn, canonical_key=ck,
                extracted_value=fv, reference_value=str(ref_val),
                status=VERIFICATION_MATCH,
            ))
            report.match_count += 1
        else:
            report.field_verifications.append(FieldVerification(
                field_name=fn, canonical_key=ck,
                extracted_value=fv, reference_value=str(ref_val),
                status=VERIFICATION_MISMATCH,
            ))
            report.mismatch_count += 1

    # Non-canonical fields are NOT_VERIFIABLE
    for f in fields:
        fn = f.get("field_name", "") if isinstance(f, dict) else getattr(f, "field_name", "")
        ck = f.get("canonical_key") if isinstance(f, dict) else getattr(f, "canonical_key", None)
        if ck not in canonical_map:
            report.field_verifications.append(FieldVerification(
                field_name=fn, canonical_key=ck,
                extracted_value=None, reference_value=None,
                status=VERIFICATION_NOT_VERIFIABLE,
            ))
            report.not_verifiable_count += 1

    # Determine overall status
    if report.mismatch_count > 0:
        report.overall_status = "MISMATCH_DETECTED"
    elif report.match_count > 0 and report.not_found_count == 0:
        report.overall_status = "VERIFIED"
    elif report.match_count > 0:
        report.overall_status = "PARTIALLY_VERIFIED"
    else:
        report.overall_status = "NOT_FOUND"

    logger.info(
        "[%s] Verification complete: status=%s, matches=%d, mismatches=%d, not_found=%d",
        document_id, report.overall_status,
        report.match_count, report.mismatch_count, report.not_found_count,
    )
    return report


def _canonical_to_column(canonical_key: str) -> str:
    """Map canonical key names to reference table column names."""
    mapping = {
        "SURVEY_NUMBER": "survey_number",
        "KHASRA_NUMBER": "khasra_number",
        "KHATA_NUMBER": "khata_number",
        "PLOT_NUMBER": "plot_number",
        "OWNER_NAME": "owner_name",
        "FATHER_NAME": "father_name",
        "VILLAGE": "village",
        "TEHSIL": "tehsil",
        "DISTRICT": "district",
        "AREA": "area",
        "LAND_CLASSIFICATION": "land_classification",
        "REGISTRATION_NUMBER": "registration_number",
        "MUTATION_NUMBER": "mutation_number",
    }
    return mapping.get(canonical_key, canonical_key.lower())


def _lookup_reference_record(
    canonical_map: dict[str, tuple[str, str | None]],
    db_session: Any = None,
) -> dict | None:
    """Look up a reference record using survey/khasra/khata/plot/registration identifiers."""
    from app.models.land_record_reference import LandRecordReference

    if db_session is None:
        from app.db.session import SessionLocal
        db_session = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        query = db_session.query(LandRecordReference)

        # Try matching on available identifier fields
        matched = False
        for ck in _MATCH_KEYS:
            if ck in canonical_map:
                fn, fv = canonical_map[ck]
                if fv:
                    col_name = _canonical_to_column(ck)
                    col = getattr(LandRecordReference, col_name, None)
                    if col is not None:
                        query = query.filter(col == fv.strip())
                        matched = True

        if not matched:
            return None

        record = query.first()
        if record is None:
            return None

        # Convert to dict
        return {
            "id": str(record.id),
            "survey_number": record.survey_number,
            "khasra_number": record.khasra_number,
            "khata_number": record.khata_number,
            "plot_number": record.plot_number,
            "owner_name": record.owner_name,
            "father_name": record.father_name,
            "village": record.village,
            "tehsil": record.tehsil,
            "district": record.district,
            "area": record.area,
            "land_classification": record.land_classification,
            "registration_number": record.registration_number,
            "mutation_number": record.mutation_number,
        }
    except Exception as exc:
        logger.warning("Reference lookup failed: %s", exc)
        return None
    finally:
        if should_close:
            db_session.close()
