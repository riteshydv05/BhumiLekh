# BhumiLekh (भूमिलेख) — Technology Stack Reference

> **Project:** Intelligent Land Record Digitization and Validation System
> **Reference Document:** `26018.pdf` — Problem Statement & Suggested Technology Specification
> **Status:** Actively Implemented

---

## Table of Contents

1. [Frontend](#1-frontend)
2. [Backend API Layer](#2-backend-api-layer)
3. [AI / ML Pipeline](#3-ai--ml-pipeline)
4. [Database & Storage](#4-database--storage)
5. [GIS & Geospatial](#5-gis--geospatial)
6. [Infrastructure & DevOps](#6-infrastructure--devops)
7. [Testing](#7-testing)
8. [Summary Matrix](#8-summary-matrix)

---

## 1. Frontend

| Technology | Version | Role |
| :--- | :--- | :--- |
| **Next.js** | 14.2.5 | React-based full-stack web framework (SSR/SSG) |
| **React** | 18.3.x | UI component library |
| **TypeScript** | 5.5.x | Type-safe JavaScript superset |
| **Tailwind CSS** | 3.4.x | Utility-first CSS framework |
| **Leaflet.js** | 1.9.4 | Interactive map rendering for cadastral GIS overlays |
| **Lucide React** | 0.428.x | Icon set for UI components |
| **PostCSS** | 8.4.x | CSS transformation toolchain |
| **clsx / tailwind-merge** | 2.x | Conditional class utilities |

> **PDF Reference:** The specification document calls for a *"user-friendly interface for document upload, automated processing, manual verification, audit tracking"* and integration with *GIS platforms* — fulfilled by Next.js + Leaflet.

---

## 2. Backend API Layer

| Technology | Role |
| :--- | :--- |
| **FastAPI** | High-performance async Python REST API framework |
| **Uvicorn** | ASGI web server (standard extras enabled) |
| **Pydantic / Pydantic Settings** | Data validation, settings management, and schema enforcement |
| **SQLAlchemy** | ORM for PostgreSQL relational data access |
| **Alembic** | Database schema migration management |
| **GeoAlchemy2** | Spatial geometry type extensions for SQLAlchemy + PostGIS |
| **Python-JOSE + Passlib** | JWT-based authentication & bcrypt password hashing |
| **Celery** | Distributed async task queue for AI processing pipelines |
| **Redis** | Message broker for Celery; session/cache store |
| **MinIO (Python SDK)** | S3-compatible object storage client for scan file management |
| **Python-Multipart** | File upload parsing (multipart/form-data) |
| **Python-Dotenv** | Environment variable management |

> **PDF Reference:** The specification calls for *"RESTful APIs / GraphQL"* for integration — implemented as FastAPI RESTful APIs. *"Role-based access control"* is handled via Python-JOSE JWT authentication.

---

## 3. AI / ML Pipeline

### 3.1 OCR Engines

| Technology | Model / Version | Role |
| :--- | :--- | :--- |
| **PaddleOCR** | PP-OCRv3 / PP-OCRv4 | **Primary OCR** — Devanagari (Hindi) & English printed text; DBNet++ (detection) + SVTR/CRNN (recognition) |
| **PaddlePaddle** | Latest | Deep learning framework powering PaddleOCR |
| **Tesseract OCR** | v5.x (`pytesseract`) | **Fallback OCR** — LSTM-based line recognizer for degraded or unsupported script cases |

> **PDF Reference:** *"Advanced OCR, Computer Vision, and Natural Language Processing techniques to recognize printed as well as handwritten text in multiple Indian languages."*

### 3.2 Handwritten Text Recognition (HTR)

| Technology | Model ID | Role |
| :--- | :--- | :--- |
| **Hugging Face Transformers** | `microsoft/trocr-base-handwritten` | **TrOCR** — ViT image encoder + RoBERTa autoregressive decoder for handwritten marginal notes and revenue officer annotations |
| **PyTorch** | Latest | Deep learning inference runtime |
| **TorchVision** | Latest | Image preprocessing for transformer pipelines |
| **Accelerate** (HF) | Latest | Distributed/multi-device inference optimization |
| **Tokenizers / SentencePiece** | Latest | Subword tokenization for TrOCR decoder |

### 3.3 Document Layout Understanding

| Technology | Model ID | Role |
| :--- | :--- | :--- |
| **Hugging Face Transformers** | `microsoft/layoutlmv3-base` | **LayoutLMv3** — Multimodal transformer: text tokens + 2D spatial bounding boxes + visual patches for cadastral table and field parsing |
| **Datasets / Evaluate** (HF) | Latest | Dataset management and metric evaluation for fine-tuning |

### 3.4 NLP & Entity Extraction

| Technology | Role |
| :--- | :--- |
| **Custom Cadastral NLP Engine** | Rule-guided heuristic parser for Khasra, Khata, Khatauni, Khewat, Mauza, Tehsil, District, and co-sharer fraction extraction |
| **Indic Regex Engine** | Unicode-aware Devanagari numeral converter (`०–९` → Arabic) and fractional ownership notation parser |
| **Land Unit Normalizer** | Converts legacy area units (Bigha, Biswa, Katha, Guntha, Kanal, Marla, Acre, Cent) to SI Hectares / m² |
| **`langdetect`** | Language & script identification for routing to Devanagari or English pipeline |

> **PDF Reference:** *"spaCy, Hugging Face Transformers, Indic NLP Library"* — implemented via custom domain NLP engine + Hugging Face Transformers.

### 3.5 Machine Learning & Anomaly Detection

| Technology | Algorithm | Role |
| :--- | :--- | :--- |
| **Scikit-Learn** | `IsolationForest` | Unsupervised anomaly detection on area discrepancy ratio, ownership share summation faults, mutation velocity, and OCR confidence variance |
| **NumPy** | Numerical computing | Feature vector construction and Bayesian confidence score aggregation |

### 3.6 Duplicate & Similarity Detection

| Technology | Algorithm | Role |
| :--- | :--- | :--- |
| **MinHash + Jaccard** | Locality-Sensitive Hashing (LSH) | O(1) re-scan & duplicate deed detection |
| **Levenshtein Distance** | Fuzzy string matching | Phonetic name and village transliteration matching |
| **pgvector** | Cosine similarity search | High-dimensional deed semantic embedding index in PostgreSQL |

### 3.7 Cloud VLM Fallback (Optional)

| Technology | Model | Role |
| :--- | :--- | :--- |
| **Google Gemini API** | `gemini-1.5-flash` | Optional Vision-Language Model (VLM) escalation for unreadable low-confidence image patches; disabled by default (`ENABLE_VLM_FALLBACK=false`) |

> **PDF Reference:** Architecture is designed for *"NIC Cloud (MeghRaj) / AWS / Azure Government Cloud"* compatibility. Gemini is the cloud-AI fallback layer.

---

## 4. Database & Storage

| Technology | Version | Role |
| :--- | :--- | :--- |
| **PostgreSQL** | 16 | Primary relational database for land records, audit trails, and user management |
| **PostGIS** | Extension | Spatial geometry types, polygon overlap detection, and cadastral boundary queries |
| **pgvector** | Extension | Vector embedding storage for semantic duplicate detection |
| **Redis** | 7-alpine | Celery message broker; task result caching; session store |
| **MinIO** | Latest | S3-compatible local object storage for raw scans, cropped patches, and processed PDFs |
| **psycopg** | 3.x (binary) | Async PostgreSQL driver |

> **PDF Reference:** Specification recommends *"PostgreSQL with PostGIS / MySQL"* — implemented as PostgreSQL 16 + PostGIS + pgvector.

---

## 5. GIS & Geospatial

| Technology | Role |
| :--- | :--- |
| **PostGIS** | Server-side spatial SQL: polygon intersection, boundary overlap detection, centroid computation |
| **GeoAlchemy2** | SQLAlchemy bridge for PostGIS geometry types (WKT/GeoJSON) |
| **Shapely** | Python-side computational geometry: polygon area validation, spatial distance checks |
| **PyProj** | Coordinate reference system (CRS) transformation: WGS 84 (SRID 4326) ↔ UTM projections |
| **GeoServer** | OGC-compliant map tile and feature server for cadastral shapefile layers |
| **Leaflet.js** | Frontend interactive map rendering with GIS overlay support |

> **PDF Reference:** *"GeoServer, OpenLayers, Leaflet, QGIS"* — implemented as GeoServer (backend tile server) + Leaflet.js (frontend map).

---

## 6. Infrastructure & DevOps

| Technology | Version | Role |
| :--- | :--- | :--- |
| **Docker** | Latest | Containerization of all services |
| **Docker Compose** | v3.x | Multi-service orchestration (PostgreSQL, Redis, MinIO) |
| **Celery** | Latest | Distributed async task processing for AI pipeline workers |
| **Python `.venv`** | 3.11+ | Isolated Python virtual environment for backend |
| **Alembic** | Latest | Schema versioning and migration management |
| **Shell Scripts** | `start.sh`, `stop.sh` | Service lifecycle management |

> **PDF Reference:** *"NIC Cloud (MeghRaj) / AWS / Azure Government Cloud"* — system is architected to be cloud-agnostic and deployable via Docker containers.

---

## 7. Testing

| Technology | Role |
| :--- | :--- |
| **Pytest** | Python unit and integration test framework |
| **pytest-asyncio** | Async test support for FastAPI async endpoints |
| **HTTPX** | Async HTTP client for API endpoint integration tests |

---

## 8. Summary Matrix

| Layer | Technology Chosen | PDF Specification Reference |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 14 + React 18 + TypeScript | User-friendly web interface |
| **Styling** | Tailwind CSS | — |
| **Map UI** | Leaflet.js | GeoServer, OpenLayers, Leaflet |
| **Backend API** | FastAPI + Uvicorn | RESTful APIs / GraphQL |
| **Task Queue** | Celery + Redis | — |
| **Primary OCR** | PaddleOCR (PP-OCRv4) | Advanced OCR (multi-language) |
| **Fallback OCR** | Tesseract v5 | OCR |
| **Handwriting HTR** | Microsoft TrOCR (HF) | OCR (handwritten) |
| **Layout Understanding** | Microsoft LayoutLMv3 (HF) | Computer Vision, NLP |
| **NLP / Entity Extraction** | Custom Domain NLP Engine | spaCy, Hugging Face, Indic NLP |
| **Anomaly Detection** | Scikit-Learn IsolationForest | Machine Learning |
| **Duplicate Detection** | MinHash + Levenshtein + pgvector | — |
| **Language Detection** | `langdetect` + Unicode Regex | Multi-language support |
| **Cloud VLM (Optional)** | Google Gemini 1.5 Flash | NIC Cloud / AWS / Azure |
| **Primary Database** | PostgreSQL 16 | PostgreSQL with PostGIS / MySQL |
| **Spatial Database** | PostGIS + GeoAlchemy2 + Shapely | PostgreSQL with PostGIS |
| **Vector Search** | pgvector | — |
| **Object Storage** | MinIO | — |
| **Cache / Broker** | Redis 7 | — |
| **GIS Server** | GeoServer + PyProj | GeoServer, QGIS |
| **Visualization** | Leaflet.js + Next.js Dashboards | Power BI, Apache Superset, Grafana |
| **Auth** | JWT (Python-JOSE) + bcrypt | Role-based access control |
| **Containerization** | Docker + Docker Compose | Cloud Infrastructure |
| **DB Migrations** | Alembic | — |
| **Testing** | Pytest + HTTPX | — |

---

> *This document reflects the actual technology choices implemented in the codebase as of September 2026, cross-referenced against the problem statement and suggested technology components defined in `26018.pdf`.*
