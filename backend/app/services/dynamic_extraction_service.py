"""Dynamic Field Extraction Service.

Replaces the fixed regex-pattern approach with document-aware field discovery.
Discovers labels, key-value pairs, tables, and entities from the actual
document text and OCR structure — not from a predefined field list.

Architecture:
  1. classify_document(text) → document type
  2. extract_key_value_pairs(text, ocr_pages) → dynamic fields from label:value patterns
  3. extract_table_fields(ocr_pages) → fields from table structures
  4. assign_canonical_key(field_name, language) → optional canonical mapping
  5. assign_data_type(field_name, field_value) → type detection
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DynamicField:
    """A single dynamically discovered field."""
    field_name: str
    field_value: str
    confidence: float = 0.85
    data_type: str = "string"
    page_number: int = 1
    bounding_box: list[float] | None = None
    source_text: str = ""
    extraction_method: str = "key_value_extraction"
    canonical_key: str | None = None
    language: str = "en"

    # Aliases for backward compatibility with LandRecordEntity
    @property
    def entity_type(self) -> str:
        return self.canonical_key or self.field_name

    @property
    def extracted_value(self) -> str:
        return self.field_value

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "field_value": self.field_value,
            "confidence": self.confidence,
            "data_type": self.data_type,
            "page_number": self.page_number,
            "bounding_box": self.bounding_box,
            "source_text": self.source_text,
            "extraction_method": self.extraction_method,
            "canonical_key": self.canonical_key,
            "language": self.language,
        }


@dataclass
class DynamicExtractionResult:
    """Result from the dynamic extraction pipeline."""
    fields: list[DynamicField] = field(default_factory=list)
    document_type: str = "Unknown"
    document_type_confidence: float = 0.0
    language: str = "en"
    error: str | None = None


# ---------------------------------------------------------------------------
# Document Classification
# ---------------------------------------------------------------------------

# Type keywords — order matters (check most specific first)
_DOC_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    ("Sale Deed", [
        r"sale\s*deed", r"conveyance\s*deed", r"विक्रय\s*पत्र", r"विक्रयदस्त",
        r"खरेदी\s*खत", r"seller", r"purchaser", r"buyer",
        r"consideration\s*amount", r"stamp\s*duty",
        r"previous\s*owner", r"new\s*owner", r"deed\s*number",
        r"sub[\-\s]*registrar",
    ]),
    ("Mutation Record", [
        r"mutation", r"dakhil\s*kharij", r"फेरफार", r"दाखिल\s*खारिज",
        r"transfer\s*of\s*ownership", r"mutation\s*no",
    ]),
    ("Lease Deed", [
        r"lease\s*deed", r"lessee", r"lessor", r"पट्टा",
        r"annual\s*rent", r"lease\s*period", r"tenancy",
    ]),
    ("Record of Rights", [
        r"record\s*of\s*rights", r"7/12", r"8A", r"jamabandi",
        r"अधिकार\s*अभिलेख", r"जमाबंदी", r"खतौनी",
        r"khasra", r"khatauni", r"khata", r"भूमिस्वामी",
    ]),
    ("Registration Document", [
        r"^registration\s*(?:office|department)",
        r"registry\s*office",
        r"नोंदणी", r"पंजीकरण",
    ]),
    ("Cadastral Record", [
        r"cadastr", r"survey\s*map", r"plot\s*map",
        r"bhunaksha", r"भूनक्शा",
    ]),
]


def classify_document(text: str) -> tuple[str, float]:
    """Classify document type from its OCR text.

    Returns (document_type, confidence).
    Falls back to 'Unknown' when no pattern matches.
    """
    if not text or len(text.strip()) < 10:
        return "Unknown", 0.0

    text_lower = text.lower()
    best_type = "Unknown"
    best_score = 0.0

    for doc_type, patterns in _DOC_TYPE_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, text_lower))
        if hits > 0:
            score = min(0.5 + (hits / len(patterns)) * 0.5, 0.99)
            if score > best_score:
                best_score = score
                best_type = doc_type

    logger.info("Document classification: type=%s confidence=%.2f", best_type, best_score)
    return best_type, best_score


# ---------------------------------------------------------------------------
# Key-Value Extraction — the core dynamic discovery engine
# ---------------------------------------------------------------------------

# Generic key-value separators
_KV_PATTERN = re.compile(
    r"^(.+?)\s*[:：\-–—=]\s*(.+)$",
    re.MULTILINE,
)

# Hindi/Marathi key-value (label followed by colon or next line)
_INDIC_KV_PATTERN = re.compile(
    r"^([\u0900-\u097F\s]{3,40})\s*[:：\-–—=]\s*(.+)$",
    re.MULTILINE,
)

# Multiline label-value: label on one line, value on next (indented or not)
_MULTILINE_KV = re.compile(
    r"^([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s.'/]{2,50})\s*[:：]?\s*$\n\s*(.{1,200})$",
    re.MULTILINE,
)

# Common noise labels to skip
_NOISE_LABELS = {
    "", "page", "date", "total", "rs", "no", "sr", "sl",
    "the", "and", "for", "this", "that", "with", "from",
}

# Labels that are too long or too short to be meaningful
_MIN_LABEL_LEN = 2
_MAX_LABEL_LEN = 80


def _is_valid_label(label: str) -> bool:
    """Check if a label is worth keeping."""
    stripped = label.strip().lower()
    if len(stripped) < _MIN_LABEL_LEN or len(stripped) > _MAX_LABEL_LEN:
        return False
    if stripped in _NOISE_LABELS:
        return False
    # Reject if it's all digits or punctuation
    if re.match(r"^[\d\s.,;:]+$", stripped):
        return False
    return True


def _is_valid_value(value: str) -> bool:
    """Check if a value is meaningful."""
    stripped = value.strip()
    if not stripped or len(stripped) > 500:
        return False
    return True


def _clean_label(label: str) -> str:
    """Clean up extracted label text."""
    label = label.strip()
    # Remove trailing colons, dashes, dots
    label = re.sub(r"[\s:：\-–—.]+$", "", label)
    # Remove leading serial numbers like "1." "a)"
    label = re.sub(r"^\d+[.)]\s*", "", label)
    return label.strip()


def _clean_value(value: str) -> str:
    """Clean up extracted value text."""
    value = value.strip()
    # Remove trailing newlines/excess whitespace
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_key_value_pairs(
    text: str,
    ocr_pages: list[dict] | None = None,
    language: str = "en",
) -> list[DynamicField]:
    """Discover key-value pairs from OCR text.

    Uses multiple strategies:
    1. Inline label:value patterns (Label: Value)
    2. Multiline label/value patterns (Label on one line, value on next)
    3. Block-level extraction from OCR blocks with proximity
    """
    fields: list[DynamicField] = []
    seen_labels: set[str] = set()

    if not text:
        return fields

    # -----------------------------------------------------------------------
    # Strategy 1: Inline key:value patterns
    # -----------------------------------------------------------------------
    for match in _KV_PATTERN.finditer(text):
        label = _clean_label(match.group(1))
        value = _clean_value(match.group(2))

        if not _is_valid_label(label) or not _is_valid_value(value):
            continue

        label_key = label.lower()
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)

        canonical = _lookup_canonical(label, language)
        dtype = _detect_data_type(label, value)

        fields.append(DynamicField(
            field_name=label,
            field_value=value,
            confidence=0.88,
            data_type=dtype,
            source_text=match.group(0).strip(),
            extraction_method="key_value_extraction",
            canonical_key=canonical,
            language=language,
        ))

    # -----------------------------------------------------------------------
    # Strategy 2: Indic script key:value
    # -----------------------------------------------------------------------
    for match in _INDIC_KV_PATTERN.finditer(text):
        label = _clean_label(match.group(1))
        value = _clean_value(match.group(2))

        if not _is_valid_label(label) or not _is_valid_value(value):
            continue

        label_key = label.lower()
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)

        canonical = _lookup_canonical(label, language)
        dtype = _detect_data_type(label, value)

        fields.append(DynamicField(
            field_name=label,
            field_value=value,
            confidence=0.85,
            data_type=dtype,
            source_text=match.group(0).strip(),
            extraction_method="key_value_extraction",
            canonical_key=canonical,
            language=language,
        ))

    # -----------------------------------------------------------------------
    # Strategy 3: Multiline label/value
    # -----------------------------------------------------------------------
    for match in _MULTILINE_KV.finditer(text):
        label = _clean_label(match.group(1))
        value = _clean_value(match.group(2))

        if not _is_valid_label(label) or not _is_valid_value(value):
            continue

        label_key = label.lower()
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)

        canonical = _lookup_canonical(label, language)
        dtype = _detect_data_type(label, value)

        fields.append(DynamicField(
            field_name=label,
            field_value=value,
            confidence=0.78,
            data_type=dtype,
            source_text=match.group(0).strip(),
            extraction_method="key_value_extraction",
            canonical_key=canonical,
            language=language,
        ))

    # -----------------------------------------------------------------------
    # Strategy 4: OCR-block-level proximity extraction
    # -----------------------------------------------------------------------
    if ocr_pages:
        block_fields = _extract_from_ocr_blocks(ocr_pages, language, seen_labels)
        fields.extend(block_fields)

    logger.info("Dynamic extraction discovered %d fields", len(fields))
    return fields


def _extract_from_ocr_blocks(
    ocr_pages: list[dict],
    language: str,
    seen_labels: set[str],
) -> list[DynamicField]:
    """Extract fields from OCR block structure using spatial proximity."""
    fields: list[DynamicField] = []

    for page_data in ocr_pages:
        page_num = page_data.get("page", 1)
        blocks = page_data.get("blocks", [])
        if not isinstance(blocks, list):
            continue

        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            block_text = str(block.get("text", "")).strip()
            if not block_text:
                continue

            # Check if this block is a label:value inline
            kv_match = re.match(r"^(.+?)\s*[:：\-–—=]\s*(.+)$", block_text)
            if kv_match:
                label = _clean_label(kv_match.group(1))
                value = _clean_value(kv_match.group(2))
                if _is_valid_label(label) and _is_valid_value(value):
                    label_key = label.lower()
                    if label_key not in seen_labels:
                        seen_labels.add(label_key)
                        canonical = _lookup_canonical(label, language)
                        fields.append(DynamicField(
                            field_name=label,
                            field_value=value,
                            confidence=min(block.get("confidence", 0.8), 0.95),
                            data_type=_detect_data_type(label, value),
                            page_number=page_num,
                            bounding_box=block.get("bbox"),
                            source_text=block_text,
                            extraction_method="key_value_extraction",
                            canonical_key=canonical,
                            language=language,
                        ))

    return fields


# ---------------------------------------------------------------------------
# Table Extraction
# ---------------------------------------------------------------------------

def extract_table_fields(
    text: str,
    ocr_pages: list[dict] | None = None,
    language: str = "en",
) -> list[DynamicField]:
    """Extract fields from table-like structures.

    Looks for rows with pipe separators or tab-separated columns.
    """
    fields: list[DynamicField] = []
    if not text:
        return fields

    lines = text.split("\n")

    # Find pipe-separated table rows
    table_rows: list[list[str]] = []
    for line in lines:
        if "|" in line and line.count("|") >= 2:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells and not all(re.match(r"^[-=]+$", c) for c in cells):
                table_rows.append(cells)

    if len(table_rows) >= 2:
        headers = table_rows[0]
        for row in table_rows[1:]:
            for j, cell in enumerate(row):
                if j < len(headers) and cell and not re.match(r"^\d+$", cell.strip()):
                    header = headers[j]
                    if _is_valid_label(header) and _is_valid_value(cell):
                        canonical = _lookup_canonical(header, language)
                        fields.append(DynamicField(
                            field_name=header,
                            field_value=cell.strip(),
                            confidence=0.80,
                            data_type=_detect_data_type(header, cell),
                            source_text=f"{header}: {cell}",
                            extraction_method="table_extraction",
                            canonical_key=canonical,
                            language=language,
                        ))

    return fields


# ---------------------------------------------------------------------------
# Canonical Key Mapping — optional, keeps both dynamic + standard
# ---------------------------------------------------------------------------

# Maps lowercase label keywords → canonical key
# Covers English, Hindi, Marathi labels
_CANONICAL_MAP: list[tuple[list[str], str]] = [
    (["survey no", "survey number", "s.no", "s no", "सर्वे नं", "सर्वे नंबर",
      "सर्व्हे नं", "भूमापन क्रमांक", "गट क्रमांक", "गट नं"], "SURVEY_NUMBER"),
    (["khasra", "khasra no", "खसरा", "खसरा नं", "खसरा संख्या"], "KHASRA_NUMBER"),
    (["khata", "khata no", "khata number", "खाता", "खाता संख्या", "खातेदार",
      "खाते क्रमांक", "खाते नं"], "KHATA_NUMBER"),
    (["plot no", "plot number", "p.no", "p no"], "PLOT_NUMBER"),
    (["village", "gram", "gaon", "गाँव", "ग्राम", "गांव", "मौजे", "गाव"], "VILLAGE"),
    (["tehsil", "taluka", "taluk", "तहसील", "तालुका"], "TEHSIL"),
    (["district", "dist", "zilla", "जिला", "जिल्हा"], "DISTRICT"),
    (["owner", "owner name", "owner's name", "malik", "मालिक", "मालिक का नाम",
      "भूमिस्वामी", "खातेदाराचे नाव", "मालकाचे नाव"], "OWNER_NAME"),
    (["father", "father's name", "father name", "s/o", "pitaji",
      "वडिलांचे नाव", "पिता"], "FATHER_NAME"),
    (["mother", "mother's name", "mother name", "w/o", "माता", "mataji"], "MOTHER_NAME"),
    (["area", "क्षेत्रफल", "क्षेत्र", "आकारणी", "hectare", "acre"], "AREA"),
    (["registration no", "reg no", "deed no", "document no",
      "नोंदणी", "दस्त"], "REGISTRATION_NUMBER"),
    (["mutation", "mutation no", "dakhil kharij", "फेरफार",
      "दाखिल खारिज"], "MUTATION_NUMBER"),
    (["registration date", "date of registration", "deed date",
      "दिनांक", "तारीख"], "REGISTRATION_DATE"),
    (["stamp duty", "stamp", "मुद्रांक शुल्क"], "STAMP_DUTY"),
    (["consideration", "consideration amount", "sale amount",
      "विक्रय मूल्य"], "CONSIDERATION_AMOUNT"),
    (["witness", "witness 1", "witness 2", "साक्षी", "गवाह"], None),  # No canonical — stays dynamic
    (["previous owner", "seller", "vendor", "विक्रेता"], "PREVIOUS_OWNER"),
    (["new owner", "purchaser", "buyer", "vendee", "क्रेता"], "NEW_OWNER"),
    (["lease", "lease no", "lease number", "पट्टा"], "LEASE_NUMBER"),
    (["lessee", "पट्टाधारक"], "LESSEE"),
    (["lessor", "पट्टादाता"], "LESSOR"),
    (["lease period", "पट्टा अवधि"], "LEASE_PERIOD"),
    (["annual rent", "rent", "वार्षिक किराया"], "ANNUAL_RENT"),
    (["property description", "property detail", "संपत्ति विवरण"], "PROPERTY_DESCRIPTION"),
]


def _lookup_canonical(label: str, language: str = "en") -> str | None:
    """Find the canonical key for a discovered label, if one exists.

    Returns None for labels without a known canonical mapping.
    Priority order:
      1. Learned label mappings (from human corrections)
      2. Hardcoded exact phrase match
      3. Hardcoded substring match
    """
    label_lower = label.lower().strip()

    # Check learned mappings first (highest priority — trained from corrections)
    try:
        from app.services.learning_service import get_learned_canonical_key
        learned = get_learned_canonical_key(label)
        if learned:
            logger.debug("Learned canonical mapping: %s → %s", label, learned)
            return learned
    except Exception:
        pass  # Learning service not available — fall through

    # Exact phrase match (hardcoded)
    for keywords, canonical_key in _CANONICAL_MAP:
        for kw in keywords:
            if kw == label_lower:
                return canonical_key

    # Substring match (lower priority)
    for keywords, canonical_key in _CANONICAL_MAP:
        for kw in keywords:
            if len(kw) >= 4 and kw in label_lower:
                return canonical_key

    return None  # Unknown field — stays dynamic


# ---------------------------------------------------------------------------
# Data Type Detection
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(
    r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$"
    r"|^\d{1,2}\s+\w+\s+\d{4}$"
)
_CURRENCY_RE = re.compile(r"(?:rs\.?|₹|inr)\s*[\d,]+", re.IGNORECASE)
_AREA_RE = re.compile(
    r"\d+\.?\d*\s*(?:hectare|acre|sq\.?\s*m|ha\.?|एकड़|हेक्टेयर|हेक्टर)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"^[\d,]+\.?\d*$")
_PERSON_KEYWORDS = {"name", "owner", "father", "mother", "witness", "seller", "buyer",
                    "purchaser", "vendor", "vendee", "lessee", "lessor",
                    "नाम", "नाव", "मालिक", "पिता", "माता"}
_IDENTIFIER_KEYWORDS = {"no", "number", "no.", "id", "code", "नं", "नंबर",
                        "संख्या", "क्रमांक"}


def _detect_data_type(label: str, value: str) -> str:
    """Infer the data type of a discovered field."""
    label_lower = label.lower()
    value = value.strip()

    # Check label-based hints first
    if any(kw in label_lower for kw in _PERSON_KEYWORDS):
        return "person"
    if any(kw in label_lower for kw in ("date", "दिनांक", "तारीख")):
        return "date"
    if any(kw in label_lower for kw in ("area", "क्षेत्रफल", "क्षेत्र", "hectare", "acre")):
        return "area"
    if any(kw in label_lower for kw in ("duty", "amount", "price", "rent", "मूल्य", "किराया", "शुल्क")):
        return "currency"
    if any(kw in label_lower for kw in ("village", "district", "tehsil", "taluka", "address",
                                         "गाव", "जिला", "जिल्हा", "तहसील", "तालुका", "पता")):
        return "address"

    # Check value-based detection
    if _DATE_RE.match(value):
        return "date"
    if _CURRENCY_RE.search(value):
        return "currency"
    if _AREA_RE.search(value):
        return "area"
    if _NUMBER_RE.match(value):
        if any(kw in label_lower for kw in _IDENTIFIER_KEYWORDS):
            return "identifier"
        return "decimal" if "." in value else "integer"

    return "string"


# ---------------------------------------------------------------------------
# Public API — main entry point for the pipeline
# ---------------------------------------------------------------------------

def extract_dynamic_fields(
    text: str,
    ocr_pages: list[dict] | None = None,
    language: str = "en",
) -> DynamicExtractionResult:
    """Full dynamic extraction pipeline.

    1. Classify document type
    2. Extract key-value pairs
    3. Extract table fields
    4. Assign canonical keys
    5. Assign data types
    6. Calculate confidence
    7. Apply learned OCR corrections and confidence adjustments

    Returns DynamicExtractionResult with all discovered fields.
    """
    # 1. Classify document
    doc_type, doc_type_conf = classify_document(text)

    # 2. Key-value extraction
    kv_fields = extract_key_value_pairs(text, ocr_pages, language)

    # 3. Table extraction
    table_fields = extract_table_fields(text, ocr_pages, language)

    # 4. Merge, deduplicate (kv wins over table for same label)
    seen: set[str] = {f.field_name.lower() for f in kv_fields}
    all_fields = list(kv_fields)
    for tf in table_fields:
        if tf.field_name.lower() not in seen:
            seen.add(tf.field_name.lower())
            all_fields.append(tf)

    # 5. Apply learned patterns from continuous learning
    all_fields = _apply_learned_improvements(all_fields)

    logger.info(
        "Dynamic extraction complete: type=%s fields=%d (kv=%d, table=%d)",
        doc_type, len(all_fields), len(kv_fields), len(table_fields),
    )

    return DynamicExtractionResult(
        fields=all_fields,
        document_type=doc_type,
        document_type_confidence=doc_type_conf,
        language=language,
    )


def _apply_learned_improvements(fields: list[DynamicField]) -> list[DynamicField]:
    """Apply learned OCR corrections and confidence adjustments from the learning system."""
    try:
        from app.services.learning_service import (
            apply_learned_ocr_corrections,
            apply_learned_confidence,
        )

        improved_count = 0
        for field in fields:
            # Apply learned OCR corrections
            if field.field_value:
                corrected = apply_learned_ocr_corrections(
                    field.field_name, field.field_value
                )
                if corrected and corrected != field.field_value:
                    logger.info(
                        "[LEARNING] OCR correction applied: %s = '%s' → '%s'",
                        field.field_name, field.field_value[:50], corrected[:50],
                    )
                    field.field_value = corrected
                    field.extraction_method = "key_value_extraction+learned_correction"
                    improved_count += 1

            # Apply learned confidence adjustments
            original_conf = field.confidence
            adjusted_conf = apply_learned_confidence(field.field_name, original_conf)
            if adjusted_conf != original_conf:
                field.confidence = adjusted_conf

        if improved_count > 0:
            logger.info("[LEARNING] Applied %d learned corrections", improved_count)

    except Exception as exc:
        logger.debug("[LEARNING] Could not apply learned improvements: %s", exc)

    return fields
