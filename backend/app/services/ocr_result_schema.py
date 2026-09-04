"""Normalized OCR result data structures.

These are the canonical output types for the OCR pipeline stage.
Downstream stages (LayoutLMv3, NLP extraction) consume OcrDocument.

Structure::

    OcrDocument
      └── pages: list[OcrPage]
            └── blocks: list[OcrBlock]
                  ├── text: str
                  ├── bbox: [x1, y1, x2, y2]   (pixel coords on page image)
                  ├── confidence: float          (0.0 – 1.0)
                  ├── language: str | None       (detected script/lang code)
                  ├── ocr_engine: str            ("paddle" | "pypdf" | "none")
                  └── timestamp: str             (ISO 8601)

JSON serialisation::

    {
        "page_count": 2,
        "full_text": "...",
        "avg_confidence": 0.91,
        "method": "paddle",
        "pages": [
            {
                "page": 1,
                "width": 1654,
                "height": 2339,
                "blocks": [
                    {
                        "text": "Survey No.: 245/A",
                        "bbox": [50, 120, 420, 148],
                        "confidence": 0.96,
                        "language": null,
                        "ocr_engine": "paddle",
                        "timestamp": "2026-09-04T12:00:00"
                    }
                ]
            }
        ]
    }
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class OcrBlock:
    """A single detected text region on a page."""

    text: str
    bbox: list[float]          # [x1, y1, x2, y2] in page-image pixels
    confidence: float          # 0.0 – 1.0
    language: str | None = None
    ocr_engine: str = "none"
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OcrPage:
    """All OCR blocks on a single page."""

    page: int                  # 1-indexed
    width: int = 0             # Page image width in pixels
    height: int = 0            # Page image height in pixels
    blocks: list[OcrBlock] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Concatenate all block texts with newlines."""
        return "\n".join(b.text for b in self.blocks if b.text.strip())

    @property
    def avg_confidence(self) -> float:
        if not self.blocks:
            return 0.0
        conf_blocks = [b.confidence for b in self.blocks if b.confidence > 0]
        return sum(conf_blocks) / len(conf_blocks) if conf_blocks else 0.0

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "width": self.width,
            "height": self.height,
            "blocks": [b.to_dict() for b in self.blocks],
        }


@dataclass
class OcrDocument:
    """Full OCR result for a document (all pages)."""

    pages: list[OcrPage] = field(default_factory=list)
    method: str = "none"       # "paddle" | "pypdf_text" | "none"
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)

    @property
    def avg_confidence(self) -> float:
        if not self.pages:
            return 0.0
        conf = [p.avg_confidence for p in self.pages]
        return sum(conf) / len(conf)

    def to_dict(self) -> dict:
        return {
            "page_count": self.page_count,
            "full_text": self.full_text,
            "avg_confidence": round(self.avg_confidence, 4),
            "method": self.method,
            "error": self.error,
            "warnings": self.warnings,
            "pages": [p.to_dict() for p in self.pages],
        }
