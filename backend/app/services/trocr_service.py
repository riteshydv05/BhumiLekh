"""Handwriting OCR Service using Microsoft TrOCR.

Model: microsoft/trocr-base-handwritten  (Hugging Face)

Design
------
* Model + processor are loaded ONCE per worker process via a thread-safe
  singleton. Loading is lazy — only triggered on the first actual inference
  call, never at import time.
* PaddleOCR remains the primary engine for printed text. This service is
  invoked only when:
    - handwriting is explicitly requested for a region, OR
    - a detected block is flagged as likely handwritten.
* TrOCR is applied to individual crop regions (``PIL.Image`` objects),
  not to full-page images. Callers are responsible for providing the
  correct crop and the corresponding bounding box in page coordinates.
* If the model cannot initialize (missing weights, no HuggingFace cache,
  network down) the service degrades gracefully: every call returns an
  ``HwOcrResult`` with ``engine="trocr"`` and ``error`` set, without
  raising or crashing the Celery worker.

Transformers 5.x compatibility note
-------------------------------------
TrOCR's processor uses a RoBERTa tokenizer. ``TrOCRProcessor.from_pretrained``
fails on transformers ≥ 5.x when the fast tokenizer serialization is
missing. We work around this by constructing the processor manually from
its two components (``ViTImageProcessor`` + ``RobertaTokenizer``), which
load correctly on all versions.

Environment variables
---------------------
TROCR_MODEL_NAME     HuggingFace model ID (default: microsoft/trocr-base-handwritten)
TROCR_DEVICE         cpu | mps | cuda  (default: auto-detected)
TROCR_LOCAL_FILES    true to forbid network download (default: false)
TROCR_MAX_NEW_TOKENS Max decode tokens per region (default: 128)

Confidence note
---------------
TrOCR's ``generate()`` does not expose a scalar confidence score by default.
We derive a proxy from the per-token softmax probabilities of the chosen
tokens, averaged across the generated sequence. This is a rough proxy, NOT
a calibrated confidence. Values are logged and stored as-is with this caveat
documented clearly.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_MODEL_NAME = os.environ.get(
    "TROCR_MODEL_NAME", "microsoft/trocr-base-handwritten"
)
_LOCAL_FILES = os.environ.get("TROCR_LOCAL_FILES", "false").lower() == "true"
_MAX_NEW_TOKENS = int(os.environ.get("TROCR_MAX_NEW_TOKENS", "128"))


def _resolve_device() -> str:
    """Pick the best available compute device: mps > cuda > cpu."""
    explicit = os.environ.get("TROCR_DEVICE", "").strip().lower()
    if explicit:
        return explicit
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


_DEVICE = _resolve_device()

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------
_processor = None
_model = None
_init_lock = threading.Lock()
_init_attempted = False
_init_failed = False
_init_error: str | None = None

# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------
try:
    from transformers import (  # noqa: F401
        TrOCRProcessor,
        VisionEncoderDecoderModel,
        ViTImageProcessor,
        RobertaTokenizer,
    )
    _TRANSFORMERS_AVAILABLE = True
except ImportError as _ie:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not installed — TrOCR disabled: %s", _ie)

try:
    import torch as _torch_guard  # noqa: F401
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    logger.warning("torch not installed — TrOCR disabled")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class HwOcrResult:
    """Result for a single handwriting region.

    Normalized output matching the required schema::

        {
            "page": 1,
            "text": "...",
            "bbox": [x1, y1, x2, y2],
            "engine": "trocr",
            "confidence": 0.84
        }

    ``confidence`` is a mean token probability (proxy score, not calibrated).
    ``error`` is set when inference fails; ``text`` will be empty in that case.
    """
    page: int
    text: str
    bbox: list[float]
    engine: str = "trocr"
    confidence: float | None = None   # None when not computable
    error: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "text": self.text,
            "bbox": self.bbox,
            "engine": self.engine,
            "confidence": self.confidence,
            "error": self.error,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Singleton init — component-level loading for transformers 5.x compatibility
# ---------------------------------------------------------------------------
def _get_model_and_processor():
    """Return (processor, model) singleton. Thread-safe. Never raises."""
    global _processor, _model, _init_attempted, _init_failed, _init_error

    if not (_TRANSFORMERS_AVAILABLE and _TORCH_AVAILABLE):
        return None, None
    if _processor is not None:
        return _processor, _model
    if _init_failed:
        return None, None

    with _init_lock:
        if _processor is not None:
            return _processor, _model
        if _init_failed:
            return None, None

        _init_attempted = True
        logger.info(
            "TrOCR: loading model %r on device=%s (local_files_only=%s)",
            _MODEL_NAME, _DEVICE, _LOCAL_FILES,
        )
        try:
            import torch
            from transformers import (
                RobertaTokenizer,
                TrOCRProcessor,
                VisionEncoderDecoderModel,
                ViTImageProcessor,
            )

            # Build processor from components to avoid transformers 5.x
            # fast-tokenizer serialization issue with TrOCR's RoBERTa tokenizer
            logger.debug("TrOCR: loading ViTImageProcessor...")
            img_processor = ViTImageProcessor.from_pretrained(
                _MODEL_NAME,
                local_files_only=_LOCAL_FILES,
            )

            logger.debug("TrOCR: loading RobertaTokenizer (slow)...")
            tokenizer = RobertaTokenizer.from_pretrained(
                _MODEL_NAME,
                local_files_only=_LOCAL_FILES,
            )

            _processor = TrOCRProcessor(
                image_processor=img_processor,
                tokenizer=tokenizer,
            )
            logger.debug("TrOCR: processor assembled")

            logger.debug("TrOCR: loading VisionEncoderDecoderModel...")
            _model = VisionEncoderDecoderModel.from_pretrained(
                _MODEL_NAME,
                local_files_only=_LOCAL_FILES,
            )
            _model.to(_DEVICE)
            _model.eval()

            logger.info(
                "TrOCR: model loaded successfully (%s, device=%s)",
                _MODEL_NAME, _DEVICE,
            )
        except Exception as exc:
            _init_failed = True
            _init_error = str(exc)
            logger.error(
                "TrOCR: model load failed — handwriting OCR disabled: %s",
                exc, exc_info=True,
            )
            return None, None

    return _processor, _model


# ---------------------------------------------------------------------------
# Confidence derivation
# ---------------------------------------------------------------------------
def _derive_confidence(scores: tuple, generated_ids) -> float | None:
    """Derive a proxy confidence from per-token generation probabilities.

    ``scores`` is a tuple of tensors (one per generated step), each of shape
    (batch=1, vocab_size) — raw logits before softmax. We apply softmax per
    step and take the probability of the actually chosen token, then average.

    Returns float in roughly [0, 1] or None if derivation fails.

    Limitation: this is a proxy score, NOT a calibrated confidence.
    High values indicate the model was certain about its token choices;
    they do not guarantee textual accuracy.
    """
    try:
        import torch
        import torch.nn.functional as F

        token_probs: list[float] = []
        for step_idx, score_tensor in enumerate(scores):
            # score_tensor shape: (1, vocab_size) — raw logits
            probs = F.softmax(score_tensor.float(), dim=-1)
            # generated_ids.sequences: (1, seq_len), offset by 1 for BOS
            chosen_token = generated_ids.sequences[0, step_idx + 1]
            prob = probs[0, chosen_token].item()
            token_probs.append(prob)

        if not token_probs:
            return None
        return round(sum(token_probs) / len(token_probs), 6)

    except Exception as exc:
        logger.debug("TrOCR: confidence derivation failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Core inference
# ---------------------------------------------------------------------------
def run_trocr_on_crop(
    image: "PILImage",
    page: int,
    bbox: list[float],
) -> HwOcrResult:
    """Run TrOCR on a single image crop and return an HwOcrResult.

    Args:
        image:  PIL Image of the cropped handwriting region (any mode).
                Should be pre-cropped to the region of interest.
                Will be converted to RGB internally if needed.
        page:   1-indexed page number (preserved in output).
        bbox:   [x1, y1, x2, y2] of this region in full-page pixel coords.
                Stored as-is in the result for downstream use.

    Returns:
        HwOcrResult — never raises. On failure, text="" and error is set.

    Confidence note:
        Reports mean token probability as a proxy score. NOT calibrated.
        Treat as a relative indicator of model certainty, not textual accuracy.
    """
    proc, model = _get_model_and_processor()

    if proc is None or model is None:
        reason = _init_error or "TrOCR model not available"
        logger.warning("TrOCR: skipping inference on page %d — %s", page, reason)
        return HwOcrResult(
            page=page,
            text="",
            bbox=list(bbox),
            confidence=None,
            error=reason,
        )

    try:
        import torch

        # Ensure RGB — TrOCR's ViT encoder requires 3-channel input
        if image.mode != "RGB":
            image = image.convert("RGB")

        pixel_values = proc(images=image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(_DEVICE)

        with torch.no_grad():
            generated = model.generate(
                pixel_values,
                max_new_tokens=_MAX_NEW_TOKENS,
                output_scores=True,
                return_dict_in_generate=True,
            )

        # Decode the recognized text
        text = proc.batch_decode(
            generated.sequences,
            skip_special_tokens=True,
        )[0].strip()

        # Derive confidence proxy from token scores
        confidence = _derive_confidence(generated.scores, generated)

        logger.info(
            "TrOCR: page=%d chars=%d confidence=%s bbox=%s",
            page, len(text),
            f"{confidence:.4f}" if confidence is not None else "n/a",
            bbox,
        )
        return HwOcrResult(
            page=page,
            text=text,
            bbox=list(bbox),
            confidence=confidence,
        )

    except Exception as exc:
        logger.error(
            "TrOCR: inference failed on page %d: %s", page, exc, exc_info=True
        )
        return HwOcrResult(
            page=page,
            text="",
            bbox=list(bbox),
            confidence=None,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Batch helper — run TrOCR over multiple regions on one page
# ---------------------------------------------------------------------------
def run_trocr_on_regions(
    page_image: "PILImage",
    regions: list[dict],
    page: int,
) -> list[HwOcrResult]:
    """Run TrOCR over a list of region dicts on a single page.

    Args:
        page_image:  Full-page PIL Image used for cropping.
        regions:     List of dicts, each requiring key ``bbox`` →
                     [x1, y1, x2, y2] in page-image pixels.
                     Optional key ``label`` for logging.
        page:        1-indexed page number.

    Returns:
        List of HwOcrResult (one per region). Never raises.
    """
    results: list[HwOcrResult] = []

    if not regions:
        logger.debug("TrOCR: no regions to process on page %d", page)
        return results

    w, h = page_image.size

    for region in regions:
        bbox = region.get("bbox", [0.0, 0.0, float(w), float(h)])
        label = region.get("label", "region")
        try:
            x1 = max(0, int(bbox[0]))
            y1 = max(0, int(bbox[1]))
            x2 = min(w, int(bbox[2]))
            y2 = min(h, int(bbox[3]))

            if x2 <= x1 or y2 <= y1:
                logger.warning(
                    "TrOCR: degenerate bbox %s for %r on page %d — skipping",
                    bbox, label, page,
                )
                continue

            crop = page_image.crop((x1, y1, x2, y2))
            results.append(run_trocr_on_crop(crop, page=page, bbox=bbox))

        except Exception as exc:
            logger.error(
                "TrOCR: region crop failed on page %d bbox=%s: %s",
                page, bbox, exc,
            )
            results.append(HwOcrResult(
                page=page,
                text="",
                bbox=list(bbox),
                error=f"Crop failed: {exc}",
            ))

    return results


# ---------------------------------------------------------------------------
# Status / diagnostics
# ---------------------------------------------------------------------------
def get_trocr_status() -> dict:
    """Return engine status dict for health checks and diagnostics."""
    return {
        "model_name": _MODEL_NAME,
        "device": _DEVICE,
        "transformers_available": _TRANSFORMERS_AVAILABLE,
        "torch_available": _TORCH_AVAILABLE,
        "initialized": _processor is not None and _model is not None,
        "init_attempted": _init_attempted,
        "init_failed": _init_failed,
        "init_error": _init_error,
        "local_files_only": _LOCAL_FILES,
        "max_new_tokens": _MAX_NEW_TOKENS,
    }
