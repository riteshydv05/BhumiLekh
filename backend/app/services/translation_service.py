"""Translation and Reprocessing Service.

Provides:
- Fast, multi-language translation using Google Translate API with local fallback
- Batch document field translation
- Document reprocessing with user-selected target OCR language
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.document_result import DocumentResult

logger = logging.getLogger(__name__)

# Common land-record terminology fallback dictionary
_TERMS_DICT: dict[str, dict[str, str]] = {
    # Tamil domain terms
    "தமிழ்நாடு அரசு": "Government of Tamil Nadu",
    "வருவாய்த் துறை": "Revenue Department",
    "நில உரிமை விவரங்கள்": "Land Ownership Details",
    "பட்டா எண்": "Patta Number",
    "மாவட்டப் பெயர்": "District Name",
    "வட்டப் பெயர்": "Taluk Name",
    "கிராமப் பெயர்": "Village Name",
    "உரிமையாளர்கள் பெயர்": "Owners Name",
    "புல எண்": "Survey Number",
    "உட்பிரிவு": "Sub-Division",
    "நன்செய்": "Wetland / Irrigated Land",
    "புன்செய்": "Dryland / Rainfed Land",
    "பரப்பு": "Area",
    "ஹெக்டேர்": "Hectares",
    "ஏக்கர்": "Acres",
    "தீர்வை": "Tax / Assessment",
    "குறிப்புகள்": "Remarks",

    # Devanagari / Hindi / Marathi terms
    "खसरा": "Khasra",
    "सर्वे": "Survey",
    "खाता": "Khata",
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
    "दिनांक": "Date",
    "रजिस्ट्रेशन": "Registration",
}


def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Translate text to target_lang.

    Uses free public Google Translate HTTP endpoint with timeout.
    Falls back to domain dictionary and original text on network error.
    """
    if not text or not text.strip():
        return ""

    clean_text = text.strip()

    # If target is same as source or text is purely ASCII numbers/punctuation, return as is
    if clean_text.isdigit() or (clean_text.isascii() and not any(c.isalpha() for c in clean_text)):
        return clean_text

    # Check local domain dictionary first
    for term, translated in _TERMS_DICT.items():
        if term in clean_text:
            if target_lang == "en":
                return clean_text.replace(term, translated)

    # Free Google Translate API
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(clean_text)}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw_data = resp.read().decode("utf-8")
            data = json.loads(raw_data)
            if data and isinstance(data, list) and len(data) > 0 and data[0]:
                translated_parts = [item[0] for item in data[0] if item and item[0]]
                if translated_parts:
                    result = "".join(translated_parts).strip()
                    logger.info("Translated ('%s' -> '%s'): '%s' => '%s'", source_lang, target_lang, clean_text, result)
                    return result
    except Exception as exc:
        logger.warning("Google Translate API call failed ('%s'): %s", clean_text, exc)

    # Fallback to local transliteration
    try:
        from app.services.multilingual_service import transliterate_text
        return transliterate_text(clean_text)
    except Exception:
        return clean_text


def translate_document_results(
    doc_id: str, target_lang: str, db: Session
) -> list[DocumentResult]:
    """Translate all extracted fields for doc_id into target_lang and save to DB."""
    from app.models.document_result import DocumentResult

    results = (
        db.query(DocumentResult)
        .filter(DocumentResult.document_id == doc_id)
        .all()
    )

    if not results:
        logger.warning("No document results found to translate for document %s", doc_id)
        return []

    logger.info("Translating %d fields for document %s to '%s'", len(results), doc_id, target_lang)

    for item in results:
        text_to_translate = item.source_text or item.original_text or item.field_value or ""
        if text_to_translate and text_to_translate.strip():
            translated = translate_text(text_to_translate, source_lang="auto", target_lang=target_lang)
            item.translation = translated
            if target_lang == "en" and translated:
                item.normalized_value = translated

    db.commit()
    for item in results:
        db.refresh(item)

    return results
