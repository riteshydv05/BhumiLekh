"""Unit tests for scikit-learn IsolationForest Anomaly Detection Service."""

import math
import numpy as np
import pytest
from app.services.anomaly_service import (
    DISCLAIMER_TEXT,
    MIN_TRAINING_SAMPLES,
    AnomalyResult,
    IsolationForestAnomalyDetector,
    LandRecordInput,
    detect_anomalies,
    extract_features,
    generate_synthetic_training_data,
    parse_number,
)
from app.services.nlp_service import LandRecordEntity


def test_parse_number():
    """Test parse_number utility for various clean and malformed inputs."""
    assert parse_number(123) == 123.0
    assert parse_number(45.67) == 45.67
    assert parse_number(" 45.67 ") == 45.67
    assert parse_number("₹ 1,00,000.50") == 100000.5
    assert parse_number("5.5 hectares") == 5.5
    assert parse_number(None) is None
    assert parse_number("invalid_string") is None
    assert parse_number(float("nan")) is None
    assert parse_number(float("inf")) is None


def test_normal_records():
    """Test normal land record scenario.
    
    Expectation:
      - Low anomaly score (< 0.4)
      - anomaly_flag is False
      - risk_classification is 'LOW'
      - Features extracted correctly
    """
    record = LandRecordInput(
        area=2.5,
        number_of_owners=2,
        mutation_frequency=1,
        numeric_field_consistency=1.0,
        unusual_area_values=0.0,
        unusual_record_patterns=0.0,
    )
    
    result = detect_anomalies(record, threshold=0.5)
    
    assert isinstance(result, AnomalyResult)
    assert result.anomaly_flag is False
    assert result.risk_classification == "LOW"
    assert result.anomaly_score < 0.5
    assert result.disclaimer == DISCLAIMER_TEXT
    assert "area" in result.features_used
    assert result.features_used["number_of_owners"] == 2.0


def test_extreme_area_values():
    """Test extreme area values scenario (e.g. 50,000 hectares or negative area).
    
    Expectation:
      - High anomaly score / flagged as anomaly
      - Correct risk classification ('HIGH' or 'MEDIUM')
      - Features reflect extreme area flag
    """
    # 1. Extreme large area
    extreme_large_record = {
        "area": 50000.0,
        "number_of_owners": 1,
        "mutation_frequency": 25,
        "unusual_area_values": 1.0,
        "unusual_record_patterns": 0.8,
    }
    
    detector = IsolationForestAnomalyDetector(contamination=0.05, random_state=42)
    detector.fit()
    
    result_large = detector.predict_record(extreme_large_record, anomaly_threshold=0.4)
    assert result_large.anomaly_flag is True
    assert result_large.risk_classification in ("MEDIUM", "HIGH")
    assert result_large.features_used["unusual_area_values"] == 1.0
    
    # 2. Negative area record
    negative_area_record = LandRecordInput(
        area=-10.5,
        number_of_owners=1,
        numeric_field_consistency=0.0,
    )
    result_neg = detect_anomalies(negative_area_record, threshold=0.4)
    assert result_neg.anomaly_flag is True
    assert result_neg.features_used["unusual_area_values"] == 1.0


def test_missing_values():
    """Test record with missing fields.
    
    Expectation:
      - Service handles missing values gracefully with imputations
      - Feature vector is created without throwing exceptions
    """
    empty_record = LandRecordInput()
    
    vec, features, notes = extract_features(empty_record)
    assert vec.shape == (6,)
    assert not np.isnan(vec).any()
    assert features["area"] == 0.0
    assert features["number_of_owners"] == 1.0  # Defaulted to 1 owner
    
    result = detect_anomalies(empty_record)
    assert isinstance(result, AnomalyResult)
    assert result.disclaimer == DISCLAIMER_TEXT


def test_malformed_values():
    """Test record with malformed/invalid fields (strings, objects, NaN, negative counts).
    
    Expectation:
      - Service parses valid parts and imputes invalid parts
      - Never crashes or raises exception
    """
    malformed_record = {
        "area": "INVALID_AREA_TEXT",
        "number_of_owners": "NOT_A_NUMBER",
        "mutation_frequency": float("nan"),
        "numeric_field_consistency": "MALFORMED",
        "owner_name": "John Doe & Jane Doe & Sam Smith",  # Should infer 3 owners from string
    }
    
    vec, features, notes = extract_features(malformed_record)
    assert vec.shape == (6,)
    assert not np.isnan(vec).any()
    assert features["number_of_owners"] == 3.0  # Inferred 3 owners from names
    
    result = detect_anomalies(malformed_record)
    assert isinstance(result, AnomalyResult)


def test_extracted_fields_list_input():
    """Test input passed as list of LandRecordEntity objects from NLP pipeline."""
    fields_list = [
        LandRecordEntity(entity_type="AREA", extracted_value="12.5", confidence=0.95),
        LandRecordEntity(entity_type="OWNER_NAME", extracted_value="Ramesh Kumar", confidence=0.90),
        LandRecordEntity(entity_type="MUTATION_NUMBER", extracted_value="MUT-2024-001", confidence=0.85),
    ]
    
    vec, features, notes = extract_features(fields_list)
    assert vec.shape == (6,)
    assert features["area"] > 0.0
    
    result = detect_anomalies(fields_list)
    assert isinstance(result, AnomalyResult)


def test_insufficient_training_data():
    """Test behavior when training dataset has fewer than MIN_TRAINING_SAMPLES.
    
    Expectation:
      - Direct fit call raises ValueError with clear message
      - Predict on unfitted model with custom small dataset handles error gracefully
    """
    detector = IsolationForestAnomalyDetector(model_version="v_test")
    small_dataset = np.array([
        [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
        [2.0, 2.0, 1.0, 1.0, 0.0, 0.0],
    ])
    
    # 1. Direct fit should raise ValueError due to insufficient samples
    with pytest.raises(ValueError) as exc_info:
        detector.fit(small_dataset)
    assert f"minimum required is {MIN_TRAINING_SAMPLES}" in str(exc_info.value)
    
    # 2. Prediction fallback test
    result = detector.predict_record({"area": 1.0})
    assert isinstance(result, AnomalyResult)


def test_configurable_threshold():
    """Test configurable threshold sensitivity."""
    detector = IsolationForestAnomalyDetector()
    detector.fit()
    
    record = {
        "area": 1500.0,
        "unusual_area_values": 0.8,
        "unusual_record_patterns": 0.6,
    }
    
    # Low threshold -> more easily flagged
    res_strict = detector.predict_record(record, anomaly_threshold=0.3)
    # High threshold -> harder to flag
    res_lenient = detector.predict_record(record, anomaly_threshold=0.95)
    
    assert res_strict.anomaly_score == res_lenient.anomaly_score
    assert res_strict.anomaly_flag is True
    assert res_lenient.anomaly_flag is False


def test_synthetic_data_marking():
    """Test that synthetic prototype dataset is explicitly marked as demo data."""
    synth_data = generate_synthetic_training_data(n_samples=50, random_seed=123)
    assert synth_data.shape == (50, 6)
    
    detector = IsolationForestAnomalyDetector()
    detector.fit(synth_data, is_synthetic=True)
    
    result = detector.predict_record({"area": 2.0})
    assert result.is_synthetic_model is True
    assert any("[SIH Prototype]" in note for note in result.notes)


def test_legal_fraud_disclaimer_presence():
    """Ensure legal ownership / fraud disclaimer is always present."""
    result = detect_anomalies({"area": 50.0})
    assert "does NOT determine legal ownership or declare fraud" in result.disclaimer
    assert "human verification" in result.disclaimer


def test_failsafe_unhandled_exception_handling():
    """Ensure top-level detect_anomalies function never raises exception even on totally corrupt input."""
    # Pass None as input
    result = detect_anomalies(None)
    assert isinstance(result, AnomalyResult)
    assert result.anomaly_flag is False
    assert result.risk_classification in ("LOW", "MEDIUM", "HIGH")
