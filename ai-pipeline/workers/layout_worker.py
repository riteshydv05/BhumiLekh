"""Layout analysis worker for spatial bounding box and document section classification."""
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from celery_app import celery_app
from app.services.layoutlmv3_service import run_layout_analysis

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.layout_worker.process_layout_analysis", bind=True)
def process_layout_analysis(self, ocr_pages: list[dict]) -> dict:
    """Analyze document layout structure and classify spatial blocks."""
    logger.info("Layout Worker: processing layout for %d pages", len(ocr_pages))
    try:
        results = run_layout_analysis(ocr_pages)
        return {"status": "success", "layout_analysis": results}
    except Exception as exc:
        logger.error("Layout Worker failed: %s", exc)
        return {"status": "error", "error": str(exc)}
