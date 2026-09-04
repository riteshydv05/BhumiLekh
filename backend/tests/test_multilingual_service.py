"""Unit tests for Multilingual Normalization, Transliteration, and Identifier Preservation."""
from __future__ import annotations

import pytest
from app.services.multilingual_service import (
    normalize_digits,
    transliterate_text,
    process_text_multilingual,
    enrich_entity,
    IDENTIFIER_ENTITY_TYPES,
)
from app.services.nlp_service import LandRecordEntity, extract_entities


class TestDigitNormalization:
    """Tests for Indic digit normalization."""

    def test_devanagari_digits(self):
        assert normalize_digits("खसरा १२३/४५") == "खसरा 123/45"
        assert normalize_digits("०१२३४५६७८९") == "0123456789"

    def test_gujarati_digits(self):
        assert normalize_digits("૧૨૩૪૫૬૭૮૯૦") == "1234567890"

    def test_bengali_digits(self):
        assert normalize_digits("১২৩৪৫৬৭৮৯০") == "1234567890"

    def test_empty_and_ascii(self):
        assert normalize_digits("") == ""
        assert normalize_digits("Survey 123") == "Survey 123"


class TestTransliteration:
    """Tests for Indic text transliteration."""

    def test_devanagari_transliteration(self):
        result = transliterate_text("खसरा संख्या १२३")
        assert "123" in result
        assert "khas" in result.lower()

    def test_owner_name_transliteration(self):
        result = transliterate_text("संतोष कुमार पाटील")
        assert any(p in result.lower() for p in ["sant", "santo", "samt", "samto"])

    def test_ascii_passthrough(self):
        assert transliterate_text("Survey No 245") == "Survey No 245"

    def test_graceful_fallback_empty(self):
        assert transliterate_text("") == ""


class TestIdentifierPreservation:
    """Tests to verify legal names and identifiers are NEVER blindly translated."""

    def test_khasra_number_identifier_preservation(self):
        original = "खसरा संख्या १२३"
        res = process_text_multilingual(original, entity_type="KHASRA_NUMBER", language="hi")

        assert res["original_text"] == original
        assert "123" in res["transliteration"]
        assert res["translation"] is None  # Must NOT be translated into English words!

    def test_owner_name_identifier_preservation(self):
        original = "संतोष कुमार पाटील"
        res = process_text_multilingual(original, entity_type="OWNER_NAME", language="hi")

        assert res["original_text"] == original
        assert res["translation"] is None  # Legal names must NEVER be replaced by translated text!
        assert any(p in res["transliteration"].lower() for p in ["sant", "santo", "samt", "samto"])

    def test_survey_number_identifier_preservation(self):
        original = "सर्वे नं. २४५/अ"
        res = process_text_multilingual(original, entity_type="SURVEY_NUMBER", language="mr")

        assert res["original_text"] == original
        assert "245" in res["transliteration"]
        assert res["translation"] is None

    def test_registration_number_identifier_preservation(self):
        original = "रजिस्ट्रेशन नं. १२३४५"
        res = process_text_multilingual(original, entity_type="REGISTRATION_NUMBER", language="hi")

        assert res["original_text"] == original
        assert "12345" in res["transliteration"]
        assert res["translation"] is None


class TestSemanticTranslation:
    """Tests for non-identifier fields receiving semantic translation assistance."""

    def test_land_classification_translation(self):
        original = "कृषि भूमि"
        res = process_text_multilingual(original, entity_type="LAND_CLASSIFICATION", language="hi")

        assert res["original_text"] == original
        assert res["translation"] == "Agricultural"
        assert res["normalized_text"] == "Agricultural"

    def test_area_unit_translation(self):
        original = "१.५ हेक्टर"
        res = process_text_multilingual(original, entity_type="AREA", language="mr")

        assert res["original_text"] == original
        assert res["translation"] == "Hectares"


class TestEntityEnrichment:
    """Tests for LandRecordEntity enrichment."""

    def test_enrich_entity_preserves_original(self):
        entity = LandRecordEntity(
            entity_type="KHASRA_NUMBER",
            extracted_value="१२३",
            source_text="खसरा संख्या १२३",
            language="hi",
        )
        enriched = enrich_entity(entity)

        assert enriched.original_text == "खसरा संख्या १२३"
        assert "123" in enriched.transliteration
        assert enriched.translation is None

        # Verify to_dict includes all 4 fields
        d = enriched.to_dict()
        assert d["original_text"] == "खसरा संख्या १२३"
        assert "normalized_text" in d
        assert "transliteration" in d
        assert "translation" in d

    def test_nlp_service_integration(self):
        ocr = {
            "page_count": 1,
            "full_text": "सर्वे नं.: १२३/A\nगाव: वाघोली",
            "avg_confidence": 0.9,
            "method": "paddle",
            "pages": [
                {
                    "page": 1,
                    "width": 600,
                    "height": 400,
                    "blocks": [
                        {"text": "सर्वे नं.: १२३/A", "bbox": [10, 10, 100, 20]},
                        {"text": "गाव: वाघोली", "bbox": [10, 30, 100, 40]},
                    ],
                }
            ],
        }

        result = extract_entities(ocr)
        assert len(result.entities) >= 1
        for e in result.entities:
            assert e.original_text != ""
            assert isinstance(e.transliteration, str)
            d = e.to_dict()
            assert "original_text" in d
            assert "transliteration" in d
            assert "translation" in d
