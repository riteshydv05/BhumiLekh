"""Language Detection Service.

Uses langdetect (a port of Google's language-detection library) to identify
the primary language of extracted text.

Falls back gracefully to "unknown" if:
  - langdetect is not installed
  - text is too short or ambiguous
  - detection raises any exception
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from langdetect import LangDetectException, detect
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed; language detection unavailable")

# Minimum characters required for a reliable detection
_MIN_CHARS = 20

# Map common langdetect codes to human-readable names
_LANG_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (Devanagari)",
    "mr": "Marathi (Devanagari)",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "bn": "Bengali",
    "ur": "Urdu",
    "or": "Odia",
    "as": "Assamese",
}

_MARATHI_KEYWORDS = [
    "गाव", "तालुका", "जिल्हा", "नमुना", "अभिलेखा", "अभिलेख", "भोगवटदार",
    "खातेदार", "हक्क", "मालिक", "फेरफार", "सात", "१२", "आकारणी", "क्षेत्रफळ",
    "महाराष्ट्र", "नमुने", "सर्व्हे", "क्षेत्र", "पोट", "खराब"
]


def detect_language(text: str) -> str:
    """Detect the primary language of *text*.

    First performs deterministic Unicode script detection (Devanagari, Gujarati, etc.).
    For Devanagari, uses domain key terms to distinguish Marathi ('mr') from Hindi ('hi').
    Falls back to langdetect for Latin/other scripts.

    Returns an ISO 639-1 code (e.g. "mr", "hi", "en") or "unknown".
    Never raises — all errors are swallowed and logged.
    """
    if not text or len(text.strip()) < 5:
        logger.debug(
            "Text too short for language detection (%d chars)", len(text or "")
        )
        return "unknown"

    clean_text = text.strip()

    # 1. Unicode Script Range Counts
    devanagari_count = 0
    bengali_count = 0
    gurmukhi_count = 0
    gujarati_count = 0
    tamil_count = 0
    telugu_count = 0
    kannada_count = 0
    malayalam_count = 0

    for char in clean_text:
        code = ord(char)
        if 0x0900 <= code <= 0x097F:
            devanagari_count += 1
        elif 0x0980 <= code <= 0x09FF:
            bengali_count += 1
        elif 0x0A00 <= code <= 0x0A7F:
            gurmukhi_count += 1
        elif 0x0A80 <= code <= 0x0AFF:
            gujarati_count += 1
        elif 0x0B80 <= code <= 0x0BFF:
            tamil_count += 1
        elif 0x0C00 <= code <= 0x0C7F:
            telugu_count += 1
        elif 0x0C80 <= code <= 0x0CFF:
            kannada_count += 1
        elif 0x0D00 <= code <= 0x0D7F:
            malayalam_count += 1

    total_indic = (
        devanagari_count + bengali_count + gurmukhi_count + gujarati_count +
        tamil_count + telugu_count + kannada_count + malayalam_count
    )

    if total_indic > 2:
        counts = {
            "ta": tamil_count,
            "te": telugu_count,
            "kn": kannada_count,
            "ml": malayalam_count,
            "gu": gujarati_count,
            "bn": bengali_count,
            "pa": gurmukhi_count,
            "mr": devanagari_count,
        }
        max_lang = max(counts, key=counts.get)
        if counts[max_lang] > 0:
            if max_lang == "mr":
                if any(kw in clean_text for kw in _MARATHI_KEYWORDS):
                    logger.info("Detected script: Devanagari -> Language: Marathi (mr)")
                    return "mr"
                logger.info("Detected script: Devanagari -> Language: Hindi/Marathi (hi)")
                return "hi"
            logger.info("Detected script -> Language: %s", max_lang)
            return max_lang

    # 2. Fall back to langdetect for non-Indic / English text
    if not _LANGDETECT_AVAILABLE:
        return "en"

    try:
        lang_code = detect(clean_text)
        # Fix langdetect false positive where non-Latin digits/symbols get classified as Portuguese (pt)
        if lang_code == "pt" and total_indic == 0:
            # Check if text is mostly numbers/Latin
            english_chars = sum(1 for c in clean_text if c.isascii())
            if english_chars / max(len(clean_text), 1) > 0.5:
                lang_code = "en"

        lang_name = _LANG_NAMES.get(lang_code, lang_code)
        logger.info("Detected language via langdetect: %s (%s)", lang_name, lang_code)
        return lang_code
    except LangDetectException as exc:
        logger.warning("Language detection failed (ambiguous text): %s", exc)
        return "en"
    except Exception as exc:
        logger.error("Language detection error: %s", exc, exc_info=True)
        return "en"


def get_language_name(lang_code: str) -> str:
    """Return a human-readable name for an ISO 639-1 language code."""
    return _LANG_NAMES.get(lang_code.lower() if lang_code else "", lang_code or "Unknown")

