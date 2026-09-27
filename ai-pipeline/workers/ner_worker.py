"""NER Worker task for multilingual entity extraction from land records."""
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from celery_app import celery_app
from app.services.nlp_service import extract_entities

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.ner_worker.process_document_ner", bind=True, max_retries=3)
def process_document_ner(self, text: str, language: str = "auto") -> dict:
    """Extract land record entities (Survey No, Khasra, Khata, Owner Name, Area) from text."""
    logger.info("NER Worker: extracting entities for lang=%s", language)
    try:
        entities = extract_entities(text, language=language)
        return {
            "status": "success",
            "entities": entities.to_dict() if hasattr(entities, "to_dict") else entities,
        }
    except Exception as exc:
        logger.error("NER Worker failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=5)
