"""Continuous AI Learning Service.

Learns from:
  1. Human corrections (PATCH on fields) → training data
  2. Verified documents (COMPLETED status) → auto-verified training data

Produces:
  - Label → canonical key mappings
  - OCR error correction patterns
  - Per-field confidence adjustments (penalize frequently-wrong fields)
  - Document-type → expected fields patterns

Architecture:
  - record_correction()        → stores a training sample
  - record_verified_document() → stores auto-verified samples
  - check_retrain_threshold()  → returns True when enough new samples
  - run_learning_cycle()       → train/test split, measure accuracy, deploy if improved
  - get_active_patterns()      → return currently deployed patterns
  - apply_learned_confidence() → adjust confidence based on correction history
  - get_learning_stats()       → dashboard statistics
"""
from __future__ import annotations

import logging
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RETRAIN_THRESHOLD = 10  # Trigger learning after this many new unused samples (low for prototype)
TEST_SPLIT_RATIO = 0.2  # 20% of samples held out for testing


# ---------------------------------------------------------------------------
# DB helper
# ---------------------------------------------------------------------------
def _get_db_session():
    from app.db.session import SessionLocal
    return SessionLocal()


# ---------------------------------------------------------------------------
# Record corrections (called from PATCH endpoint)
# ---------------------------------------------------------------------------
def record_correction(
    document_id: str,
    field_result_id: str | None,
    field_name: str,
    original_value: str | None,
    corrected_value: str | None,
    correction_type: str = "value_correction",
    canonical_key: str | None = None,
    document_type: str | None = None,
    language: str | None = None,
    ocr_confidence: float | None = None,
    extraction_method: str | None = None,
) -> dict:
    """Store a human correction as a training sample.

    Called when a user edits (PATCH), adds (POST), or deletes (DELETE) a field.
    """
    from app.models.training_sample import TrainingSample

    db = _get_db_session()
    try:
        sample = TrainingSample(
            document_id=uuid.UUID(str(document_id)),
            field_result_id=uuid.UUID(str(field_result_id)) if field_result_id else None,
            field_name=field_name,
            canonical_key=canonical_key,
            original_value=original_value,
            corrected_value=corrected_value,
            correction_type=correction_type,
            document_type=document_type,
            language=language,
            ocr_confidence=ocr_confidence,
            extraction_method=extraction_method,
            used_in_training=False,
        )
        db.add(sample)
        db.commit()

        logger.info(
            "[LEARNING] Recorded %s: field=%s, original=%s, corrected=%s, doc=%s",
            correction_type, field_name,
            (original_value or "")[:50], (corrected_value or "")[:50],
            document_id,
        )

        # Check if we should trigger learning
        should_learn = check_retrain_threshold(db)
        db.close()

        return {
            "status": "recorded",
            "correction_type": correction_type,
            "field_name": field_name,
            "should_trigger_learning": should_learn,
        }
    except Exception as exc:
        logger.error("[LEARNING] Failed to record correction: %s", exc)
        db.rollback()
        db.close()
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Record verified documents (called from pipeline)
# ---------------------------------------------------------------------------
def record_verified_document(document_id: str) -> int:
    """Auto-record all verified fields from a completed document as training data.

    Only records fields with HIGH confidence that passed validation.
    Returns number of samples recorded.
    """
    from app.models.document import Document
    from app.models.document_result import DocumentResult
    from app.models.training_sample import TrainingSample

    db = _get_db_session()
    count = 0
    try:
        doc = db.query(Document).filter(
            Document.id == uuid.UUID(str(document_id))
        ).first()
        if not doc:
            return 0

        # Only learn from documents that completed successfully
        if doc.status not in ("COMPLETED", "VERIFIED"):
            return 0

        results = db.query(DocumentResult).filter(
            DocumentResult.document_id == doc.id
        ).all()

        for r in results:
            # Only auto-verify fields with decent confidence and valid status
            confidence = r.confidence or 0.0
            if confidence < 0.70:
                continue
            if r.validation_status in ("invalid", "mismatch"):
                continue

            # Check if we already have a training sample for this field
            existing = db.query(TrainingSample).filter(
                TrainingSample.document_id == doc.id,
                TrainingSample.field_name == r.field_name,
            ).first()
            if existing:
                continue

            sample = TrainingSample(
                document_id=doc.id,
                field_result_id=r.id,
                field_name=r.field_name,
                canonical_key=r.canonical_key,
                original_value=r.field_value,
                corrected_value=r.field_value,  # Same as original (auto-verified)
                correction_type="auto_verified",
                document_type=doc.document_type,
                language=doc.detected_language,
                ocr_confidence=confidence,
                extraction_method=r.extraction_method,
                used_in_training=False,
            )
            db.add(sample)
            count += 1

        db.commit()
        logger.info(
            "[LEARNING] Auto-verified %d fields from document %s (type=%s)",
            count, document_id, doc.document_type,
        )
    except Exception as exc:
        logger.error("[LEARNING] Failed to record verified document: %s", exc)
        db.rollback()
    finally:
        db.close()

    return count


# ---------------------------------------------------------------------------
# Check retrain threshold
# ---------------------------------------------------------------------------
def check_retrain_threshold(db=None) -> bool:
    """Return True if enough new training samples have accumulated."""
    from app.models.training_sample import TrainingSample

    should_close = False
    if db is None:
        db = _get_db_session()
        should_close = True

    try:
        unused_count = db.query(TrainingSample).filter(
            TrainingSample.used_in_training == False  # noqa: E712
        ).count()
        return unused_count >= RETRAIN_THRESHOLD
    except Exception as exc:
        logger.warning("[LEARNING] Threshold check failed: %s", exc)
        return False
    finally:
        if should_close:
            db.close()


# ---------------------------------------------------------------------------
# Core Learning Cycle
# ---------------------------------------------------------------------------
def run_learning_cycle() -> dict:
    """Execute a full learning cycle.

    Steps:
      1. Collect all unused training samples
      2. Split into train (80%) and test (20%) sets
      3. Learn patterns from training set
      4. Measure accuracy on test set BEFORE applying new patterns
      5. Measure accuracy on test set AFTER applying new patterns
      6. Deploy only if accuracy improves (no regressions)
      7. Mark samples as used, save snapshot

    Returns a summary dict.
    """
    from app.models.training_sample import TrainingSample
    from app.models.learning_model import LearningSnapshot

    db = _get_db_session()
    try:
        # 1. Collect unused samples
        unused_samples = db.query(TrainingSample).filter(
            TrainingSample.used_in_training == False  # noqa: E712
        ).all()

        if len(unused_samples) < 3:
            return {
                "status": "skipped",
                "reason": f"Only {len(unused_samples)} unused samples (need >= 3)",
            }

        logger.info("[LEARNING] Starting learning cycle with %d new samples", len(unused_samples))

        # 2. Split into train/test
        import random
        random.shuffle(unused_samples)
        split_idx = max(1, int(len(unused_samples) * (1 - TEST_SPLIT_RATIO)))
        train_samples = unused_samples[:split_idx]
        test_samples = unused_samples[split_idx:] if split_idx < len(unused_samples) else unused_samples[-1:]

        logger.info("[LEARNING] Train=%d, Test=%d", len(train_samples), len(test_samples))

        # 3. Get current active patterns (before learning)
        current_patterns = get_active_patterns(db)

        # 4. Measure accuracy BEFORE on test set
        accuracy_before = _measure_accuracy(test_samples, current_patterns)
        logger.info("[LEARNING] Accuracy BEFORE: %.4f", accuracy_before)

        # 5. Learn new patterns from training set
        new_patterns = _learn_patterns(train_samples, current_patterns)

        # 6. Measure accuracy AFTER on test set
        accuracy_after = _measure_accuracy(test_samples, new_patterns)
        logger.info("[LEARNING] Accuracy AFTER: %.4f", accuracy_after)

        improvement = accuracy_after - accuracy_before

        # 7. Determine next version
        latest = db.query(LearningSnapshot).order_by(
            LearningSnapshot.version.desc()
        ).first()
        next_version = (latest.version + 1) if latest else 1

        # Deploy if improved or first version
        should_deploy = accuracy_after >= accuracy_before or next_version == 1

        if should_deploy and latest:
            # Undeploy previous version
            latest.deployed = False

        snapshot = LearningSnapshot(
            version=next_version,
            training_samples_count=len(train_samples),
            patterns_json=new_patterns,
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after,
            improvement_delta=improvement,
            deployed=should_deploy,
            deployment_notes=(
                f"Deployed: improvement={improvement:+.4f}"
                if should_deploy
                else f"Rejected: regression={improvement:+.4f}"
            ),
        )
        db.add(snapshot)

        # Mark samples as used
        for s in unused_samples:
            s.used_in_training = True
            s.dataset_version = next_version

        db.commit()

        result = {
            "status": "deployed" if should_deploy else "rejected",
            "version": next_version,
            "training_samples": len(train_samples),
            "test_samples": len(test_samples),
            "accuracy_before": round(accuracy_before, 4),
            "accuracy_after": round(accuracy_after, 4),
            "improvement_delta": round(improvement, 4),
            "patterns_learned": {
                "label_mappings": len(new_patterns.get("label_mappings", {})),
                "ocr_corrections": len(new_patterns.get("ocr_corrections", {})),
                "confidence_adjustments": len(new_patterns.get("confidence_adjustments", {})),
                "doctype_fields": len(new_patterns.get("doctype_fields", {})),
            },
        }
        logger.info("[LEARNING] Cycle complete: %s", result)
        return result

    except Exception as exc:
        logger.error("[LEARNING] Learning cycle failed: %s", exc, exc_info=True)
        db.rollback()
        return {"status": "error", "error": str(exc)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Learn patterns from training samples
# ---------------------------------------------------------------------------
def _learn_patterns(samples: list, current_patterns: dict) -> dict:
    """Derive patterns from training samples.

    Learns:
      - label_mappings: field_name → canonical_key (from corrections that added canonical keys)
      - ocr_corrections: original_value → corrected_value char-level patterns
      - confidence_adjustments: field_name → penalty/boost based on correction frequency
      - doctype_fields: document_type → list of expected field names
    """
    # Start from current patterns (cumulative learning)
    patterns = {
        "label_mappings": dict(current_patterns.get("label_mappings", {})),
        "ocr_corrections": dict(current_patterns.get("ocr_corrections", {})),
        "confidence_adjustments": dict(current_patterns.get("confidence_adjustments", {})),
        "doctype_fields": dict(current_patterns.get("doctype_fields", {})),
        "correction_counts": dict(current_patterns.get("correction_counts", {})),
        "field_accuracy_rates": dict(current_patterns.get("field_accuracy_rates", {})),
    }

    # Track correction frequency per field
    field_corrections: Counter = Counter()
    field_total: Counter = Counter()
    doctype_field_sets: dict[str, set] = defaultdict(set)

    for sample in samples:
        field_total[sample.field_name] += 1

        # Learn label → canonical key mappings
        if sample.canonical_key and sample.field_name:
            label_lower = sample.field_name.strip().lower()
            patterns["label_mappings"][label_lower] = sample.canonical_key

        # Learn OCR corrections
        if (
            sample.correction_type == "value_correction"
            and sample.original_value
            and sample.corrected_value
            and sample.original_value != sample.corrected_value
        ):
            field_corrections[sample.field_name] += 1

            # Store commonly seen corrections
            orig = sample.original_value.strip()
            corr = sample.corrected_value.strip()
            if len(orig) < 200 and len(corr) < 200:
                key = f"{sample.field_name}::{orig}"
                patterns["ocr_corrections"][key] = corr

        # Learn document-type → field patterns
        if sample.document_type and sample.document_type != "Unknown":
            doctype_field_sets[sample.document_type].add(sample.field_name)

    # Calculate confidence adjustments
    for field_name in field_total:
        total = field_total[field_name]
        corrections = field_corrections.get(field_name, 0)
        accuracy_rate = 1.0 - (corrections / total) if total > 0 else 1.0

        # Penalize fields that are frequently corrected
        # If 50% of samples for a field were corrections, penalty = -0.15
        penalty = 0.0
        if corrections > 0 and total >= 2:
            correction_ratio = corrections / total
            penalty = -0.30 * correction_ratio  # Max -0.30 penalty

        patterns["confidence_adjustments"][field_name] = round(penalty, 4)
        patterns["field_accuracy_rates"][field_name] = round(accuracy_rate, 4)
        patterns["correction_counts"][field_name] = {
            "total": total,
            "corrections": corrections,
            "accuracy": round(accuracy_rate, 4),
        }

    # Merge doctype fields (cumulative)
    for dt, fields in doctype_field_sets.items():
        existing = set(patterns["doctype_fields"].get(dt, []))
        existing.update(fields)
        patterns["doctype_fields"][dt] = sorted(existing)

    logger.info(
        "[LEARNING] Learned: %d label mappings, %d OCR corrections, %d confidence adjustments, %d doctype patterns",
        len(patterns["label_mappings"]),
        len(patterns["ocr_corrections"]),
        len(patterns["confidence_adjustments"]),
        len(patterns["doctype_fields"]),
    )
    return patterns


# ---------------------------------------------------------------------------
# Measure accuracy on test set
# ---------------------------------------------------------------------------
def _measure_accuracy(test_samples: list, patterns: dict) -> float:
    """Measure how well patterns predict test sample corrections.

    For value_correction samples:
      - Check if OCR corrections would have caught the error
    For auto_verified samples:
      - Check if confidence adjustment would NOT reject this field
    For all:
      - Check if label mapping matches canonical key

    Returns accuracy 0.0–1.0.
    """
    if not test_samples:
        return 0.5  # No data — neutral

    correct = 0
    total = 0

    label_map = patterns.get("label_mappings", {})
    ocr_corr = patterns.get("ocr_corrections", {})

    for sample in test_samples:
        total += 1

        if sample.correction_type == "auto_verified":
            # Verified fields should NOT be penalized below threshold
            adj = patterns.get("confidence_adjustments", {}).get(sample.field_name, 0.0)
            base_conf = sample.ocr_confidence or 0.85
            adjusted = base_conf + adj
            if adjusted >= 0.5:  # Would still pass
                correct += 1

        elif sample.correction_type == "value_correction":
            # Check if OCR correction map would fix this
            key = f"{sample.field_name}::{sample.original_value or ''}"
            predicted = ocr_corr.get(key)
            if predicted == sample.corrected_value:
                correct += 1
            # Partial credit: at least the canonical key mapping is right
            elif sample.canonical_key:
                label_lower = sample.field_name.strip().lower()
                if label_map.get(label_lower) == sample.canonical_key:
                    correct += 0.5

        elif sample.correction_type == "field_added":
            # We learn that this field should exist for this doc type
            dt = sample.document_type
            if dt and dt in patterns.get("doctype_fields", {}):
                if sample.field_name in patterns["doctype_fields"][dt]:
                    correct += 1

        else:
            # field_deleted or other — count as correct if patterns don't predict it
            correct += 0.5

    return correct / total if total > 0 else 0.5


# ---------------------------------------------------------------------------
# Get active deployed patterns
# ---------------------------------------------------------------------------
def get_active_patterns(db=None) -> dict:
    """Return the currently deployed learned patterns.

    Returns empty patterns dict if no snapshot is deployed.
    """
    from app.models.learning_model import LearningSnapshot

    should_close = False
    if db is None:
        db = _get_db_session()
        should_close = True

    try:
        snapshot = db.query(LearningSnapshot).filter(
            LearningSnapshot.deployed == True  # noqa: E712
        ).order_by(LearningSnapshot.version.desc()).first()

        if snapshot and snapshot.patterns_json:
            return snapshot.patterns_json
        return {
            "label_mappings": {},
            "ocr_corrections": {},
            "confidence_adjustments": {},
            "doctype_fields": {},
            "correction_counts": {},
            "field_accuracy_rates": {},
        }
    except Exception as exc:
        logger.warning("[LEARNING] Failed to load active patterns: %s", exc)
        return {
            "label_mappings": {},
            "ocr_corrections": {},
            "confidence_adjustments": {},
            "doctype_fields": {},
            "correction_counts": {},
            "field_accuracy_rates": {},
        }
    finally:
        if should_close:
            db.close()


# ---------------------------------------------------------------------------
# Apply learned confidence adjustments
# ---------------------------------------------------------------------------
def apply_learned_confidence(field_name: str, raw_confidence: float) -> float:
    """Adjust a field's confidence based on historical correction rates.

    If a field is frequently corrected, its confidence is penalized.
    Returns adjusted confidence (clamped 0.0–1.0).
    """
    try:
        patterns = get_active_patterns()
        adjustment = patterns.get("confidence_adjustments", {}).get(field_name, 0.0)
        adjusted = raw_confidence + adjustment
        return max(0.0, min(1.0, adjusted))
    except Exception:
        return raw_confidence


# ---------------------------------------------------------------------------
# Apply learned OCR corrections
# ---------------------------------------------------------------------------
def apply_learned_ocr_corrections(field_name: str, value: str) -> str | None:
    """Check if we have a learned correction for this field+value combination.

    Returns the corrected value if found, otherwise None.
    """
    try:
        patterns = get_active_patterns()
        ocr_corrections = patterns.get("ocr_corrections", {})
        key = f"{field_name}::{value.strip()}"
        return ocr_corrections.get(key)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Get learned canonical key for a label
# ---------------------------------------------------------------------------
def get_learned_canonical_key(field_name: str) -> str | None:
    """Check if the learning system has a canonical key mapping for this label.

    Returns the canonical key if found, otherwise None.
    """
    try:
        patterns = get_active_patterns()
        label_lower = field_name.strip().lower()
        return patterns.get("label_mappings", {}).get(label_lower)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Learning Statistics (for dashboard)
# ---------------------------------------------------------------------------
def get_learning_stats() -> dict:
    """Return comprehensive learning statistics for the dashboard."""
    from app.models.training_sample import TrainingSample
    from app.models.learning_model import LearningSnapshot

    db = _get_db_session()
    try:
        total_samples = db.query(TrainingSample).count()
        unused_samples = db.query(TrainingSample).filter(
            TrainingSample.used_in_training == False  # noqa: E712
        ).count()

        # Correction type breakdown
        correction_counts = {}
        for ct in ("value_correction", "field_added", "field_deleted", "auto_verified"):
            correction_counts[ct] = db.query(TrainingSample).filter(
                TrainingSample.correction_type == ct
            ).count()

        # Most frequently corrected fields
        corrections_only = db.query(TrainingSample).filter(
            TrainingSample.correction_type == "value_correction"
        ).all()
        field_counter: Counter = Counter()
        for s in corrections_only:
            field_counter[s.field_name] += 1
        frequently_corrected = field_counter.most_common(10)

        # Document type distribution
        doctype_counter: Counter = Counter()
        all_samples = db.query(TrainingSample).all()
        for s in all_samples:
            if s.document_type:
                doctype_counter[s.document_type] += 1

        # Version history
        snapshots = db.query(LearningSnapshot).order_by(
            LearningSnapshot.version.desc()
        ).limit(10).all()

        active_snapshot = None
        version_history = []
        for snap in snapshots:
            entry = {
                "version": snap.version,
                "training_samples_count": snap.training_samples_count,
                "accuracy_before": snap.accuracy_before,
                "accuracy_after": snap.accuracy_after,
                "improvement_delta": snap.improvement_delta,
                "deployed": snap.deployed,
                "deployment_notes": snap.deployment_notes,
                "created_at": snap.created_at.isoformat() if snap.created_at else None,
            }
            version_history.append(entry)
            if snap.deployed:
                active_snapshot = entry

        # Active patterns summary
        active_patterns = get_active_patterns(db)
        patterns_summary = {
            "label_mappings_count": len(active_patterns.get("label_mappings", {})),
            "ocr_corrections_count": len(active_patterns.get("ocr_corrections", {})),
            "confidence_adjustments_count": len(active_patterns.get("confidence_adjustments", {})),
            "doctype_patterns_count": len(active_patterns.get("doctype_fields", {})),
        }

        return {
            "total_training_samples": total_samples,
            "unused_samples": unused_samples,
            "retrain_threshold": RETRAIN_THRESHOLD,
            "ready_to_learn": unused_samples >= RETRAIN_THRESHOLD,
            "correction_type_breakdown": correction_counts,
            "frequently_corrected_fields": [
                {"field_name": f, "correction_count": c}
                for f, c in frequently_corrected
            ],
            "document_type_distribution": dict(doctype_counter),
            "active_version": active_snapshot,
            "version_history": version_history,
            "patterns_summary": patterns_summary,
            "field_accuracy_rates": active_patterns.get("field_accuracy_rates", {}),
        }
    except Exception as exc:
        logger.error("[LEARNING] Failed to get stats: %s", exc)
        return {
            "total_training_samples": 0,
            "unused_samples": 0,
            "retrain_threshold": RETRAIN_THRESHOLD,
            "ready_to_learn": False,
            "error": str(exc),
        }
    finally:
        db.close()
