"""Services module — document processing pipeline."""

from app.services.layoutlmv3_service import (
    LayoutBlock,
    LayoutDocument,
    LayoutInferenceResult,
    LayoutLMv3ProcessorService,
    LayoutPage,
    build_layout_document,
    classify_block_type,
    convert_ocr_blocks_to_layout,
    create_layout_from_ocr,
    denormalize_bbox,
    normalize_bbox,
    run_layoutlmv3_inference,
    get_layoutlmv3_status,
    prepare_layoutlmv3_inputs,
    prepare_layoutlmv3_batch,
)

from app.services.ocr_result_schema import OcrBlock, OcrDocument, OcrPage

from app.services.ocr_service import OCRResult, run_ocr, run_ocr_structured

from app.services.anomaly_service import (
    AnomalyResult,
    IsolationForestAnomalyDetector,
    LandRecordInput,
    detect_anomalies as detect_ml_anomalies,
    extract_features,
    generate_synthetic_training_data,
)

__all__ = [
    "OcrBlock",
    "OcrDocument",
    "OcrPage",
    "OCRResult",
    "run_ocr",
    "run_ocr_structured",
    "LayoutBlock",
    "LayoutDocument",
    "LayoutInferenceResult",
    "LayoutLMv3ProcessorService",
    "LayoutPage",
    "build_layout_document",
    "classify_block_type",
    "convert_ocr_blocks_to_layout",
    "create_layout_from_ocr",
    "denormalize_bbox",
    "normalize_bbox",
    "run_layoutlmv3_inference",
    "get_layoutlmv3_status",
    "prepare_layoutlmv3_inputs",
    "prepare_layoutlmv3_batch",
    "AnomalyResult",
    "IsolationForestAnomalyDetector",
    "LandRecordInput",
    "detect_ml_anomalies",
    "extract_features",
    "generate_synthetic_training_data",
]