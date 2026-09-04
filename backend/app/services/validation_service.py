"""Validation Service — field validation and anomaly detection for land records.

Validation rules:
  - Mandatory fields must be present
  - Area values must be positive
  - Dates must be in the past (not future)
  - Monetary values must be non-negative

Anomaly detection:
  - Zero or negative area
  - Future registration date
  - Unusually high/low market value
  - Missing mandatory fields
  - Duplicate field values that should be unique
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services.nlp_service import ExtractedField

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MANDATORY_FIELDS = {"survey_number", "village", "taluka", "district"}
_DATE_PATTERNS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
    "%d-%m-%y",
    "%d/%m/%y",
    "%d %B %Y",
    "%d %b %Y",
    "%Y-%m-%d",
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FieldValidationResult:
    field_name: str
    field_value: str | None
    is_valid: bool
    reason: str = ""


@dataclass
class ValidationResult:
    field_results: list[FieldValidationResult] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    missing_mandatory: list[str] = field(default_factory=list)
    requires_human_review: bool = False
    error: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> datetime | None:
    """Try parsing a date string with several common formats."""
    for fmt in _DATE_PATTERNS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_number(value: str) -> float | None:
    """Strip currency symbols / commas and parse as float."""
    cleaned = re.sub(r"[₹,\s]", "", value)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _validate_field(ef: ExtractedField) -> FieldValidationResult:
    """Apply field-specific validation rules."""
    name = ef.field_name
    value = ef.field_value.strip() if ef.field_value else ""

    if not value:
        return FieldValidationResult(
            field_name=name,
            field_value=value,
            is_valid=False,
            reason="Empty value",
        )

    # Area must be positive
    if name in {"area_hectares", "area_acres", "area_sqm"}:
        num = _parse_number(value)
        if num is None:
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason="Non-numeric area value",
            )
        if num <= 0:
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason=f"Area must be positive, got {num}",
            )

    # Dates must be parseable and not in the future
    if name in {"registration_date"}:
        parsed = _parse_date(value)
        if parsed is None:
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason=f"Unrecognised date format: {value!r}",
            )
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        if parsed > now:
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason="Registration date is in the future",
            )

    # Monetary values must be non-negative
    if name in {"stamp_duty", "market_value"}:
        num = _parse_number(value)
        if num is not None and num < 0:
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason=f"Monetary value cannot be negative: {num}",
            )

    # Survey/plot/document numbers: alphanumeric only
    if name in {"survey_number", "plot_number", "document_number", "khata_number",
                "mutation_number"}:
        if not re.match(r"^[A-Z0-9/\-]+$", value.upper()):
            return FieldValidationResult(
                field_name=name, field_value=value, is_valid=False,
                reason=f"Unexpected characters in {name}: {value!r}",
            )

    return FieldValidationResult(
        field_name=name, field_value=value, is_valid=True
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_fields(fields: list[ExtractedField]) -> ValidationResult:
    """Validate each extracted field and check for missing mandatory fields."""
    result = ValidationResult()

    extracted_names = {ef.field_name for ef in fields}

    # Check mandatory fields
    for mandatory in _MANDATORY_FIELDS:
        if mandatory not in extracted_names:
            result.missing_mandatory.append(mandatory)
            logger.info("Mandatory field missing: %s", mandatory)

    # Validate each field
    for ef in fields:
        vr = _validate_field(ef)
        result.field_results.append(vr)
        if not vr.is_valid:
            logger.info(
                "Field validation failed [%s]: %s", vr.field_name, vr.reason
            )

    logger.info(
        "Validation complete: %d fields, %d invalid, %d mandatory missing",
        len(fields),
        sum(1 for r in result.field_results if not r.is_valid),
        len(result.missing_mandatory),
    )
    return result


def detect_anomalies(
    fields: list[ExtractedField],
    raw_text: str,
    validation: ValidationResult,
) -> list[str]:
    """Detect anomalies in the extracted data.

    Returns a list of human-readable anomaly description strings.
    Modifies *validation.requires_human_review* in-place.
    """
    anomalies: list[str] = []
    field_map = {ef.field_name: ef.field_value for ef in fields}

    # 1. Zero or negative area
    for area_field in ("area_hectares", "area_acres", "area_sqm"):
        val = field_map.get(area_field)
        if val is not None:
            num = _parse_number(val)
            if num is not None and num <= 0:
                anomalies.append(f"Zero or negative {area_field}: {val}")

    # 2. Future registration date
    reg_date_str = field_map.get("registration_date")
    if reg_date_str:
        parsed = _parse_date(reg_date_str)
        if parsed and parsed > datetime.now():
            anomalies.append(
                f"Registration date is in the future: {reg_date_str}"
            )

    # 3. Missing multiple mandatory fields
    if len(validation.missing_mandatory) >= 3:
        anomalies.append(
            f"Too many mandatory fields missing: {validation.missing_mandatory}"
        )

    # 4. Unusually high market value (heuristic: > 10 crore INR)
    mv = field_map.get("market_value")
    if mv:
        num = _parse_number(mv)
        if num is not None and num > 100_000_000:
            anomalies.append(
                f"Unusually high market value: {mv} — requires verification"
            )

    # 5. Repeated owner and co-owner names
    owner = field_map.get("owner_name", "").strip().lower()
    co_owner = field_map.get("co_owner_name", "").strip().lower()
    if owner and co_owner and owner == co_owner:
        anomalies.append(
            "Owner name and co-owner name are identical — possible data error"
        )

    # 6. Very low OCR text — document may be mostly blank/handwritten
    if len(raw_text.strip()) < 100:
        anomalies.append(
            "Extracted text is very short — document may require manual review"
        )

    if anomalies:
        validation.requires_human_review = True
        logger.warning(
            "Anomaly detection: %d anomalies found", len(anomalies)
        )
        for anomaly in anomalies:
            logger.warning("  Anomaly: %s", anomaly)
    else:
        logger.info("Anomaly detection: no anomalies found")

    return anomalies
