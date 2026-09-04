"""Tests for the LayoutLMv3 layout-processing service.

Covers:
    - OCR-to-layout conversion
    - Bounding-box normalization
    - Page handling
    - Malformed OCR data
    - LayoutLMv3 processor service initialization
"""
from __future__ import annotations

import io
import json

import pytest
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_synthetic_image_bytes(
    width: int = 600,
    height: int = 300,
) -> bytes:
    """Create a PNG image with white background."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_ocr_document(
    pages: list[dict] | None = None,
    method: str = "paddle",
) -> dict:
    """Create a synthetic OcrDocument dict for testing."""
    if pages is None:
        pages = [
            {
                "page": 1,
                "width": 600,
                "height": 400,
                "blocks": [
                    {
                        "text": "Survey No: 245/A",
                        "bbox": [18.0, 39.0, 200.0, 60.0],
                        "confidence": 0.95,
                        "language": None,
                        "ocr_engine": "paddle",
                        "timestamp": "2026-09-04T12:00:00",
                    },
                    {
                        "text": "District: Pune",
                        "bbox": [18.0, 80.0, 150.0, 100.0],
                        "confidence": 0.92,
                        "language": None,
                        "ocr_engine": "paddle",
                        "timestamp": "2026-09-04T12:00:00",
                    },
                ],
            },
            {
                "page": 2,
                "width": 600,
                "height": 400,
                "blocks": [
                    {
                        "text": "Owner Name: Ram Sharma",
                        "bbox": [20.0, 50.0, 300.0, 75.0],
                        "confidence": 0.88,
                        "language": None,
                        "ocr_engine": "paddle",
                        "timestamp": "2026-09-04T12:00:00",
                    },
                ],
            },
        ]
    return {
        "page_count": len(pages),
        "full_text": "\n\n".join(
            "\n".join(b["text"] for b in p["blocks"]) for p in pages
        ),
        "avg_confidence": 0.9,
        "method": method,
        "error": None,
        "warnings": [],
        "pages": pages,
    }


def _make_page_images(num_pages: int = 1) -> dict[int, Image.Image]:
    """Create synthetic PIL images for pages."""
    images: dict[int, Image.Image] = {}
    for i in range(1, num_pages + 1):
        img = Image.new("RGB", (600, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), f"Page {i}", fill=(0, 0, 0))
        images[i] = img
    return images


# ---------------------------------------------------------------------------
# Test: Bounding-box normalization
# ---------------------------------------------------------------------------

class TestBoundingBoxNormalization:
    """Tests for normalize_bbox and denormalize_bbox functions."""

    def test_normalize_bbox_basic(self):
        from app.services.layoutlmv3_service import normalize_bbox

        bbox = [18.0, 39.0, 200.0, 60.0]
        result = normalize_bbox(bbox, 600, 400)

        assert len(result) == 4
        assert result == [30, 98, 333, 150]  # 18/600*1000=30, 39/400*1000=98, etc.

    def test_normalize_bbox_clamps(self):
        from app.services.layoutlmv3_service import normalize_bbox

        # Bbox exceeding page dimensions should be clamped
        bbox = [-10.0, -5.0, 700.0, 500.0]
        result = normalize_bbox(bbox, 600, 400)

        assert result[0] == 0
        assert result[1] == 0
        assert result[2] == 1000
        assert result[3] == 1000

    def test_normalize_bbox_swapped_coords(self):
        from app.services.layoutlmv3_service import normalize_bbox

        # If x2 < x1 after normalization, they should be swapped
        bbox = [500.0, 50.0, 100.0, 80.0]
        result = normalize_bbox(bbox, 600, 400)

        assert result[0] <= result[2]
        assert result[1] <= result[3]

    def test_normalize_bbox_invalid_dimensions(self):
        from app.services.layoutlmv3_service import normalize_bbox

        with pytest.raises(ValueError):
            normalize_bbox([0, 0, 10, 10], 0, 400)

        with pytest.raises(ValueError):
            normalize_bbox([0, 0, 10, 10], 600, 0)

    def test_normalize_bbox_invalid_length(self):
        from app.services.layoutlmv3_service import normalize_bbox

        with pytest.raises(ValueError):
            normalize_bbox([0, 0, 10], 600, 400)

        with pytest.raises(ValueError):
            normalize_bbox([0, 0, 10, 10, 20], 600, 400)

    def test_denormalize_bbox_roundtrip(self):
        from app.services.layoutlmv3_service import (
            normalize_bbox,
            denormalize_bbox,
        )

        original = [18.0, 39.0, 200.0, 60.0]
        normalized = normalize_bbox(original, 600, 400)
        denormalized = denormalize_bbox(normalized, 600, 400)

        # Allow small rounding errors
        for orig, denorm in zip(original, denormalized):
            assert abs(orig - denorm) < 2.0, f"Roundtrip failed: {orig} vs {denorm}"

    def test_denormalize_bbox_invalid_dimensions(self):
        from app.services.layoutlmv3_service import denormalize_bbox

        with pytest.raises(ValueError):
            denormalize_bbox([0, 0, 100, 100], 0, 400)


# ---------------------------------------------------------------------------
# Test: OCR-to-Layout Conversion
# ---------------------------------------------------------------------------

class TestOcrToLayoutConversion:
    """Tests for convert_ocr_blocks_to_layout and build_layout_document."""

    def test_convert_ocr_blocks_creates_layout_blocks(self):
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {
                "text": "Survey No: 245/A",
                "bbox": [18.0, 39.0, 200.0, 60.0],
                "confidence": 0.95,
            },
            {
                "text": "District: Pune",
                "bbox": [18.0, 80.0, 150.0, 100.0],
                "confidence": 0.92,
            },
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )

        assert len(layout_blocks) == 2
        assert all(isinstance(lb, type(layout_blocks[0])) for lb in layout_blocks)

    def test_convert_skips_empty_blocks(self):
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": "", "bbox": [0, 0, 10, 10], "confidence": 0.0},
            {"text": "  ", "bbox": [0, 0, 10, 10], "confidence": 0.0},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )

        assert len(layout_blocks) == 0

    def test_layout_blocks_have_normalized_bboxes(self):
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {
                "text": "Test Text",
                "bbox": [10.0, 20.0, 100.0, 40.0],
                "confidence": 0.9,
            },
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 200, 200, 1
        )

        assert len(layout_blocks) == 1
        lb = layout_blocks[0]
        assert all(0 <= c <= 1000 for c in lb.bbox_normalized)
        assert lb.confidence == 0.9
        assert lb.ocr_block_index == 0
        assert lb.page_num == 1

    def test_layout_block_words_split(self):
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {
                "text": "Survey No 245 A",
                "bbox": [0, 0, 100, 20],
                "confidence": 0.9,
            },
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 200, 200, 1
        )

        assert len(layout_blocks) == 1
        assert layout_blocks[0].words == ["Survey", "No", "245", "A"]

    def test_build_layout_document(self):
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = _make_ocr_document()
        layout_doc = build_layout_document(ocr_doc)

        assert layout_doc.page_count == 2
        assert layout_doc.method == "paddle"
        assert layout_doc.ocr_raw is not None
        assert layout_doc.total_layout_blocks > 0

    def test_build_layout_document_with_images(self):
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = _make_ocr_document()
        images = _make_page_images(2)
        layout_doc = build_layout_document(ocr_doc, page_images=images)

        assert layout_doc.has_page_images is True
        assert layout_doc.pages[0].image is not None
        assert layout_doc.pages[1].image is not None

    def test_ocr_blocks_preserved_unchanged(self):
        """Verify that raw OCR data is not modified during conversion."""
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = _make_ocr_document()
        original_ocr_text = ocr_doc["pages"][0]["blocks"][0]["text"]

        layout_doc = build_layout_document(ocr_doc)

        # The ocr_raw should preserve original data
        assert layout_doc.ocr_raw["pages"][0]["blocks"][0]["text"] == original_ocr_text

    def test_layout_block_to_dict(self):
        from app.services.layoutlmv3_service import LayoutBlock

        lb = LayoutBlock(
            words=["Survey", "No"],
            bbox_normalized=[30, 98, 333, 150],
            block_type="field",
            confidence=0.95,
            ocr_block_index=0,
            page_num=1,
            region_hint="survey_number_field",
        )

        d = lb.to_dict()
        assert d["words"] == ["Survey", "No"]
        assert d["bbox_normalized"] == [30, 98, 333, 150]
        assert d["block_type"] == "field"
        assert d["region_hint"] == "survey_number_field"
        assert json.dumps(d)  # Must be JSON-serializable

    def test_layout_page_to_dict(self):
        from app.services.layoutlmv3_service import LayoutPage

        page = LayoutPage(
            page_num=1,
            width=600,
            height=400,
            ocr_blocks=[{"text": "Test"}],
            layout_blocks=[],
        )

        d = page.to_dict()
        assert d["page_num"] == 1
        assert d["width"] == 600
        assert d["ocr_block_count"] == 1
        assert d["layout_block_count"] == 0


# ---------------------------------------------------------------------------
# Test: Block Type Classification
# ---------------------------------------------------------------------------

class TestBlockTypeClassification:
    """Tests for classify_block_type heuristic."""

    def test_title_detection(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "LAND SURVEY RECORD", "confidence": 0.95}
        assert classify_block_type(block) == "title"

    def test_field_detection(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "Survey No: 245/A", "confidence": 0.95}
        assert classify_block_type(block) == "field"

    def test_form_detection(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "Address: 123 Main St", "confidence": 0.9}
        assert classify_block_type(block) == "form"

    def test_table_detection(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "col1\tcol2\tcol3", "confidence": 0.9}
        assert classify_block_type(block) == "table"

    def test_signature_detection(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "Ram", "confidence": 0.8}
        assert classify_block_type(block) == "signature"

    def test_text_default(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "This is a normal paragraph of text.", "confidence": 0.9}
        assert classify_block_type(block) == "text"

    def test_empty_text(self):
        from app.services.layoutlmv3_service import classify_block_type

        block = {"text": "", "confidence": 0.0}
        assert classify_block_type(block) == "unknown"


# ---------------------------------------------------------------------------
# Test: Page Handling
# ---------------------------------------------------------------------------

class TestPageHandling:
    """Tests for LayoutPage and LayoutDocument page-level operations."""

    def test_layout_page_ocr_text(self):
        from app.services.layoutlmv3_service import LayoutPage

        page = LayoutPage(
            page_num=1,
            width=600,
            height=400,
            ocr_blocks=[
                {"text": "Line 1"},
                {"text": "Line 2"},
            ],
        )
        assert "Line 1" in page.ocr_text
        assert "Line 2" in page.ocr_text

    def test_layout_page_empty_ocr(self):
        from app.services.layoutlmv3_service import LayoutPage

        page = LayoutPage(page_num=1, ocr_blocks=[])
        assert page.ocr_text == ""

    def test_layout_document_page_count(self):
        from app.services.layoutlmv3_service import LayoutDocument, LayoutPage

        doc = LayoutDocument(pages=[
            LayoutPage(page_num=1, layout_blocks=[]),
            LayoutPage(page_num=2, layout_blocks=[]),
        ])
        assert doc.page_count == 2

    def test_layout_document_total_layout_blocks(self):
        from app.services.layoutlmv3_service import LayoutDocument, LayoutBlock, LayoutPage

        doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                layout_blocks=[
                    LayoutBlock(words=["a"], bbox_normalized=[0, 0, 100, 100]),
                    LayoutBlock(words=["b"], bbox_normalized=[0, 0, 100, 100]),
                ],
            ),
            LayoutPage(
                page_num=2,
                layout_blocks=[
                    LayoutBlock(words=["c"], bbox_normalized=[0, 0, 100, 100]),
                ],
            ),
        ])
        assert doc.total_layout_blocks == 3

    def test_prepare_layoutlmv3_inputs_single_page(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                width=600,
                height=400,
                layout_blocks=[
                    LayoutBlock(
                        words=["Survey", "No"],
                        bbox_normalized=[30, 98, 333, 150],
                        block_type="field",
                    ),
                    LayoutBlock(
                        words=["245", "A"],
                        bbox_normalized=[333, 98, 400, 150],
                        block_type="text",
                    ),
                ],
            ),
        ])

        inputs = prepare_layoutlmv3_inputs(layout_doc, page_num=1)

        assert "image" in inputs
        assert "words" in inputs
        assert "bboxes" in inputs
        assert inputs["page_num"] == 1
        assert len(inputs["words"]) == 4
        assert len(inputs["bboxes"]) == 4

    def test_prepare_layoutlmv3_inputs_page_not_found(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(page_num=1, layout_blocks=[]),
        ])

        inputs = prepare_layoutlmv3_inputs(layout_doc, page_num=99)
        assert inputs == {}

    def test_prepare_layoutlmv3_inputs_empty_blocks(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(page_num=1, layout_blocks=[]),
        ])

        inputs = prepare_layoutlmv3_inputs(layout_doc, page_num=1)
        assert inputs == {}

    def test_prepare_layoutlmv3_batch(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_batch,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                layout_blocks=[
                    LayoutBlock(words=["a"], bbox_normalized=[0, 0, 100, 100]),
                ],
            ),
            LayoutPage(
                page_num=2,
                layout_blocks=[
                    LayoutBlock(words=["b"], bbox_normalized=[0, 0, 100, 100]),
                ],
            ),
        ])

        inputs_list = prepare_layoutlmv3_batch(layout_doc)
        assert len(inputs_list) == 2
        assert all("words" in inp for inp in inputs_list)

    def test_layout_document_to_dict(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
        )

        doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                width=600,
                height=400,
                layout_blocks=[
                    LayoutBlock(
                        words=["Test"],
                        bbox_normalized=[30, 98, 333, 150],
                        block_type="field",
                    ),
                ],
            ),
        ])

        d = doc.to_dict()
        assert d["page_count"] == 1
        assert d["total_layout_blocks"] == 1
        assert "pages" in d
        assert len(d["pages"]) == 1
        assert d["pages"][0]["layout_block_count"] == 1
        assert json.dumps(d)  # Must be JSON-serializable


# ---------------------------------------------------------------------------
# Test: Malformed OCR Data
# ---------------------------------------------------------------------------

class TestMalformedOcrData:
    """Tests for graceful handling of malformed or incomplete OCR data."""

    def test_build_layout_document_with_empty_pages(self):
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = {"pages": [], "method": "paddle"}
        layout_doc = build_layout_document(ocr_doc)

        assert layout_doc.page_count == 0
        assert layout_doc.total_layout_blocks == 0

    def test_build_layout_document_missing_page_data(self):
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = {
            "pages": [
                {"blocks": []},  # Missing page, width, height
            ],
            "method": "paddle",
        }
        layout_doc = build_layout_document(ocr_doc)

        assert layout_doc.page_count == 1
        assert layout_doc.pages[0].width == 0
        assert layout_doc.pages[0].height == 0

    def test_build_layout_document_missing_blocks(self):
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = {
            "pages": [
                {"page": 1, "width": 600, "height": 400, "blocks": None},
            ],
            "method": "paddle",
        }
        layout_doc = build_layout_document(ocr_doc)

        assert layout_doc.pages[0].layout_blocks == []

    def test_build_layout_document_missing_bbox(self):
        """Blocks with missing bbox should be handled gracefully."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": "Test", "bbox": None, "confidence": 0.9},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )

        assert len(layout_blocks) == 1
        assert layout_blocks[0].bbox_normalized == [0.0, 0.0, 0.0, 0.0]

    def test_build_layout_document_missing_text(self):
        """Blocks with missing text should be handled gracefully."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": None, "bbox": [0, 0, 10, 10], "confidence": 0.9},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )

        assert len(layout_blocks) == 0

    def test_build_layout_document_negative_bbox(self):
        """Negative bbox coordinates should be handled (clamped)."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": "Test", "bbox": [-100, -50, 200, 30], "confidence": 0.9},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 200, 200, 1
        )

        assert len(layout_blocks) == 1
        lb = layout_blocks[0]
        assert lb.bbox_normalized[0] >= 0

    def test_build_layout_document_zero_dimensions(self):
        """Zero page dimensions should not crash; blocks get zero-area bboxes."""
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = {
            "pages": [
                {
                    "page": 1,
                    "width": 0,
                    "height": 0,
                    "blocks": [
                        {"text": "Test", "bbox": [10, 20, 100, 40], "confidence": 0.9},
                    ],
                },
            ],
            "method": "paddle",
        }
        layout_doc = build_layout_document(ocr_doc)
        # Block with zero page dims gets zero bbox (ValueError caught) but is NOT dropped
        assert len(layout_doc.pages[0].layout_blocks) == 1
        assert layout_doc.pages[0].layout_blocks[0].bbox_normalized == [0.0, 0.0, 0.0, 0.0]

    def test_build_layout_document_non_list_blocks(self):
        """If blocks is a non-list type, handle gracefully (returns empty)."""
        from app.services.layoutlmv3_service import build_layout_document

        ocr_doc = {
            "pages": [
                {"page": 1, "width": 600, "height": 400, "blocks": "not_a_list"},
            ],
            "method": "paddle",
        }
        layout_doc = build_layout_document(ocr_doc)
        # Non-list blocks should result in empty layout blocks
        assert layout_doc.pages[0].layout_blocks == []

    def test_convert_ocr_blocks_non_dict(self):
        """If an OCR block is not a dict, handle gracefully."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        # Blocks with wrong types should be handled gracefully
        ocr_blocks_typed = [
            {"text": "Valid", "bbox": [0, 0, 10, 10], "confidence": 0.9},
            {"text": 12345, "bbox": [0, 0, 10, 10], "confidence": 0.9},  # int text
        ]

        # Int text should be converted to string and processed
        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks_typed, 600, 400, 1
        )
        assert len(layout_blocks) >= 1

    def test_convert_ocr_blocks_negative_confidence(self):
        """Negative confidence should be handled."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": "Test", "bbox": [0, 0, 10, 10], "confidence": -0.5},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )
        assert len(layout_blocks) == 1
        assert layout_blocks[0].confidence == -0.5

    def test_convert_ocr_blocks_very_large_bbox(self):
        """Very large bbox coordinates should be clamped."""
        from app.services.layoutlmv3_service import convert_ocr_blocks_to_layout

        ocr_blocks = [
            {"text": "Test", "bbox": [0, 0, 999999, 999999], "confidence": 0.9},
        ]

        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, 600, 400, 1
        )
        assert len(layout_blocks) == 1
        lb = layout_blocks[0]
        assert max(lb.bbox_normalized) <= 1000


# ---------------------------------------------------------------------------
# Test: LayoutLMv3 Processor Service
# ---------------------------------------------------------------------------

class TestLayoutLMv3ProcessorService:
    """Tests for LayoutLMv3ProcessorService initialization and status."""

    def test_service_creation(self):
        from app.services.layoutlmv3_service import LayoutLMv3ProcessorService

        service = LayoutLMv3ProcessorService()
        assert service._initialized is False
        assert service.is_available is False

    def test_get_status(self):
        from app.services.layoutlmv3_service import get_layoutlmv3_status

        status = get_layoutlmv3_status()
        assert "transformers_available" in status
        assert "model_available" in status
        assert "initialized" in status
        assert status["checkpoint"] == "microsoft/layoutlmv3-base"

    def test_service_not_available_without_init(self):
        from app.services.layoutlmv3_service import LayoutLMv3ProcessorService

        service = LayoutLMv3ProcessorService()
        assert service.is_available is False

    def test_initialize_returns_bool(self):
        from app.services.layoutlmv3_service import LayoutLMv3ProcessorService

        service = LayoutLMv3ProcessorService()
        result = service.initialize()
        # May be True or False depending on model availability
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Test: Layout Inference Result
# ---------------------------------------------------------------------------

class TestLayoutInferenceResult:
    """Tests for LayoutInferenceResult dataclass."""

    def test_result_creation(self):
        from app.services.layoutlmv3_service import LayoutInferenceResult

        result = LayoutInferenceResult(
            page_num=1,
            blocks=[{"word": "test", "label": "text"}],
            requires_fine_tuning=True,
            message="Base checkpoint needs fine-tuning",
        )
        assert result.page_num == 1
        assert len(result.blocks) == 1
        assert result.requires_fine_tuning is True

    def test_result_to_dict(self):
        from app.services.layoutlmv3_service import LayoutInferenceResult

        result = LayoutInferenceResult(
            page_num=1,
            blocks=[],
            requires_fine_tuning=True,
        )
        d = result.to_dict()
        assert d["page_num"] == 1
        assert d["requires_fine_tuning"] is True
        assert json.dumps(d)  # Must be JSON-serializable


# ---------------------------------------------------------------------------
# Test: Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:
    """Tests for create_layout_from_ocr and run_layoutlmv3_inference."""

    def test_create_layout_from_ocr(self):
        from app.services.layoutlmv3_service import create_layout_from_ocr

        ocr_doc = _make_ocr_document()
        layout_doc = create_layout_from_ocr(ocr_doc)

        assert layout_doc.page_count == 2
        assert layout_doc.ocr_raw is not None
        assert layout_doc.total_layout_blocks > 0

    def test_run_layoutlmv3_inference_not_initialized(self):
        from app.services.layoutlmv3_service import (
            LayoutInferenceResult,
            run_layoutlmv3_inference,
        )

        # If model is not initialized, initialize() will be called inside
        # but since we don't have a page image with actual content,
        # the function may return early or raise — either way it should not crash
        ocr_doc = _make_ocr_document()
        try:
            result = run_layoutlmv3_inference(ocr_doc)
            # If initialization succeeds, we should get a result
            assert isinstance(result, LayoutInferenceResult)
        except RuntimeError as exc:
            # Expected if model cannot be loaded
            assert "LayoutLMv3" in str(exc)

    def test_create_layout_from_ocr_with_images(self):
        from app.services.layoutlmv3_service import create_layout_from_ocr

        ocr_doc = _make_ocr_document()
        images = _make_page_images(2)
        layout_doc = create_layout_from_ocr(ocr_doc, page_images=images)

        assert layout_doc.has_page_images is True
        assert layout_doc.pages[0].image is not None

    def test_create_layout_document_preserves_ocr(self):
        """Verify that create_layout_from_ocr preserves OCR data unchanged."""
        from app.services.layoutlmv3_service import create_layout_from_ocr

        ocr_doc = _make_ocr_document()
        original_block_text = ocr_doc["pages"][0]["blocks"][0]["text"]

        layout_doc = create_layout_from_ocr(ocr_doc)

        assert layout_doc.ocr_raw["pages"][0]["blocks"][0]["text"] == original_block_text
        # Layout blocks should have separate data
        assert layout_doc.pages[0].layout_blocks[0].words != [original_block_text]


# ---------------------------------------------------------------------------
# Test: prepare_layoutlmv3_inputs edge cases
# ---------------------------------------------------------------------------

class TestPrepareLayoutlmv3InputsEdgeCases:
    """Edge case tests for prepare_layoutlmv3_inputs."""

    def test_single_word_block(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                layout_blocks=[
                    LayoutBlock(
                        words=["Single"],
                        bbox_normalized=[0, 0, 100, 100],
                    ),
                ],
            ),
        ])

        inputs = prepare_layoutlmv3_inputs(layout_doc)
        assert inputs["words"] == ["Single"]
        assert len(inputs["bboxes"]) == 1

    def test_block_with_multiple_words(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                layout_blocks=[
                    LayoutBlock(
                        words=["Survey", "No", "245"],
                        bbox_normalized=[0, 0, 300, 100],
                    ),
                ],
            ),
        ])

        inputs = prepare_layoutlmv3_inputs(layout_doc)
        assert inputs["words"] == ["Survey", "No", "245"]
        assert len(inputs["bboxes"]) == 3
        # All bboxes should be the same (one per word in block)
        assert all(b == [0, 0, 300, 100] for b in inputs["bboxes"])

    def test_first_page_default(self):
        from app.services.layoutlmv3_service import (
            LayoutBlock,
            LayoutPage,
            LayoutDocument,
            prepare_layoutlmv3_inputs,
        )

        layout_doc = LayoutDocument(pages=[
            LayoutPage(
                page_num=1,
                layout_blocks=[
                    LayoutBlock(
                        words=["Page1"],
                        bbox_normalized=[0, 0, 100, 100],
                    ),
                ],
            ),
            LayoutPage(
                page_num=2,
                layout_blocks=[
                    LayoutBlock(
                        words=["Page2"],
                        bbox_normalized=[0, 0, 100, 100],
                    ),
                ],
            ),
        ])

        # page_num=None should default to first page (page_num=1)
        inputs = prepare_layoutlmv3_inputs(layout_doc)
        assert inputs["page_num"] == 1
        assert inputs["words"] == ["Page1"]

        # Explicit page_num=2
        inputs2 = prepare_layoutlmv3_inputs(layout_doc, page_num=2)
        assert inputs2["page_num"] == 2
        assert inputs2["words"] == ["Page2"]
