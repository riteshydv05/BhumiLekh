"""Tests for the TrOCR handwriting OCR service.

Test strategy:
  - Schema and dataclass tests run without any model (instant)
  - Engine status tests check import-time state
  - Model initialization and inference tests are marked and run actual TrOCR
    (these download / load the model; slow on first run)
  - Graceful-degradation tests use monkeypatching to simulate model failure
  - A real handwriting sample test processes a synthetic image and reports
    actual TrOCR output (we do NOT assert specific text — accuracy on
    synthetic images is explicitly not claimed)

Confidence accuracy disclaimer:
  TrOCR was trained on real handwriting (IAM, SROIE, etc.). Synthetic PIL-
  rendered text does NOT look like handwriting to the model. Output on
  synthetic samples is unreliable and is only used to verify the pipeline
  plumbing works end-to-end, NOT to validate recognition accuracy.
"""
from __future__ import annotations

import io
import json

import pytest


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_handwriting_like_image(
    text: str = "Survey 245/A Pune",
    width: int = 400,
    height: int = 80,
) -> "PIL.Image.Image":
    """Return a PIL Image that superficially resembles a handwriting strip."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), color=(252, 248, 240))
    draw = ImageDraw.Draw(img)
    # Slightly off-white background and dark text mimic paper
    draw.text((10, height // 2 - 12), text, fill=(15, 25, 60))
    return img


def _make_synthetic_page_image(lines: list[str], width=700, height=300):
    """Return a full-page PIL Image with multiple text lines."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 30
    for line in lines:
        draw.text((20, y), line, fill=(20, 20, 20))
        y += 40
    return img


# ---------------------------------------------------------------------------
# 1. HwOcrResult dataclass tests (no model needed)
# ---------------------------------------------------------------------------

class TestHwOcrResult:

    def test_import(self):
        from app.services.trocr_service import HwOcrResult  # noqa: F401

    def test_defaults(self):
        from app.services.trocr_service import HwOcrResult
        r = HwOcrResult(page=1, text="hello", bbox=[0.0, 0.0, 100.0, 50.0])
        assert r.page == 1
        assert r.text == "hello"
        assert r.bbox == [0.0, 0.0, 100.0, 50.0]
        assert r.engine == "trocr"
        assert r.confidence is None
        assert r.error is None
        assert r.timestamp  # auto-set

    def test_to_dict_keys(self):
        from app.services.trocr_service import HwOcrResult
        r = HwOcrResult(page=2, text="test", bbox=[1.0, 2.0, 3.0, 4.0], confidence=0.85)
        d = r.to_dict()
        required = {"page", "text", "bbox", "engine", "confidence", "error", "timestamp"}
        assert required.issubset(d.keys())
        assert d["page"] == 2
        assert d["text"] == "test"
        assert d["bbox"] == [1.0, 2.0, 3.0, 4.0]
        assert d["engine"] == "trocr"
        assert d["confidence"] == 0.85

    def test_json_serializable(self):
        from app.services.trocr_service import HwOcrResult
        r = HwOcrResult(page=1, text="abc", bbox=[0.0, 0.0, 50.0, 20.0], confidence=0.72)
        d = r.to_dict()
        json_str = json.dumps(d)  # must not raise
        parsed = json.loads(json_str)
        assert parsed["engine"] == "trocr"
        assert parsed["confidence"] == 0.72

    def test_error_result(self):
        from app.services.trocr_service import HwOcrResult
        r = HwOcrResult(page=1, text="", bbox=[0.0, 0.0, 10.0, 10.0], error="model unavailable")
        assert r.text == ""
        assert r.error == "model unavailable"
        assert r.to_dict()["error"] == "model unavailable"

    def test_bbox_list_of_floats(self):
        from app.services.trocr_service import HwOcrResult
        r = HwOcrResult(page=1, text="x", bbox=[10.5, 20.3, 100.7, 50.1])
        for coord in r.bbox:
            assert isinstance(coord, float)


# ---------------------------------------------------------------------------
# 2. Service-level import and status tests (no model)
# ---------------------------------------------------------------------------

class TestTrOCRServiceMeta:

    def test_module_imports(self):
        import app.services.trocr_service as svc  # noqa: F401

    def test_get_trocr_status_keys(self):
        from app.services.trocr_service import get_trocr_status
        s = get_trocr_status()
        required = {
            "model_name", "device", "transformers_available",
            "torch_available", "initialized", "init_attempted",
            "init_failed", "init_error", "local_files_only", "max_new_tokens",
        }
        assert required.issubset(s.keys())

    def test_transformers_available(self):
        from app.services.trocr_service import _TRANSFORMERS_AVAILABLE
        assert _TRANSFORMERS_AVAILABLE is True

    def test_torch_available(self):
        from app.services.trocr_service import _TORCH_AVAILABLE
        assert _TORCH_AVAILABLE is True

    def test_model_name(self):
        from app.services.trocr_service import _MODEL_NAME
        assert "trocr" in _MODEL_NAME.lower() or "handwritten" in _MODEL_NAME.lower()

    def test_device_is_string(self):
        from app.services.trocr_service import _DEVICE
        assert isinstance(_DEVICE, str)
        assert _DEVICE in {"cpu", "mps", "cuda"}

    def test_max_new_tokens(self):
        from app.services.trocr_service import _MAX_NEW_TOKENS
        assert isinstance(_MAX_NEW_TOKENS, int)
        assert _MAX_NEW_TOKENS > 0


# ---------------------------------------------------------------------------
# 3. Graceful degradation (monkeypatched model failure)
# ---------------------------------------------------------------------------

class TestTrOCRGracefulDegradation:

    def test_run_on_crop_returns_error_result_when_model_unavailable(
        self, monkeypatch
    ):
        """When _get_model_and_processor returns (None, None), run_trocr_on_crop
        must return an HwOcrResult with text='' and error set — never raise."""
        from PIL import Image
        import app.services.trocr_service as svc

        monkeypatch.setattr(svc, "_get_model_and_processor", lambda: (None, None))
        monkeypatch.setattr(svc, "_init_error", "test simulated failure")

        img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        result = svc.run_trocr_on_crop(img, page=1, bbox=[0.0, 0.0, 200.0, 50.0])

        assert result.text == ""
        assert result.error is not None
        assert result.page == 1
        assert result.engine == "trocr"
        assert result.bbox == [0.0, 0.0, 200.0, 50.0]

    def test_run_on_regions_with_unavailable_model(self, monkeypatch):
        """run_trocr_on_regions must not raise even when model is unavailable."""
        from PIL import Image
        import app.services.trocr_service as svc

        monkeypatch.setattr(svc, "_get_model_and_processor", lambda: (None, None))
        monkeypatch.setattr(svc, "_init_error", "simulated")

        page_img = Image.new("RGB", (400, 300), color=(255, 255, 255))
        regions = [
            {"bbox": [10.0, 20.0, 200.0, 60.0], "label": "line1"},
            {"bbox": [10.0, 70.0, 200.0, 110.0], "label": "line2"},
        ]
        results = svc.run_trocr_on_regions(page_img, regions, page=1)
        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r.error is not None
            assert r.text == ""
            assert r.engine == "trocr"

    def test_degenerate_bbox_is_skipped(self, monkeypatch):
        """A bbox where x2 <= x1 or y2 <= y1 must be silently skipped."""
        from PIL import Image
        import app.services.trocr_service as svc

        monkeypatch.setattr(svc, "_get_model_and_processor", lambda: (None, None))

        page_img = Image.new("RGB", (400, 300))
        regions = [
            {"bbox": [100.0, 50.0, 50.0, 100.0]},   # x2 < x1 — degenerate
            {"bbox": [10.0, 10.0, 200.0, 10.0]},    # y2 == y1 — degenerate
        ]
        results = svc.run_trocr_on_regions(page_img, regions, page=1)
        # Both skipped → empty list
        assert results == []

    def test_run_on_regions_empty_list_returns_empty(self, monkeypatch):
        from PIL import Image
        from app.services.trocr_service import run_trocr_on_regions

        img = Image.new("RGB", (100, 100))
        results = run_trocr_on_regions(img, [], page=1)
        assert results == []

    def test_run_on_crop_converts_non_rgb(self, monkeypatch):
        """Grayscale and RGBA images must be handled without error."""
        from PIL import Image
        import app.services.trocr_service as svc

        monkeypatch.setattr(svc, "_get_model_and_processor", lambda: (None, None))

        for mode in ("L", "RGBA", "P"):
            img = Image.new(mode, (100, 40), color=200 if mode == "L" else (200, 200, 200, 255))
            # Should not raise even with unavailable model
            result = svc.run_trocr_on_crop(img, page=1, bbox=[0.0, 0.0, 100.0, 40.0])
            assert isinstance(result, svc.HwOcrResult)


# ---------------------------------------------------------------------------
# 4. Model initialization test (loads actual TrOCR model)
# ---------------------------------------------------------------------------

class TestTrOCRModelInit:
    """These tests actually load the TrOCR model. They are slow but critical.
    They require network access on first run (model downloaded to HF cache).
    """

    def test_model_initializes(self):
        """TrOCR model and processor must load without error."""
        from app.services.trocr_service import _get_model_and_processor, get_trocr_status
        proc, model = _get_model_and_processor()
        status = get_trocr_status()

        assert proc is not None, (
            f"TrOCR processor failed to load. Status: {status}"
        )
        assert model is not None, (
            f"TrOCR model failed to load. Status: {status}"
        )
        assert status["initialized"] is True
        assert status["init_failed"] is False
        assert status["init_error"] is None

    def test_status_reflects_initialization(self):
        from app.services.trocr_service import _get_model_and_processor, get_trocr_status
        _get_model_and_processor()  # ensure initialized
        status = get_trocr_status()
        assert status["init_attempted"] is True
        assert status["device"] in {"cpu", "mps", "cuda"}


# ---------------------------------------------------------------------------
# 5. Real inference on synthetic handwriting sample
# ---------------------------------------------------------------------------

class TestTrOCRInference:
    """End-to-end inference tests.

    IMPORTANT: We do NOT assert specific recognized text for synthetic
    images. TrOCR was trained on real handwriting (IAM dataset). PIL-
    rendered text does NOT look like handwriting to the model. The purpose
    of these tests is to verify the pipeline plumbing is correct, not to
    validate OCR accuracy.

    Real accuracy should be tested with actual scanned handwritten samples.
    """

    def test_run_on_single_crop_returns_result_struct(self):
        """run_trocr_on_crop must return a valid HwOcrResult on any image."""
        from app.services.trocr_service import HwOcrResult, run_trocr_on_crop
        img = _make_handwriting_like_image("hello world")
        bbox = [0.0, 0.0, float(img.width), float(img.height)]
        result = run_trocr_on_crop(img, page=1, bbox=bbox)

        assert isinstance(result, HwOcrResult)
        assert result.page == 1
        assert result.engine == "trocr"
        assert result.bbox == bbox
        assert isinstance(result.text, str)  # may be wrong text — that's OK
        # Confidence is either a float in [0,1] or None
        if result.confidence is not None:
            assert 0.0 <= result.confidence <= 1.0

    def test_run_on_crop_returns_string_text(self):
        """text field must always be a string, even if recognition fails."""
        from app.services.trocr_service import run_trocr_on_crop
        img = _make_handwriting_like_image("Land Record")
        result = run_trocr_on_crop(img, page=2, bbox=[5.0, 5.0, 395.0, 75.0])
        assert isinstance(result.text, str)

    def test_run_on_crop_page_number_preserved(self):
        from app.services.trocr_service import run_trocr_on_crop
        img = _make_handwriting_like_image("test")
        result = run_trocr_on_crop(img, page=3, bbox=[0.0, 0.0, 100.0, 30.0])
        assert result.page == 3

    def test_run_on_crop_bbox_preserved(self):
        from app.services.trocr_service import run_trocr_on_crop
        img = _make_handwriting_like_image("test")
        bbox = [10.0, 20.0, 300.0, 70.0]
        result = run_trocr_on_crop(img, page=1, bbox=bbox)
        assert result.bbox == bbox

    def test_result_is_json_serializable(self):
        from app.services.trocr_service import run_trocr_on_crop
        img = _make_handwriting_like_image("Survey No 245")
        result = run_trocr_on_crop(img, page=1, bbox=[0.0, 0.0, 400.0, 80.0])
        d = result.to_dict()
        json_str = json.dumps(d, default=str)  # must not raise
        parsed = json.loads(json_str)
        assert parsed["engine"] == "trocr"

    def test_run_on_regions_batch(self):
        """run_trocr_on_regions must return one result per valid region."""
        from app.services.trocr_service import run_trocr_on_regions
        page_img = _make_synthetic_page_image([
            "Owner: Ramesh Sharma",
            "Survey: 245/A",
        ])
        regions = [
            {"bbox": [10.0, 10.0, 680.0, 55.0], "label": "owner"},
            {"bbox": [10.0, 55.0, 680.0, 100.0], "label": "survey"},
        ]
        results = run_trocr_on_regions(page_img, regions, page=1)
        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r.page == 1
            assert r.engine == "trocr"
            assert isinstance(r.text, str)
            assert len(r.bbox) == 4

    def test_confidence_proxy_is_float_or_none(self):
        """Confidence must be a float in [0,1] or None — never negative."""
        from app.services.trocr_service import run_trocr_on_crop
        img = _make_handwriting_like_image("test confidence")
        result = run_trocr_on_crop(img, page=1, bbox=[0.0, 0.0, 400.0, 80.0])
        if result.confidence is not None:
            assert isinstance(result.confidence, float)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Confidence out of range: {result.confidence}"
            )

    def test_report_actual_trocr_output(self):
        """Process a synthetic handwriting sample and print the real TrOCR output.

        We do NOT assert specific text — only report what the model produces.
        This is intentional: PIL-rendered text is not real handwriting.
        """
        from app.services.trocr_service import run_trocr_on_crop, get_trocr_status

        status = get_trocr_status()
        print(f"\n{'='*60}")
        print("TrOCR Engine Status:")
        print(json.dumps(status, indent=2))
        print(f"{'='*60}")

        samples = [
            "Survey No: 245/A",
            "Village: Wagholi",
            "Owner: Ramesh Kumar",
        ]
        for sample_text in samples:
            img = _make_handwriting_like_image(sample_text, width=500, height=80)
            bbox = [0.0, 0.0, 500.0, 80.0]
            result = run_trocr_on_crop(img, page=1, bbox=bbox)

            print(f"\nInput:      {sample_text!r}")
            print(f"TrOCR out:  {result.text!r}")
            print(f"Confidence: {result.confidence}")
            print(f"Error:      {result.error}")
            print(f"Engine:     {result.engine}")
            print(f"Device:     {status['device']}")

        # Only assert the structural contract, not accuracy
        assert result.engine == "trocr"
        assert isinstance(result.text, str)
        print(f"\n{'='*60}")
        print("NOTE: Accuracy on PIL-rendered text is not meaningful.")
        print("Test with real scanned handwriting for accuracy evaluation.")
        print(f"{'='*60}\n")
