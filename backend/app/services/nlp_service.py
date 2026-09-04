"""NLP Service — Multilingual Named Entity Recognition for Land Records.

Architecture:
    OCR (text + bboxes) → NER extraction → Land-record field mapping → Structured record

    OCR
     ↓
    normalized text
     ↓
    NER/entity extraction  (IndicNER model OR rule-based fallback)
     ↓
    land-record field mapping
     ↓
    structured record

The IndicNER model (ai4bharat/IndicNER) provides token-classification for
Indic languages. However, it is a gated repository and requires authentication.
When unavailable, the service falls back to rule-based extraction.

IMPORTANT:
    No single NER model perfectly identifies all land-record fields.
    Rule-based extraction supplements NER for fields that are not
    well-suited to classification (e.g., dates, area values, registration numbers).

Extracted entities include:
    owner_name, father_name, mother_name
    survey_number, khasra_number, khata_number, plot_number
    village, tehsil, district
    area, land_classification
    registration_number, mutation_number
    date

Storage per entity:
    - extracted_value, entity_type, source_text
    - page, bounding_box (when available), confidence, extraction_method
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Land-record entity types
# ---------------------------------------------------------------------------

LAND_RECORD_ENTITY_TYPES = {
    "OWNER_NAME",
    "FATHER_NAME",
    "MOTHER_NAME",
    "SURVEY_NUMBER",
    "KHASRA_NUMBER",
    "KHATA_NUMBER",
    "PLOT_NUMBER",
    "VILLAGE",
    "TEHSIL",
    "DISTRICT",
    "AREA",
    "LAND_CLASSIFICATION",
    "REGISTRATION_NUMBER",
    "MUTATION_NUMBER",
    "DATE",
}

# Mapping from NER label names to land-record entity types
NER_LABEL_TO_ENTITY: dict[str, str] = {
    "B-owner": "OWNER_NAME",
    "I-owner": "OWNER_NAME",
    "B-father": "FATHER_NAME",
    "I-father": "FATHER_NAME",
    "B-mother": "MOTHER_NAME",
    "I-mother": "MOTHER_NAME",
    "B-survey": "SURVEY_NUMBER",
    "I-survey": "SURVEY_NUMBER",
    "B-khasra": "KHASRA_NUMBER",
    "I-khasra": "KHASRA_NUMBER",
    "B-khata": "KHATA_NUMBER",
    "I-khata": "KHATA_NUMBER",
    "B-plot": "PLOT_NUMBER",
    "I-plot": "PLOT_NUMBER",
    "B-village": "VILLAGE",
    "I-village": "VILLAGE",
    "B-tehsil": "TEHSIL",
    "I-tehsil": "TEHSIL",
    "B-district": "DISTRICT",
    "I-district": "DISTRICT",
    "B-area": "AREA",
    "I-area": "AREA",
    "B-land_class": "LAND_CLASSIFICATION",
    "I-land_class": "LAND_CLASSIFICATION",
    "B-registration": "REGISTRATION_NUMBER",
    "I-registration": "REGISTRATION_NUMBER",
    "B-mutation": "MUTATION_NUMBER",
    "I-mutation": "MUTATION_NUMBER",
    "B-date": "DATE",
    "I-date": "DATE",
}

# Language codes supported by IndicNER (Indic language family)
INDIC_LANGUAGES = {
    "hi", "mr", "gu", "ta", "te", "kn", "ml", "pa", "bn", "ur", "or",
    "as", "kok", "mai", "ne", "sa", "rw", "gom", "brx", "sat", "doi",
}
INDIC_LANGUAGES.add("en")

# ---------------------------------------------------------------------------
# Dataclasses — structured entity storage (separate from raw OCR)
# ---------------------------------------------------------------------------

_ENTITY_TO_FIELD_NAME_MAP: dict[str, str] = {
    "VILLAGE": "village",
    "TEHSIL": "taluka",
    "DISTRICT": "district",
    "AREA": "area_hectares",
    "DATE": "registration_date",
    "SURVEY_NUMBER": "survey_number",
    "KHASRA_NUMBER": "khasra_number",
    "KHATA_NUMBER": "khata_number",
    "PLOT_NUMBER": "plot_number",
    "OWNER_NAME": "owner_name",
    "FATHER_NAME": "father_name",
    "MOTHER_NAME": "mother_name",
    "REGISTRATION_NUMBER": "registration_number",
    "MUTATION_NUMBER": "mutation_number",
}


@dataclass
class LandRecordEntity:
    """A single extracted entity from land-record text."""

    entity_type: str
    extracted_value: str
    original_text: str = ""
    normalized_text: str = ""
    transliteration: str = ""
    translation: str | None = None
    source_text: str = ""
    page: int = 1
    bounding_box: list[float] | None = None
    confidence: float = 0.0
    extraction_method: str = "rule"
    language: str = "en"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def field_name(self) -> str:
        if hasattr(self, "_custom_field_name") and self._custom_field_name:
            return self._custom_field_name
        upper_type = (self.entity_type or "").upper()
        return _ENTITY_TO_FIELD_NAME_MAP.get(upper_type, self.entity_type.lower() if self.entity_type else "")

    @field_name.setter
    def field_name(self, value: str) -> None:
        self._custom_field_name = value
        self.entity_type = value

    @property
    def field_value(self) -> str:
        return self.extracted_value

    @field_value.setter
    def field_value(self, value: str) -> None:
        self.extracted_value = value

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "extracted_value": self.extracted_value,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "original_text": self.original_text or self.source_text or self.extracted_value,
            "normalized_text": self.normalized_text or self.extracted_value,
            "transliteration": self.transliteration,
            "translation": self.translation,
            "source_text": self.source_text,
            "page": self.page,
            "bounding_box": self.bounding_box,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
            "language": self.language,
            "timestamp": self.timestamp,
        }


class ExtractedField(LandRecordEntity):
    """Backward-compatible class supporting field_name and field_value positional/keyword arguments."""

    def __init__(
        self,
        field_name: str = "",
        field_value: str = "",
        confidence: float = 0.0,
        entity_type: str = "",
        extracted_value: str = "",
        **kwargs: Any,
    ) -> None:
        final_entity_type = entity_type or field_name
        final_extracted_value = extracted_value or field_value
        super().__init__(
            entity_type=final_entity_type,
            extracted_value=final_extracted_value,
            confidence=confidence,
            **kwargs,
        )
        self._custom_field_name = field_name or entity_type


@dataclass
class ExtractionStatus:
    """Status of an extraction run."""

    success: bool
    method: str
    message: str = ""
    model_available: bool = False
    language_supported: bool = True
    entities_extracted: int = 0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "method": self.method,
            "message": self.message,
            "model_available": self.model_available,
            "language_supported": self.language_supported,
            "entities_extracted": self.entities_extracted,
        }


@dataclass
class ExtractionResult:
    """Full extraction result."""

    entities: list[LandRecordEntity] = field(default_factory=list)
    status: ExtractionStatus | None = None
    error: str | None = None
    language: str = "unknown"

    @property
    def fields(self) -> list[LandRecordEntity]:
        """Backward-compatible alias for entities."""
        return self.entities

    def to_dict(self) -> dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "status": self.status.to_dict() if self.status else None,
            "error": self.error,
            "language": self.language,
            "entity_count": len(self.entities),
        }

    @property
    def field_map(self) -> dict[str, str]:
        """Return entity_type -> extracted_value map (first wins per type)."""
        result: dict[str, str] = {}
        for e in self.entities:
            if e.entity_type not in result:
                result[e.entity_type] = e.extracted_value
        return result


# ---------------------------------------------------------------------------
# Rule-based patterns for land-record fields (always available)
# ---------------------------------------------------------------------------

_LAND_RECORD_PATTERNS: dict[str, list[tuple[re.Pattern[str], float]]] = {
    "en": [
        # Survey Number
        (re.compile(
            r"(?:survey\s*no\.?|survey\s*number|s\.?\s*no\.?)\s*[:\-]?\s*([A-Z0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.90),
        # Khasra Number
        (re.compile(
            r"(?:khasra\s*no\.?|khasra\s*number|khasrauni|khasra)\s*[:\-]?\s*([0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.88),
        # Khata Number
        (re.compile(
            r"(?:khata\s*no\.?|khata\s*number|khatauni|khata)\s*[:\-]?\s*([0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.88),
        # Plot Number
        (re.compile(
            r"(?:plot\s*no\.?|plot\s*number|p\.?\s*no\.?)\s*[:\-]?\s*([A-Z0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.85),
        # Village
        (re.compile(
            r"(?:village|gram|gaon|gramin)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{2,28})(?=\s{2,}|[\n,.]|\s+(?:Tehsil|District|State|Taluka|Area|Owner|Reg|Doc|Pin)|$)",
            re.IGNORECASE,
        ), 0.80),
        # Tehsil / Taluka
        (re.compile(
            r"(?:tehsil|taluka|taluk|t\.?\s*q\.?)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{2,28})(?=\s{2,}|[\n,.]|\s+(?:District|State|Area|Owner|Reg|Doc|Pin|Village)|$)",
            re.IGNORECASE,
        ), 0.80),
        # District
        (re.compile(
            r"(?:district|dist\.?|zilla)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{2,28})(?=\s{2,}|[\n,.]|\s+(?:State|Area|Owner|Reg|Doc|Pin|Village|Taluka)|$)",
            re.IGNORECASE,
        ), 0.80),
        # Area with units
        (re.compile(
            r"([0-9]+(?:\.[0-9]+)?)\s*(?:hectare|hectares|ha\.?|acre|acres|ac\.?|sq\.?\s*m\.?|square\s*met(?:re|er)s?)",
            re.IGNORECASE,
        ), 0.85),
        # Registration Number
        (re.compile(
            r"(?:registration\s*no\.?|reg\.?\s*no\.?|deed\s*no\.?|document\s*no\.?)\s*[:\-]?\s*([A-Z0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.85),
        # Mutation Number
        (re.compile(
            r"(?:mutation\s*no\.?|dakhil\s*kharij|dakhil\s*khari)\s*[:\-]?\s*([0-9/\-\.]+)",
            re.IGNORECASE,
        ), 0.82),
        # Date
        (re.compile(
            r"(?:registration\s*date|date\s*of\s*registration|deed\s*date|executed\s*on|date\s*of\s*execution)\s*[:\-]?\s*"
            r"(\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})",
            re.IGNORECASE,
        ), 0.90),
        # Owner Name
        (re.compile(
            r"(?:owner(?:'s)?\s*name|malik\s*ka\s*naam|bhumiswami|vendee|purchaser)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s\.]{2,59})(?=s/o|w/o|d/o|[\n,.]|\s{2,}|$)",
            re.IGNORECASE,
        ), 0.75),
        # Father's Name
        (re.compile(
            r"(?:father['\u2019']?\s*(?:name|s\s+name)|father\s*name|s/o|s\.?\s*o\.?|father|pitaji|pitamah)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s\.]{2,59})",
            re.IGNORECASE,
        ), 0.72),
        # Mother's Name
        (re.compile(
            r"(?:mother['\u2019']?\s*(?:name|s\s+name)|mother\s*name|w/o|w\.?\s*o\.?|mother|mataji|mata)\s*[:\-]?\s*([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s\.]{2,59})",
            re.IGNORECASE,
        ), 0.72),
    ],
    "hi": [
        (re.compile(
            r"(?:सर्वे\s*नं\.?|सर्वे\s*नम्बर|सर्वे)\s*[:\-]?\s*([0-9०-९A-Za-z\/\-\.]+)",
            re.IGNORECASE,
        ), 0.90),
        (re.compile(
            r"(?:खेत)\s*[:\-]?\s*([A-Za-z\u0900-\u097F]{2,25})",
            re.IGNORECASE,
        ), 0.80),
    ],
    "mr": [
        (re.compile(
            r"(?:सर्वे\s*नं\.?|सर्वे\s*नम्बर|सर्वे)\s*[:\-]?\s*([0-9०-९A-Za-z\/\-\.]+)",
            re.IGNORECASE,
        ), 0.90),
        (re.compile(
            r"(?:गाव|गाँव)\s*[:\-]?\s*([अ-ऑA-Za-z\u0900-\u097F]{2,25})",
            re.IGNORECASE,
        ), 0.80),
    ],
}

_DEFAULT_PATTERNS = _LAND_RECORD_PATTERNS.get("en", [])


# ---------------------------------------------------------------------------
# NER Model Loader (optional, graceful degradation)
# ---------------------------------------------------------------------------

class _NERModelLoader:
    """Lazy-loading wrapper for the IndicNER model."""

    _instance: "_NERModelLoader | None" = None
    _initialized: bool = False
    _init_error: str | None = None
    _model: Any = None
    _tokenizer: Any = None
    _model_name: str = ""
    _supported_languages: set[str] = set()

    def __new__(cls) -> "_NERModelLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self,
        model_name: str = "ai4bharat/IndicNER",
        supported_languages: set[str] | None = None,
    ) -> bool:
        """Load the IndicNER model and tokenizer."""
        if self._initialized and self._model is not None:
            return True
        if supported_languages is None:
            supported_languages = INDIC_LANGUAGES.copy()
        try:
            from transformers import AutoTokenizer, AutoModelForTokenClassification
            import torch

            logger.info("Loading NER model: %s", model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForTokenClassification.from_pretrained(model_name)
            self._model.eval()
            self._model_name = model_name
            self._supported_languages = supported_languages
            self._initialized = True
            logger.info("NER model loaded successfully: %s", model_name)
            return True
        except Exception as exc:
            self._init_error = str(exc)
            logger.error("NER model loading failed for %s: %s", model_name, exc, exc_info=True)
            self._initialized = False
            return False

    @property
    def is_available(self) -> bool:
        return self._initialized and self._model is not None and self._tokenizer is not None

    @property
    def init_error(self) -> str | None:
        return self._init_error


# ---------------------------------------------------------------------------
# Public API — extract_entities
# ---------------------------------------------------------------------------

def _get_language(text: str) -> str:
    """Detect the primary language of text. Falls back to 'en'."""
    try:
        from app.services.language_service import detect_language
        return detect_language(text)
    except Exception:
        return "en"


def _load_patterns(language: str) -> list[tuple[re.Pattern[str], float]]:
    """Return regex patterns for the given language."""
    patterns = _LAND_RECORD_PATTERNS.get(language)
    if patterns is None:
        logger.info("No language-specific patterns for %s, using default (en)", language)
        return _DEFAULT_PATTERNS
    return patterns


def _pattern_to_entity(pattern: re.Pattern[str]) -> str | None:
    """Map a compiled regex pattern to a land-record entity type.

    Removes lookahead sections from the pattern before checking for
    keywords to avoid false matches (e.g. 'village' in the lookahead
    of the district pattern).
    """
    full_pattern = pattern.pattern
    # Remove lookahead sections (?=...) to avoid false keyword matches
    clean = re.sub(r'\(\?=[^)]*\)', '', full_pattern).lower()

    # Keywords and their entity types - checked in order (specific first)
    keywords: list[tuple[str, str]] = [
        (r"registration\s*date", "DATE"),
        (r"date\s*of\s*registration", "DATE"),
        (r"executed\s*on", "DATE"),
        (r"hectare", "AREA"),
        (r"acre", "AREA"),
        (r"square", "AREA"),
        (r"survey", "SURVEY_NUMBER"),
        (r"सर्वे", "SURVEY_NUMBER"),
        (r"khasra", "KHASRA_NUMBER"),
        (r"खसरा", "KHASRA_NUMBER"),
        (r"khata", "KHATA_NUMBER"),
        (r"खाता", "KHATA_NUMBER"),
        (r"plot", "PLOT_NUMBER"),
        (r"गट", "PLOT_NUMBER"),
        (r"village", "VILLAGE"),
        (r"gaon", "VILLAGE"),
        (r"गाव", "VILLAGE"),
        (r"गाँव", "VILLAGE"),
        (r"ग्राम", "VILLAGE"),
        (r"tehsil", "TEHSIL"),
        (r"taluka", "TEHSIL"),
        (r"तहसील", "TEHSIL"),
        (r"तालुका", "TEHSIL"),
        (r"district", "DISTRICT"),
        (r"zilla", "DISTRICT"),
        (r"जिला", "DISTRICT"),
        (r"जिल्हा", "DISTRICT"),
        (r"registration\s*no", "REGISTRATION_NUMBER"),
        (r"document\s*no", "REGISTRATION_NUMBER"),
        (r"deed\s*no", "REGISTRATION_NUMBER"),
        (r"mutation", "MUTATION_NUMBER"),
        (r"owner", "OWNER_NAME"),
        (r"father", "FATHER_NAME"),
        (r"mother", "MOTHER_NAME"),
    ]

    for keyword, entity_type in keywords:
        words = [w for w in re.split(r'[\s\\\*\+\?]+', keyword) if w and not w.startswith('(')]
        if words and all(w in clean for w in words):
            return entity_type
    return None


def _rule_based_extract(
    text: str,
    language: str = "en",
    page: int = 1,
    bbox: list[float] | None = None,
) -> list[LandRecordEntity]:
    """Rule-based extraction of land-record entities from text."""
    entities: list[LandRecordEntity] = []
    patterns = _load_patterns(language)

    for pattern, base_confidence in patterns:
        try:
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if not value:
                    continue
                entity_type = _pattern_to_entity(pattern)
                if entity_type is None:
                    continue
                entity = LandRecordEntity(
                    entity_type=entity_type,
                    extracted_value=value,
                    source_text=match.group(0).strip(),
                    page=page,
                    bounding_box=bbox,
                    confidence=base_confidence,
                    extraction_method="rule",
                    language=language,
                )
                entities.append(entity)
        except Exception as exc:
            logger.warning("Rule extraction pattern error: %s", exc)

    # Deduplicate — first match wins for each entity type
    seen: set[str] = set()
    deduped: list[LandRecordEntity] = []
    for e in entities:
        if e.entity_type not in seen:
            seen.add(e.entity_type)
            deduped.append(e)
    return deduped


def _ner_based_extract(
    text: str,
    language: str = "en",
    page: int = 1,
    bbox: list[float] | None = None,
) -> list[LandRecordEntity]:
    """NER-based extraction using IndicNER model."""
    loader = _NERModelLoader()
    if not loader.is_available:
        return []
    if language not in loader._supported_languages:
        logger.warning("Language %s not supported by NER model", language)
        return []
    return []


def extract_entities(
    ocr_result_or_text: dict | str,
    language: str = "en",
) -> ExtractionResult:
    """Extract land-record entities from OCR results or plain text.

    Args:
        ocr_result_or_text: OCR output dict with "pages" key OR plain text string.
        language: Detected language code (e.g. 'en', 'hi', 'mr'). Used if string is passed.

    Returns:
        ExtractionResult with entities and status information.
    """
    if isinstance(ocr_result_or_text, str):
        lines = [line.strip() for line in ocr_result_or_text.split("\n") if line.strip()]
        blocks = [{"text": line, "bbox": None, "confidence": 1.0} for line in lines]
        ocr_result = {
            "pages": [{"page": 1, "blocks": blocks}],
            "method": "plain_text",
            "language": language,
        }
    else:
        ocr_result = ocr_result_or_text or {}

    pages = ocr_result.get("pages", [])
    method = ocr_result.get("method", "none")

    if not pages:
        return ExtractionResult(
            entities=[],
            status=ExtractionStatus(
                success=False, method="none",
                message="No pages in OCR result",
            ),
            error="No pages in OCR result",
        )

    # Collect all text per page
    all_text: list[tuple[int, list[tuple[str, list[float] | None]], int, int]] = []
    for page_data in pages:
        page_num = page_data.get("page", 1)
        width = page_data.get("width", 0)
        height = page_data.get("height", 0)
        raw_blocks = page_data.get("blocks", [])
        if not isinstance(raw_blocks, list):
            raw_blocks = []

        page_text_parts: list[tuple[str, list[float] | None]] = []
        for block in raw_blocks:
            if not isinstance(block, dict):
                continue
            raw_text = block.get("text", "")
            if raw_text is None:
                continue
            text = str(raw_text).strip()
            if not text:
                continue
            bbox = block.get("bbox")
            page_text_parts.append((text, bbox))

        if page_text_parts:
            all_text.append((page_num, page_text_parts, width, height))

    if not all_text:
        return ExtractionResult(
            entities=[],
            status=ExtractionStatus(
                success=False, method="none",
                message="No text found in OCR blocks",
            ),
            error="No text found in OCR blocks",
        )

    # Detect overall language
    full_text = "\n".join(
        text for _, parts, _, _ in all_text for text, _ in parts
    )
    language = _get_language(full_text)

    # Extract entities using rule-based approach
    all_entities: list[LandRecordEntity] = []
    for page_num, parts, width, height in all_text:
        for text, bbox in parts:
            entities = _rule_based_extract(text, language, page_num, bbox)
            all_entities.extend(entities)

    # Try NER extraction if model available
    loader = _NERModelLoader()
    ner_available = loader.is_available
    ner_entities: list[LandRecordEntity] = []

    if ner_available:
        for page_num, parts, width, height in all_text:
            for text, bbox in parts:
                ner_result = _ner_based_extract(text, language, page_num, bbox)
                ner_entities.extend(ner_result)

    # Merge: NER entities first, then rule-based for remaining types
    seen_types: set[str] = set()
    merged_entities: list[LandRecordEntity] = []

    for e in ner_entities:
        if e.entity_type not in seen_types:
            seen_types.add(e.entity_type)
            merged_entities.append(e)

    for e in all_entities:
        if e.entity_type not in seen_types:
            seen_types.add(e.entity_type)
            merged_entities.append(e)

    # Enrich all entities with multilingual normalization/transliteration/translation
    try:
        from app.services.multilingual_service import enrich_entity
        for entity in merged_entities:
            enrich_entity(entity)
    except Exception as exc:
        logger.warning("Multilingual enrichment error: %s", exc)

    # Determine extraction method
    if ner_available and merged_entities:
        extraction_method = "mixed"
        message = "NER model + rule-based extraction used."
    elif ner_available:
        extraction_method = "ner"
        message = "NER model available but no entities found."
    else:
        extraction_method = "rule"
        message = "NER model unavailable; rule-based extraction used. Configure IndicNER for improved accuracy."

    status = ExtractionStatus(
        success=len(merged_entities) > 0,
        method=extraction_method,
        message=message,
        model_available=ner_available,
        language_supported=True,
        entities_extracted=len(merged_entities),
    )

    return ExtractionResult(
        entities=merged_entities,
        status=status,
        language=language,
    )


def score_confidence(result: ExtractionResult) -> ExtractionResult:
    """Apply post-extraction confidence adjustments (no-op pass-through)."""
    return result


def get_nlp_status() -> dict:
    """Return status information for NLP services."""
    loader = _NERModelLoader()
    rule_languages = set(_LAND_RECORD_PATTERNS.keys())
    return {
        "ner_model_available": loader.is_available,
        "ner_model_name": loader._model_name if loader.is_available else None,
        "ner_init_error": loader.init_error,
        "rule_based_available": True,
        "rule_supported_languages": sorted(rule_languages),
        "indic_supported_languages": sorted(INDIC_LANGUAGES),
        "note": (
            "NER model (ai4bharat/IndicNER) is gated and requires authentication. "
            "Rule-based extraction works for all Indic languages."
        ),
    }


def extract_entities_from_text(
    text: str,
    language: str | None = None,
    page: int = 1,
) -> list[LandRecordEntity]:
    """Convenience: extract entities from raw text without full OCR result."""
    if language is None:
        language = _get_language(text)
    entities = _rule_based_extract(text, language, page)
    if entities:
        return entities
    return _rule_based_extract(text, "en", page)
