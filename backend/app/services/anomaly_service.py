"""Anomaly Detection Service using scikit-learn IsolationForest.

Purpose:
  Identify potentially suspicious or unusual land-record records.

IMPORTANT DISCLAIMER:
  IsolationForest MUST NOT determine legal ownership or declare fraud.
  It only produces an anomaly/risk signal for human verification.

Feature-building layer workflow:
  structured record
        ↓
  feature vector
        ↓
  IsolationForest
        ↓
  anomaly score
        ↓
  risk classification

Storage / Return output fields:
  - anomaly_score
  - raw_decision_score
  - anomaly_flag
  - risk_classification
  - model_version
  - features_used
  - created_at
  - is_synthetic_model
  - disclaimer
  - notes
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Disclaimers
# ---------------------------------------------------------------------------

DISCLAIMER_TEXT: str = (
    "This anomaly signal is generated automatically for human verification only. "
    "It does NOT determine legal ownership or declare fraud."
)

MODEL_VERSION_DEFAULT: str = "v1.0.0-synthetic-sih"
DEFAULT_THRESHOLD: float = 0.5
MIN_TRAINING_SAMPLES: int = 10

FEATURE_NAMES: List[str] = [
    "area",
    "number_of_owners",
    "mutation_frequency",
    "numeric_field_consistency",
    "unusual_area_values",
    "unusual_record_patterns",
]

# ---------------------------------------------------------------------------
# Data Models / Schemas
# ---------------------------------------------------------------------------

@dataclass
class LandRecordInput:
    """Structured representation of a land record for anomaly feature building."""

    area: Optional[Union[float, int, str]] = None
    number_of_owners: Optional[Union[int, float, str]] = None
    mutation_frequency: Optional[Union[float, int, str]] = None
    numeric_field_consistency: Optional[float] = None
    unusual_area_values: Optional[float] = None
    unusual_record_patterns: Optional[float] = None
    
    # Additional raw fields / metadata dictionary for dynamic extraction
    raw_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyResult:
    """Standard output result of anomaly detection analysis."""

    anomaly_score: float  # Normalized risk score between 0.0 (normal) and 1.0 (anomalous)
    raw_decision_score: float  # Raw IsolationForest decision_function value
    anomaly_flag: bool  # True if anomaly_score >= configurable threshold
    risk_classification: str  # "LOW", "MEDIUM", "HIGH"
    model_version: str
    features_used: Dict[str, float]
    created_at: str  # ISO 8601 string
    is_synthetic_model: bool = True
    disclaimer: str = DISCLAIMER_TEXT
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to JSON-serializable dictionary."""
        return {
            "anomaly_score": round(self.anomaly_score, 4),
            "raw_decision_score": round(self.raw_decision_score, 4),
            "anomaly_flag": self.anomaly_flag,
            "risk_classification": self.risk_classification,
            "model_version": self.model_version,
            "features_used": {k: round(v, 4) for k, v in self.features_used.items()},
            "created_at": self.created_at,
            "is_synthetic_model": self.is_synthetic_model,
            "disclaimer": self.disclaimer,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Feature Extraction Layer (Structured Record → Feature Vector)
# ---------------------------------------------------------------------------

def parse_number(val: Any) -> Optional[float]:
    """Safely convert string/number to float. Returns None if malformed or missing."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, str):
        cleaned = re.sub(r"[^\d.\-]", "", val)
        if not cleaned:
            return None
        try:
            num = float(cleaned)
            if math.isnan(num) or math.isinf(num):
                return None
            return num
        except ValueError:
            return None
    return None


def extract_features(
    record: Union[LandRecordInput, Dict[str, Any], List[Any]]
) -> Tuple[np.ndarray, Dict[str, float], List[str]]:
    """Convert a structured land record into a normalized 1D numeric feature vector.
    
    Accepts LandRecordInput, dict, or list of ExtractedField items.
    
    Returns:
      - feature_vector: 1D numpy array of shape (6,)
      - features_used: dict mapping feature name to numeric value
      - extraction_notes: list of warnings/notes encountered during feature extraction
    """
    notes: List[str] = []
    
    # Standardize input to dict representation
    data: Dict[str, Any] = {}
    if isinstance(record, LandRecordInput):
        data = {
            "area": record.area,
            "number_of_owners": record.number_of_owners,
            "mutation_frequency": record.mutation_frequency,
            "numeric_field_consistency": record.numeric_field_consistency,
            "unusual_area_values": record.unusual_area_values,
            "unusual_record_patterns": record.unusual_record_patterns,
        }
        if record.raw_fields:
            data.update(record.raw_fields)
    elif isinstance(record, dict):
        data = dict(record)
    elif isinstance(record, list):
        # Support list of LandRecordEntity / ExtractedField / dict objects from NLP/validation services
        for item in record:
            if hasattr(item, "field_name") and hasattr(item, "field_value"):
                data[getattr(item, "field_name")] = getattr(item, "field_value")
            elif hasattr(item, "entity_type") and hasattr(item, "extracted_value"):
                name = str(getattr(item, "entity_type")).lower()
                data[name] = getattr(item, "extracted_value")
            elif isinstance(item, dict):
                key = item.get("field_name") or item.get("entity_type", "").lower()
                val = item.get("field_value") or item.get("extracted_value")
                if key:
                    data[key] = val

    # 1. Feature: Area (standardized area in hectares)
    area_val = parse_number(data.get("area"))
    if area_val is None:
        # Check alternative keys
        for k in ("area_hectares", "area_acres", "area_sqm", "land_area"):
            if k in data and parse_number(data[k]) is not None:
                parsed = parse_number(data[k])
                if k == "area_sqm" and parsed is not None:
                    area_val = parsed / 10000.0  # convert sqm to hectares
                elif k == "area_acres" and parsed is not None:
                    area_val = parsed * 0.404686  # convert acres to hectares
                else:
                    area_val = parsed
                break
                
    f_area: float = 0.0
    if area_val is None:
        notes.append("Missing area value; defaulted to 0.0")
        f_area = 0.0
    elif area_val < 0:
        notes.append(f"Negative area detected ({area_val}); flagged in features")
        f_area = -1.0
    else:
        # Log scale area to prevent extreme magnitude distortion while preserving rank
        f_area = float(np.log1p(area_val))

    # 2. Feature: Number of Owners
    owners_val = parse_number(data.get("number_of_owners"))
    if owners_val is None:
        for k in ("owner_count", "owners", "num_owners", "owners_count"):
            if k in data and parse_number(data[k]) is not None:
                owners_val = parse_number(data[k])
                break
    
    # Infer from list of owner names if provided as text/list
    if owners_val is None:
        owners_list = data.get("owners_list") or data.get("owner_names")
        if isinstance(owners_list, list):
            owners_val = float(len(owners_list))
        elif isinstance(data.get("owner_name"), str):
            # Count commas or 'and' in owner_name
            owner_str = data["owner_name"]
            parts = re.split(r"[,;&]|\band\b", owner_str, flags=re.IGNORECASE)
            owners_val = float(len([p for p in parts if p.strip()]))

    f_owners: float = 1.0
    if owners_val is None or owners_val <= 0:
        notes.append("Missing or non-positive owner count; defaulted to 1.0")
        f_owners = 1.0
    else:
        f_owners = float(owners_val)

    # 3. Feature: Mutation Frequency
    mut_val = parse_number(data.get("mutation_frequency"))
    if mut_val is None:
        for k in ("mutation_count", "mutations", "mutations_per_year"):
            if k in data and parse_number(data[k]) is not None:
                mut_val = parse_number(data[k])
                break
                
    f_mutation_freq: float = 0.0
    if mut_val is None or mut_val < 0:
        f_mutation_freq = 0.0
    else:
        f_mutation_freq = float(mut_val)

    # 4. Feature: Numeric Field Consistency (1.0 = highly consistent, 0.0 = inconsistent)
    f_consistency: float = 1.0
    if data.get("numeric_field_consistency") is not None:
        parsed_cons = parse_number(data.get("numeric_field_consistency"))
        if parsed_cons is not None:
            f_consistency = max(0.0, min(1.0, parsed_cons))
    else:
        # Heuristic consistency check based on available fields
        penalty = 0.0
        if area_val is not None and area_val <= 0:
            penalty += 0.5
        if owners_val is not None and owners_val > 100:  # Excessive owners ratio
            penalty += 0.3
        mv = parse_number(data.get("market_value"))
        sd = parse_number(data.get("stamp_duty"))
        if mv is not None and mv < 0:
            penalty += 0.4
        if sd is not None and sd < 0:
            penalty += 0.4
        f_consistency = float(max(0.0, 1.0 - penalty))

    # 5. Feature: Unusual Area Values Indicator (0.0 = normal range, 1.0 = extreme anomaly)
    f_unusual_area: float = 0.0
    if data.get("unusual_area_values") is not None:
        parsed_ua = parse_number(data.get("unusual_area_values"))
        if parsed_ua is not None:
            f_unusual_area = max(0.0, min(1.0, parsed_ua))
    else:
        if area_val is None:
            f_unusual_area = 0.3  # Missing area is moderately unusual
        elif area_val <= 0:
            f_unusual_area = 1.0  # Zero or negative area is extreme anomaly
        elif area_val > 1000.0:  # Unusually large plot > 1,000 ha
            f_unusual_area = 0.9
        elif area_val < 0.0001:  # Microscopic plot < 1 sqm
            f_unusual_area = 0.7
        else:
            f_unusual_area = 0.0

    # 6. Feature: Unusual Record Patterns (0.0 = normal pattern, 1.0 = high structural anomaly)
    f_unusual_patterns: float = 0.0
    if data.get("unusual_record_patterns") is not None:
        parsed_up = parse_number(data.get("unusual_record_patterns"))
        if parsed_up is not None:
            f_unusual_patterns = max(0.0, min(1.0, parsed_up))
    else:
        pattern_score = 0.0
        # Check duplicate owner/co-owner
        owner = str(data.get("owner_name", "")).strip().lower()
        co_owner = str(data.get("co_owner_name", "")).strip().lower()
        if owner and co_owner and owner == co_owner:
            pattern_score += 0.4
            notes.append("Owner and co-owner names are identical")
            
        # Check future date
        reg_date = str(data.get("registration_date", ""))
        if "future" in reg_date.lower() or "209" in reg_date or "2100" in reg_date:
            pattern_score += 0.5
            notes.append("Suspicious registration date")

        # Check high mutation frequency (> 10 mutations)
        if f_mutation_freq > 10:
            pattern_score += 0.4
            notes.append(f"Unusually high mutation frequency ({f_mutation_freq})")

        f_unusual_patterns = float(min(1.0, pattern_score))

    features_used: Dict[str, float] = {
        "area": f_area,
        "number_of_owners": f_owners,
        "mutation_frequency": f_mutation_freq,
        "numeric_field_consistency": f_consistency,
        "unusual_area_values": f_unusual_area,
        "unusual_record_patterns": f_unusual_patterns,
    }

    feature_vector = np.array(
        [
            f_area,
            f_owners,
            f_mutation_freq,
            f_consistency,
            f_unusual_area,
            f_unusual_patterns,
        ],
        dtype=np.float64,
    )

    return feature_vector, features_used, notes


# ---------------------------------------------------------------------------
# Synthetic Dataset Generator for SIH Prototype
# ---------------------------------------------------------------------------

def generate_synthetic_training_data(
    n_samples: int = 500,
    anomaly_ratio: float = 0.05,
    random_seed: int = 42,
) -> np.ndarray:
    """Generate a clean synthetic dataset for training/demoing the SIH prototype.
    
    NOTE: This is synthetic sample data for demonstration/prototype testing.
          It must be replaced with government-approved real-world dataset when available.
    """
    rng = np.random.RandomState(random_seed)
    n_anomalies = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomalies

    # 1. Normal records distribution
    normal_areas = np.log1p(rng.uniform(0.1, 20.0, size=n_normal))  # areas 0.1 to 20 ha
    normal_owners = rng.choice([1, 2, 3, 4], size=n_normal, p=[0.5, 0.3, 0.15, 0.05])
    normal_mutations = rng.poisson(lam=0.8, size=n_normal)
    normal_consistency = rng.uniform(0.9, 1.0, size=n_normal)
    normal_unusual_area = np.zeros(n_normal)
    normal_unusual_patterns = rng.uniform(0.0, 0.1, size=n_normal)

    normal_data = np.column_stack([
        normal_areas,
        normal_owners,
        normal_mutations,
        normal_consistency,
        normal_unusual_area,
        normal_unusual_patterns,
    ])

    # 2. Anomalous records distribution
    anom_areas = rng.choice([0.0, -1.0, np.log1p(15000.0)], size=n_anomalies)
    anom_owners = rng.choice([0, 50, 120], size=n_anomalies)
    anom_mutations = rng.uniform(15, 50, size=n_anomalies)
    anom_consistency = rng.uniform(0.0, 0.3, size=n_anomalies)
    anom_unusual_area = rng.choice([0.8, 1.0], size=n_anomalies)
    anom_unusual_patterns = rng.uniform(0.6, 1.0, size=n_anomalies)

    anomaly_data = np.column_stack([
        anom_areas,
        anom_owners,
        anom_mutations,
        anom_consistency,
        anom_unusual_area,
        anom_unusual_patterns,
    ])

    dataset = np.vstack([normal_data, anomaly_data])
    rng.shuffle(dataset)
    return dataset


# ---------------------------------------------------------------------------
# IsolationForest Anomaly Detector Class
# ---------------------------------------------------------------------------

class IsolationForestAnomalyDetector:
    """IsolationForest wrapper tailored for land record anomaly detection."""

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
        model_version: str = MODEL_VERSION_DEFAULT,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model_version = model_version
        self.is_synthetic_model: bool = True
        self.is_fitted: bool = False
        
        self._model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
        )

    def fit(
        self,
        training_data: Optional[np.ndarray] = None,
        is_synthetic: bool = True,
    ) -> IsolationForestAnomalyDetector:
        """Fit the IsolationForest model.
        
        If training_data is None, uses synthetic sample training data for the SIH prototype.
        """
        if training_data is None:
            logger.info("No training dataset supplied; generating synthetic sample dataset for prototype")
            training_data = generate_synthetic_training_data(
                n_samples=500, anomaly_ratio=self.contamination, random_seed=self.random_state
            )
            self.is_synthetic_model = True
        else:
            self.is_synthetic_model = is_synthetic

        if len(training_data) < MIN_TRAINING_SAMPLES:
            raise ValueError(
                f"Insufficient training data: received {len(training_data)} samples, "
                f"minimum required is {MIN_TRAINING_SAMPLES}"
            )

        self._model.fit(training_data)
        self.is_fitted = True
        logger.info(
            "IsolationForest fitted successfully with %d samples (synthetic=%s, version=%s)",
            len(training_data),
            self.is_synthetic_model,
            self.model_version,
        )
        return self

    def predict_record(
        self,
        record: Union[LandRecordInput, Dict[str, Any], List[Any]],
        anomaly_threshold: float = DEFAULT_THRESHOLD,
    ) -> AnomalyResult:
        """Predict anomaly score and risk classification for a single record.
        
        This method will NEVER raise an exception; if an error occurs, it catches it
        and returns a safe default AnomalyResult with warning notes.
        """
        created_at_iso = datetime.now(timezone.utc).isoformat()
        notes: List[str] = []

        try:
            if not self.is_fitted:
                logger.warning("Model not fitted prior to prediction; fitting on synthetic prototype dataset")
                self.fit()

            # 1. Feature extraction layer
            feature_vec, features_used, ext_notes = extract_features(record)
            notes.extend(ext_notes)

            # 2. Reshape for sklearn input (1, n_features)
            X_input = feature_vec.reshape(1, -1)

            # 3. IsolationForest raw decision function
            # Sklearn decision_function output: positive = inlier/normal, negative = outlier/anomaly
            raw_score = float(self._model.decision_function(X_input)[0])

            # 4. Map raw score to 0.0–1.0 normalized anomaly score scale
            # Typical decision function values range between -0.4 and +0.4
            # We map negative scores (outliers) to higher anomaly scores (0.5 to 1.0)
            normalized_score = float(max(0.0, min(1.0, 0.5 - (raw_score * 1.25))))

            # 5. Threshold and Risk Classification
            anomaly_flag = bool(normalized_score >= anomaly_threshold)

            if normalized_score < 0.4:
                risk_class = "LOW"
            elif normalized_score < 0.7:
                risk_class = "MEDIUM"
            else:
                risk_class = "HIGH"

            if anomaly_flag:
                notes.append(
                    f"Anomaly flag triggered: score {normalized_score:.4f} >= threshold {anomaly_threshold:.4f}"
                )

            if self.is_synthetic_model:
                notes.append("[SIH Prototype] Evaluated using synthetic training model")

            return AnomalyResult(
                anomaly_score=normalized_score,
                raw_decision_score=raw_score,
                anomaly_flag=anomaly_flag,
                risk_classification=risk_class,
                model_version=self.model_version,
                features_used=features_used,
                created_at=created_at_iso,
                is_synthetic_model=self.is_synthetic_model,
                disclaimer=DISCLAIMER_TEXT,
                notes=notes,
            )

        except Exception as exc:
            logger.error("Error during anomaly detection prediction: %s", exc, exc_info=True)
            # Safe fallback result to ensure document processing NEVER fails
            fallback_features = {f: 0.0 for f in FEATURE_NAMES}
            notes.append(f"Fallback safe mode executed due to processing error: {exc}")
            return AnomalyResult(
                anomaly_score=0.0,
                raw_decision_score=0.0,
                anomaly_flag=False,
                risk_classification="LOW",
                model_version=self.model_version,
                features_used=fallback_features,
                created_at=created_at_iso,
                is_synthetic_model=self.is_synthetic_model,
                disclaimer=DISCLAIMER_TEXT,
                notes=notes,
            )


# ---------------------------------------------------------------------------
# Global Singleton / Cached Instance Management
# ---------------------------------------------------------------------------

_GLOBAL_DETECTOR: Optional[IsolationForestAnomalyDetector] = None


def get_anomaly_detector() -> IsolationForestAnomalyDetector:
    """Get or initialize cached default IsolationForest anomaly detector."""
    global _GLOBAL_DETECTOR
    if _GLOBAL_DETECTOR is None:
        _GLOBAL_DETECTOR = IsolationForestAnomalyDetector()
        _GLOBAL_DETECTOR.fit()  # Fits on synthetic dataset for prototype
    return _GLOBAL_DETECTOR


# ---------------------------------------------------------------------------
# Main Public API Entry Point (Fail-safe)
# ---------------------------------------------------------------------------

def detect_anomalies(
    record: Union[LandRecordInput, Dict[str, Any], List[Any]],
    threshold: float = DEFAULT_THRESHOLD,
    detector: Optional[IsolationForestAnomalyDetector] = None,
) -> AnomalyResult:
    """Analyze a land record for statistical anomalies using scikit-learn IsolationForest.
    
    IMPORTANT:
      This service only produces a risk signal for human verification.
      It does NOT determine legal ownership or declare fraud.
      
      This function NEVER raises an exception, guaranteeing document pipeline safety.
    """
    try:
        if detector is None:
            detector = get_anomaly_detector()
        return detector.predict_record(record, anomaly_threshold=threshold)
    except Exception as exc:
        logger.error("Unhandled error in detect_anomalies: %s", exc, exc_info=True)
        return AnomalyResult(
            anomaly_score=0.0,
            raw_decision_score=0.0,
            anomaly_flag=False,
            risk_classification="LOW",
            model_version=MODEL_VERSION_DEFAULT,
            features_used={f: 0.0 for f in FEATURE_NAMES},
            created_at=datetime.now(timezone.utc).isoformat(),
            is_synthetic_model=True,
            disclaimer=DISCLAIMER_TEXT,
            notes=[f"Safety fallback triggered: {exc}"],
        )
