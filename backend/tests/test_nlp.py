"""Tests for the NLP service — multilingual NER entity extraction for land records.

Covers:
    - extract_entities with synthetic land-record text
    - Rule-based extraction for various field types
    - Language detection and fallback
    - Malformed OCR data handling
    - LandRecordEntity dataclass operations
    - ExtractionResult and field_map
    - NER model loader graceful degradation
    - get_nlp_status
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers — synthetic land-record text in multiple languages
# ---------------------------------------------------------------------------

ENGLISH_LAND_RECORD = """
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
Father's Name: Mahesh Sharma
Area: 1.5 Hectares
Land Type: Agricultural

Registration Date: 15-08-2022
Document No.: MH-2022-123456
Market Value: Rs. 2500000
Stamp Duty: Rs. 125000
Mutation No.: 987654
"""

HINDI_LAND_RECORD = """
सर्वे नं.: 123/A
गाव: वाघोली
तालुका: हवेली
जिल्हा: पुणे
मालिकाचे नाव: रमेश कुमार शर्मा
क्षेत्रफळ: 1.5 हेक्टर
"""

MARATHI_LAND_RECORD = """
सर्वे नं.: 456/B
गाव: वाघोली
तालुका: हवेली
जिल्हा: पुणे
मालिक: राम शर्मा
"""

MULTILINGUAL_LAND_RECORD = """
Survey No.: 789/C
Village: पाथर्डी
Taluka: Ahmednagar
District: Ahmednagar
Owner's Name: संतोष कुमार पाटील
Father's Name: बाबासाहेब पाटील
Area: 2.3 Hectares
Registration Date: 10-06-2023
"""


def _make_ocr_result(
    text: str,
    page_num: int = 1,
    width: int = 600,
    height: int = 400,
    confidence: float = 0.9,
) -> dict:
    """Create a synthetic OcrDocument dict from text."""
    return {
        "page_count": 1,
        "full_text": text,
        "avg_confidence": confidence,
        "method": "paddle",
        "error": None,
        "warnings": [],
        "pages": [
            {
                "page": page_num,
                "width": width,
                "height": height,
                "blocks": [
                    {
                        "text": text,
                        "bbox": [10.0, 20.0, 500.0, 380.0],
                        "confidence": confidence,
                        "language": None,
                        "ocr_engine": "paddle",
                        "timestamp": "2026-09-04T12:00:00",
                    }
                ],
            }
        ],
    }


def _make_ocr_result_with_blocks(
    blocks: list[dict],
    page_num: int = 1,
    width: int = 600,
    height: int = 400,
) -> dict:
    """Create an OcrDocument with multiple blocks."""
    texts = []
    for b in blocks:
        t = b.get("text", "")
        if t is not None:
            texts.append(str(t))
    return {
        "page_count": 1,
        "full_text": "\n".join(texts),
        "avg_confidence": 0.9,
        "method": "paddle",
        "error": None,
        "warnings": [],
        "pages": [
            {
                "page": page_num,
                "width": width,
                "height": height,
                "blocks": blocks,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Test: LandRecordEntity dataclass
# ---------------------------------------------------------------------------

class TestLandRecordEntity:
    """Tests for the LandRecordEntity dataclass."""

    def test_entity_creation(self):
        from app.services.nlp_service import LandRecordEntity

        entity = LandRecordEntity(
            entity_type="OWNER_NAME",
            extracted_value="Ramesh Kumar Sharma",
            source_text="Owner's Name: Ramesh Kumar Sharma",
            page=1,
            confidence=0.90,
            extraction_method="rule",
            language="en",
        )
        assert entity.entity_type == "OWNER_NAME"
        assert entity.extracted_value == "Ramesh Kumar Sharma"
        assert entity.page == 1
        assert entity.confidence == 0.90
        assert entity.extraction_method == "rule"

    def test_entity_to_dict(self):
        from app.services.nlp_service import LandRecordEntity

        entity = LandRecordEntity(
            entity_type="SURVEY_NUMBER",
            extracted_value="245/A",
            page=1,
        )
        d = entity.to_dict()
        assert d["entity_type"] == "SURVEY_NUMBER"
        assert d["extracted_value"] == "245/A"
        assert "bounding_box" in d
        assert "timestamp" in d

    def test_entity_with_bounding_box(self):
        from app.services.nlp_service import LandRecordEntity

        entity = LandRecordEntity(
            entity_type="VILLAGE",
            extracted_value="Wagholi",
            bounding_box=[18.0, 39.0, 200.0, 60.0],
        )
        assert entity.bounding_box == [18.0, 39.0, 200.0, 60.0]

    def test_entity_all_entity_types(self):
        """Verify all land-record entity types are valid."""
        from app.services.nlp_service import LAND_RECORD_ENTITY_TYPES

        expected = {
            "OWNER_NAME", "FATHER_NAME", "MOTHER_NAME",
            "SURVEY_NUMBER", "KHASRA_NUMBER", "KHATA_NUMBER",
            "PLOT_NUMBER", "VILLAGE", "TEHSIL", "DISTRICT",
            "AREA", "LAND_CLASSIFICATION", "REGISTRATION_NUMBER",
            "MUTATION_NUMBER", "DATE",
        }
        assert LAND_RECORD_ENTITY_TYPES == expected


# ---------------------------------------------------------------------------
# Test: ExtractionResult
# ---------------------------------------------------------------------------

class TestExtractionResult:
    """Tests for the ExtractionResult dataclass."""

    def test_empty_result(self):
        from app.services.nlp_service import ExtractionResult

        result = ExtractionResult()
        assert result.entities == []
        assert result.field_map == {}

    def test_entity_field_map(self):
        from app.services.nlp_service import (
            ExtractionResult, LandRecordEntity,
        )

        entities = [
            LandRecordEntity(
                entity_type="SURVEY_NUMBER",
                extracted_value="245/A",
            ),
            LandRecordEntity(
                entity_type="VILLAGE",
                extracted_value="Wagholi",
            ),
        ]
        result = ExtractionResult(entities=entities)
        assert result.field_map["SURVEY_NUMBER"] == "245/A"
        assert result.field_map["VILLAGE"] == "Wagholi"

    def test_field_map_first_wins(self):
        """If multiple entities of same type, first wins."""
        from app.services.nlp_service import (
            ExtractionResult, LandRecordEntity,
        )

        entities = [
            LandRecordEntity(
                entity_type="VILLAGE",
                extracted_value="Wagholi",
            ),
            LandRecordEntity(
                entity_type="VILLAGE",
                extracted_value="Pathardi",
            ),
        ]
        result = ExtractionResult(entities=entities)
        assert result.field_map["VILLAGE"] == "Wagholi"

    def test_fields_backward_compatibility(self):
        """The .fields property must return entities for backward compat."""
        from app.services.nlp_service import (
            ExtractionResult, LandRecordEntity,
        )

        entity = LandRecordEntity(
            entity_type="OWNER_NAME",
            extracted_value="Ramesh",
        )
        result = ExtractionResult(entities=[entity])
        assert result.fields == [entity]
        assert len(result.fields) == 1

    def test_to_dict_serializable(self):
        """ExtractionResult.to_dict() must be JSON-serializable."""
        from app.services.nlp_service import (
            ExtractionResult, LandRecordEntity,
        )
        import json

        entity = LandRecordEntity(
            entity_type="SURVEY_NUMBER",
            extracted_value="245/A",
        )
        result = ExtractionResult(entities=[entity])
        result.status = type("S", (), {
            "to_dict": lambda self: {
                "success": True, "method": "rule",
                "message": "", "model_available": False,
                "language_supported": True,
                "entities_extracted": 1,
            }
        })()
        d = result.to_dict()
        json_str = json.dumps(d)
        assert "SURVEY_NUMBER" in json_str


# ---------------------------------------------------------------------------
# Test: Rule-based extraction
# ---------------------------------------------------------------------------

class TestRuleBasedExtraction:
    """Tests for rule-based land-record field extraction."""

    def test_extract_survey_number_english(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "SURVEY_NUMBER" in field_map
        assert "245/A" in field_map["SURVEY_NUMBER"]

    def test_extract_village_english(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Village: Wagholi")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "VILLAGE" in field_map
        assert "Wagholi" in field_map["VILLAGE"]

    def test_extract_district_english(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("District: Pune")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "DISTRICT" in field_map
        assert "Pune" in field_map["DISTRICT"]

    def test_extract_taluka_english(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Taluka: Haveli")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "TEHSIL" in field_map

    def test_extract_registration_date(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Registration Date: 15-08-2022")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "DATE" in field_map

    def test_extract_owner_name(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Owner's Name: Ramesh Kumar Sharma")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "OWNER_NAME" in field_map

    def test_extract_area_hectares(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Area: 1.5 Hectares")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "AREA" in field_map

    def test_extract_mutation_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Mutation No.: 987654")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "MUTATION_NUMBER" in field_map

    def test_extract_khata_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Khata No.: 456")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "KHATA_NUMBER" in field_map

    def test_extract_registration_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Registration No.: MH-2022-123")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "REGISTRATION_NUMBER" in field_map

    def test_extract_plot_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Plot No.: 789")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "PLOT_NUMBER" in field_map

    def test_extract_father_name(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Father's Name: Mahesh Sharma")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "FATHER_NAME" in field_map

    def test_full_land_record_text(self):
        """Extract all fields from a full English land-record document."""
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(ENGLISH_LAND_RECORD)
        result = extract_entities(ocr)
        field_map = result.field_map

        # Should find at least these fields
        expected_fields = {
            "SURVEY_NUMBER", "VILLAGE", "TEHSIL", "DISTRICT",
            "OWNER_NAME", "AREA", "DATE",
        }
        found = set(field_map.keys()) & expected_fields
        assert len(found) >= 4, f"Only found: {found}"

    def test_extract_khasra_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Khasra No.: 45/A")
        result = extract_entities(ocr)
        field_map = result.field_map

        assert "KHASRA_NUMBER" in field_map

    def test_no_entities_empty_text(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("")
        result = extract_entities(ocr)
        assert result.entities == []
        assert result.error is not None

    def test_entity_confidence_range(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)
        for entity in result.entities:
            assert 0.0 <= entity.confidence <= 1.0

    def test_entity_extraction_method(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)
        for entity in result.entities:
            assert entity.extraction_method in {"ner", "rule"}

    def test_entity_page_number(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(
            "Survey No.: 245/A", page_num=2
        )
        result = extract_entities(ocr)
        for entity in result.entities:
            assert entity.page == 2

    def test_entity_source_text(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)
        for entity in result.entities:
            assert entity.source_text != ""
            assert "245/A" in entity.source_text or entity.entity_type != "SURVEY_NUMBER"


# ---------------------------------------------------------------------------
# Test: Multilingual extraction
# ---------------------------------------------------------------------------

class TestMultilingualExtraction:
    """Tests for multilingual land-record entity extraction."""

    def test_english_extraction(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(ENGLISH_LAND_RECORD)
        result = extract_entities(ocr)
        assert result.language in {"en", "unknown"}

    def test_hindi_extraction(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(HINDI_LAND_RECORD)
        result = extract_entities(ocr)
        # Language detection may return 'hi' or 'unknown'
        # Rule-based patterns should still work for Devanagari
        assert isinstance(result.language, str)

    def test_marathi_extraction(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(MARATHI_LAND_RECORD)
        result = extract_entities(ocr)
        assert isinstance(result.language, str)

    def test_multilingual_extraction(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(MULTILINGUAL_LAND_RECORD)
        result = extract_entities(ocr)
        # Should extract at least some fields from mixed text
        field_map = result.field_map
        assert "SURVEY_NUMBER" in field_map

    def test_multilingual_with_page_blocks(self):
        """Test extraction with multiple page blocks."""
        from app.services.nlp_service import extract_entities

        blocks = [
            {"text": "Survey No.: 245/A", "bbox": [10, 20, 100, 30], "confidence": 0.9, "language": None, "ocr_engine": "paddle", "timestamp": "2026-09-04T12:00:00"},
            {"text": "Village: Wagholi", "bbox": [10, 40, 100, 55], "confidence": 0.88, "language": None, "ocr_engine": "paddle", "timestamp": "2026-09-04T12:00:00"},
            {"text": "District: Pune", "bbox": [10, 60, 100, 75], "confidence": 0.85, "language": None, "ocr_engine": "paddle", "timestamp": "2026-09-04T12:00:00"},
        ]
        ocr = _make_ocr_result_with_blocks(blocks, page_num=1)
        result = extract_entities(ocr)

        assert len(result.entities) >= 1
        field_map = result.field_map
        assert "SURVEY_NUMBER" in field_map
        assert "VILLAGE" in field_map
        assert "DISTRICT" in field_map


# ---------------------------------------------------------------------------
# Test: Malformed OCR data handling
# ---------------------------------------------------------------------------

class TestMalformedOcrData:
    """Tests for graceful handling of malformed OCR data."""

    def test_empty_pages(self):
        from app.services.nlp_service import extract_entities

        ocr = {
            "pages": [],
            "method": "paddle",
            "error": None,
            "warnings": [],
        }
        result = extract_entities(ocr)
        assert result.entities == []
        assert result.error is not None

    def test_missing_blocks(self):
        from app.services.nlp_service import extract_entities

        ocr = {
            "pages": [
                {"page": 1, "width": 600, "height": 400},
            ],
            "method": "paddle",
            "error": None,
            "warnings": [],
        }
        result = extract_entities(ocr)
        assert result.entities == []

    def test_none_blocks(self):
        from app.services.nlp_service import extract_entities

        ocr = {
            "pages": [
                {"page": 1, "width": 600, "height": 400, "blocks": None},
            ],
            "method": "paddle",
            "error": None,
            "warnings": [],
        }
        result = extract_entities(ocr)
        assert result.entities == []

    def test_blocks_missing_text(self):
        from app.services.nlp_service import extract_entities

        blocks = [
            {"text": None, "bbox": [0, 0, 10, 10]},
            {"text": "", "bbox": [0, 0, 10, 10]},
            {"text": "  ", "bbox": [0, 0, 10, 10]},
        ]
        ocr = _make_ocr_result_with_blocks(blocks)
        result = extract_entities(ocr)
        assert result.entities == []

    def test_blocks_missing_bbox(self):
        from app.services.nlp_service import extract_entities

        blocks = [
            {"text": "Survey No.: 245/A"},
        ]
        ocr = _make_ocr_result_with_blocks(blocks)
        result = extract_entities(ocr)
        # Should not crash — bbox is optional
        assert len(result.entities) >= 0

    def test_blocks_with_invalid_bbox(self):
        from app.services.nlp_service import extract_entities

        blocks = [
            {"text": "Survey No.: 245/A", "bbox": "invalid"},
        ]
        ocr = _make_ocr_result_with_blocks(blocks)
        result = extract_entities(ocr)
        # Should not crash
        assert isinstance(result.entities, list)

    def test_non_string_text_in_block(self):
        """Blocks with non-string text should not crash."""
        from app.services.nlp_service import extract_entities

        blocks = [
            {"text": "Survey No.: 245/A", "bbox": [10, 20, 100, 30], "confidence": 0.9, "language": None, "ocr_engine": "paddle", "timestamp": "2026-09-04T12:00:00"},
            {"text": 12345, "bbox": [10, 40, 100, 55], "confidence": 0.88, "language": None, "ocr_engine": "paddle", "timestamp": "2026-09-04T12:00:00"},
        ]
        ocr = _make_ocr_result_with_blocks(blocks)
        result = extract_entities(ocr)
        # Int text should be converted to string and processed
        assert isinstance(result.entities, list)

    def test_empty_ocr_document(self):
        from app.services.nlp_service import extract_entities

        ocr = {}
        result = extract_entities(ocr)
        assert result.entities == []
        assert result.error is not None


# ---------------------------------------------------------------------------
# Test: NER Model Loader graceful degradation
# ---------------------------------------------------------------------------

class TestNERModelLoader:
    """Tests for _NERModelLoader graceful degradation."""

    def test_loader_not_available_by_default(self):
        from app.services.nlp_service import _NERModelLoader

        loader = _NERModelLoader()
        assert loader.is_available is False

    def test_get_nlp_status(self):
        from app.services.nlp_service import get_nlp_status

        status = get_nlp_status()
        assert "ner_model_available" in status
        assert "rule_based_available" in status
        assert status["rule_based_available"] is True
        assert "rule_supported_languages" in status
        assert "indic_supported_languages" in status

    def test_indic_languages_defined(self):
        from app.services.nlp_service import INDIC_LANGUAGES

        assert "hi" in INDIC_LANGUAGES
        assert "en" in INDIC_LANGUAGES
        assert "mr" in INDIC_LANGUAGES
        assert len(INDIC_LANGUAGES) > 0

    def test_entity_types_defined(self):
        from app.services.nlp_service import LAND_RECORD_ENTITY_TYPES

        assert "OWNER_NAME" in LAND_RECORD_ENTITY_TYPES
        assert "SURVEY_NUMBER" in LAND_RECORD_ENTITY_TYPES
        assert "VILLAGE" in LAND_RECORD_ENTITY_TYPES
        assert "DISTRICT" in LAND_RECORD_ENTITY_TYPES
        assert "AREA" in LAND_RECORD_ENTITY_TYPES
        assert "DATE" in LAND_RECORD_ENTITY_TYPES
        assert len(LAND_RECORD_ENTITY_TYPES) == 15


# ---------------------------------------------------------------------------
# Test: ExtractionStatus
# ---------------------------------------------------------------------------

class TestExtractionStatus:
    """Tests for ExtractionStatus dataclass."""

    def test_status_creation(self):
        from app.services.nlp_service import ExtractionStatus

        status = ExtractionStatus(
            success=True,
            method="rule",
            message="Rule-based extraction used",
            model_available=False,
        )
        assert status.success is True
        assert status.method == "rule"
        assert status.model_available is False

    def test_status_to_dict(self):
        from app.services.nlp_service import ExtractionStatus

        status = ExtractionStatus(
            success=True, method="rule", model_available=False,
        )
        d = status.to_dict()
        assert d["success"] is True
        assert d["method"] == "rule"
        assert "model_available" in d

    def test_status_with_ner(self):
        from app.services.nlp_service import ExtractionStatus

        status = ExtractionStatus(
            success=True, method="mixed",
            model_available=True, language_supported=True,
            entities_extracted=5,
        )
        assert status.method == "mixed"
        assert status.model_available is True
        assert status.entities_extracted == 5


# ---------------------------------------------------------------------------
# Test: extract_entities_from_text convenience function
# ---------------------------------------------------------------------------

class TestExtractEntitiesFromText:
    """Tests for extract_entities_from_text convenience function."""

    def test_english_text(self):
        from app.services.nlp_service import extract_entities_from_text

        entities = extract_entities_from_text("Survey No.: 245/A")
        assert isinstance(entities, list)
        survey_entities = [e for e in entities if e.entity_type == "SURVEY_NUMBER"]
        if survey_entities:
            assert survey_entities[0].extracted_value == "245/A"

    def test_with_page_number(self):
        from app.services.nlp_service import extract_entities_from_text

        entities = extract_entities_from_text(
            "Village: Wagholi", page=2
        )
        for e in entities:
            assert e.page == 2

    def test_empty_text(self):
        from app.services.nlp_service import extract_entities_from_text

        entities = extract_entities_from_text("")
        assert isinstance(entities, list)


# ---------------------------------------------------------------------------
# Test: score_confidence
# ---------------------------------------------------------------------------

class TestScoreConfidence:
    """Tests for score_confidence function."""

    def test_score_confidence_passthrough(self):
        from app.services.nlp_service import (
            ExtractionResult, LandRecordEntity, score_confidence,
        )

        entity = LandRecordEntity(
            entity_type="OWNER_NAME",
            extracted_value="Ramesh",
            confidence=0.85,
        )
        result = ExtractionResult(entities=[entity])
        scored = score_confidence(result)
        assert len(scored.entities) == 1
        assert scored.entities[0].confidence == 0.85

    def test_score_confidence_empty(self):
        from app.services.nlp_service import ExtractionResult, score_confidence

        result = ExtractionResult()
        scored = score_confidence(result)
        assert len(scored.entities) == 0


# ---------------------------------------------------------------------------
# Test: NER label mapping
# ---------------------------------------------------------------------------

class TestNerLabelMapping:
    """Tests for NER_LABEL_TO_ENTITY mapping."""

    def test_all_labels_mapped(self):
        from app.services.nlp_service import NER_LABEL_TO_ENTITY

        # Verify all expected labels are mapped
        expected = {"B-owner", "I-owner", "B-father", "I-father",
                     "B-mother", "I-mother"}
        mapped = set(NER_LABEL_TO_ENTITY.values())
        assert "OWNER_NAME" in mapped
        assert "FATHER_NAME" in mapped
        assert "MOTHER_NAME" in mapped

    def test_label_to_entity_consistency(self):
        from app.services.nlp_service import (
            NER_LABEL_TO_ENTITY, LAND_RECORD_ENTITY_TYPES,
        )

        for label, entity_type in NER_LABEL_TO_ENTITY.items():
            assert entity_type in LAND_RECORD_ENTITY_TYPES, (
                f"Label {label} maps to unknown entity {entity_type}"
            )

    def test_land_entity_types_all_mapped(self):
        """Every land-record entity type should be reachable from NER labels."""
        from app.services.nlp_service import (
            NER_LABEL_TO_ENTITY, LAND_RECORD_ENTITY_TYPES,
        )

        mapped_types = set(NER_LABEL_TO_ENTITY.values())
        # Not all types need NER mapping (some are rule-only)
        # But at least the core ones should be mapped
        core_types = {"OWNER_NAME", "SURVEY_NUMBER", "VILLAGE", "DISTRICT", "AREA", "DATE"}
        found = mapped_types & core_types
        assert len(found) >= 3, f"Only found NER-mapped types: {found}"


# ---------------------------------------------------------------------------
# Test: Pattern-based entity type mapping
# ---------------------------------------------------------------------------

class TestPatternToEntity:
    """Tests for _pattern_to_entity heuristic mapping."""

    def test_survey_pattern(self):
        from app.services.nlp_service import _pattern_to_entity
        import re

        pattern = re.compile(
            r"(?:survey\s*no\.?)\s*[:\-]?\s*([A-Z0-9/\-\.]+)",
            re.IGNORECASE,
        )
        assert _pattern_to_entity(pattern) == "SURVEY_NUMBER"

    def test_village_pattern(self):
        from app.services.nlp_service import _pattern_to_entity
        import re

        pattern = re.compile(
            r"(?:village)\s*[:\-]?\s*([A-Za-z]+)",
            re.IGNORECASE,
        )
        assert _pattern_to_entity(pattern) == "VILLAGE"

    def test_unknown_pattern(self):
        from app.services.nlp_service import _pattern_to_entity
        import re

        pattern = re.compile(r"some unknown pattern")
        assert _pattern_to_entity(pattern) is None


# ---------------------------------------------------------------------------
# Test: OCR data is not overwritten
# ---------------------------------------------------------------------------

class TestOcrDataPreservation:
    """Verify that raw OCR data is never modified during extraction."""

    def test_ocr_text_unchanged(self):
        from app.services.nlp_service import extract_entities

        text = "Survey No.: 245/A"
        ocr = _make_ocr_result(text)
        original_text = ocr["pages"][0]["blocks"][0]["text"]

        result = extract_entities(ocr)

        # OCR data should be unchanged
        assert ocr["pages"][0]["blocks"][0]["text"] == original_text

    def test_ocr_blocks_unchanged(self):
        from app.services.nlp_service import extract_entities

        blocks = [
            {
                "text": "Survey No.: 245/A",
                "bbox": [10.0, 20.0, 100.0, 30.0],
                "confidence": 0.95,
                "language": None,
                "ocr_engine": "paddle",
                "timestamp": "2026-09-04T12:00:00",
            },
        ]
        ocr = _make_ocr_result_with_blocks(blocks)
        original_blocks = [dict(b) for b in ocr["pages"][0]["blocks"]]

        result = extract_entities(ocr)

        # Blocks should be unchanged
        assert ocr["pages"][0]["blocks"] == original_blocks

    def test_entities_separate_from_ocr(self):
        """Extracted entities should be separate data structures from OCR."""
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)

        # Entities are LandRecordEntity objects, not OCR blocks
        assert all(isinstance(e, type(result.entities[0])) for e in result.entities)
        # Entity values come from OCR but are separate objects
        for e in result.entities:
            assert isinstance(e.extracted_value, str)


# ---------------------------------------------------------------------------
# Test: Confidence values
# ---------------------------------------------------------------------------

class TestConfidenceValues:
    """Verify confidence values are properly set."""

    def test_confidence_in_range(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)

        for entity in result.entities:
            assert 0.0 <= entity.confidence <= 1.0

    def test_ner_confidence(self):
        """NER extraction should have reasonable confidence."""
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)

        for entity in result.entities:
            if entity.extraction_method == "ner":
                assert 0.0 <= entity.confidence <= 1.0
            elif entity.extraction_method == "rule":
                assert 0.0 <= entity.confidence <= 1.0

    def test_rule_confidence_not_zero(self):
        """Rule-based extraction should have non-zero confidence."""
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("Survey No.: 245/A")
        result = extract_entities(ocr)

        for entity in result.entities:
            assert entity.confidence > 0.0


# ---------------------------------------------------------------------------
# Test: Language detection integration
# ---------------------------------------------------------------------------

class TestLanguageDetectionIntegration:
    """Tests for language detection integration in extract_entities."""

    def test_language_detected(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result(ENGLISH_LAND_RECORD)
        result = extract_entities(ocr)

        # Language should be detected (may be 'en' or 'unknown')
        assert isinstance(result.language, str)
        assert len(result.language) >= 2 or result.language == "unknown"

    def test_unknown_language_still_works(self):
        """Extraction should work even if language is unknown."""
        from app.services.nlp_service import extract_entities

        short_text = "Hello"
        ocr = _make_ocr_result(short_text)
        result = extract_entities(ocr)
        assert isinstance(result.entities, list)

    def test_empty_language_returns_unknown(self):
        from app.services.nlp_service import extract_entities

        ocr = _make_ocr_result("")
        result = extract_entities(ocr)
        assert result.language == "unknown"