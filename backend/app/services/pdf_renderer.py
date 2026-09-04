"""PDF-to-image renderer using pypdfium2.

pypdfium2 is a pure-Python binding to PDFium — no system dependencies
(poppler, ghostscript, etc.) required.

Usage::

    from app.services.pdf_renderer import render_pdf_pages
    pages = render_pdf_pages(pdf_bytes, dpi=150)
    # pages: list of (page_num, PIL.Image, width_px, height_px)
"""
from __future__ import annotations

import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional import — service degrades if pypdfium2 is absent
# ---------------------------------------------------------------------------
try:
    import pypdfium2 as pdfium
    _PDFIUM_AVAILABLE = True
except ImportError:
    _PDFIUM_AVAILABLE = False
    logger.warning("pypdfium2 not installed — PDF rendering to images unavailable")

try:
    from PIL import Image as PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False
    logger.warning("Pillow not installed — image operations unavailable")


# DPI for rasterisation. 150 DPI gives ~1240×1754 for A4.
# 200 DPI gives better quality for small text but uses more RAM.
DEFAULT_DPI = 150


def is_available() -> bool:
    return _PDFIUM_AVAILABLE and _PILLOW_AVAILABLE


def render_pdf_pages(
    pdf_bytes: bytes,
    dpi: int = DEFAULT_DPI,
    max_pages: int | None = None,
) -> list[tuple[int, "PILImage.Image", int, int]]:
    """Render each page of a PDF to a PIL Image.

    Args:
        pdf_bytes:  Raw PDF content.
        dpi:        Resolution for rasterisation (default 150).
        max_pages:  Cap on number of pages to render (None = all).

    Returns:
        List of (page_number_1indexed, PIL_Image, width_px, height_px).
        Empty list on any error.

    Never raises.
    """
    if not _PDFIUM_AVAILABLE:
        logger.warning("pdf_renderer: pypdfium2 unavailable, returning empty")
        return []
    if not _PILLOW_AVAILABLE:
        logger.warning("pdf_renderer: Pillow unavailable, returning empty")
        return []

    pages_out: list[tuple[int, PILImage.Image, int, int]] = []

    try:
        doc = pdfium.PdfDocument(pdf_bytes)
        total_pages = len(doc)
        pages_to_render = (
            min(total_pages, max_pages)
            if max_pages is not None
            else total_pages
        )

        logger.info(
            "pdf_renderer: rendering %d/%d pages at %d DPI",
            pages_to_render, total_pages, dpi,
        )

        scale = dpi / 72.0  # PDFium uses 72 DPI internally

        for i in range(pages_to_render):
            try:
                page = doc[i]
                bitmap = page.render(scale=scale, rotation=0)
                pil_img = bitmap.to_pil()
                w, h = pil_img.size
                pages_out.append((i + 1, pil_img, w, h))
                logger.debug(
                    "pdf_renderer: page %d rendered (%dx%d)", i + 1, w, h
                )
                page.close()
            except Exception as exc:
                logger.warning(
                    "pdf_renderer: page %d render failed: %s", i + 1, exc
                )

        doc.close()

    except Exception as exc:
        logger.error("pdf_renderer: failed to open PDF: %s", exc, exc_info=True)

    logger.info(
        "pdf_renderer: %d pages rendered successfully", len(pages_out)
    )
    return pages_out


def image_bytes_to_pil(
    image_bytes: bytes,
    page_num: int = 1,
) -> tuple[int, "PILImage.Image", int, int] | None:
    """Wrap raw image bytes as a single-page PIL Image tuple.

    Returns (page_num, PIL_Image, width, height) or None on error.
    Never raises.
    """
    if not _PILLOW_AVAILABLE:
        return None
    try:
        img = PILImage.open(BytesIO(image_bytes))
        img = img.convert("RGB")  # PaddleOCR expects RGB
        w, h = img.size
        return (page_num, img, w, h)
    except Exception as exc:
        logger.error("pdf_renderer: failed to open image: %s", exc, exc_info=True)
        return None
