"""Unit and Integration Tests for Intelligent Language Identification and OCR Model Selection."""

import io
import pytest
from app.services.intelligent_ocr_router import (
    DetectedLanguage,
    IntelligentOCRResult,
    SelectedOcrModel,
    analyze_script_distribution,
    count_unicode_scripts,
    detect_handwriting_candidate_blocks,
    identify_language_and_scripts,
    process_document_intelligently,
    select_ocr_models,
)


def test_count_unicode_scripts():
    """Verify accurate Unicode block character counting across Indic scripts."""
    # Tamil text
    tamil_sample = "நில ஆவண விவரப் பதிவு 145/2"
    counts = count_unicode_scripts(tamil_sample)
    assert counts["Tamil"] > 10
    assert counts["Devanagari"] == 0
    assert counts["Digit"] >= 3

    # Devanagari text
    hindi_sample = "भूलेख खतौनी खाता संख्या 102"
    counts = count_unicode_scripts(hindi_sample)
    assert counts["Devanagari"] > 10
    assert counts["Tamil"] == 0

    # Telugu text
    telugu_sample = "భూమి రికార్డు పత్రం"
    counts = count_unicode_scripts(telugu_sample)
    assert counts["Telugu"] > 5

    # Kannada text
    kannada_sample = "ಭೂ ದಾಖಲೆಗಳು 2026"
    counts = count_unicode_scripts(kannada_sample)
    assert counts["Kannada"] > 5


def test_analyze_script_distribution_tamil():
    """Verify single-script Tamil detection."""
    text = "நில ஆவண விவரப் பதிவு மாதிரி பதிவு மாவட்டம் மதுரை வட்டம் மதுரை வடக்கு"
    languages = analyze_script_distribution(text)
    assert len(languages) >= 1
    assert languages[0].code == "ta"
    assert languages[0].name == "Tamil"
    assert languages[0].script == "Tamil"
    assert languages[0].is_primary is True
    assert languages[0].confidence > 0.85


def test_analyze_script_distribution_marathi_disambiguation():
    """Verify Marathi detection via domain keywords over Devanagari."""
    text = "महाराष्ट्र शासन गाव नमुना सात बारा जिल्हा पुणे तालुका हवेली खातेदार"
    languages = analyze_script_distribution(text)
    assert languages[0].code == "mr"
    assert languages[0].name == "Marathi"
    assert languages[0].script == "Devanagari"


def test_analyze_script_distribution_mixed_language():
    """Verify detection of mixed language content (Tamil + English alphanumeric)."""
    text = (
        "நில ஆவண விவரப் பதிவு Land Record Registration Department\n"
        "District: Madurai, Survey Number: 145/2, Patta: 78\n"
        "மாவட்டம் மதுரை வட்டம் மதுரை வடக்கு"
    )
    languages = analyze_script_distribution(text)
    assert len(languages) >= 2
    codes = [l.code for l in languages]
    assert "ta" in codes
    assert "en" in codes


def test_select_ocr_models_tamil():
    """Verify model routing for Tamil printed text."""
    langs = [DetectedLanguage(code="ta", name="Tamil", script="Tamil", confidence=0.98, is_primary=True, char_share=0.95)]
    models = select_ocr_models(langs, is_mixed_language=False, has_handwriting=False)

    assert len(models) == 1
    assert models[0].engine == "paddle_ta"
    assert models[0].text_type == "printed"
    assert "Tamil" in models[0].description


def test_select_ocr_models_with_handwriting():
    """Verify TrOCR model selection when handwriting is detected."""
    langs = [DetectedLanguage(code="hi", name="Hindi", script="Devanagari", confidence=0.95, is_primary=True, char_share=0.90)]
    models = select_ocr_models(langs, is_mixed_language=False, has_handwriting=True)

    engines = [m.engine for m in models]
    assert "paddle_hi" in engines
    assert "trocr" in engines

    trocr_model = next(m for m in models if m.engine == "trocr")
    assert trocr_model.text_type == "handwritten"
    assert "microsoft/trocr-base-handwritten" in trocr_model.model_name


def test_select_ocr_models_mixed_multilingual():
    """Verify multi-model selection for mixed-language content."""
    langs = [
        DetectedLanguage(code="te", name="Telugu", script="Telugu", confidence=0.90, is_primary=True, char_share=0.80),
        DetectedLanguage(code="en", name="English", script="Latin", confidence=0.85, is_primary=False, char_share=0.20),
    ]
    models = select_ocr_models(langs, is_mixed_language=True, has_handwriting=False)

    engines = [m.engine for m in models]
    assert "paddle_te" in engines
    assert "paddle_en" in engines


def test_detect_handwriting_candidate_blocks():
    """Verify low-confidence blocks are flagged as handwriting candidates."""
    mock_pages = [
        {
            "page": 1,
            "blocks": [
                {"text": "Printed Header", "confidence": 0.98, "ocr_engine": "paddle_hi", "bbox": [10, 10, 200, 30]},
                {"text": "Handwritten Sig", "confidence": 0.42, "ocr_engine": "paddle_hi", "bbox": [10, 50, 150, 80]},
            ]
        }
    ]
    candidates = detect_handwriting_candidate_blocks(mock_pages, confidence_threshold=0.60)
    assert len(candidates) == 1
    assert candidates[0]["text"] == "Handwritten Sig"
    assert candidates[0]["confidence"] == 0.42


def test_intelligent_ocr_result_structure():
    """Verify IntelligentOCRResult to_dict returns the expected user-requested structure."""
    result = IntelligentOCRResult(
        detected_languages=[
            DetectedLanguage(code="ta", name="Tamil", script="Tamil", confidence=0.98, is_primary=True, char_share=0.88, char_count=88),
            DetectedLanguage(code="en", name="English", script="Latin", confidence=0.85, is_primary=False, char_share=0.12, char_count=12),
        ],
        is_mixed_language=True,
        text_type_breakdown={"printed_blocks": 15, "handwritten_blocks": 2, "dominant_type": "printed"},
        selected_ocr_models=[
            SelectedOcrModel(engine="paddle_ta", model_name="PaddleOCR-TA", text_type="printed", language="ta", description="Tamil OCR"),
            SelectedOcrModel(engine="trocr", model_name="microsoft/trocr-base-handwritten", text_type="handwritten", language="ta", description="TrOCR"),
        ],
        overall_confidence=0.94,
        page_count=1,
        extracted_text="நில ஆவண விவரப் பதிவு\nSurvey No 145/2",
        pages=[
            {
                "page": 1,
                "blocks": [
                    {"text": "நில ஆவண விவரப் பதிவு", "confidence": 0.98, "language": "ta", "text_type": "printed", "ocr_model": "paddle_ta"}
                ]
            }
        ]
    )

    data = result.to_dict()
    assert "detected_languages" in data
    assert "primary_language" in data
    assert data["primary_language"]["code"] == "ta"
    assert data["is_mixed_language"] is True
    assert "selected_ocr_models" in data
    assert len(data["selected_ocr_models"]) == 2
    assert data["confidence_score"] == 0.94
    assert data["extracted_text"].startswith("நில")
    assert len(data["pages"]) == 1
