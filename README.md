# 🏛️ BhumiLekh (भूमिलेख) — Intelligent Land Record Digitization & Validation System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_PostGIS-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3+-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **BhumiLekh** is a production-ready, accessible, offline-first digital service portal and AI pipeline designed for Indian Revenue Departments, Land Registries (LRMS/DILRMP), nodal officers, and citizens. It automates the transcription of complex, multilingual, and historical land records, validates cadastral boundaries using PostGIS, detects spatial and transactional anomalies, and facilitates human-in-the-loop (HITL) verification with continuous model learning.

---

## 📌 Table of Contents

- [Key Highlights](#-key-highlights)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start (One-Click Launch)](#-quick-start-one-click-launch)
- [Manual Step-by-Step Setup](#-manual-step-by-step-setup)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Core Functional Modules](#-core-functional-modules)
  - [1. Multilingual OCR & Layout Understanding](#1-multilingual-ocr--layout-understanding)
  - [2. Dynamic Land Record Templates](#2-dynamic-land-record-templates)
  - [3. Multi-Tier Anomaly & Fraud Detection](#3-multi-tier-anomaly--fraud-detection)
  - [4. GIS Cadastral Boundary & Spatial Validation](#4-gis-cadastral-boundary--spatial-validation)
  - [5. Human-in-the-Loop (HITL) Verification](#5-human-in-the-loop-hitl-verification)
  - [6. Continuous Active Learning](#6-continuous-active-learning)
  - [7. Indian Government UI & Accessibility Standard](#7-indian-government-ui--accessibility-standard)
- [REST API Reference](#-rest-api-reference)
- [Portal Routes & Navigation](#-portal-routes--navigation)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [📚 50 Architecture, Feasibility & Scalability Questions (Q&A)](./TECH_STACK_AND_FEASIBILITY_QNA.md)

---

## 🚀 Key Highlights

- **Multilingual OCR Across 13 Indian Scheduled Languages**: Native handling of Hindi, Marathi, Gujarati, Bengali, Punjabi, Telugu, Tamil, Kannada, Malayalam, Odia, Assamese, Urdu, and English using PaddleOCR and Microsoft TrOCR for handwritten patwari notes.
- **Visual Document Understanding (VDU)**: LayoutLMv3-powered spatial alignment and bounding-box level token extraction for complex multi-column revenue tabular formats.
- **Dynamic Revenue Record Parsing**: Pre-built extractors for **7/12 extracts (Maharashtra/Gujarat)**, **RoR (Record of Rights)**, **Patta / Chitta (Tamil Nadu)**, **Jamabandi / Khasra-Khatauni (UP, Punjab, Haryana)**, and **Bhoomi RTC (Karnataka)**.
- **Cadastral GIS & PostGIS Spatial Engine**: Interactive Leaflet parcel viewer backed by PostGIS spatial queries (GeoJSON polygons, centroid computations, boundary encroachment, and area mismatch detection).
- **Multi-Level Fraud & Anomaly Detection**: Isolation Forest machine learning and deterministic business rules flagging duplicate filings (SHA-256 + vector similarity via `pgvector`), land classification discrepancies, illegal sub-divisions, and conflicting ownership shares.
- **External LRMS/DILRMP Integration**: Pluggable connectors and mock adapters for state Land Record Management Systems (Bhulekh, Bhoomi, Banglarbhumi, AnyRoR).
- **Audited Human-in-the-Loop Review**: Split-screen verification interface displaying scanned document pages side-by-side with editable fields, field-level confidence badges (`HIGH`, `MEDIUM`, `LOW`), anomaly alerts, and full audit logs.
- **Continuous Learning Loop**: Human corrections in the verification console automatically feed into versioned training snapshots to iteratively adapt OCR and entity recognition confidence.
- **Strict Indian Government UI Identity**: Built following official digital service guidelines with high-contrast accessibility mode, dynamic font scaling (`A-`, `A`, `A+`), and WCAG 2.1 AA compliance.

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph Client ["Client Layer (Next.js 14 App Router)"]
        UI["Portal UI & Dashboard\n(React 18 / TailwindCSS)"]
        HITL["HITL Verification Console\n(Split Screen / Bounding Boxes)"]
        GIS_UI["Cadastral Map Viewer\n(Leaflet / GeoJSON)"]
    end

    subgraph Gateway ["API & Application Server"]
        API["FastAPI Gateway (Port 8000)\nPydantic v2 / OAuth2 JWT"]
        DocService["Document & Storage Manager"]
        IntegService["LRMS / DILRMP Adapter"]
        GISService["GIS & Spatial Query Engine"]
    end

    subgraph Queue ["Asynchronous Task Engine"]
        Redis[("Redis 7 (Port 6379)\nBroker & Cache")]
        CeleryWorker["Celery Distributed Workers\nAI Pipeline Orchestration"]
    end

    subgraph AIPipeline ["AI & Machine Learning Services"]
        Paddle["PaddleOCR Engine\n(Printed Indic Scripts)"]
        TrOCR["TrOCR Engine\n(Handwritten Endorsements)"]
        LayoutLM["LayoutLMv3 Service\n(Spatial Key-Value Extraction)"]
        AnomalyEngine["Anomaly Engine\n(Isolation Forest + Rule Engine)"]
        ActiveLearn["Continuous Learning Engine\n(Snapshot & Weight Tuner)"]
    end

    subgraph DataStorage ["Persistent Data Tier"]
        Postgres[("PostgreSQL 16 (Port 5432)\n+ PostGIS Spatial Extension\n+ pgvector Embeddings")]
        MinIO[("MinIO Object Storage (Port 9000/9001)\nS3-Compatible Document Vault")]
    end

    UI -->|REST / JSON| API
    HITL -->|Field Corrections & Verifications| API
    GIS_UI -->|GeoJSON FeatureCollections| API

    API --> DocService
    API --> IntegService
    API --> GISService
    API --> Postgres
    DocService --> MinIO

    API -->|Dispatches Tasks| Redis
    Redis --> CeleryWorker

    CeleryWorker --> Paddle
    CeleryWorker --> TrOCR
    CeleryWorker --> LayoutLM
    CeleryWorker --> AnomalyEngine
    ActiveLearn --> CeleryWorker

    CeleryWorker -->|Stores Results & Embeddings| Postgres
```

---

## 💻 Tech Stack

| Domain | Technologies | Purpose |
|---|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript 5, TailwindCSS 3 | Accessible, responsive Indian Government Portal UI |
| **Mapping & GIS** | Leaflet 1.9, React-Leaflet, PostGIS | Interactive cadastral parcel mapping & boundary polygon visualization |
| **Icons & Style** | Lucide React, Clsx, Tailwind-Merge | Accessible icons and dynamic styling utilities |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2, Python 3.10+ | High-performance async REST API and file streaming |
| **ORM & Database** | SQLAlchemy 2.0, GeoAlchemy2, PostgreSQL 16 | Relational data, cadastral geometries, and audit logs |
| **Spatial & Vectors** | PostGIS 3.4, pgvector | Spatial polygon operations and document similarity vectors |
| **Job Queue** | Celery 5.3, Redis 7 (Alpine) | Async multi-stage AI pipeline execution |
| **Object Storage** | MinIO (S3-compatible) | Secure storage for scanned PDFs, TIFFs, and rendered page images |
| **OCR Engines** | PaddleOCR, PyTesseract, Microsoft TrOCR | Multilingual printed and handwritten optical character recognition |
| **Document NLP** | Hugging Face Transformers, PyTorch, LayoutLMv3 | Visual document token layout and key-value extraction |
| **Anomaly Detection** | Scikit-learn (Isolation Forest), NumPy | Outlier identification, area mismatch, and fraud rule checks |
| **Infrastructure** | Docker, Docker Compose, Bash orchestration | Local multi-service infrastructure containerization |

---

## 📂 Repository Structure

```text
BhumiLekh/
└── land-record-ai-system/
    ├── docker-compose.yml       # Docker definition for PostgreSQL+PostGIS, Redis, MinIO
    ├── start.sh                 # Unified dev startup script (containers, backend, celery, frontend)
    ├── stop.sh                  # Graceful shutdown script for all running processes & ports
    ├── .env.example             # Template for all environment variables
    │
    ├── backend/                 # FastAPI Application
    │   ├── app/
    │   │   ├── main.py          # FastAPI application factory, CORS, routers & lifecycle
    │   │   ├── api/v1/          # REST route handlers (documents, integration, auth, records)
    │   │   ├── core/            # Configuration settings, security & JWT helpers
    │   │   ├── db/              # SQLAlchemy session and idempotent schema migrations (migrate.py)
    │   │   ├── models/          # Database models (Document, Result, Parcel, AuditLog, etc.)
    │   │   ├── schemas/         # Pydantic request/response schemas
    │   │   ├── services/        # Business logic (OCR, LayoutLM, Anomaly, GIS, LRMS, Learning)
    │   │   └── workers/         # Celery tasks and pipeline orchestration
    │   ├── requirements.txt     # Python backend dependencies
    │   └── tests/               # Pytest suite for backend and OCR services
    │
    ├── frontend/                # Next.js 14 Client Application
    │   ├── app/                 # Next.js App Router pages
    │   │   ├── page.tsx         # Home landing portal (Hero, Quick Services, Workflow)
    │   │   ├── dashboard/       # Operations dashboard with live KPIs and document lists
    │   │   ├── upload/          # Drag-and-drop document upload with real-time stage progress
    │   │   ├── documents/       # Document repository with filtering, search & inspection
    │   │   ├── verify/          # Split-screen Human-in-the-Loop verification console
    │   │   ├── map/             # Interactive Leaflet GIS cadastral parcel viewer
    │   │   ├── help/            # Help desk, accepted document types & operating instructions
    │   │   ├── privacy/         # Privacy & data protection charter
    │   │   └── terms/           # Terms of service
    │   ├── components/          # Reusable UI components (Layout, GIS, Viewer, Dashboard)
    │   ├── context/             # Accessibility Context (Font size, contrast, 13 languages)
    │   ├── lib/                 # Centralized API client (`api.ts`)
    │   └── package.json         # Node.js dependencies and scripts
    │
    ├── ai-pipeline/             # AI Pipeline Worker Specifications & Standalone Models
    │   ├── celery_app.py        # Celery broker configuration
    │   └── workers/             # Specialized OCR, NER, Layout, and Anomaly workers
    │
    ├── validation-engine/       # Deterministic & Statistical Rule Validation
    │   ├── engine.py            # Central validation evaluation coordinator
    │   └── rules/               # Field, spatial, cross-record, and cross-database rules
    │
    ├── gis/                     # GIS Cadastral Data & GeoServer Configuration
    │   ├── geoserver/           # WMS / WFS layer configurations
    │   └── sample_shapefiles/   # Sample village parcel boundaries
    │
    ├── infra/                   # Container Infrastructure Dockerfiles
    │   └── postgres/            # Dockerfile for PostgreSQL 16 + PostGIS + pgvector
    │
    ├── logs/                    # Runtime service logs (backend.log, celery.log, frontend.log)
    └── .pids/                   # Process IDs for clean daemon lifecycle management
```

---

## ⚙️ Prerequisites

Before launching the system, ensure the following tools are installed on your workstation:

1. **Docker & Docker Compose** (v24.0+ / Compose v2.20+)
2. **Python** 3.10 or 3.11 (with `venv` and `pip`)
3. **Node.js** 18.x or 20.x (LTS) & **npm** 9.x+
4. **Git**
5. *(Optional for native system OCR)*: `tesseract-ocr` and `poppler-utils` (`brew install tesseract poppler` on macOS).

---

## ⚡ Quick Start (One-Click Launch)

The repository includes a battle-tested startup script that starts the Docker storage and database services, runs schema migrations with synthetic cadastral seeds, starts the FastAPI server, spawns the Celery AI worker, and launches the Next.js development server.

### 1. Clone and Navigate
```bash
git clone https://github.com/your-org/BhumiLekh.git
cd BhumiLekh/land-record-ai-system
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Launch All Services
```bash
chmod +x start.sh stop.sh
./start.sh
```

### 4. Service Endpoints
Once startup completes, the following services will be live:

| Service | URL | Description / Credentials |
|---|---|---|
| **Frontend Portal** | [http://localhost:3000](http://localhost:3000) | Citizen & Officer Government Portal |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | Core FastAPI Engine |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for exploring all endpoints |
| **Backend Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | System health & readiness status |
| **MinIO Web Console** | [http://localhost:9001](http://localhost:9001) | User: `minio_admin` \| Pass: `minio_password` |
| **MinIO S3 API** | `http://localhost:9000` | S3-compatible document bucket storage |
| **PostgreSQL + PostGIS** | `localhost:5432` | DB: `land_records` \| User: `land_admin` \| Pass: `land_password` |
| **Redis Broker** | `localhost:6379` | Celery message broker and cache |

### 5. Stop Services
To shut down the application and cleanly terminate background processes:
```bash
./stop.sh
```
*(To also stop the Docker containers, run `docker compose stop`).*

---

## 🛠️ Manual Step-by-Step Setup

If you prefer to start components independently for debugging or development:

### Step 1: Start Containerized Infrastructure
```bash
docker compose up -d
```
Verify containers are healthy:
```bash
docker ps
```

### Step 2: Set Up Backend Virtual Environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Database Migrations & Seed Cadastral Data
```bash
python -m app.db.migrate
```
*This idempotently creates all PostgreSQL tables, activates the PostGIS extension, configures spatial indexes, and seeds synthetic cadastral parcels.*

### Step 4: Start FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Start Celery AI Worker (in a separate terminal)
```bash
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info -c 2
```

### Step 6: Start Next.js Frontend (in a separate terminal)
```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ Configuration & Environment Variables

All core parameters are configured in `.env`. Key options include:

```ini
# Application Configuration
APP_NAME="Land Record AI System"
APP_ENV=development

# Database (PostgreSQL + PostGIS + pgvector)
DATABASE_URL=postgresql+psycopg://land_admin:land_password@localhost:5432/land_records
POSTGIS_ENABLED=true

# Redis / Celery Task Broker
REDIS_URL=redis://localhost:6379/0

# MinIO Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_password
MINIO_SECURE=false
MINIO_BUCKET=land-documents

# Security & Authentication
JWT_SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256

# AI OCR & Layout Models
OCR_MODEL_PATH=./models/paddleocr
TROCR_MODEL_NAME=microsoft/trocr-base-handwritten

# Optional: National Bhashini Translation & OCR API
ENABLE_BHASHINI=false
BHASHINI_API_KEY=
BHASHINI_API_URL=

# Optional: Vision-Language Model (VLM) Fallback
ENABLE_VLM_FALLBACK=false
VLM_CONFIDENCE_THRESHOLD=0.60
DEFAULT_VLM_PROVIDER=gemini # gemini | openai | anthropic
GEMINI_API_KEY=
```

---

## 🔍 Core Functional Modules

### 1. Multilingual OCR & Layout Understanding
- **PaddleOCR Engine**: Extracts printed multi-lingual text in native Devanagari and regional scripts with character-level confidence scores.
- **Microsoft TrOCR**: High-precision transformer-based vision model for transcribing handwritten mutation notes, patwari marginalia, and registrar remarks.
- **LayoutLMv3**: Visual Document Understanding (VDU) aligning detected text bounding boxes with standardized key-value semantic categories.

### 2. Dynamic Land Record Templates
Revenue documents vary widely across Indian states. BhumiLekh includes dynamic extraction profiles:
- **7/12 (Satbara Utara)**: Gaon Namuna 7 (ownership) & 12 (crop/cultivation) extraction.
- **Khasra / Khatauni / Jamabandi**: Northern states revenue registers, extraction of Khata Number, Khasra Number, and Land Ceiling Classifications.
- **Patta & Chitta**: Southern states land ownership certificates and survey land settlement records.
- **Bhoomi RTC**: Karnataka computerized Land Records format.

### 3. Multi-Tier Anomaly & Fraud Detection
The system subjects all extracted records to a 4-level validation pipeline:
1. **Field-Level Rules**: Format validation of Survey Numbers (`123/A`, `456/1-2`), Aadhaar/PAN hashing, valid registration dates, and standardized area units (Hectares, Acres, Bigha, Guntha, Sq. Yards).
2. **Record-Level Consistency**: Checks that the sum of co-owner land shares equals exactly 100% (or 1.0) and flags illegal sub-divisions.
3. **Cross-Record & Historical Verification**: Validates transaction continuity against previous mutation records to prevent double-sale fraud.
4. **Spatial Overlap & GIS Verification**: Executes PostGIS `ST_Intersects` and `ST_Overlaps` queries against cadastral base maps to detect boundary encroachment.

### 4. GIS Cadastral Boundary & Spatial Validation
- Interactive cadastral map powered by **Leaflet**.
- Renders parcel boundaries stored as GeoJSON / PostGIS `geometry(Polygon, 4326)`.
- Clicking any parcel displays ownership details, khasra number, computed vs. documented area, and spatial conflict flags.

### 5. Human-in-the-Loop (HITL) Verification
When confidence falls below threshold or an anomaly is triggered:
- The document is routed to the **Verification Console** (`/verify`).
- Officers view the scanned deed alongside editable fields with color-coded confidence indicators (`HIGH` $\ge 85\%$, `MEDIUM` $60-84\%$, `LOW` $< 60\%$).
- Reviewers can approve, correct values, or escalate for field inspection.

### 6. Continuous Active Learning
- Every manual correction made during HITL review is automatically cataloged in `training_samples`.
- Model versions and accuracy deltas are tracked in `learning_snapshots`.
- Re-triggering learning updates OCR character frequency mappings and extraction confidence weights without requiring full model retraining.

### 7. Indian Government UI & Accessibility Standard
- **Strict Light Theme**: Official Indian government portal palette (Warm Amber `#E89B1C`, Deep Saffron `#E05A10`, Crisp Neutral Gray `#F8F9FA`, Charcoal `#1F2937`).
- **Zero Dark Mode**: Adheres strictly to government portal design conventions.
- **High-Contrast Light Mode**: Increases contrast ratios for users with visual impairments.
- **Font Resizing Engine**: Instant client-side scaling (`A-`, `A`, `A+`, `Reset`).
- **Language Localization**: Multi-lingual interface switching across 13 Indian scheduled languages.

---

## 📡 REST API Reference

The FastAPI backend provides structured REST endpoints under `/api/v1`:

### Documents API (`/api/v1/documents`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload PDF/TIFF/Image & trigger Celery processing pipeline |
| `GET` | `/documents` | List uploaded documents with status and search filters |
| `GET` | `/documents/{id}` | Get comprehensive document detail with extraction stages |
| `GET` | `/documents/{id}/file` | Stream raw document file or rendered page image |
| `GET` | `/documents/{id}/status` | Fast polling endpoint for async pipeline progress |
| `GET` | `/documents/{id}/results` | Retrieve extracted structured fields with confidence scores |
| `PATCH` | `/documents/{id}/fields/{field_id}` | Update field value during HITL verification |
| `POST` | `/documents/{id}/reprocess` | Re-run AI extraction pipeline with explicit language override |
| `POST` | `/documents/{id}/translate` | Translate extracted fields into a target Indian language |
| `GET` | `/documents/{id}/validation` | Retrieve anomaly and rule violation reports |
| `GET` | `/documents/{id}/duplicates` | Check duplicate filings via cryptographic and vector similarity |

### GIS & LRMS Integration API (`/api/v1/documents/integration`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/integration/status` | Status of connected state LRMS/DILRMP adapters |
| `GET` | `/integration/lrms/lookup` | Search state registries by Survey/Khasra/Khata number |
| `GET` | `/integration/gis/parcels` | Retrieve cadastral parcels as GeoJSON FeatureCollection |
| `GET` | `/integration/gis/parcels/{id}` | Retrieve specific parcel boundary geometry and metadata |
| `GET` | `/integration/gis/nearby` | Spatial query returning parcels within radial distance |

### Continuous Learning API (`/api/v1/documents/learning`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/learning/stats` | Active learning sample counts and accuracy metrics |
| `POST` | `/learning/trigger` | Trigger active learning adaptation cycle |
| `GET` | `/learning/history` | Versioned history of learning snapshots and improvements |

---

## 🗺️ Portal Routes & Navigation

| Route | Page | Description |
|---|---|---|
| `/` | **Home Portal** | Government landing page with quick services, workflow guide, and pipeline status |
| `/dashboard` | **System Dashboard** | Operational KPIs, status breakdown, and recent documents queue |
| `/upload` | **Document Upload** | Multi-file uploader with real-time Celery pipeline stage tracker |
| `/documents` | **Document Repository** | Searchable archive with filters by state, language, status, and date |
| `/documents/[id]` | **Document Details** | Dual-pane viewer with page navigation and structured field breakdown |
| `/verify` | **Verification Console** | HITL review station with field editing, confidence badges, and approval workflow |
| `/map` | **Land Map (GIS)** | Interactive PostGIS cadastral parcel viewer with boundary inspection |
| `/help` | **Help Desk** | Document format specifications, legal standards, and operating guidelines |
| `/privacy` | **Privacy Policy** | Data security and citizen privacy disclosures |
| `/terms` | **Terms of Service** | Legal and prototype verification terms |

---

## 🧪 Testing & Quality Assurance

### Run Backend Unit & Integration Tests
```bash
cd backend
source .venv/bin/activate
pytest -v
```

### TypeScript Validation (Frontend)
```bash
cd frontend
npx tsc --noEmit
```

### Production Build Verification
```bash
cd frontend
npm run build
```

---

## ❓ Troubleshooting & FAQs

### 1. Port 3000 or 8000 is already in use
The startup script automatically attempts to clear lingering dev processes. To manually kill processes on standard ports:
```bash
lsof -ti :3000 | xargs kill -9
lsof -ti :8000 | xargs kill -9
```

### 2. Celery Worker is not picking up tasks
Ensure Redis is running and reachable:
```bash
docker exec land-record-redis redis-cli ping
# Output should be: PONG
```
Check Celery logs:
```bash
tail -f logs/celery.log
```

### 3. Database migrations or PostGIS issues
To re-run migrations manually:
```bash
cd backend
source .venv/bin/activate
python -m app.db.migrate
```

### 4. MinIO S3 Connection Refused
Verify that the MinIO container is healthy:
```bash
docker ps --filter "name=land-record-minio"
```
Log in to the MinIO web console at [http://localhost:9001](http://localhost:9001) (`minio_admin` / `minio_password`) and verify the `land-documents` bucket exists.

---

## 📄 License & Attribution

This project is developed under the **MIT License**.

Designed and built in compliance with the **Digital India Land Records Modernization Programme (DILRMP)** standards and open-source accessibility guidelines.
