# Walkthrough: Indian Government Digital-Service Land Record Portal

## Overview
Built a responsive, accessible, professional Indian government-style digital service portal for the **Intelligent Land Record Digitization and Validation System**.

---

## 1. Design Identity & System Requirements
- **Theme**: Strict Light Theme with Indian Government identity (Warm Yellow `#E89B1C`, Indian Saffron/Orange `#E05A10`, Crisp White, Light Neutral Gray `#F8F9FA`, Charcoal text `#1F2937`).
- **NO Dark Mode**: There is **no dark mode toggle and no dark mode**.
- **Accessibility System**:
  - **High Contrast Light Mode**: Increases text darkness to `#000000` with high-contrast outlines and borders without dark mode.
  - **Font Resizing**: Real-time scalable font controls (`A-`, `A`, `A+`, `Reset`).
  - **Multilingual Support**: Header selector supporting 13 scheduled Indian languages (English, Hindi, Marathi, Gujarati, Bengali, Punjabi, Telugu, Tamil, Kannada, Malayalam, Odia, Assamese, Urdu).

---

## 2. Implemented Routes & Navigation
Every navigation link points to an active route with zero broken links:

| Route | Page Name | Features |
|---|---|---|
| `/` | **Home Portal** | Government hero, 4 Quick Services cards, 5-stage How It Works guide, local AI pipeline system status cards. |
| `/dashboard` | **System Dashboard** | Live KPI summary cards (Total, Processing, Completed, Audit Required, Failed), Recent Documents table with direct View and Verify actions. |
| `/upload` | **Document Upload** | Drag & Drop + file browser (PDF, JPEG, PNG, TIFF up to 50MB), client validation, and real-time Celery polling progress bar through 4 pipeline stages. |
| `/documents` | **My Documents** | Complete land records repository with search by filename/ID, status filter, language filter, responsive data table, and empty states. |
| `/documents/[id]` | **Document Details** | Split view: Left original scan preview (`DocumentViewer` with zoom/rotate), Right 5 structured sections (Land Owner, Land Identifiers & Area, Location Jurisdiction, Registration/Mutation, Anomaly Detection). |
| `/verify` | **Verification Console** | Split-screen human-in-the-loop review: Left original document viewer, Right editable fields with Confidence Badges (`HIGH`, `MEDIUM`, `LOW`), anomaly flags, and Approve / Flag for Escalation actions. Responsive vertical stack on mobile. |
| `/map` | **Land Map (GIS)** | Dynamic Leaflet cadastral boundary viewer with interactive parcel polygons, survey coordinates, and land ownership metadata panel. |
| `/help` | **Help Desk** | Operating instructions, accepted document formats, and FAQ. |
| `/privacy` | **Privacy Policy** | Offline-first data protection and governance policy. |
| `/terms` | **Terms of Service** | Legal and prototype verification terms. |
| `/contact` | **Contact Nodal Office**| Department coordinates and technical inquiry submission form. |
| `/_not-found` | **404 Handling** | Accessible government 404 error screen. |

---

## 3. Centralized API Integration (`frontend/lib/api.ts`)
Configured to connect directly to the FastAPI backend:
- `uploadDocument(file)` $\to$ `POST /api/v1/documents/upload`
- `getDocuments()` $\to$ `GET /api/v1/documents`
- `getDocument(id)` $\to$ `GET /api/v1/documents/{id}`
- `getDocumentStatus(id)` $\to$ `GET /api/v1/documents/{id}/status`
- `getDocumentResults(id)` $\to$ `GET /api/v1/documents/{id}/results`
- `getDocumentFileUrl(id)` $\to$ `GET /api/v1/documents/{id}/file`

---

## 4. Verification & Build Results

### TypeScript Type-check
```bash
./node_modules/.bin/tsc --noEmit
# Exit code: 0 (0 errors)
```

### Next.js Production Build
```bash
npm run build
# Exit code: 0 (13/13 static & dynamic routes generated successfully)
```

```
Route (app)                              Size     First Load JS
┌ ○ /                                    4.46 kB        98.4 kB
├ ○ /_not-found                          137 B          87.3 kB
├ ○ /contact                             2.71 kB        96.6 kB
├ ○ /dashboard                           1.67 kB        99.8 kB
├ ○ /documents                           2.23 kB         100 kB
├ ƒ /documents/[id]                      3.51 kB         101 kB
├ ○ /help                                2.64 kB        96.6 kB
├ ○ /map                                 2.91 kB        96.8 kB
├ ○ /privacy                             2.32 kB        96.3 kB
├ ○ /terms                               2.12 kB          96 kB
├ ○ /upload                              5.64 kB        99.6 kB
└ ○ /verify                              2.83 kB         101 kB
```
