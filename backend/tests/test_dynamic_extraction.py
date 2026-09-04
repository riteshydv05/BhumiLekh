"""Tests: Dynamic Field Extraction Architecture.

MOST IMPORTANT TEST:
Two different synthetic documents with different field sets must
produce different extracted_fields records WITHOUT modifying the
database schema.

Document A = Record of Rights (RoR):
  - Owner Name, Survey Number, Village, Area

Document B = Sale Deed:
  - Previous Owner, New Owner, Deed Number, Witness 1, Stamp Duty

Both must work using the same extraction pipeline with no schema changes.
"""
import pytest
from app.services.dynamic_extraction_service import (
    DynamicField,
    DynamicExtractionResult,
    classify_document,
    extract_key_value_pairs,
    extract_table_fields,
    extract_dynamic_fields,
    _lookup_canonical,
    _detect_data_type,
)


# =====================================================================
# Synthetic Document Texts
# =====================================================================

DOCUMENT_A_TEXT = """
Record of Rights (7/12 Extract)
Jamabandi / Khasra

Owner Name: Ramesh Kumar
Father's Name: Suresh Kumar
Survey Number: 123/4A
Khasra Number: 456
Village: Rampur
Tehsil: Sadar
District: Lucknow
Area: 2.5 hectares
Registration Date: 15/08/2023
"""

DOCUMENT_B_TEXT = """
Sale Deed
Sub-Registrar Office, Pune

Previous Owner: Ramesh Kumar
New Owner: Sita Devi
Deed Number: D-2024-00123
Consideration Amount: Rs. 15,00,000
Stamp Duty: Rs. 90,000
Witness 1: Mohan Lal
Witness 2: Hari Prasad
Registration Date: 01/03/2024
Sub-Registrar: Sri K.P. Sharma
"""


# =====================================================================
# Test 1: Document A — Record of Rights
# =====================================================================

class TestDocumentA:
    """Document A should produce RoR-specific fields."""

    def test_classification(self):
        doc_type, confidence = classify_document(DOCUMENT_A_TEXT)
        assert doc_type == "Record of Rights"
        assert confidence > 0.5

    def test_extraction_produces_ror_fields(self):
        result = extract_dynamic_fields(DOCUMENT_A_TEXT)
        field_names = {f.field_name for f in result.fields}
        field_values = {f.field_name: f.field_value for f in result.fields}

        # Must find these RoR-specific fields
        assert "Owner Name" in field_names, f"Missing 'Owner Name', got: {field_names}"
        assert "Survey Number" in field_names, f"Missing 'Survey Number', got: {field_names}"
        assert "Village" in field_names, f"Missing 'Village', got: {field_names}"

        # Value checks
        assert field_values["Owner Name"] == "Ramesh Kumar"
        assert field_values["Survey Number"] == "123/4A"
        assert field_values["Village"] == "Rampur"

    def test_canonical_keys_assigned(self):
        result = extract_dynamic_fields(DOCUMENT_A_TEXT)
        canonical_map = {f.field_name: f.canonical_key for f in result.fields}

        assert canonical_map.get("Owner Name") == "OWNER_NAME"
        assert canonical_map.get("Survey Number") == "SURVEY_NUMBER"
        assert canonical_map.get("Village") == "VILLAGE"

    def test_data_types_detected(self):
        result = extract_dynamic_fields(DOCUMENT_A_TEXT)
        type_map = {f.field_name: f.data_type for f in result.fields}

        assert type_map.get("Owner Name") == "person"
        assert type_map.get("Area") == "area"

    def test_no_sale_deed_fields(self):
        """RoR document must NOT produce Sale Deed-specific fields."""
        result = extract_dynamic_fields(DOCUMENT_A_TEXT)
        field_names = {f.field_name for f in result.fields}

        assert "Previous Owner" not in field_names
        assert "New Owner" not in field_names
        assert "Deed Number" not in field_names
        assert "Stamp Duty" not in field_names


# =====================================================================
# Test 2: Document B — Sale Deed
# =====================================================================

class TestDocumentB:
    """Document B should produce Sale Deed-specific fields."""

    def test_classification(self):
        doc_type, confidence = classify_document(DOCUMENT_B_TEXT)
        assert doc_type == "Sale Deed"
        assert confidence > 0.5

    def test_extraction_produces_sale_deed_fields(self):
        result = extract_dynamic_fields(DOCUMENT_B_TEXT)
        field_names = {f.field_name for f in result.fields}
        field_values = {f.field_name: f.field_value for f in result.fields}

        # Must find these Sale Deed-specific fields
        assert "Previous Owner" in field_names, f"Missing 'Previous Owner', got: {field_names}"
        assert "New Owner" in field_names, f"Missing 'New Owner', got: {field_names}"
        assert "Deed Number" in field_names, f"Missing 'Deed Number', got: {field_names}"

        # Value checks
        assert field_values["Previous Owner"] == "Ramesh Kumar"
        assert field_values["New Owner"] == "Sita Devi"
        assert field_values["Deed Number"] == "D-2024-00123"

    def test_canonical_keys_for_sale_deed(self):
        result = extract_dynamic_fields(DOCUMENT_B_TEXT)
        canonical_map = {f.field_name: f.canonical_key for f in result.fields}

        assert canonical_map.get("Previous Owner") == "PREVIOUS_OWNER"
        assert canonical_map.get("New Owner") == "NEW_OWNER"
        assert canonical_map.get("Stamp Duty") == "STAMP_DUTY"
        # Witnesses have NO canonical key — they stay dynamic
        if "Witness 1" in canonical_map:
            assert canonical_map["Witness 1"] is None, \
                "Witness fields should have canonical_key=None"

    def test_data_types_for_sale_deed(self):
        result = extract_dynamic_fields(DOCUMENT_B_TEXT)
        type_map = {f.field_name: f.data_type for f in result.fields}

        assert type_map.get("Previous Owner") == "person"
        assert type_map.get("New Owner") == "person"
        assert type_map.get("Stamp Duty") == "currency"

    def test_no_ror_specific_fields(self):
        """Sale Deed must NOT produce RoR-specific fields like Survey Number."""
        result = extract_dynamic_fields(DOCUMENT_B_TEXT)
        field_names = {f.field_name for f in result.fields}

        assert "Survey Number" not in field_names
        assert "Khasra Number" not in field_names


# =====================================================================
# Test 3: Both documents produce DIFFERENT field sets
# =====================================================================

class TestDynamicDifference:
    """Prove that two different documents produce different field sets
    without any database schema change."""

    def test_different_field_sets(self):
        result_a = extract_dynamic_fields(DOCUMENT_A_TEXT)
        result_b = extract_dynamic_fields(DOCUMENT_B_TEXT)

        fields_a = {f.field_name for f in result_a.fields}
        fields_b = {f.field_name for f in result_b.fields}

        # They MUST have different field sets
        assert fields_a != fields_b, \
            f"Documents A and B produced identical field sets: {fields_a}"

        # Each must have unique fields not in the other
        only_a = fields_a - fields_b
        only_b = fields_b - fields_a

        assert len(only_a) > 0, "Document A has no unique fields vs Document B"
        assert len(only_b) > 0, "Document B has no unique fields vs Document A"

        print(f"\nDocument A fields ({len(fields_a)}): {sorted(fields_a)}")
        print(f"Document B fields ({len(fields_b)}): {sorted(fields_b)}")
        print(f"Only in A: {sorted(only_a)}")
        print(f"Only in B: {sorted(only_b)}")

    def test_different_document_types(self):
        type_a, _ = classify_document(DOCUMENT_A_TEXT)
        type_b, _ = classify_document(DOCUMENT_B_TEXT)

        assert type_a != type_b, \
            f"Both documents classified as the same type: {type_a}"

    def test_different_canonical_keys(self):
        result_a = extract_dynamic_fields(DOCUMENT_A_TEXT)
        result_b = extract_dynamic_fields(DOCUMENT_B_TEXT)

        canonicals_a = {f.canonical_key for f in result_a.fields if f.canonical_key}
        canonicals_b = {f.canonical_key for f in result_b.fields if f.canonical_key}

        only_a = canonicals_a - canonicals_b
        only_b = canonicals_b - canonicals_a

        assert len(only_a) > 0 or len(only_b) > 0, \
            "Both documents produced identical canonical key sets"

    def test_serialization_schema_independent(self):
        """Both documents produce dict-serializable results that can be stored
        in the same document_results table without schema changes."""
        result_a = extract_dynamic_fields(DOCUMENT_A_TEXT)
        result_b = extract_dynamic_fields(DOCUMENT_B_TEXT)

        for f in result_a.fields + result_b.fields:
            d = f.to_dict()
            assert "field_name" in d
            assert "field_value" in d
            assert "data_type" in d
            assert "confidence" in d
            assert "canonical_key" in d  # can be None
            assert "extraction_method" in d


# =====================================================================
# Test 4: Canonical Mapping
# =====================================================================

class TestCanonicalMapping:
    """Verify that canonical mapping is optional and works correctly."""

    def test_known_label_maps(self):
        assert _lookup_canonical("Owner Name") == "OWNER_NAME"
        assert _lookup_canonical("Survey Number") == "SURVEY_NUMBER"
        assert _lookup_canonical("खाता संख्या") == "KHATA_NUMBER"
        assert _lookup_canonical("Stamp Duty") == "STAMP_DUTY"

    def test_unknown_label_returns_none(self):
        assert _lookup_canonical("Witness 1") is None
        assert _lookup_canonical("Some Random Field") is None
        assert _lookup_canonical("Sub-Registrar") is None

    def test_canonical_null_for_novel_fields(self):
        """Novel fields discovered from documents must have canonical_key=None."""
        result = extract_dynamic_fields(DOCUMENT_B_TEXT)
        sub_registrar = [f for f in result.fields if "Sub-Registrar" in f.field_name]
        if sub_registrar:
            assert sub_registrar[0].canonical_key is None


# =====================================================================
# Test 5: Data Type Detection
# =====================================================================

class TestDataTypeDetection:
    def test_person_detection(self):
        assert _detect_data_type("Owner Name", "Ramesh Kumar") == "person"
        assert _detect_data_type("Father's Name", "Suresh Kumar") == "person"

    def test_date_detection(self):
        assert _detect_data_type("Registration Date", "15/08/2023") == "date"

    def test_currency_detection(self):
        assert _detect_data_type("Stamp Duty", "Rs. 90,000") == "currency"

    def test_area_detection(self):
        assert _detect_data_type("Area", "2.5 hectares") == "area"

    def test_address_detection(self):
        assert _detect_data_type("Village", "Rampur") == "address"

    def test_number_detection(self):
        assert _detect_data_type("Plot No", "123") in ("integer", "identifier")


# =====================================================================
# Test 6: Table Extraction
# =====================================================================

class TestTableExtraction:
    def test_pipe_table(self):
        table_text = """
| Field Name | Value |
|-----------|-------|
| Owner | Ram Das |
| Area | 5 hectares |
| Village | Sehore |
"""
        fields = extract_table_fields(table_text)
        assert len(fields) > 0
        assert any(f.extraction_method == "table_extraction" for f in fields)
