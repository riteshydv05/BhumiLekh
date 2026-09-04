"""LayoutLMv3 Document Layout Understanding Service.

Purpose:
    Convert OCR results (text + bounding boxes + page dimensions) into the
    representation required by LayoutLMv3 for document layout understanding.

Architecture:
    OcrDocument (raw OCR) → LayoutDocument (layout-processed) → LayoutLMv3 inputs

The raw OCR results are never modified. Layout information is stored separately
in LayoutBlock / LayoutPage / LayoutDocument structures.

LayoutLMv3 requires:
    - tokenized words (one token per word)
    - normalized bounding boxes [x1, y1, x2, y2] in range [0, 1000]
    - page image (PIL Image)
    - attention mask and token type ids

Important:
    The base microsoft/layoutlmv3-base checkpoint is a general-purpose
    document layout model trained on PubLayNet. It does NOT directly classify
    land-record fields (survey numbers, owner names, etc.) without fine-tuning.

    This service provides the preparation/inference architecture. Future
    fine-tuning on land-record datasets is required for field-level
    classification. See docs/FINE_TUNING.md for details.

Example structure::

    LayoutDocument
      └── pages: list[LayoutPage]
            ├── page_num: int
            ├── width: int
            ├── height: int
            ├── image: PIL.Image
            ├── ocr_blocks: list[OcrBlock]      ← raw OCR, unchanged
            └── layout_blocks: list[LayoutBlock]  ← processed for LayoutLMv3
                  ├── words: list[str]
                  ├── bbox_normalized: [x1, y1, x2, y2]  # 0-1000 range
                  ├── block_type: str          # "text" | "table" | "form" | "field"
                  └── confidence: float
"""
from __future__ import annotations

import logging
import torch
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LayoutLMv3 requires bounding boxes in [0, 1000] normalized coordinate space
# ---------------------------------------------------------------------------
LAYOUTLMV3_MAX_COORD = 1000


# ---------------------------------------------------------------------------
# Dataclasses — separate storage for layout-processed data (not OCR)
# ---------------------------------------------------------------------------

@dataclass
class LayoutBlock:
    """A single layout-processed block ready for LayoutLMv3 input.

    Unlike OcrBlock (which stores raw pixel coordinates), LayoutBlock
    stores normalized coordinates and additional metadata needed by
    LayoutLMv3.

    Fields:
        words: Tokenized words in this block.
        bbox_normalized: Bounding box [x1, y1, x2, y2] in [0, 1000] range.
        block_type: Semantic type — "text", "table", "form", "field",
                    "title", "signature", "unknown".
        confidence: Original OCR confidence (preserved from OcrBlock).
        ocr_block_index: Reference to the source OcrBlock index.
        page_num: 1-indexed page number.
        region_hint: Optional hint for land-record specific regions
                     (e.g., "survey_number_field", "owner_name_field").
    """

    words: list[str]
    bbox_normalized: list[float]
    block_type: str = "text"
    confidence: float = 0.0
    ocr_block_index: int = 0
    page_num: int = 1
    region_hint: str | None = None

    def to_dict(self) -> dict:
        return {
            "words": self.words,
            "bbox_normalized": self.bbox_normalized,
            "block_type": self.block_type,
            "confidence": self.confidence,
            "ocr_block_index": self.ocr_block_index,
            "page_num": self.page_num,
            "region_hint": self.region_hint,
        }


@dataclass
class LayoutPage:
    """A page containing both raw OCR blocks and layout-processed blocks.

    The OCR blocks are preserved unchanged. The layout blocks are derived
    from OCR blocks but stored separately.

    Fields:
        page_num: 1-indexed page number.
        width: Page width in pixels.
        height: Page height in pixels.
        image: PIL Image of the page (may be None if not available).
        ocr_blocks: Raw OCR blocks (unchanged from OCR service output).
        layout_blocks: Layout-processed blocks for LayoutLMv3.
    """

    page_num: int
    width: int = 0
    height: int = 0
    image: Any = None  # PIL.Image or None
    ocr_blocks: list[dict] = field(default_factory=list)
    layout_blocks: list[LayoutBlock] = field(default_factory=list)

    @property
    def ocr_text(self) -> str:
        """Concatenate all raw OCR block texts."""
        return "\n".join(
            b["text"] for b in self.ocr_blocks if b.get("text", "").strip()
        )

    @property
    def has_layout_blocks(self) -> bool:
        return len(self.layout_blocks) > 0

    def to_dict(self) -> dict:
        return {
            "page_num": self.page_num,
            "width": self.width,
            "height": self.height,
            "ocr_block_count": len(self.ocr_blocks),
            "layout_block_count": len(self.layout_blocks),
            "layout_blocks": [lb.to_dict() for lb in self.layout_blocks],
        }


@dataclass
class LayoutDocument:
    """Full layout-processed document.

    Contains both the original OcrDocument data (for reference) and
    the LayoutLMv3-ready layout blocks stored separately.

    Fields:
        pages: List of LayoutPage objects.
        method: OCR method used ("paddle", "pypdf_text", etc.).
        ocr_raw: Reference to the original OcrDocument dict (unchanged).
        page_images: Dict mapping page_num → PIL Image.
    """

    pages: list[LayoutPage] = field(default_factory=list)
    method: str = "none"
    ocr_raw: dict | None = None
    page_images: dict[int, Any] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_layout_blocks(self) -> int:
        return sum(len(p.layout_blocks) for p in self.pages)

    @property
    def has_page_images(self) -> bool:
        return len(self.page_images) > 0

    def to_dict(self) -> dict:
        return {
            "page_count": self.page_count,
            "method": self.method,
            "total_layout_blocks": self.total_layout_blocks,
            "has_page_images": self.has_page_images,
            "pages": [p.to_dict() for p in self.pages],
        }


# ---------------------------------------------------------------------------
# Bounding Box Utilities
# ---------------------------------------------------------------------------

def normalize_bbox(
    bbox: list[float],
    page_width: int,
    page_height: int,
    max_coord: int = LAYOUTLMV3_MAX_COORD,
) -> list[float]:
    """Normalize pixel bounding box to LayoutLMv3 coordinate space [0, 1000].

    LayoutLMv3 expects bounding boxes as [x1, y1, x2, y2] where coordinates
    are in the range [0, 1000] relative to the page dimensions.

    Formula::
        norm_coord = round(pixel_coord / page_dim * max_coord)

    Args:
        bbox: Original bbox [x1, y1, x2, y2] in pixel coordinates.
        page_width: Page width in pixels.
        page_height: Page height in pixels.
        max_coord: Maximum coordinate value (default 1000 for LayoutLMv3).

    Returns:
        Normalized bbox [x1, y1, x2, y2] in [0, max_coord] range.

    Raises:
        ValueError: If page dimensions are zero or negative.
    """
    if page_width <= 0 or page_height <= 0:
        raise ValueError(
            f"Invalid page dimensions: width={page_width}, height={page_height}. "
            "Must be positive integers."
        )

    if len(bbox) != 4:
        raise ValueError(
            f"Bounding box must have exactly 4 coordinates, got {len(bbox)}: {bbox}"
        )

    x1, y1, x2, y2 = bbox
    x1_norm = max(0, min(max_coord, round(x1 / page_width * max_coord)))
    y1_norm = max(0, min(max_coord, round(y1 / page_height * max_coord)))
    x2_norm = max(0, min(max_coord, round(x2 / page_width * max_coord)))
    y2_norm = max(0, min(max_coord, round(y2 / page_height * max_coord)))

    # Ensure x2 >= x1 and y2 >= y1 after normalization
    if x2_norm < x1_norm:
        x1_norm, x2_norm = x2_norm, x1_norm
    if y2_norm < y1_norm:
        y1_norm, y2_norm = y2_norm, y1_norm

    # Clamp to valid range
    return [
        max(0, min(max_coord, x1_norm)),
        max(0, min(max_coord, y1_norm)),
        max(0, min(max_coord, x2_norm)),
        max(0, min(max_coord, y2_norm)),
    ]


def denormalize_bbox(
    bbox_normalized: list[float],
    page_width: int,
    page_height: int,
    max_coord: int = LAYOUTLMV3_MAX_COORD,
) -> list[float]:
    """Convert normalized bbox back to pixel coordinates.

    Inverse of normalize_bbox.

    Returns:
        Bounding box [x1, y1, x2, y2] in pixel coordinates.
    """
    if page_width <= 0 or page_height <= 0:
        raise ValueError("Page dimensions must be positive.")

    x1 = bbox_normalized[0] / max_coord * page_width
    y1 = bbox_normalized[1] / max_coord * page_height
    x2 = bbox_normalized[2] / max_coord * page_width
    y2 = bbox_normalized[3] / max_coord * page_height

    return [x1, y1, x2, y2]


# ---------------------------------------------------------------------------
# OCR-to-Layout Conversion
# ---------------------------------------------------------------------------

def classify_block_type(ocr_block: dict) -> str:
    """Classify an OCR block into a semantic type.

    Uses heuristic rules based on text content and confidence.
    This is a rule-based classifier; fine-tuning a model is required
    for accurate land-record field classification.

    Classification rules:
        - "title": Short uppercase text (likely document title/heading)
        - "form": Contains form-like patterns (labels with colons)
        - "table": Text with tab/pipe-separated columns
        - "field": Key-value pairs with recognized land-record keywords
        - "text": Default — normal paragraph text
        - "signature": Very short text that might be a signature

    Note:
        This heuristic classification is NOT sufficient for production
        land-record field extraction. Fine-tuning LayoutLMv3 on
        annotated land-record documents is required.
    """
    text = ocr_block.get("text", "")
    if text is not None:
        text = str(text).strip()
    confidence = ocr_block.get("confidence", 0.0)

    if not text:
        return "unknown"

    # Title detection: short uppercase text
    if text.isupper() and 5 < len(text) < 80:
        return "title"

    # Table detection: tab or pipe separated content
    if "\t" in text or "|" in text:
        return "table"

    # Form detection: contains colon-separated key-value pairs
    if ":" in text and len(text.split(":")) >= 2:
        key = text.split(":")[0].strip().lower()
        land_record_keywords = {
            "survey", "district", "area", "village", "taluka", "owner",
            "kaderno", "pgis", "plot", "land", "measure", "document",
            "date", "registration", "section", "block", "tehsil",
            "total", "name", "father", "husband", "wife",
        }
        if any(kw in key for kw in land_record_keywords):
            return "field"
        return "form"

    # Signature detection: very short text
    if len(text) <= 3 and confidence > 0.5:
        return "signature"

    return "text"


def convert_ocr_blocks_to_layout(
    ocr_blocks: list[dict],
    page_width: int,
    page_height: int,
    page_num: int,
) -> list[LayoutBlock]:
    """Convert OCR block dicts into LayoutBlock objects with normalized bboxes.

    Each OCR block becomes one LayoutBlock. The raw OCR data is preserved
    in LayoutBlock.ocr_block_index for reference.

    Args:
        ocr_blocks: List of OCR block dicts from the OCR service.
        page_width: Page width in pixels.
        page_height: Page height in pixels.
        page_num: 1-indexed page number.

    Returns:
        List of LayoutBlock objects with normalized bounding boxes.
    """
    layout_blocks: list[LayoutBlock] = []

    # Handle non-list or None ocr_blocks
    if not isinstance(ocr_blocks, list):
        logger.warning(
            "Page %d: ocr_blocks is not a list (%s). Returning empty.",
            page_num, type(ocr_blocks),
        )
        return layout_blocks

    for idx, block in enumerate(ocr_blocks):
        # Skip non-dict blocks
        if not isinstance(block, dict):
            logger.warning(
                "Block %d on page %d is not a dict (%s). Skipping.",
                idx, page_num, type(block),
            )
            continue

        text = block.get("text", "")
        if text is None:
            continue
        text = str(text).strip()
        if not text:
            continue

        bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
        confidence = block.get("confidence", 0.0)

        # Handle missing/None bbox
        if bbox is None:
            bbox = [0.0, 0.0, 0.0, 0.0]

        # Normalize bounding box to LayoutLMv3 coordinate space
        try:
            bbox_normalized = normalize_bbox(
                bbox, page_width, page_height
            )
        except ValueError as exc:
            logger.warning(
                "Block %d on page %d: %s. Using zero bbox.",
                idx, page_num, exc,
            )
            bbox_normalized = [0.0, 0.0, 0.0, 0.0]

        block_type = classify_block_type(block)

        # Split text into words for token-level processing
        words = text.split()
        if not words:
            continue

        layout_block = LayoutBlock(
            words=words,
            bbox_normalized=bbox_normalized,
            block_type=block_type,
            confidence=confidence,
            ocr_block_index=idx,
            page_num=page_num,
        )
        layout_blocks.append(layout_block)

    return layout_blocks


def build_layout_document(
    ocr_document: dict,
    page_images: dict[int, Any] | None = None,
) -> LayoutDocument:
    """Build a LayoutDocument from an OcrDocument dict.

    This is the main entry point for converting raw OCR results into
    LayoutLMv3-ready layout information.

    The original OCR data is preserved in the LayoutDocument.ocr_raw field
    and is never modified. Layout information is stored separately.

    Args:
        ocr_document: The OcrDocument dict from the OCR service
                      (must have "pages" key with page data).
        page_images: Optional dict mapping page_num → PIL Image.

    Returns:
        LayoutDocument with layout-processed blocks.
    """
    pages_data = ocr_document.get("pages", [])
    method = ocr_document.get("method", "none")
    layout_pages: list[LayoutPage] = []
    images = page_images or {}

    for page_data in pages_data:
        page_num = page_data.get("page", 1)
        width = page_data.get("width", 0)
        height = page_data.get("height", 0)
        ocr_blocks = page_data.get("blocks", []) or []

        # Convert OCR blocks to layout blocks
        layout_blocks = convert_ocr_blocks_to_layout(
            ocr_blocks, width, height, page_num
        )

        layout_page = LayoutPage(
            page_num=page_num,
            width=width,
            height=height,
            image=images.get(page_num),
            ocr_blocks=ocr_blocks,
            layout_blocks=layout_blocks,
        )
        layout_pages.append(layout_page)

    return LayoutDocument(
        pages=layout_pages,
        method=method,
        ocr_raw=ocr_document,
        page_images=images,
    )


# ---------------------------------------------------------------------------
# LayoutLMv3 Input Preparation
# ---------------------------------------------------------------------------

def prepare_layoutlmv3_inputs(
    layout_document: LayoutDocument,
    page_num: int | None = None,
) -> dict[str, Any]:
    """Prepare inputs for LayoutLMv3 model inference on a specific page.

    Converts LayoutBlock data into the format expected by
    LayoutLMv3Processor (text tokens + normalized bboxes + image).

    LayoutLMv3Processor expects:
        - images: PIL Image(s)
        - text: list of words (tokenized per word)
        - boxes: list of normalized bboxes [x1, y1, x2, y2] in [0, 1000]

    Each LayoutBlock becomes one "word" in the LayoutLMv3 input.
    Blocks within a page are concatenated in order.

    Args:
        layout_document: The layout-processed document.
        page_num: Specific page to prepare. If None, uses first page.

    Returns:
        Dict with keys: "image", "words", "bboxes" ready for LayoutLMv3Processor.
        Returns empty dict if page not found or no layout blocks.
    """
    # Find the target page
    target_page = None
    for p in layout_document.pages:
        if page_num is None and target_page is None:
            target_page = p
        elif p.page_num == page_num:
            target_page = p
            break

    if target_page is None:
        logger.warning("Page %s not found in layout document", page_num)
        return {}

    if not target_page.has_layout_blocks:
        logger.warning("Page %d has no layout blocks", target_page.page_num)
        return {}

    # Collect all words and bboxes from layout blocks
    all_words: list[str] = []
    all_bboxes: list[list[float]] = []

    for lb in target_page.layout_blocks:
        all_words.extend(lb.words)
        # Duplicate bbox for each word in the block (LayoutLMv3 needs
        # one bbox per token/word)
        for _ in lb.words:
            all_bboxes.append(lb.bbox_normalized)

    if not all_words:
        return {}

    return {
        "image": target_page.image,
        "words": all_words,
        "bboxes": all_bboxes,
        "page_num": target_page.page_num,
        "page_width": target_page.width,
        "page_height": target_page.height,
    }


def prepare_layoutlmv3_batch(
    layout_document: LayoutDocument,
    page_nums: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Prepare inputs for multiple pages.

    Args:
        layout_document: The layout-processed document.
        page_nums: List of page numbers to prepare. If None, all pages.

    Returns:
        List of input dicts, one per page.
    """
    if page_nums is None:
        page_nums = [p.page_num for p in layout_document.pages]

    inputs_list: list[dict[str, Any]] = []
    for pn in page_nums:
        inputs = prepare_layoutlmv3_inputs(layout_document, page_num=pn)
        if inputs:
            inputs_list.append(inputs)

    return inputs_list


# ---------------------------------------------------------------------------
# LayoutLMv3 Inference Service
# ---------------------------------------------------------------------------

@dataclass
class LayoutInferenceResult:
    """Result of a LayoutLMv3 inference call.

    Note:
        With the base microsoft/layoutlmv3-base checkpoint (trained on
        PubLayNet), these results indicate document structure (text blocks,
        tables, forms, titles) but NOT land-record field classification.
        For land-record field classification, fine-tuning is required.
    """

    page_num: int
    blocks: list[dict]  # Each dict has: words, bbox, block_type, score
    document_structure: str | None = None
    requires_fine_tuning: bool = True
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "page_num": self.page_num,
            "blocks": self.blocks,
            "document_structure": self.document_structure,
            "requires_fine_tuning": self.requires_fine_tuning,
            "message": self.message,
        }


class LayoutLMv3ProcessorService:
    """Service for loading LayoutLMv3 model and running inference.

    This service wraps the LayoutLMv3 model for document layout understanding.
    With the base checkpoint, it provides document structure detection
    (PubLayNet classes). For land-record-specific field classification,
    the model must be fine-tuned.

    Usage::

        service = LayoutLMv3ProcessorService()
        layout_doc = build_layout_document(ocr_dict, page_images)
        inputs = prepare_layoutlmv3_inputs(layout_doc, page_num=1)
        result = service.infer(layout_doc, page_num=1)
    """

    def __init__(self) -> None:
        self.model = None
        self.processor = None
        self._initialized = False
        self._init_error: str | None = None

    def initialize(self) -> bool:
        """Initialize the LayoutLMv3 model and processor.

        Loads microsoft/layoutlmv3-base checkpoint.

        Returns:
            True if initialization succeeded, False otherwise.
            Does not raise — errors are stored in self._init_error.
        """
        if self._initialized:
            return self._initialized

        try:
            from transformers import (
                LayoutLMv3ForTokenClassification,
                LayoutLMv3Processor,
            )

            logger.info(
                "Loading LayoutLMv3 processor and model (microsoft/layoutlmv3-base)..."
            )

            try:
                self.processor = LayoutLMv3Processor.from_pretrained(
                    "microsoft/layoutlmv3-base",
                    apply_ocr=False,
                    local_files_only=True,
                )
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                    "microsoft/layoutlmv3-base",
                    local_files_only=True,
                )
            except Exception:
                self.processor = LayoutLMv3Processor.from_pretrained(
                    "microsoft/layoutlmv3-base",
                    apply_ocr=False,
                )
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                    "microsoft/layoutlmv3-base"
                )
            self.model.eval()

            self._initialized = True
            logger.info("LayoutLMv3 processor and model loaded successfully.")
            return True

        except Exception as exc:
            self._init_error = str(exc)
            logger.error(
                "LayoutLMv3 initialization failed: %s", exc, exc_info=True
            )
            return False

    @property
    def is_available(self) -> bool:
        """Whether the LayoutLMv3 model is loaded and ready for inference."""
        return self._initialized and self.model is not None and self.processor is not None

    def infer(
        self,
        layout_document: LayoutDocument,
        page_num: int | None = None,
    ) -> LayoutInferenceResult:
        """Run LayoutLMv3 inference on a page.

        IMPORTANT: With the base checkpoint, this returns PubLayNet structure
        labels (text, title, list, table, figure). It does NOT classify
        land-record fields. For that, fine-tuning is required.

        Args:
            layout_document: The layout-processed document.
            page_num: Page number to infer on. If None, uses first page.

        Returns:
            LayoutInferenceResult with document structure information.

        Raises:
            RuntimeError: If the model is not initialized.
        """
        if not self.is_available:
            raise RuntimeError(
                "LayoutLMv3 model not initialized. Call initialize() first. "
                f"Error was: {self._init_error}"
            )

        inputs = prepare_layoutlmv3_inputs(layout_document, page_num=page_num)
        if not inputs:
            return LayoutInferenceResult(
                page_num=page_num or 1,
                blocks=[],
                requires_fine_tuning=True,
                message="No layout blocks available for inference",
            )

        image = inputs["image"]
        words = inputs["words"]
        bboxes = inputs["bboxes"]
        pn = inputs["page_num"]

        try:
            # Use LayoutLMv3Processor to encode inputs
            encoding = self.processor(
                images=image,
                text=words,
                boxes=bboxes,
                return_tensors="pt",
                truncation=True,
                padding=True,
            )

            # Run inference
            with torch.no_grad():
                outputs = self.model(**encoding)

            # Parse outputs into block-level results
            blocks = self._parse_inference_outputs(
                encoding, outputs, words, bboxes, pn
            )

            return LayoutInferenceResult(
                page_num=pn,
                blocks=blocks,
                document_structure="base_checkpoint_structure",
                requires_fine_tuning=True,
                message=(
                    "Base LayoutLMv3 checkpoint provides general document "
                    "structure detection (PubLayNet classes). "
                    "Land-record field classification requires fine-tuning."
                ),
            )

        except Exception as exc:
            logger.error(
                "LayoutLMv3 inference failed on page %d: %s", pn, exc, exc_info=True
            )
            raise RuntimeError(f"LayoutLMv3 inference failed: {exc}") from exc

    def _parse_inference_outputs(
        self,
        encoding: Any,
        outputs: Any,
        words: list[str],
        bboxes: list[list[float]],
        page_num: int,
    ) -> list[dict]:
        """Parse model outputs into block-level results.

        Maps model predictions back to the original words/bboxes.
        """
        import torch

        # Get predicted token type IDs
        predictions = torch.argmax(outputs.logits, dim=-1).squeeze(0)
        predicted_ids = predictions.tolist()

        # LayoutLMv3 token classification head IDs (from the model config)
        # id2label typically maps: 0-other, 1-text, 2-title, 3-list, 4-table, 5-figure
        id2label = self.model.config.id2label if hasattr(self.model.config, "id2label") else {}

        blocks: list[dict] = []
        for i, word in enumerate(words):
            if i < len(predicted_ids):
                label_id = predicted_ids[i]
                label = id2label.get(label_id, f"unknown_{label_id}")
            else:
                label = "unknown"

            blocks.append({
                "word": word,
                "bbox": bboxes[i],
                "label": label,
                "label_id": predicted_ids[i] if i < len(predicted_ids) else -1,
                "page_num": page_num,
            })

        return blocks


def get_layoutlmv3_status() -> dict:
    """Return status information for LayoutLMv3 availability.

    Returns:
        Dict with initialization status and any error messages.
    """
    try:
        from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
        processor_available = True
        model_available = True
    except ImportError:
        processor_available = False
        model_available = False

    service = LayoutLMv3ProcessorService()
    initialized = service.is_available

    return {
        "transformers_available": processor_available,
        "model_available": model_available,
        "initialized": initialized,
        "checkpoint": "microsoft/layoutlmv3-base",
        "note": (
            "Base checkpoint provides general document structure detection. "
            "Land-record field classification requires fine-tuning on "
            "annotated land-record datasets."
        ),
    }


# ---------------------------------------------------------------------------
# Public convenience functions
# ---------------------------------------------------------------------------

def create_layout_from_ocr(
    ocr_document: dict,
    page_images: dict[int, Any] | None = None,
) -> LayoutDocument:
    """Convenience function: convert OCR document to LayoutDocument.

    Usage::

        ocr_dict = run_ocr_structured(file_bytes, content_type)
        layout_doc = create_layout_from_ocr(ocr_dict, page_images)
    """
    return build_layout_document(ocr_document, page_images)


def run_layoutlmv3_inference(
    ocr_document: dict,
    page_num: int | None = None,
    page_images: dict[int, Any] | None = None,
) -> LayoutInferenceResult:
    """End-to-end: convert OCR to layout and run LayoutLMv3 inference.

    Note:
        With the base checkpoint, this provides document structure
        detection only. Land-record field classification requires
        additional fine-tuning.

    Returns:
        LayoutInferenceResult with structure labels.
    """
    layout_doc = build_layout_document(ocr_document, page_images)
    service = LayoutLMv3ProcessorService()

    if not service.initialize():
        raise RuntimeError(
            "Cannot initialize LayoutLMv3. Check that transformers and "
            "the model checkpoint are available."
        )

    return service.infer(layout_doc, page_num=page_num)
