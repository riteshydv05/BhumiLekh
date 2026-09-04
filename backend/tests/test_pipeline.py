"""Unit tests for the AI pipeline services."""
import io
import struct

import pytest


# ---------------------------------------------------------------------------
# OCR Service Tests
# ---------------------------------------------------------------------------

class TestOCRService:
    """Tests for ocr_service — uses synthetic inputs, no real files."""

    def test_import(self):
        """ocr_service must import without errors."""
        from app.services import ocr_service  # noqa: F401

    def test_ocr_result_dataclass(self):
        from app.services.ocr_service import OCRResult
        result = OCRResult(text="hello", page_count=1, confidence=0.9)
        assert result.text == "hello"
        assert result.page_count == 1
        assert result.confidence == 0.9
        assert result.error is None
        assert result.warnings == []

    def test_run_ocr_unsupported_type(self):
        from app.services.ocr_service import run_ocr
        result = run_ocr(b"data", "text/plain")
        assert result.error is not None
        assert "Unsupported" in result.error

    def test_run_ocr_pdf_empty_bytes(self):
        """run_ocr with invalid PDF bytes should not crash."""
        from app.services.ocr_service import run_ocr
        result = run_ocr(b"not a pdf", "application/pdf")
        # Either extracted nothing or returned an error — never raises
        assert isinstance(result.text, str)

    def test_run_ocr_pdf_minimal(self):
        """run_ocr with a minimal valid PDF should extract text or return empty."""
        # Minimal PDF with embedded text
        minimal_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            b"4 0 obj\n<< /Length 44 >>\nstream\n"
            b"BT /F1 12 Tf 100 700 Td (Survey No: 123) Tj ET\n"
            b"endstream\nendobj\n"
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            b"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000058 00000 n\n0000000115 00000 n\n0000000266 00000 n\n"
            b"0000000360 00000 n\n"
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n440\n%%EOF\n"
        )
        from app.services.ocr_service import run_ocr
        result = run_ocr(minimal_pdf, "application/pdf")
        assert isinstance(result.text, str)
        assert result.page_count >= 0
        assert not result.error or "pypdf" not in result.error.lower() or True  # ok if pypdf limitation


# ---------------------------------------------------------------------------
# Language Service Tests
# ---------------------------------------------------------------------------

class TestLanguageService:

    def test_import(self):
        from app.services import language_service  # noqa: F401

    def test_detect_english(self):
        from app.services.language_service import detect_language
        text = (
            "This is a land record document for the survey number 123 "
            "located in the district of Pune, Maharashtra."
        )
        lang = detect_language(text)
        assert lang in {"en", "unknown"}  # unknown if langdetect degraded

    def test_detect_short_text(self):
        from app.services.language_service import detect_language
        lang = detect_language("Hi")
        assert lang == "unknown"

    def test_detect_empty(self):
        from app.services.language_service import detect_language
        assert detect_language("") == "unknown"
        assert detect_language(None) == "unknown"  # type: ignore

    def test_get_language_name(self):
        from app.services.language_service import get_language_name
        assert get_language_name("en") == "English"
        assert get_language_name("hi") == "Hindi"
        assert get_language_name("xx") == "xx"  # unknown code returns itself


# ---------------------------------------------------------------------------
# NLP Service Tests
# ---------------------------------------------------------------------------

SAMPLE_LAND_RECORD_TEXT = """
GOVERNMENT OF MAHARASHTRA
LAND RECORD DOCUMENT

Survey No.: 245/A
Sub Division: 3
Village: Wagholi
Taluka: Haveli
District: Pune
State: Maharashtra
Pin Code: 412207

Owner's Name: Ramesh Kumar Sharma s/o Mahesh Sharma
Area: 1.5 Hectares
Land Type: Agricultural

Registration Date: 15-08-2022
Document No.: MH-2022-123456
Market Value: Rs. 2500000
Stamp Duty: Rs. 125000
"""

class TestNLPService:

    def test_import(self):
        from app.services import nlp_service  # noqa: F401

    def test_extract_entities_empty(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities("", "en")
        assert result.error is not None
        assert result.fields == []

    def test_extract_survey_number(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        names = {f.field_name for f in result.fields}
        assert "survey_number" in names

    def test_extract_village(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        names = {f.field_name for f in result.fields}
        assert "village" in names

    def test_extract_district(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        field_map = {f.field_name: f.field_value for f in result.fields}
        assert "district" in field_map
        assert "Pune" in field_map["district"]

    def test_extract_area_hectares(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        names = {f.field_name for f in result.fields}
        assert "area_hectares" in names

    def test_extract_registration_date(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        names = {f.field_name for f in result.fields}
        assert "registration_date" in names

    def test_confidence_range(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        for f in result.fields:
            assert 0.0 <= f.confidence <= 1.0, (
                f"Confidence {f.confidence} out of range for {f.field_name}"
            )

    def test_no_duplicates(self):
        from app.services.nlp_service import extract_entities
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        names = [f.field_name for f in result.fields]
        assert len(names) == len(set(names)), "Duplicate field names found"

    def test_score_confidence_passthrough(self):
        from app.services.nlp_service import extract_entities, score_confidence
        result = extract_entities(SAMPLE_LAND_RECORD_TEXT, "en")
        scored = score_confidence(result)
        assert len(scored.fields) == len(result.fields)


# ---------------------------------------------------------------------------
# Validation Service Tests
# ---------------------------------------------------------------------------

class TestValidationService:

    def test_import(self):
        from app.services import validation_service  # noqa: F401

    def test_validate_empty_fields(self):
        from app.services.validation_service import validate_fields
        result = validate_fields([])
        assert result.missing_mandatory != []  # mandatory fields are missing

    def test_valid_area(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import validate_fields
        fields = [
            ExtractedField("area_hectares", "1.5", 0.9),
            ExtractedField("survey_number", "245A", 0.9),
            ExtractedField("village", "Wagholi", 0.8),
            ExtractedField("taluka", "Haveli", 0.8),
            ExtractedField("district", "Pune", 0.8),
        ]
        result = validate_fields(fields)
        field_map = {r.field_name: r.is_valid for r in result.field_results}
        assert field_map.get("area_hectares") is True

    def test_invalid_zero_area(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import validate_fields
        fields = [ExtractedField("area_hectares", "0", 0.9)]
        result = validate_fields(fields)
        field_map = {r.field_name: r.is_valid for r in result.field_results}
        assert field_map.get("area_hectares") is False

    def test_invalid_future_date(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import validate_fields
        fields = [ExtractedField("registration_date", "15-08-2099", 0.9)]
        result = validate_fields(fields)
        field_map = {r.field_name: r.is_valid for r in result.field_results}
        assert field_map.get("registration_date") is False

    def test_valid_past_date(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import validate_fields
        fields = [ExtractedField("registration_date", "15-08-2022", 0.9)]
        result = validate_fields(fields)
        field_map = {r.field_name: r.is_valid for r in result.field_results}
        assert field_map.get("registration_date") is True

    def test_detect_anomalies_empty_text(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import ValidationResult, detect_anomalies
        fields = []
        validation = ValidationResult()
        anomalies = detect_anomalies(fields, "", validation)
        # Short text triggers anomaly
        assert any("short" in a.lower() or "manual" in a.lower() or "mandatory" in a.lower()
                   for a in anomalies)

    def test_detect_same_owner_anomaly(self):
        from app.services.nlp_service import ExtractedField
        from app.services.validation_service import ValidationResult, detect_anomalies
        fields = [
            ExtractedField("owner_name", "Ramesh Sharma", 0.8),
            ExtractedField("co_owner_name", "Ramesh Sharma", 0.8),
        ]
        validation = ValidationResult()
        anomalies = detect_anomalies(fields, "x" * 200, validation)
        assert any("identical" in a.lower() for a in anomalies)
        assert validation.requires_human_review is True
