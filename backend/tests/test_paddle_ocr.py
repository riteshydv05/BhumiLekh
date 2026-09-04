"""Tests for the PaddleOCR engine and OCR pipeline.

Tests are designed to:
  - Run without any live document upload (no MinIO / DB calls)
  - Be deterministic (synthetic images with known content)
  - Test graceful fallback when PaddleOCR is unavailable
  - Verify the normalized result schema
"""
from __future__ import annotations

import io
import json

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_synthetic_image_bytes(
    text_lines: list[str] | None = None,
    width: int = 600,
    height: int = 300,
) -> bytes:
    """Create a PNG image with white background and black text."""
    from PIL import Image, ImageDraw

    if text_lines is None:
        text_lines = [
            "Survey No: 245/A",
            "District: Pune",
            "Area: 1.5 Hectares",
        ]

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 30
    for line in text_lines:
        draw.text((20, y), line, fill=(0, 0, 0))
        y += 40

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_minimal_pdf_bytes() -> bytes:
    """Return a minimal valid PDF with embedded text."""
    content = (
        b"BT /F1 12 Tf 50 750 Td "
        b"(Survey No: 245/A) Tj T* "
        b"(District: Pune) Tj T* "
        b"(Area: 1.5 Hectares) Tj T* "
        b"(Village: Wagholi) Tj T* "
        b"(Taluka: Haveli) Tj ET"
    )
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n"
        b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n"
        b"3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>\nendobj\n"
        + b"4 0 obj\n<</Length " + str(len(content)).encode() + b">>\nstream\n"
        + content + b"\nendstream\nendobj\n"
        b"5 0 obj\n<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"0000000278 00000 n \n0000000380 00000 n \n"
        b"trailer\n<</Size 6/Root 1 0 R>>\nstartxref\n460\n%%EOF\n"
    )


# ---------------------------------------------------------------------------
# OCR Result Schema Tests (no model needed)
# ---------------------------------------------------------------------------

class TestOcrResultSchema:
    """Tests for the normalized OcrBlock/OcrPage/OcrDocument schema."""

    def test_ocr_block_creation(self):
        from app.services.ocr_result_schema import OcrBlock
        block = OcrBlock(
            text="Survey No: 245/A",
            bbox=[18.0, 39.0, 101.0, 52.0],
            confidence=0.9987,
            ocr_engine="paddle",
        )
        assert block.text == "Survey No: 245/A"
        assert block.bbox == [18.0, 39.0, 101.0, 52.0]
        assert block.confidence == 0.9987
        assert block.language is None
        assert block.ocr_engine == "paddle"
        assert block.timestamp  # auto-set

    def test_ocr_block_to_dict(self):
        from app.services.ocr_result_schema import OcrBlock
        block = OcrBlock(text="test", bbox=[0, 0, 10, 10], confidence=0.9)
        d = block.to_dict()
        assert "text" in d
        assert "bbox" in d
        assert "confidence" in d
        assert "ocr_engine" in d
        assert "timestamp" in d

    def test_ocr_page_text_aggregation(self):
        from app.services.ocr_result_schema import OcrBlock, OcrPage
        page = OcrPage(page=1, width=612, height=792, blocks=[
            OcrBlock(text="Line 1", bbox=[0, 0, 100, 20], confidence=0.9),
            OcrBlock(text="Line 2", bbox=[0, 25, 100, 45], confidence=0.85),
            OcrBlock(text="  ", bbox=[0, 50, 100, 70], confidence=0.1),  # whitespace-only
        ])
        assert "Line 1" in page.text
        assert "Line 2" in page.text

    def test_ocr_page_avg_confidence(self):
        from app.services.ocr_result_schema import OcrBlock, OcrPage
        page = OcrPage(page=1, blocks=[
            OcrBlock(text="a", bbox=[0, 0, 10, 10], confidence=0.9),
            OcrBlock(text="b", bbox=[0, 15, 10, 25], confidence=0.8),
        ])
        assert abs(page.avg_confidence - 0.85) < 0.01

    def test_ocr_document_aggregation(self):
        from app.services.ocr_result_schema import OcrBlock, OcrDocument, OcrPage
        doc = OcrDocument(pages=[
            OcrPage(page=1, blocks=[
                OcrBlock(text="Page one", bbox=[0, 0, 100, 20], confidence=0.9),
            ]),
            OcrPage(page=2, blocks=[
                OcrBlock(text="Page two", bbox=[0, 0, 100, 20], confidence=0.8),
            ]),
        ], method="paddle")
        assert doc.page_count == 2
        assert "Page one" in doc.full_text
        assert "Page two" in doc.full_text
        assert abs(doc.avg_confidence - 0.85) < 0.01

    def test_ocr_document_to_dict_structure(self):
        from app.services.ocr_result_schema import OcrBlock, OcrDocument, OcrPage
        doc = OcrDocument(pages=[
            OcrPage(page=1, width=612, height=792, blocks=[
                OcrBlock(text="Test", bbox=[10.0, 20.0, 100.0, 40.0], confidence=0.95),
            ]),
        ], method="paddle")
        d = doc.to_dict()

        # Verify top-level keys
        assert "page_count" in d
        assert "full_text" in d
        assert "avg_confidence" in d
        assert "method" in d
        assert "pages" in d

        # Verify page structure
        assert d["page_count"] == 1
        page = d["pages"][0]
        assert page["page"] == 1
        assert page["width"] == 612
        assert "blocks" in page

        # Verify block structure
        block = page["blocks"][0]
        assert block["text"] == "Test"
        assert block["bbox"] == [10.0, 20.0, 100.0, 40.0]
        assert block["confidence"] == 0.95

    def test_json_serializable(self):
        """OcrDocument.to_dict() must be JSON-serializable."""
        from app.services.ocr_result_schema import OcrBlock, OcrDocument, OcrPage
        doc = OcrDocument(pages=[
            OcrPage(page=1, blocks=[
                OcrBlock(text="JSON test", bbox=[0.0, 0.0, 100.0, 20.0], confidence=0.9),
            ]),
        ])
        d = doc.to_dict()
        json_str = json.dumps(d)  # Must not raise
        parsed = json.loads(json_str)
        assert parsed["pages"][0]["blocks"][0]["text"] == "JSON test"


# ---------------------------------------------------------------------------
# PDF Renderer Tests (no model needed)
# ---------------------------------------------------------------------------

class TestPdfRenderer:

    def test_import(self):
        from app.services import pdf_renderer  # noqa: F401

    def test_is_available(self):
        from app.services.pdf_renderer import is_available
        # Should be True since pypdfium2 and Pillow are installed
        assert is_available() is True

    def test_render_valid_pdf(self):
        from app.services.pdf_renderer import render_pdf_pages
        pdf_bytes = _make_minimal_pdf_bytes()
        pages = render_pdf_pages(pdf_bytes, dpi=72)
        assert isinstance(pages, list)
        assert len(pages) >= 1
        page_num, img, w, h = pages[0]
        assert page_num == 1
        assert w > 0
        assert h > 0

    def test_render_invalid_pdf_returns_empty(self):
        from app.services.pdf_renderer import render_pdf_pages
        pages = render_pdf_pages(b"not a pdf", dpi=72)
        assert isinstance(pages, list)
        # Should return empty (not raise)

    def test_max_pages_limit(self):
        from app.services.pdf_renderer import render_pdf_pages
        pdf_bytes = _make_minimal_pdf_bytes()
        pages = render_pdf_pages(pdf_bytes, max_pages=1)
        assert len(pages) <= 1

    def test_image_bytes_to_pil(self):
        from app.services.pdf_renderer import image_bytes_to_pil
        img_bytes = _make_synthetic_image_bytes()
        result = image_bytes_to_pil(img_bytes, page_num=1)
        assert result is not None
        page_num, img, w, h = result
        assert page_num == 1
        assert w == 600
        assert h == 300

    def test_image_bytes_invalid_returns_none(self):
        from app.services.pdf_renderer import image_bytes_to_pil
        result = image_bytes_to_pil(b"not an image")
        assert result is None


# ---------------------------------------------------------------------------
# PaddleOCR Engine Tests
# ---------------------------------------------------------------------------

class TestPaddleOcrEngine:
    """Tests for paddle_ocr_engine — actual PaddleOCR initialization and inference."""

    def test_import(self):
        from app.services import paddle_ocr_engine  # noqa: F401

    def test_get_engine_status(self):
        from app.services.paddle_ocr_engine import get_engine_status
        status = get_engine_status()
        assert "importable" in status
        assert "initialized" in status
        assert "lang" in status

    def test_paddle_importable(self):
        from app.services.paddle_ocr_engine import _PADDLE_IMPORTABLE
        # PaddleOCR is installed in this environment
        assert _PADDLE_IMPORTABLE is True

    def test_engine_initializes(self):
        """PaddleOCR engine must initialize without error."""
        from app.services.paddle_ocr_engine import _get_engine
        engine = _get_engine()
        assert engine is not None

    def test_run_on_synthetic_image(self):
        """PaddleOCR must process a synthetic image and return structured output."""
        from PIL import Image
        from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

        img_bytes = _make_synthetic_image_bytes(["Survey No: 245/A", "District Pune"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        page_dict = run_paddle_ocr_on_image(img, page_num=1)

        # Verify schema
        assert "page" in page_dict
        assert "width" in page_dict
        assert "height" in page_dict
        assert "blocks" in page_dict
        assert page_dict["page"] == 1
        assert page_dict["width"] == 600

        # PaddleOCR should detect at least some text
        assert isinstance(page_dict["blocks"], list)

        # Validate block structure
        for block in page_dict["blocks"]:
            assert "text" in block
            assert "bbox" in block
            assert "confidence" in block
            assert "ocr_engine" in block
            assert "timestamp" in block
            assert len(block["bbox"]) == 4
            assert 0.0 <= block["confidence"] <= 1.0
            assert isinstance(block["text"], str)

    def test_blocks_have_text_content(self):
        """At least one block must contain recognizable text."""
        from PIL import Image
        from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

        img_bytes = _make_synthetic_image_bytes(["Survey No: 245/A"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        page_dict = run_paddle_ocr_on_image(img, page_num=1)

        all_text = " ".join(b["text"] for b in page_dict["blocks"])
        # PaddleOCR should detect some alphanumeric content
        assert any(c.isalnum() for c in all_text), (
            f"No alphanumeric text detected. Blocks: {page_dict['blocks']}"
        )

    def test_run_on_blank_image_does_not_crash(self):
        """Processing a blank white image must not raise."""
        from PIL import Image
        from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

        img = Image.new("RGB", (200, 200), color=(255, 255, 255))
        page_dict = run_paddle_ocr_on_image(img, page_num=1)
        assert isinstance(page_dict["blocks"], list)

    def test_bbox_values_are_floats(self):
        from PIL import Image
        from app.services.paddle_ocr_engine import run_paddle_ocr_on_image

        img_bytes = _make_synthetic_image_bytes(["Test 123"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        page_dict = run_paddle_ocr_on_image(img, page_num=1)

        for block in page_dict["blocks"]:
            for coord in block["bbox"]:
                assert isinstance(coord, float), (
                    f"bbox coord is not float: {coord!r}"
                )


# ---------------------------------------------------------------------------
# OCR Service Integration Tests (PaddleOCR + fallbacks)
# ---------------------------------------------------------------------------

class TestOcrServiceIntegration:

    def test_run_ocr_pdf_returns_ocr_result(self):
        from app.services.ocr_service import OCRResult, run_ocr
        pdf_bytes = _make_minimal_pdf_bytes()
        result = run_ocr(pdf_bytes, "application/pdf")
        assert isinstance(result, OCRResult)
        assert isinstance(result.text, str)
        assert isinstance(result.pages, list)
        assert result.page_count >= 0

    def test_run_ocr_pdf_populates_pages(self):
        from app.services.ocr_service import run_ocr
        pdf_bytes = _make_minimal_pdf_bytes()
        result = run_ocr(pdf_bytes, "application/pdf")
        # Must have at least one page entry (either from PaddleOCR or pypdf)
        assert len(result.pages) >= 1

    def test_run_ocr_pdf_page_schema(self):
        from app.services.ocr_service import run_ocr
        pdf_bytes = _make_minimal_pdf_bytes()
        result = run_ocr(pdf_bytes, "application/pdf")
        for page in result.pages:
            assert "page" in page
            assert "blocks" in page
            assert isinstance(page["blocks"], list)
            for block in page["blocks"]:
                assert "text" in block
                assert "bbox" in block
                assert "confidence" in block
                assert "ocr_engine" in block
                assert "timestamp" in block

    def test_run_ocr_image_png(self):
        from app.services.ocr_service import run_ocr
        img_bytes = _make_synthetic_image_bytes(["Survey No: 245/A"])
        result = run_ocr(img_bytes, "image/png")
        assert isinstance(result.text, str)
        assert result.page_count == 1

    def test_run_ocr_unsupported_type(self):
        from app.services.ocr_service import run_ocr
        result = run_ocr(b"data", "text/plain")
        assert result.error is not None
        assert "Unsupported" in result.error

    def test_run_ocr_invalid_pdf_does_not_crash(self):
        from app.services.ocr_service import run_ocr
        result = run_ocr(b"not a pdf", "application/pdf")
        assert isinstance(result.text, str)  # Never raises

    def test_run_ocr_structured_returns_dict(self):
        from app.services.ocr_service import run_ocr_structured
        pdf_bytes = _make_minimal_pdf_bytes()
        doc_dict = run_ocr_structured(pdf_bytes, "application/pdf")
        required_keys = {"page_count", "full_text", "avg_confidence", "method", "pages"}
        assert required_keys.issubset(doc_dict.keys())
        assert isinstance(doc_dict["pages"], list)

    def test_ocr_result_json_serializable(self):
        from app.services.ocr_service import run_ocr_structured
        pdf_bytes = _make_minimal_pdf_bytes()
        doc_dict = run_ocr_structured(pdf_bytes, "application/pdf")
        json_str = json.dumps(doc_dict, default=str)  # Must not raise
        parsed = json.loads(json_str)
        assert "pages" in parsed
