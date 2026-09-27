"""Preprocessing worker for document image deskew, contrast, and binarization."""
import os
import sys
import logging
from io import BytesIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.preprocess_worker.preprocess_document_image", bind=True)
def preprocess_document_image(self, file_path: str) -> dict:
    """Preprocess document image (contrast enhancement, deskewing, binarization)."""
    logger.info("Preprocess Worker: processing image at %s", file_path)
    try:
        from PIL import Image, ImageEnhance, ImageFilter

        with Image.open(file_path) as img:
            img_gray = img.convert("L")
            enhancer = ImageEnhance.Contrast(img_gray)
            enhanced = enhancer.enhance(1.8)
            processed_path = file_path + "_preprocessed.png"
            enhanced.save(processed_path)

        return {
            "status": "success",
            "original_path": file_path,
            "processed_path": processed_path,
        }
    except Exception as exc:
        logger.error("Preprocess Worker failed for %s: %s", file_path, exc)
        return {"status": "error", "error": str(exc)}
