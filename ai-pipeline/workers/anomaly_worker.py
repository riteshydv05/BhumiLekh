"""Anomaly detection worker for cross-checking extracted entities against historical records."""
import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from celery_app import celery_app
from app.services.anomaly_service import detect_anomalies

logger = logging.getLogger(__name__)

@celery_app.task(name="workers.anomaly_worker.detect_document_anomalies", bind=True)
def detect_document_anomalies(self, extracted_entities: dict) -> dict:
    """Run IsolationForest ML anomaly & fraud risk scoring."""
    logger.info("Anomaly Worker: checking document anomalies")
    try:
        report = detect_anomalies(extracted_entities)
        return {"status": "success", "anomaly_report": report}
    except Exception as exc:
        logger.error("Anomaly Worker failed: %s", exc)
        return {"status": "error", "error": str(exc)}
