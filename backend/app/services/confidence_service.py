"""Confidence Scoring Service — categorize and flag extraction confidence levels.

Thresholds:
  HIGH      ≥ 0.85  — auto-accept
  MEDIUM    0.60–0.84 — review recommended
  LOW       0.30–0.59 — manual verification required
  UNCERTAIN < 0.30  — unreliable, likely needs re-extraction

Never invents confidence scores. Only categorizes values already produced
by OCR/extraction engines.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
THRESHOLD_HIGH = 0.85
THRESHOLD_MEDIUM = 0.60
THRESHOLD_LOW = 0.30


@dataclass
class FieldConfidence:
    """Confidence assessment for a single field."""
    field_name: str
    raw_score: float
    category: str          # HIGH | MEDIUM | LOW | UNCERTAIN
    needs_review: bool     # True when MEDIUM, LOW, or UNCERTAIN
    auto_accept: bool      # True only for HIGH


@dataclass
class DocumentConfidenceReport:
    """Confidence report for all fields in a document."""
    field_scores: list[FieldConfidence] = field(default_factory=list)
    overall_confidence: float = 0.0
    overall_category: str = "UNCERTAIN"
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    uncertain_count: int = 0
    flagged_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_confidence": round(self.overall_confidence, 4),
            "overall_category": self.overall_category,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "uncertain_count": self.uncertain_count,
            "flagged_fields": self.flagged_fields,
            "field_scores": [
                {
                    "field_name": fs.field_name,
                    "raw_score": round(fs.raw_score, 4),
                    "category": fs.category,
                    "needs_review": fs.needs_review,
                    "auto_accept": fs.auto_accept,
                }
                for fs in self.field_scores
            ],
        }


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def categorize_confidence(score: float) -> str:
    """Map a 0–1 confidence score to a human-readable category."""
    if score >= THRESHOLD_HIGH:
        return "HIGH"
    if score >= THRESHOLD_MEDIUM:
        return "MEDIUM"
    if score >= THRESHOLD_LOW:
        return "LOW"
    return "UNCERTAIN"


def score_field(field_name: str, raw_score: float | None) -> FieldConfidence:
    """Assess a single field's confidence level.

    If raw_score is None or missing, it is treated as UNCERTAIN (0.0).
    Applies learned confidence adjustments from the continuous learning system.
    """
    if raw_score is None or raw_score < 0:
        raw_score = 0.0

    # Apply learned confidence adjustments (penalize frequently-corrected fields)
    adjusted_score = raw_score
    try:
        from app.services.learning_service import apply_learned_confidence
        adjusted_score = apply_learned_confidence(field_name, raw_score)
    except Exception:
        pass  # Learning service not available — use raw score

    category = categorize_confidence(adjusted_score)
    needs_review = category in ("MEDIUM", "LOW", "UNCERTAIN")
    auto_accept = category == "HIGH"

    return FieldConfidence(
        field_name=field_name,
        raw_score=adjusted_score,
        category=category,
        needs_review=needs_review,
        auto_accept=auto_accept,
    )


def score_document_fields(fields: list[Any]) -> DocumentConfidenceReport:
    """Score all fields for a document and produce a confidence report.

    `fields` is a list of objects/dicts with at least `field_name` and
    `confidence` attributes.
    """
    report = DocumentConfidenceReport()

    scored: list[FieldConfidence] = []
    total_conf = 0.0

    for f in fields:
        name = getattr(f, "field_name", "") or getattr(f, "entity_type", "unknown")
        conf = getattr(f, "confidence", None)
        if conf is None and isinstance(f, dict):
            conf = f.get("confidence")
            name = f.get("field_name", name)

        fc = score_field(name, conf)
        scored.append(fc)
        total_conf += fc.raw_score

        if fc.category == "HIGH":
            report.high_count += 1
        elif fc.category == "MEDIUM":
            report.medium_count += 1
        elif fc.category == "LOW":
            report.low_count += 1
        else:
            report.uncertain_count += 1

        if fc.needs_review:
            report.flagged_fields.append(name)

    report.field_scores = scored

    if scored:
        report.overall_confidence = total_conf / len(scored)
    report.overall_category = categorize_confidence(report.overall_confidence)

    logger.info(
        "Confidence report: overall=%.2f (%s), H=%d M=%d L=%d U=%d, flagged=%d",
        report.overall_confidence, report.overall_category,
        report.high_count, report.medium_count,
        report.low_count, report.uncertain_count,
        len(report.flagged_fields),
    )
    return report
