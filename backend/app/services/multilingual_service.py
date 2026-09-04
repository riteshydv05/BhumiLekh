"""Multilingual Normalization, Transliteration, and Translation Service.

Features:
- Preserves raw OCR text intact as `original_text`.
- Converts Indic numerals (Devanagari, Gujarati, Bengali, etc.) to ASCII digits (0-9).
- Transliterates Indic text into Latin/Roman phonetic representations (`transliteration`) using IndicXlit / indic-transliteration.
- Standardizes domain terms (e.g. "खसरा", "सर्वे", "कृषि", "हेक्टर") into normalized representations (`normalized_text`).
- Provides semantic translation (`translation`) ONLY for non-identifier / non-legal-name fields (e.g. land classification, unit names).
- STRICTLY preserves legal names and parcel identifiers (survey, khasra, khata, mutation numbers) without blind translation.
- Graceful fallback if selected Indic model or script is unsupported.
- No external paid APIs required (runs 100% locally).
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.nlp_service import LandRecordEntity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indic numeral mapping (Devanagari, Gujarati, Bengali, Gurmukhi, etc.)
# ---------------------------------------------------------------------------
_INDIC_DIGIT_MAP = {
    # Devanagari / Marathi / Hindi
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
    # Gujarati
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4",
    "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9",
    # Bengali / Assamese
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
    # Gurmukhi (Punjabi)
    "੦": "0", "੧": "1", "੨": "2", "੩": "3", "੪": "4",
    "੫": "5", "੬": "6", "੭": "7", "੮": "8", "੯": "9",
    # Odia
    "૦": "0", "୧": "1", "୨": "2", "୩": "3", "୪": "4",
    "୫": "5", "୬": "6", "୭": "7", "੮": "8", "୯": "9",
    # Telugu
    "੮": "0", "౧": "1", "౨": "2", "౩": "3", "౪": "4",
    "౫": "5", "౬": "6", "౭": "7", "౮": "8", "౯": "9",
    # Kannada
    "೦": "0", "೧": "1", "೨": "2", "೩": "3", "೪": "4",
    "೫": "5", "೬": "6", "೭": "7", "೮": "8", "೯": "9",
    # Malayalam
    "൦": "0", "൧": "1", "൨": "2", "൩": "3", "൪": "4",
    "൫": "5", "൬": "6", "൭": "7", "൮": "8", "൯": "9",
}

_DIGIT_TRANSLATE_TABLE = str.maketrans(_INDIC_DIGIT_MAP)


def normalize_digits(text: str) -> str:
    """Convert Indic numerals in text to standard ASCII digits (0-9)."""
    if not text:
        return ""
    return text.translate(_DIGIT_TRANSLATE_TABLE)


# ---------------------------------------------------------------------------
# Identifiers that MUST NEVER be blindly translated into English words
# ---------------------------------------------------------------------------
IDENTIFIER_ENTITY_TYPES: set[str] = {
    "OWNER_NAME",
    "FATHER_NAME",
    "MOTHER_NAME",
    "SURVEY_NUMBER",
    "KHASRA_NUMBER",
    "KHATA_NUMBER",
    "PLOT_NUMBER",
    "REGISTRATION_NUMBER",
    "MUTATION_NUMBER",
}

# ---------------------------------------------------------------------------
# Common land-record domain terminology translations (Semantic assistance)
# ---------------------------------------------------------------------------
_DOMAIN_DICTIONARY: dict[str, str] = {
    # Devanagari / Hindi / Marathi terms
    "खसरा": "Khasra",
    "खसरा संख्या": "Khasra Number",
    "खसरा नं": "Khasra Number",
    "सर्वे": "Survey",
    "सर्वे नंबर": "Survey Number",
    "सर्वे नं": "Survey Number",
    "खाता": "Khata",
    "खाता संख्या": "Khata Number",
    "खाता नं": "Khata Number",
    "गाव": "Village",
    "गाँव": "Village",
    "ग्राम": "Village",
    "तालुका": "Tehsil/Taluka",
    "तहसील": "Tehsil/Taluka",
    "जिल्हा": "District",
    "जिला": "District",
    "क्षेत्रफल": "Area",
    "क्षेत्र": "Area",
    "हेक्टर": "Hectares",
    "एकड़": "Acres",
    "कृषि": "Agricultural",
    "शेती": "Agricultural",
    "अकृषि": "Non-Agricultural",
    "बिनशेती": "Non-Agricultural",
    "मालिक": "Owner",
    "मालिकाचे नाव": "Owner Name",
    "दिनांक": "Date",
    "रजिस्ट्रेशन": "Registration",
}

# ---------------------------------------------------------------------------
# Transliteration via Indic-Transliteration (with graceful fallback)
# ---------------------------------------------------------------------------

_SANSCRIPT_AVAILABLE = False
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _sanscript_transliterate
    _SANSCRIPT_AVAILABLE = True
except ImportError:
    _SANSCRIPT_AVAILABLE = False
    logger.warning("indic-transliteration package not found; using fallback transliterator")


def _detect_indic_script(text: str) -> str | None:
    """Detect the Indic script scheme for sanscript."""
    if not text:
        return None

    for char in text:
        code = ord(char)
        if 0x0900 <= code <= 0x097F:
            return "DEVANAGARI"
        elif 0x0980 <= code <= 0x09FF:
            return "BENGALI"
        elif 0x0A00 <= code <= 0x0A7F:
            return "GURMUKHI"
        elif 0x0A80 <= code <= 0x0AFF:
            return "GUJARATI"
        elif 0x0B00 <= code <= 0x0B7F:
            return "ORIYA"
        elif 0x0B80 <= code <= 0x0BFF:
            return "TAMIL"
        elif 0x0C00 <= code <= 0x0C7F:
            return "TELUGU"
        elif 0x0C80 <= code <= 0x0CFF:
            return "KANNADA"
        elif 0x0D00 <= code <= 0x0D7F:
            return "MALAYALAM"

    return None


def transliterate_text(text: str, source_lang: str | None = None) -> str:
    """Transliterate text into readable Latin/Roman phonetic script.

    Uses indic_transliteration.sanscript if available.
    Converts Indic digits to ASCII digits.
    Never raises — returns original text if transliteration is unsupported or fails.
    """
    if not text:
        return ""

    # Convert digits first
    digit_normalized = normalize_digits(text)

    if not _SANSCRIPT_AVAILABLE:
        return digit_normalized

    try:
        script_name = _detect_indic_script(text)
        if not script_name:
            return digit_normalized

        script_scheme = getattr(sanscript, script_name, None)
        if not script_scheme:
            return digit_normalized

        # Transliterate to ITRANS (Phonetic Romanization)
        romanized = _sanscript_transliterate(digit_normalized, script_scheme, sanscript.ITRANS)
        # Clean up double capitals from ITRANS notation (e.g. khasarA -> khasra)
        romanized = re.sub(r'([A-Z]{2,})', lambda m: m.group(1).capitalize(), romanized)
        return romanized.strip()
    except Exception as exc:
        logger.warning("Transliteration failed for text '%s': %s", text, exc)
        return digit_normalized


# ---------------------------------------------------------------------------
# Normalization & Translation Pipeline
# ---------------------------------------------------------------------------

def process_text_multilingual(
    text: str,
    entity_type: str | None = None,
    language: str = "en",
) -> dict[str, str | None]:
    """Process OCR text to generate original, normalized, transliterated, and translated fields.

    Args:
        text: Raw OCR text.
        entity_type: Target entity type (e.g. 'KHASRA_NUMBER', 'OWNER_NAME', 'LAND_CLASSIFICATION').
        language: Detected language code (e.g. 'hi', 'mr', 'en').

    Returns:
        Dict with keys:
            - original_text (str): Exact raw OCR text preserved.
            - normalized_text (str): Digit-normalized and standardized text.
            - transliteration (str): Phonetic Latin/Roman transliteration.
            - translation (str | None): Semantic English translation (omitted/equal for identifiers).
    """
    original = text or ""
    if not original.strip():
        return {
            "original_text": original,
            "normalized_text": "",
            "transliteration": "",
            "translation": None,
        }

    # 1. Transliteration (phonetic Latin + ASCII digits)
    translit = transliterate_text(original, source_lang=language)

    # 2. Digit Normalization
    digit_norm = normalize_digits(original)

    # 3. Check if this is an identifier or legal name field
    is_identifier = entity_type in IDENTIFIER_ENTITY_TYPES if entity_type else False

    # 4. Optional Bhashini Hosted API Integration (if enabled & configured)
    bhashini_translit = None
    bhashini_translation = None
    try:
        from app.services.external.bhashini_service import BhashiniService
        bhashini = BhashiniService()
        if bhashini.is_configured:
            b_res_trans = bhashini.transliterate(original, source_lang=language)
            if b_res_trans.get("status") == "success" and b_res_trans.get("transliteration"):
                bhashini_translit = b_res_trans["transliteration"]

            if not is_identifier:
                b_res_tr = bhashini.translate(original, source_lang=language, is_identifier=is_identifier)
                if b_res_tr.get("status") == "success" and b_res_tr.get("translation"):
                    bhashini_translation = b_res_tr["translation"]
    except Exception as exc:
        logger.warning("Bhashini optional service call skipped due to error: %s", exc)

    # Use Bhashini transliteration if available, else local transliteration
    final_translit = bhashini_translit or translit

    # 5. Construct normalized_text & translation
    if is_identifier:
        # DO NOT translate legal names or parcel numbers blindly!
        normalized_text = final_translit
        translation = None  # Never replace legal names/identifiers with translated text
    else:
        # Non-identifier fields (e.g. LAND_CLASSIFICATION, AREA, VILLAGE, TEHSIL)
        matched_translation = bhashini_translation
        if not matched_translation:
            for term, translated_term in _DOMAIN_DICTIONARY.items():
                if term in original:
                    matched_translation = translated_term
                    break

        if matched_translation:
            translation = matched_translation
            normalized_text = matched_translation
        else:
            if language == "en":
                translation = digit_norm
                normalized_text = digit_norm
            else:
                translation = final_translit
                normalized_text = final_translit

    return {
        "original_text": original,
        "normalized_text": normalized_text,
        "transliteration": final_translit,
        "translation": translation,
    }


def enrich_entity(entity: LandRecordEntity) -> LandRecordEntity:
    """Enrich a LandRecordEntity with multilingual fields.

    Mutates the entity by assigning:
    - original_text
    - normalized_text
    - transliteration
    - translation
    """
    # Use source_text or extracted_value as raw original text
    raw_text = entity.original_text or entity.source_text or entity.extracted_value

    processed = process_text_multilingual(
        text=raw_text,
        entity_type=entity.entity_type,
        language=entity.language,
    )

    entity.original_text = processed["original_text"] or raw_text
    entity.transliteration = processed["transliteration"] or ""
    entity.translation = processed["translation"]
    
    # If normalized_text is set, update extracted_value if it was raw Indic digits
    if processed["normalized_text"]:
        entity.normalized_text = processed["normalized_text"]

    return entity
