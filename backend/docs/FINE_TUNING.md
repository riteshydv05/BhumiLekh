# LayoutLMv3 Integration — Fine-Tuning Requirements

## Current State (MVP)

The `layoutlmv3_service.py` module provides the **architecture** for document layout understanding using `microsoft/layoutlmv3-base`. It converts OCR results (text + bounding boxes + page dimensions) into LayoutLMv3-ready inputs.

## What Works Without Fine-Tuning

- **Document structure detection**: LayoutLMv3-base (trained on PubLayNet) can classify page regions into general structure labels: `text`, `title`, `list`, `table`, `figure`.
- **OCR-to-layout conversion**: Bounding box normalization, block classification, and LayoutLMv3 input preparation work correctly.
- **Layout inference architecture**: The `LayoutLMv3ProcessorService` initializes the model and runs inference — but returns PubLayNet labels only.

## What Requires Fine-Tuning

**Land-record field classification does NOT work with the base checkpoint.** The base model has no knowledge of land-record concepts such as:

| Field Type | Example | Requires |
|------------|---------|------------|
| Survey number | `Survey No: 245/A` | Fine-tuned model |
| Owner name | `Owner: Ram Sharma` | Fine-tuned model |
| Village | `Village: Wagholi` | Fine-tuned model |
| Kaderno/Plot | `Kaderno: 1234` | Fine-tuned model |
| District | `District: Pune` | Fine-tuned model |
| Area | `Area: 1.5 Hectares` | Fine-tuned model |
| Taluka/Tehsil | `Taluka: Haveli` | Fine-tuned model |

### Steps to Enable Land-Record Classification

1. **Create annotated dataset**: Label OCR blocks on land-record documents with field types (e.g., `survey_number`, `owner_name`, `village`, `kaderno`, `area`, `district`, `taluka`).

2. **Fine-tune LayoutLMv3**:
   ```python
   from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor, Trainer, TrainingArguments

   # Load base model
   model = LayoutLMv3ForTokenClassification.from_pretrained(
       "microsoft/layoutlmv3-base",
       num_labels=num_land_record_fields,
   )
   processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")

   # Prepare training data using LayoutBlock objects from this service
   # (layout blocks with words + normalized bboxes + page images)

   # Train with custom dataset
   trainer = Trainer(model=model, ...)
   trainer.train()
   ```

3. **Replace checkpoint**: Update `LAYOUTLMV3_MODEL_NAME` in `config.py` to point to the fine-tuned model.

4. **Update `classify_block_type`**: The current heuristic classification in `classify_block_type()` should be replaced or augmented with model-based classification after fine-tuning.

## Architecture Overview

```
document
 ├── pages
 │    ├── image          ← PIL Image (page_images dict)
 │    ├── OCR blocks      ← Raw OCR output (unchanged)
 │    └── layout blocks   ← LayoutLMv3-ready (LayoutBlock)
 │          ├── words
 │          ├── bbox_normalized [0-1000]
 │          ├── block_type
 │          └── region_hint (future: model-predicted)
```

## Key Files

- `app/services/layoutlmv3_service.py` — Layout-processing service
- `app/workers/pipeline_tasks.py` — Pipeline integration (`_stage_layout_analysis`)
- `app/services/ocr_result_schema.py` — Raw OCR data (never modified)
- `tests/test_layoutlmv3.py` — Tests for the layout service