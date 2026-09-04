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
    "hi": "Hindi",
    "mr": "Marathi",
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


def detect_language(text: str) -> str:
    """Detect the primary language of *text*.

    Returns an ISO 639-1 code (e.g. "en", "hi") or "unknown".
    Never raises — all errors are swallowed and logged.
    """
    if not text or len(text.strip()) < _MIN_CHARS:
        logger.debug(
            "Text too short for language detection (%d chars)", len(text or "")
        )
        return "unknown"

    if not _LANGDETECT_AVAILABLE:
        logger.warning("Language detection skipped: langdetect not installed")
        return "unknown"

    try:
        lang_code = detect(text)
        lang_name = _LANG_NAMES.get(lang_code, lang_code)
        logger.info("Detected language: %s (%s)", lang_name, lang_code)
        return lang_code
    except LangDetectException as exc:
        logger.warning("Language detection failed (ambiguous text): %s", exc)
        return "unknown"
    except Exception as exc:
        logger.error("Language detection error: %s", exc, exc_info=True)
        return "unknown"


def get_language_name(lang_code: str) -> str:
    """Return a human-readable name for an ISO 639-1 language code."""
    return _LANG_NAMES.get(lang_code, lang_code)
