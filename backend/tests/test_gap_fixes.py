"""Comprehensive Test Suite for BhumiLekh Gap Implementation.

Validates all 6 phases:
1. Dynamic Multi-Engine OCR Routing & Script Detection
2. Indic-Aware Handwritten Text Recognition (HTR)
3. Multilingual NLP Entity Extraction & Land Terminology
4. State-Specific Land Validation Rules (MH, UP, MP, TN, KA, AP/TS, WB)
5. Cadastral Map Vectorization & GIS Integration
6. AI Pipeline Background Workers
"""
import io
import json
import pytest
import numpy as np
from PIL import Image, ImageDraw

from app.services.paddle_ocr_engine import detect_script, _normalize_lang, get_engine_status
from app.services.trocr_service import run_trocr_on_crop, get_trocr_status, HwOcrResult
from app.services.nlp_service import extract_entities

from app.services.multilingual_service import process_text_multilingual, normalize_digits, _DOMAIN_DICTIONARY
from app.services.validation_service import validate_record_with_engine, detect_anomalies

from app.services.gis_service import extract_cadastral_polygons_from_map


# ===========================================================================
# 1. OCR Routing & Script Detection Tests
# ===========================================================================
class TestMultilingualOcrRouting:
    @pytest.mark.parametrize(
        "sample_text, expected_code",
        [
            ("महाराष्ट्र शासन ७/१२", "hi"),
            ("उत्तर प्रदेश खतौनी खाता संख्या", "hi"),
            ("தமிழ்நாடு அரசு பட்டா சிட்டா", "ta"),
            ("తెలంగాణ ప్రభుత్వం అడంగల్", "te"),
            ("ಕರ್ನಾಟಕ ಸರ್ಕಾರ ಭೂಮಿ ಪಹಣಿ", "kn"),
            ("കേരള റവന്യൂ വകുപ്പ് പോക്കുവരവ്", "ml"),
            ("ગુજરાત સરકાર મહેસૂલ ૭/૧૨", "gu"),
            ("পশ্চিমবঙ্গ সরকার বাংলারভূমি খতিয়ান", "bn"),
            ("ਪੰਜਾਬ ਸਰਕਾਰ ਜਮ੍ਹਾਬੰਦੀ", "pa"),
            ("ଓଡ଼ିଶା ସରକାର ଭୂଲେଖ ଜମି ପଟ୍ଟା", "or"),
            ("Government of Karnataka Land Title Deed", "en"),
        ],
    )
    def test_detect_script_multilingual(self, sample_text, expected_code):
        detected = detect_script(sample_text)
        assert detected == expected_code

    def test_normalize_lang_mapping(self):
        assert _normalize_lang("hi") == "hi"
        assert _normalize_lang("mr") == "hi"  # Marathi maps to Devanagari hi model
        assert _normalize_lang("ta") == "ta"
        assert _normalize_lang("te") == "te"
        assert _normalize_lang("kn") == "kn"
        assert _normalize_lang("ml") == "ml"
        assert _normalize_lang("gu") == "gu"
        assert _normalize_lang("bn") == "bn"
        assert _normalize_lang("pa") == "pa"
        assert _normalize_lang("or") == "or"
        assert _normalize_lang("en") == "en"

    def test_engine_status(self):
        status = get_engine_status()
        assert "importable" in status
        assert "initialized" in status
        assert "lang" in status


# ===========================================================================
# 2. Indic-Aware HTR Tests
# ===========================================================================
class TestIndicAwareHTR:
    def test_indic_htr_routing(self):
        # Create a small test image
        img = Image.new("RGB", (120, 40), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "104", fill=(0, 0, 0))

        # Indic HTR should be routed to indic_htr(lang)
        res_hi = run_trocr_on_crop(img, 1, (0, 0, 100, 40), language="hi")
        assert isinstance(res_hi, HwOcrResult)
        assert res_hi.engine == "indic_htr(hi)"

        res_ta = run_trocr_on_crop(img, 1, (0, 0, 100, 40), language="ta")
        assert isinstance(res_ta, HwOcrResult)
        assert res_ta.engine == "indic_htr(ta)"

    def test_trocr_service_status(self):
        status = get_trocr_status()
        assert "model_name" in status
        assert "device" in status


# ===========================================================================
# 3. Multilingual NLP Entity Extraction & Terminology Tests
# ===========================================================================
class TestMultilingualNlpAndTerminology:
    def test_tamil_extraction(self):
        text = "மாவட்டம்: மதுரை, வட்டம்: மேலூர், கிராமம்: மேலூர், பட்டா எண்: 450, புல எண்: 88/2A, உரிமையாளர்: முத்துசாமி"
        result = extract_entities(text, language="ta")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("village") == "மேலூர்"
        assert (entity_map.get("taluka") or entity_map.get("tehsil") or entity_map.get("district")) is not None

    def test_telugu_extraction(self):
        text = "జిల్లా: రంగారెడ్డి, మండలం: షాద్‌నగర్, గ్రామం: షాద్‌నగర్, సర్వే నంబర్: 104/A, ఖాతా సంఖ్య: 512"
        result = extract_entities(text, language="te")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "రంగారెడ్డి"
        assert entity_map.get("survey_number") == "104/A"

    def test_kannada_extraction(self):
        text = "ಜಿಲ್ಲೆ: ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ, ತಾಲೂಕು: ದೇವನಹಳ್ಳಿ, ಗ್ರಾಮ: ದೇವನಹಳ್ಳಿ, ಸರ್ವೆ ನಂ: 72/1, ವಿಸ್ತೀರ್ಣ: 2.34 ಎಕರೆ"
        result = extract_entities(text, language="kn")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ"
        assert (entity_map.get("taluka") or entity_map.get("tehsil")) == "ದೇವನಹಳ್ಳಿ"

    def test_gujarati_extraction(self):
        text = "જિલ્લો: અમદાવાદ, તાલુકો: સાનંદ, ગામ: સાનંદ, સર્વે નંબર: 315/2, ખાતા નંબર: 120"
        result = extract_entities(text, language="gu")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "અમદાવાદ"
        assert entity_map.get("village") == "સાનંદ"
        assert entity_map.get("survey_number") == "315/2"

    def test_bengali_extraction(self):
        text = "জেলা: দক্ষিণ ২৪ পরগনা, ব্লক: বারুইপুর, মৌজা: বারুইপুর, দাগ নম্বর: 520, খতিয়ান নম্বর: 304"
        result = extract_entities(text, language="bn")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "দক্ষিণ ২৪ পরগনা"
        assert entity_map.get("village") == "বারুইপুর"

    def test_punjabi_extraction(self):
        text = "ਜ਼ਿਲ੍ਹਾ: ਲੁਧਿਆਣਾ, ਤਹਿਸੀਲ: ਖੰਨਾ, ਪਿੰਡ: ਸਮਰਾਲਾ, ਖਸਰਾ ਨੰਬਰ: 210, ਖਾਤਾ ਨੰਬਰ: 55"
        result = extract_entities(text, language="pa")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "ਲੁਧਿਆਣਾ"
        assert entity_map.get("village") == "ਸਮਰਾਲਾ"
        assert entity_map.get("khasra_number") == "210"

    def test_malayalam_extraction(self):
        text = "ജില്ല: എറണാകുളം, താലൂക്ക്: ആലുവ, വില്ലേജ്: അങ്കമാലി, സർവേ നമ്പർ: 140/3"
        result = extract_entities(text, language="ml")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "എറണാകുളം"
        assert entity_map.get("village") == "അങ്കമാലി"
        assert entity_map.get("survey_number") == "140/3"

    def test_odia_extraction(self):
        text = "ଜିଲ୍ଲା: କଟକ, ତହସିଲ: ବାଙ୍କୀ, ଗ୍ରାମ: ବାଙ୍କୀ, ପ୍ଲଟ ନମ୍ବର: 412, ଖାତା ନମ୍ବର: 65"
        result = extract_entities(text, language="or")
        entity_map = {e.field_name: e.field_value for e in result.entities}
        assert entity_map.get("district") == "କଟକ"
        assert (entity_map.get("taluka") or entity_map.get("tehsil")) == "ବାଙ୍କୀ"
        assert entity_map.get("plot_number") == "412"
        assert entity_map.get("khata_number") == "65"

    def test_multilingual_domain_terminology(self):
        # Verify domain dictionary supports Indic languages
        assert "புல எண்" in _DOMAIN_DICTIONARY
        assert "సర్వే నంబర్" in _DOMAIN_DICTIONARY
        assert "ಸರ್ವೇ ನಂಬರ್" in _DOMAIN_DICTIONARY
        assert "ਖਸਰਾ" in _DOMAIN_DICTIONARY
        assert "വില്ലേജ്" in _DOMAIN_DICTIONARY
        assert "ଖାତା" in _DOMAIN_DICTIONARY
        assert "খতিয়ান" in _DOMAIN_DICTIONARY

        processed = process_text_multilingual("ಸರ್ವೆ ನಂ: ೭೨/೧", language="kn")
        assert "normalized_text" in processed





# ===========================================================================
# 4. State Land Validation Rules Tests
# ===========================================================================
class TestStateLandValidationRules:
    def test_maharashtra_712_validation(self):
        valid_rec = {
            "state": "Maharashtra",
            "document_type": "7/12",
            "survey_number": "245/1A",
            "khata_number": "45",
            "village": "Shivajinagar",
            "area": 1.45,
            "area_unit": "hectare",
        }
        res = validate_record_with_engine(valid_rec)
        assert res["is_valid"] is True
        assert res["failed_count"] == 0

    def test_uttar_pradesh_khatauni_validation(self):
        valid_rec = {
            "state": "Uttar Pradesh",
            "document_type": "khatauni",
            "khasra_number": "142",
            "khata_number": "88",
            "area": 0.854,
            "area_unit": "hectare",
        }
        res = validate_record_with_engine(valid_rec)
        assert res["is_valid"] is True

    def test_tamil_nadu_patta_validation(self):
        valid_rec = {
            "state": "Tamil Nadu",
            "document_type": "patta_chitta",
            "patta_number": "450",
            "survey_number": "88/2A",
            "area": 1.12,
            "area_unit": "hectare",
        }
        res = validate_record_with_engine(valid_rec)
        assert res["is_valid"] is True

    def test_karnataka_bhoomi_validation(self):
        valid_rec = {
            "state": "Karnataka",
            "document_type": "rtc",
            "survey_number": "72/1",
            "hissa_number": "1",
            "area": 2.34,
            "area_unit": "acre",
        }
        res = validate_record_with_engine(valid_rec)
        assert res["is_valid"] is True

    def test_area_sanity_and_anomaly_detection(self):
        from app.services.anomaly_service import detect_anomalies as detect_ml_anomalies

        crazy_rec = {
            "area": 50000.0,
            "area_unit": "acre",
            "survey_number": "101",
        }
        anomalies = detect_ml_anomalies(crazy_rec)
        assert anomalies.anomaly_flag is True


# ===========================================================================
# 5. Cadastral Map Vectorization & GIS Tests

# ===========================================================================
class TestCadastralVectorizationAndGis:
    def test_cadastral_polygon_extraction(self):
        # Create synthetic map image with 3 distinct parcel polygons and text
        img = np.ones((600, 800), dtype=np.uint8) * 255
        import cv2

        cv2.rectangle(img, (50, 50), (350, 250), 0, 3)
        cv2.putText(img, "101", (150, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)

        cv2.rectangle(img, (400, 50), (750, 250), 0, 3)
        cv2.putText(img, "102", (550, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)

        cv2.rectangle(img, (50, 300), (750, 550), 0, 3)
        cv2.putText(img, "103", (350, 430), cv2.FONT_HERSHEY_SIMPLEX, 1.5, 0, 3)

        buf = io.BytesIO()
        Image.fromarray(img).save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        result = extract_cadastral_polygons_from_map(raw_bytes, extract_labels=True)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 3

        # Verify GeoJSON polygon format
        for feature in result["features"]:
            assert feature["type"] == "Feature"
            assert feature["geometry"]["type"] == "Polygon"
            coords = feature["geometry"]["coordinates"][0]
            assert len(coords) >= 4  # Closed polygon has >= 4 points
            assert coords[0] == coords[-1]  # Closed ring
            assert "survey_number" in feature["properties"]
            assert feature["properties"]["extracted_area_px"] > 1000


# ===========================================================================
# 6. AI Pipeline Background Workers Tests
# ===========================================================================
class TestAiPipelineWorkers:
    def test_ner_worker(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai-pipeline"))

        from workers.ner_worker import process_document_ner
        res = process_document_ner("तालुका: हवेली, जिल्हा: पुणे, सर्व्हे क्र.: 245/1A", language="mr")
        assert res["status"] == "success"
        assert "entities" in res

    def test_anomaly_worker(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai-pipeline"))

        from workers.anomaly_worker import detect_document_anomalies
        res = detect_document_anomalies({"area": 1.45, "area_unit": "hectare"})
        assert res["status"] == "success"
        assert "anomaly_report" in res

    def test_layout_worker(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ai-pipeline"))

        from workers.layout_worker import process_layout_analysis
        res = process_layout_analysis([
            {
                "page_num": 1,
                "width": 800,
                "height": 600,
                "blocks": [{"text": "Sample", "bbox": [10, 10, 50, 50], "confidence": 0.95}],
            }
        ])
        assert res["status"] == "success"
        assert "layout_analysis" in res
