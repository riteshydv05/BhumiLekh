"""OCR Worker task for background document processing."""
import os
import sys
import logging

# Ensure backend app is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from celery_app import celery_app
from app.services.ocr_service import run_ocr, run_ocr_structured

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.ocr_worker.process_document_ocr", bind=True, max_retries=3)
def process_document_ocr(self, file_path: str, content_type: str, language: str = "auto") -> dict:
    """Background task to extract multilingual text and bounding boxes from a file."""
    logger.info("OCR Worker: processing %s (lang=%s)", file_path, language)
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        result = run_ocr_structured(file_bytes, content_type=content_type, language=language)
        logger.info("OCR Worker completed: %d pages, method=%s", result["page_count"], result["method"])
        return result
    except Exception as exc:
        logger.error("OCR Worker error processing %s: %s", file_path, exc, exc_info=True)
        raise self.retry(exc=exc, countdown=10)
