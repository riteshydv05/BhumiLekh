"""Celery Application configuration for BhumiLekh AI Pipeline.

Manages background worker tasks:
  - ocr_worker (Multilingual OCR & Text Extraction)
  - ner_worker (Indic NER & Land Record Entity Extraction)
  - preprocess_worker (Image Deskew, Denoise & Binarization)
  - layout_worker (LayoutLMv3 Bounding Box & Document Structure)
  - anomaly_worker (IsolationForest Land Fraud & Discrepancy Detection)
"""
import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "bhumilekh_ai_pipeline",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "workers.ocr_worker",
        "workers.ner_worker",
        "workers.preprocess_worker",
        "workers.layout_worker",
        "workers.anomaly_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        "workers.ocr_worker.*": {"queue": "ocr"},
        "workers.ner_worker.*": {"queue": "ner"},
        "workers.preprocess_worker.*": {"queue": "preprocess"},
        "workers.layout_worker.*": {"queue": "layout"},
        "workers.anomaly_worker.*": {"queue": "anomaly"},
    },
    task_track_started=True,
    task_time_limit=600,
)

if __name__ == "__main__":
    celery_app.start()
