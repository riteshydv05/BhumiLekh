# CHANGELOG — Land Record AI System Stabilization

## Session Date: 2026-09-04

---

### 1. Infrastructure & Startup (`start.sh`)

- Startup script now implements proper sequencing — Docker infra → wait-for-Postgres → wait-for-Redis → DB migrations → FastAPI → Celery → Next.js.
- PID tracking organized under `.pids/` directory.
- Logs written to `logs/backend.log`, `logs/celery.log`, `logs/frontend.log`.
- Added automated DB migration step integrated into startup.

**File**: `start.sh`

---

### 2. Database Migrations (`backend/app/db/migrate.py`)

- `document_results` table was missing columns required by the pipeline.
- Automated migration adds `original_text`, `normalized_text`, `transliteration`, `translation` columns if absent.
- Migration runs automatically on app startup via FastAPI `lifespan` handler.

**File**: `backend/app/db/migrate.py`

---

### 3. FastAPI Backend (`backend/app/main.py`)

- Added global exception handler to prevent unhandled exceptions from breaking CORS.
- Added lifespan handler that runs DB migration on startup.

**File**: `backend/app/main.py`

---

### 4. OCR Performance (`backend/app/services/paddle_ocr_engine.py`)

- PaddleOCR init was extremely slow (~60s) because it defaulted to heavy server models.
- Switched to `PP-OCRv4_mobile_det` + `devanagari_PP-OCRv5_mobile_rec` for Devanagari.
- Added batch recognition (`text_recognition_batch_size=8`).
- Added `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` to bypass remote connectivity checks.
- **Result**: OCR init reduced from ~60s to ~6s.

**File**: `backend/app/services/paddle_ocr_engine.py`

---

### 5. TrOCR & LayoutLMv3 Cache

- Both services now prioritize local Hugging Face cache to prevent network timeouts.

**Files**: `backend/app/services/trocr_service.py`, `backend/app/services/layoutlmv3_service.py`

---

### 6. Frontend — Field Display Bug (CRITICAL)

**Root cause**: Backend stores `field_name` as lowercase (e.g. `father_name`, `taluka`, `area_hectares`) via `_ENTITY_TO_FIELD_NAME_MAP`, but the frontend uses UPPERCASE lookups (e.g. `getField("FATHER_NAME")`, `getField("TEHSIL")`, `getField("AREA")`).

Additionally, some backend field names don't match frontend entity names even after case normalization:
- `TEHSIL` → stored as `taluka`
- `AREA` → stored as `area_hectares`
- `DATE` → stored as `registration_date`

- Added `FIELD_ALIASES` map that registers all possible lookup keys (original, uppercase, and entity-type aliases).
- **Result**: All extracted fields now display correctly instead of "Not available".

**File**: `frontend/app/documents/[id]/page.tsx`

---

### 7. Frontend — Verification Page Empty

**Root cause**: `setActiveDoc(doc)` was never called after fetching document data, so the split-screen verification viewer never rendered.

- Added `setActiveDoc(doc)` in the Promise.all resolution handler.

**File**: `frontend/app/verify/page.tsx`

---

### 8. Frontend — Document Detail Polling

- Added automatic polling (2.5s interval) for document status updates while processing. Stops polling once document reaches a terminal state.

**File**: `frontend/app/documents/[id]/page.tsx`

---

### 9. API Response Structure (`backend/app/api/v1/documents.py`)

- `get_document_results` endpoint now returns both `results` and `fields` keys with all new columns.

**File**: `backend/app/api/v1/documents.py`

---

## Files Modified

| File | Change |
|------|--------|
| `start.sh` | Startup sequence |
| `backend/app/db/migrate.py` | New — automated migration |
| `backend/app/main.py` | Lifespan + exception handler |
| `backend/app/services/paddle_ocr_engine.py` | Mobile models + batching |
| `backend/app/services/trocr_service.py` | Local cache priority |
| `backend/app/services/layoutlmv3_service.py` | Local cache priority |
| `backend/app/api/v1/documents.py` | Response structure |
| `frontend/app/documents/[id]/page.tsx` | Field alias mapping + polling |
| `frontend/app/verify/page.tsx` | activeDoc fix |

---

## Current Status

| Component | Status |
|-----------|--------|
| PostgreSQL + PostGIS + pgvector | ✅ Running |
| Redis | ✅ Running |
| MinIO | ✅ Running |
| FastAPI (port 8000) | ✅ No errors |
| Celery Worker | ✅ Tasks registered |
| Next.js (port 3000) | ✅ Build passes |
| PaddleOCR | ✅ ~6s init, mobile models |
| NLP Entity Extraction | ✅ 7 fields from sample |
| Validation + IsolationForest | ✅ Working |
| End-to-end pipeline | ✅ Working |
| Field Display | ✅ Fixed |
| Verification Console | ✅ Fixed |

---

## Known Limitations

1. **IndicNER**: Gated HuggingFace repo — falls back to rule-based extraction.
2. **Bhashini / VLM**: Disabled by config. Core system works without them.
3. **Devanagari handwriting**: TrOCR activates only when PaddleOCR confidence < 0.50.
