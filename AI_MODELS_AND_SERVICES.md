# BhumiLekh (भूमिलेख) — Artificial Intelligence & Machine Learning Architecture

This document provides a comprehensive technical inventory of all Artificial Intelligence (AI), Machine Learning (ML), Deep Learning (DL), Computer Vision (CV), and Natural Language Processing (NLP) models, pipelines, and services implemented within the **BhumiLekh Intelligent Land Record Digitization & Validation System**.

---

## 1. Executive Summary & Architecture Philosophy

BhumiLekh is engineered as a **Sovereign, Local-First, Hybrid Multi-Engine AI Platform**. Land records constitute sensitive national critical data infrastructure; therefore, the core architecture is built to run air-gapped within state and national government data centers without mandatory dependencies on external public cloud APIs.

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 Incoming Physical Scans                 │
                  │                 (PDF, TIFF, JPEG, PNG)                  │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                       [ PDF Pre-renderer ]
                                               │
                                               ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                      STAGE 1: MULTI-ENGINE OCR & VISION                          │
     │                                                                                  │
     │  ┌─────────────────────────┐   ┌────────────────────────┐   ┌─────────────────┐  │
     │  │   PaddleOCR (v3/v4)     │   │   Microsoft TrOCR      │   │  Tesseract OCR  │  │
     │  │ (Devanagari & English)  │   │  (ViT + RoBERTa HTR)   │   │   (Fallback)    │  │
     │  └────────────┬────────────┘   └───────────┬────────────┘   └────────┬────────┘  │
     └───────────────┼────────────────────────────┼─────────────────────────┼───────────┘
                     └────────────────────┬───────┴─────────────────────────┘
                                          ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                STAGE 2: MULTIMODAL DOCUMENT UNDERSTANDING                        │
     │                                                                                  │
     │  ┌────────────────────────────────────────┐  ┌────────────────────────────────┐  │
     │  │      Microsoft LayoutLMv3 Base         │  │   Dynamic Layout & Table Grid  │  │
     │  │ (2D Spatial Bounding Boxes + Visual)   │  │       Reconstruction Parser    │  │
     │  └───────────────────┬────────────────────┘  └───────────────┬────────────────┘  │
     └──────────────────────┼───────────────────────────────────────┼───────────────────┘
                            └───────────────────┬───────────────────┘
                                                ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                STAGE 3: DOMAIN NLP & REGIONAL NORMALIZATION                      │
     │                                                                                  │
     │  ┌───────────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐  │
     │  │ Cadastral Entity Parsing  │  │ Devanagari Numeral &  │  │ Geometric Unit   │  │
     │  │ (Khasra, Khatauni, Mouza) │  │  Fraction Normalizer  │  │ Harmonization    │  │
     │  └─────────────┬─────────────┘  └───────────┬───────────┘  └────────┬─────────┘  │
     └────────────────┼────────────────────────────┼───────────────────────┼────────────┘
                      └────────────────────┬───────┴───────────────────────┘
                                           ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                STAGE 4: VALIDATION, ANOMALY & RISK SCORING                       │
     │                                                                                  │
     │  ┌───────────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐  │
     │  │  Scikit-Learn ML Engine   │  │ Mathematical Confidence│ │  PostGIS GIS     │  │
     │  │     (IsolationForest)     │  │ Aggregation (Bayesian) │ │ Cadastral Match  │  │
     │  └─────────────┬─────────────┘  └───────────┬───────────┘  └────────┬─────────┘  │
     └────────────────┼────────────────────────────┼───────────────────────┼────────────┘
                      └────────────────────┬───────┴───────────────────────┘
                                           ▼
     ┌──────────────────────────────────────────────────────────────────────────────────┐
     │                       STAGE 5: DECISION & VERIFICATION                           │
     │                                                                                  │
     │      ┌─────────────────────────┐             ┌─────────────────────────┐         │
     │      │   Confidence >= 90%     │             │    Confidence < 90%     │         │
     │      │  Instant Auto-Approval  │             │ Tehsildar Audit Station │         │
     │      └─────────────────────────┘             └────────────┬────────────┘         │
     │                                                           │                      │
     │                                            [ Optional Cloud VLM Fallback ]       │
     │                                            (Google Gemini 1.5 Flash Escalate)    │
     └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Inventory of AI / ML Models & Services

### 1. Printed Document OCR: PaddleOCR (PP-OCRv4 / PP-OCRv3)
* **Architecture:** Multi-stage deep convolutional and transformer architecture:
  * **Text Detection (DBNet / DBNet++):** Differentiable Binarization network capable of accurately isolating rotated, curved, and degraded text lines in dense colonial and cadastral registries.
  * **Direction Classifier:** 180-degree angle detection network to automatically orient upside-down or misfed scanner pages.
  * **Text Recognition (SVTR / CRNN):** Single Visual Model for Text Recognition, combining localized patch attention with sequence modeling.
* **Target Scripts:** Bilingual models supporting **Devanagari (Hindi)** and **Latin (English)**.
* **Implementation File:** [`backend/app/services/paddle_ocr_engine.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/paddle_ocr_engine.py) & [`backend/app/services/ocr_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/ocr_service.py)
* **Framework:** `paddlepaddle`, `paddleocr`
* **Key Role:** Primary text digitization engine executing locally on CPU or CUDA GPUs.

---

### 2. Handwritten Text Recognition (HTR): Microsoft TrOCR
* **Model ID:** `microsoft/trocr-base-handwritten` (Hugging Face)
* **Architecture:** 
  * **Image Encoder:** Vision Transformer (`ViTImageProcessor`), decomposing image crops of handwritten notes into non-overlapping patches.
  * **Text Decoder:** RoBERTa-based autoregressive Language Model Decoder (`RobertaTokenizer`).
* **Implementation File:** [`backend/app/services/trocr_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/trocr_service.py)
* **Framework:** PyTorch (`torch`), Hugging Face `transformers`, `accelerate`
* **Execution Design:**
  * Lazy singleton loading per Celery worker process.
  * Applied specifically to cropped sub-regions flagged as cursive handwriting (marginal notations, revenue officer signatures, remarks column).
  * Confidence proxy derived mathematically from token softmax probabilities across the autoregressive decode sequence.

---

### 3. Document Layout Understanding: Microsoft LayoutLMv3
* **Model ID:** `microsoft/layoutlmv3-base` (Hugging Face)
* **Architecture:** Multimodal Transformer that jointly models:
  1. **Text Tokens:** Subword embeddings from OCR recognition.
  2. **2D Spatial Layout:** Normalized coordinate bounding boxes $[x_1, y_1, x_2, y_2]$ mapped to a continuous $[0, 1000]$ integer coordinate space.
  3. **Visual Tokens:** Linear projection of document image patches aligned with corresponding words.
* **Implementation File:** [`backend/app/services/layoutlmv3_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/layoutlmv3_service.py)
* **Framework:** Hugging Face `transformers`, `datasets`, `evaluate`, PyTorch
* **Key Role:** Understands semantic layout boundaries, distinguishing title headers, tabular grids, stamp endorsements, and key-value label pairs.

---

### 4. Machine Learning Anomaly Detection: Scikit-Learn IsolationForest
* **Model:** `sklearn.ensemble.IsolationForest`
* **Algorithm:** Unsupervised ensemble of isolation trees partitioning high-dimensional numerical feature spaces.
* **Feature Vector Inputs:**
  * Area discrepancy ratio ($\frac{\text{Stated Area}}{\text{Calculated Boundary Area}}$)
  * Ownership share summation anomalies (flags cases where aggregated shares $> 1.00$ or $< 0.95$)
  * Mutation interval velocity (detects unusually rapid re-registrations on the same parcel)
  * OCR extraction confidence variance
* **Implementation File:** [`backend/app/services/anomaly_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/anomaly_service.py)
* **Framework:** `scikit-learn`, `numpy`
* **Risk Classifications:** Produces an objective anomaly score mapping to `LOW`, `MEDIUM`, and `HIGH` risk flags to guide Tehsildar investigation without replacing legal judicial discretion.

---

### 5. Cadastral NLP & Domain Entity Extraction Engine
* **Technology:** Rule-guided heuristic parser, Indic regex pattern engines, and contextual token analyzers.
* **Target Entities:**
  * **Khasra Number (खसरा संख्या):** Primary parcel survey ID (e.g., `123/4`, `45 क`).
  * **Khata / Khatauni (खाता / खतौनी):** Operational landholder registry ledger number.
  * **Khewat (खेवट):** Proprietary landholder rights account.
  * **Mauza / Village (मौजा / ग्राम):** Revenue jurisdictional village demarcations.
  * **Tehsil / Pargana / District (तहसील / परगना / जनपद):** Administrative hierarchical tiers.
  * **Co-sharer Percentages:** Fractional ownership shares (e.g., `1/2 भाग`, `1/4 हिस्सा`).
* **Implementation File:** [`backend/app/services/nlp_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/nlp_service.py) & [`backend/app/services/dynamic_extraction_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/dynamic_extraction_service.py)
* **Specialized Sub-components:**
  * **Devanagari Numerals Converter:** Automatically standardizes Devanagari digits (`०, १, २, ३, ४, ५, ६, ७, ८, ९`) into Arabic numbers.
  * **Land Area Normalizer:** Converts non-standard legacy units (Bigha, Biswa, Biswansi, Katha, Guntha, Kanal, Marla, Acre, Cent) into uniform Standard International (SI) Hectares and Square Metres.

---

### 6. Vector Similarity & Duplicate Deed Detection
* **Technologies:**
  * **MinHash & Jaccard Indexing:** Rapid $O(1)$ locality-sensitive hashing to detect re-scans of existing files.
  * **Levenshtein String Distance:** Fuzzy matching across phonetic name transliterations and village titles.
  * **pgvector Embeddings:** High-dimensional vector search on PostgreSQL to index deed semantic embeddings.
* **Implementation File:** [`backend/app/services/duplicate_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/duplicate_service.py)
* **Database Extension:** `pgvector` on PostgreSQL

---

### 7. Language Identification & Script Detection
* **Model / Library:** `langdetect` + Devanagari Unicode Block Range Analyzer (`[\u0900-\u097F]`).
* **Implementation File:** [`backend/app/services/language_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/language_service.py) & [`backend/app/services/multilingual_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/multilingual_service.py)
* **Key Role:** Analyzes incoming document crops to decide whether to route the batch through Devanagari OCR pipelines, English cadastral pipelines, or hybrid bilingual routes.

---

### 8. Mathematical Confidence Scoring & Aggregation Service
* **Methodology:** Multi-factor weighted probabilistic aggregation.
* **Formula Formulation:**
  $$\text{Composite Trust Score} = w_1 \cdot \text{OCR\_Confidence} + w_2 \cdot \text{Spatial\_Score} + w_3 \cdot \text{Schema\_Score} + w_4 \cdot \text{Checksum\_Score}$$
* **Implementation File:** [`backend/app/services/confidence_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/confidence_service.py)
* **Execution:**
  * Categorizes fields into Confidence Bins:
    * **High ($\ge 90\%$):** Automated ingestion into digital repository.
    * **Moderate ($75\% - 89\%$):** Queued for quick spot-check verification.
    * **Low ($< 75\%$):** Triggers side-by-side audit modal with mandatory officer sign-off.

---

### 9. Geospatial AI & Cadastral GIS Alignment
* **Technologies:** PostGIS Spatial Extensions, Shapely, GeoAlchemy2, PyProj
* **Algorithms:**
  * Polygon topological boundary intersection and overlap detection.
  * Bounding box centroid computation and spatial distance checks.
  * Coordinate reference system harmonization (WGS 84 / SRID 4326 vs. UTM projections).
* **Implementation File:** [`backend/app/services/gis_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/gis_service.py)
* **Key Role:** Flags spatial boundary overlaps when extracted deed areas conflict with cadastral shapefile survey maps.

---

### 10. Vision-Language Model (VLM) Cloud Fallback: Google Gemini 1.5 Flash
* **Model ID:** `gemini-1.5-flash`
* **Implementation File:** [`backend/app/services/external/gemini_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/external/gemini_service.py)
* **Integration Principles:**
  * **Strictly Optional:** Disabled by default (`ENABLE_VLM_FALLBACK=false`) to preserve total air-gapped sovereign compliance.
  * **Selective Escalation:** Only invoked when explicit cloud authorization is granted AND local OCR confidence falls below threshold.
  * **Data Minimization:** Only transcribes cropped, unreadable image patches rather than transmitting entire sensitive record archives.
  * **Non-Destructive:** Outputs are tagged `source="gemini_vlm"` in PostgreSQL audit trails.

---

### 11. Continuous Active Learning & Tehsildar Feedback Loop
* **Architecture:** Human-in-the-loop (HITL) dataset collector.
* **Implementation File:** [`backend/app/services/learning_service.py`](file:///Users/apple/Desktop/BhumiLekh/land-record-ai-system/backend/app/services/learning_service.py)
* **Mechanism:**
  * Every manual correction made by a revenue officer inside the Verification Audit Station is recorded alongside the original image crop bounding box and raw OCR output.
  * Automatically compiles balanced training pairs for future fine-tuning of PaddleOCR and LayoutLMv3 checkpoints on regional land registry dialects.

---

## 3. Technology & Model Specifications Matrix

| AI / ML Component | Base Model / Library | Architecture Type | Input Modality | Target Language / Script | Deployment Location |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Printed OCR Engine** | PaddleOCR (PP-OCRv4) | DBNet++ + SVTR / CRNN | Image (Scan) | Hindi (Devanagari) & English | Local Celery Worker |
| **Fallback OCR Engine** | Tesseract OCR v5.x | LSTM Line Recognizer | Image (Scan) | Hindi, English | Local Container |
| **Handwriting HTR** | `microsoft/trocr-base-handwritten` | ViT Encoder + RoBERTa Decoder | Image Crop | English & Latinized Script | Local Celery Worker |
| **Layout Understanding** | `microsoft/layoutlmv3-base` | Multimodal Transformer | Image + Tokens + BBoxes | Multilingual Layouts | Local Celery Worker |
| **Anomaly Detection** | Scikit-Learn `IsolationForest` | Ensemble Tree Partitioner | Tabular Feature Vector | Numeric / Categorical | Local FastAPI Worker |
| **Duplicate Detection** | MinHash + Levenshtein + pgvector | LSH & Cosine Distance | Text + Embeddings | Language Agnostic | PostgreSQL + Redis |
| **Language Identification**| `langdetect` + Unicode Regex | N-gram Frequency + Range Filter | Raw Text | Indic + Latin Scripts | Local Backend Worker |
| **Entity Extraction** | Domain Rule & Context Engine | Heuristic Deterministic Graph | OCR Text BBoxes | Hindi, English, Urdu-revenue | Local Backend Worker |
| **Spatial Engine** | PostGIS + Shapely | Computational Geometry | GeoJSON / WKT Geometry | Spatial Geometry | PostgreSQL Database |
| **VLM Fallback (Opt.)** | Google Gemini 1.5 Flash | Multimodal Large Vision Model | Compressed Image Crop | Multilingual | Cloud API (Optional) |

---

## 4. Hardware & Operational Requirements

* **Local Inference Environment:**
  * **CPU:** 4+ Cores (Intel Xeon / AMD EPYC / Apple Silicon)
  * **RAM:** Minimum 8 GB (16 GB recommended for concurrent TrOCR + LayoutLMv3 caching)
  * **GPU Acceleration (Optional):** NVIDIA CUDA 11.8+ or Apple Metal Performance Shaders (MPS) for high-throughput batch processing.
* **Storage:**
  * MinIO S3 Object Storage for raw scan files and cropped visual patches.
  * PostgreSQL 15+ with PostGIS and pgvector for relational, spatial, and vector intelligence.
