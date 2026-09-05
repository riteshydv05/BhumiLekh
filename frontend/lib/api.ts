/**
 * Centralized API Client for Land Record AI System.
 * Connects to FastAPI backend at /api/v1.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: string;
  created_at: string;
  updated_at?: string;
  ocr_confidence?: number | null;
  detected_language?: string | null;
  document_type?: string | null;
  page_count?: number;
  error_message?: string | null;
  processing_metadata?: {
    pipeline_start?: string;
    pipeline_end?: string;
    stages?: Record<string, any>;
    [key: string]: any;
  } | null;
}

export interface DocumentResultItem {
  id: string;
  document_id: string;
  field_name: string;
  field_value: string | null;
  normalized_value?: string | null;
  data_type?: string | null;
  confidence: number | null;
  page_number?: number | null;
  bounding_box?: number[] | null;
  source_text?: string | null;
  extraction_method?: string | null;
  canonical_key?: string | null;
  original_text: string | null;
  normalized_text: string | null;
  transliteration: string | null;
  translation: string | null;
  validated: boolean;
  validation_status?: string | null;
  anomaly_flag: boolean;
  anomaly_reason: string | null;
  created_at?: string;
}

export interface DocumentResultsResponse {
  document_id: string;
  status: string;
  document_type?: string | null;
  count: number;
  field_count: number;
  results: DocumentResultItem[];
  fields: DocumentResultItem[];
}

export interface DocumentStatusResponse {
  id: string;
  status: string;
  error_message: string | null;
  ocr_confidence: number | null;
  detected_language: string | null;
  updated_at: string | null;
}

export interface OcrPage {
  id: string;
  page_number: number;
  raw_text: string | null;
  language: string | null;
  ocr_confidence: number | null;
  ocr_engine: string | null;
  blocks_json: any[] | null;
  created_at: string | null;
}

export interface OcrPagesResponse {
  document_id: string;
  page_count: number;
  pages: OcrPage[];
}

/**
 * Upload a document file to the backend.
 */
/**
 * Upload a document file to the backend.
 */
export async function uploadDocument(file: File, language?: string): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  if (language) {
    formData.append("language", language);
  }

  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = "Upload failed";
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

/**
 * Re-run AI OCR and extraction pipeline with a target language.
 */
export async function reprocessDocument(documentId: string, language: string): Promise<{ document_id: string; status: string; language: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/reprocess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language }),
  });

  if (!res.ok) throw new Error(`Failed to reprocess document (${res.status})`);
  return res.json();
}

/**
 * Translate document extracted fields to target language (e.g. 'en', 'hi', 'mr', 'ta').
 */
export async function translateDocument(documentId: string, targetLanguage: string): Promise<{ document_id: string; target_language: string; fields_translated: number; fields: DocumentResultItem[] }> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_language: targetLanguage }),
  });

  if (!res.ok) throw new Error(`Failed to translate document fields (${res.status})`);
  return res.json();
}

/**
 * Retrieve list of all documents.
 */
export async function getDocuments(): Promise<DocumentItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/documents`, {
      method: "GET",
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error(`Failed to fetch documents (${res.status})`);
    }

    return res.json();
  } catch (err: any) {
    console.error("getDocuments error:", err);
    throw err;
  }
}

/**
 * Retrieve detailed metadata for a single document.
 */
export async function getDocument(id: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Document not found or error (${res.status})`);
  }

  return res.json();
}

/**
 * Poll document processing status.
 */
export async function getDocumentStatus(id: string): Promise<DocumentStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/status`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Status check failed (${res.status})`);
  }

  return res.json();
}

/**
 * Retrieve extracted land record field results for a document.
 */
export async function getDocumentResults(id: string): Promise<DocumentResultsResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/results`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to retrieve results (${res.status})`);
  }

  return res.json();
}

/**
 * Get raw OCR pages for a document.
 */
export async function getDocumentOcr(id: string): Promise<OcrPagesResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/ocr`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to retrieve OCR pages (${res.status})`);
  }

  return res.json();
}

/**
 * Add a manual field to a document.
 */
export async function addDocumentField(
  documentId: string,
  body: { field_name: string; field_value?: string; data_type?: string; canonical_key?: string },
): Promise<DocumentResultItem> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/fields`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`Failed to add field (${res.status})`);
  return res.json();
}

/**
 * Edit an existing field.
 */
export async function updateDocumentField(
  documentId: string,
  fieldId: string,
  body: Partial<DocumentResultItem>,
): Promise<DocumentResultItem> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/fields/${fieldId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`Failed to update field (${res.status})`);
  return res.json();
}

/**
 * Delete a field.
 */
export async function deleteDocumentField(
  documentId: string,
  fieldId: string,
): Promise<{ status: string; field_id: string }> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}/fields/${fieldId}`, {
    method: "DELETE",
  });

  if (!res.ok) throw new Error(`Failed to delete field (${res.status})`);
  return res.json();
}

/**
 * Get direct streaming URL for the original document file.
 */
export function getDocumentFileUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/file`;
}

// ---------------------------------------------------------------------------
// Validation Results
// ---------------------------------------------------------------------------

export interface FieldValidation {
  id: string;
  field_name: string;
  confidence_score: number | null;
  confidence_category: string | null;
  validation_passed: boolean;
  validation_errors: string[] | null;
  verification_status: string | null;
  reference_value: string | null;
  anomaly_detected: boolean;
  anomaly_details: string | null;
  is_duplicate_flag: boolean;
}

export interface ValidationResponse {
  document_id: string;
  overall_confidence: number | null;
  overall_confidence_category: string | null;
  high_count: number;
  medium_count: number;
  low_count: number;
  uncertain_count: number;
  flagged_fields: string[];
  anomalies: string[];
  requires_human_review: boolean;
  field_validations: FieldValidation[];
  count: number;
}

export async function getDocumentValidation(id: string): Promise<ValidationResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/validation`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to retrieve validation results (${res.status})`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Cross-Database Verification
// ---------------------------------------------------------------------------

export interface FieldVerification {
  field_name: string;
  canonical_key: string | null;
  extracted_value: string | null;
  reference_value: string | null;
  status: string;
  source: string;
}

export interface VerificationResponse {
  document_id: string;
  overall_status: string;
  match_count: number;
  mismatch_count: number;
  not_found_count: number;
  not_verifiable_count: number;
  reference_record_id: string | null;
  field_verifications: FieldVerification[];
}

export async function getDocumentVerification(id: string): Promise<VerificationResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/verification`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to retrieve verification results (${res.status})`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Duplicate Detection
// ---------------------------------------------------------------------------

export interface DuplicateCandidate {
  document_id: string;
  filename: string;
  match_type: string;
  matched_fields: string[];
  similarity_score: number;
}

export interface DuplicateResponse {
  document_id: string;
  file_hash: string;
  has_file_duplicate: boolean;
  has_content_duplicate: boolean;
  duplicate_count: number;
  duplicates: DuplicateCandidate[];
}

export async function getDocumentDuplicates(id: string): Promise<DuplicateResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/${id}/duplicates`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to retrieve duplicate results (${res.status})`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Continuous AI Learning
// ---------------------------------------------------------------------------

export interface CorrectionCount {
  total: number;
  corrections: number;
  accuracy: number;
}

export interface FrequentlyCorrectedField {
  field_name: string;
  correction_count: number;
}

export interface LearningVersion {
  version: number;
  training_samples_count: number;
  accuracy_before: number | null;
  accuracy_after: number | null;
  improvement_delta: number | null;
  deployed: boolean;
  deployment_notes: string | null;
  patterns_summary?: {
    label_mappings: number;
    ocr_corrections: number;
    confidence_adjustments: number;
    doctype_fields: number;
  };
  created_at: string | null;
}

export interface LearningStatsResponse {
  total_training_samples: number;
  unused_samples: number;
  retrain_threshold: number;
  ready_to_learn: boolean;
  correction_type_breakdown: Record<string, number>;
  frequently_corrected_fields: FrequentlyCorrectedField[];
  document_type_distribution: Record<string, number>;
  active_version: LearningVersion | null;
  version_history: LearningVersion[];
  patterns_summary: {
    label_mappings_count: number;
    ocr_corrections_count: number;
    confidence_adjustments_count: number;
    doctype_patterns_count: number;
  };
  field_accuracy_rates: Record<string, number>;
}

export interface LearningCycleResult {
  status: string;
  version?: number;
  training_samples?: number;
  test_samples?: number;
  accuracy_before?: number;
  accuracy_after?: number;
  improvement_delta?: number;
  reason?: string;
  error?: string;
  patterns_learned?: {
    label_mappings: number;
    ocr_corrections: number;
    confidence_adjustments: number;
    doctype_fields: number;
  };
}

export interface LearningHistoryResponse {
  total_versions: number;
  versions: LearningVersion[];
}

export async function getLearningStats(): Promise<LearningStatsResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/learning/stats`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to retrieve learning stats (${res.status})`);
  return res.json();
}

export async function triggerLearningCycle(): Promise<LearningCycleResult> {
  const res = await fetch(`${API_BASE_URL}/documents/learning/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) throw new Error(`Failed to trigger learning cycle (${res.status})`);
  return res.json();
}

export async function getLearningHistory(): Promise<LearningHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/learning/history`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to retrieve learning history (${res.status})`);
  return res.json();
}

// ---------------------------------------------------------------------------
// GIS / LRMS Integration
// ---------------------------------------------------------------------------

export interface GeoJSONGeometry {
  type: string;
  coordinates: number[][][] | number[][] | number[];
}

export interface ParcelProperties {
  id: string;
  survey_number: string | null;
  khasra_number: string | null;
  khata_number: string | null;
  plot_number: string | null;
  owner_name: string | null;
  father_name: string | null;
  village: string | null;
  tehsil: string | null;
  district: string | null;
  state: string | null;
  area: string | null;
  land_classification: string | null;
  registration_number: string | null;
  mutation_number: string | null;
  lrms_id: string | null;
  dilrmp_id: string | null;
  source_database: string | null;
  centroid_lat: number | null;
  centroid_lng: number | null;
  matched_from_document?: string;
  matched_identifiers?: Record<string, string>;
}

export interface GeoJSONFeature {
  type: "Feature";
  id: string;
  geometry: GeoJSONGeometry | null;
  properties: ParcelProperties;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
  metadata?: {
    total_parcels: number;
    source: string;
    crs: string;
    note: string;
  };
}

export interface LRMSLookupResponse {
  status: string;
  source_system: string;
  match_score: number;
  matched_fields: string[];
  record?: Record<string, unknown>;
  error?: string;
}

export interface DocumentParcelResponse {
  status: string;
  document_id: string;
  parcel?: GeoJSONFeature;
  message?: string;
}

export interface IntegrationStatus {
  active_adapter: string;
  available_adapters: { name: string; status: string; description: string }[];
  postgis_enabled: boolean;
  data_source_label: string;
}

export async function getGISParcels(village?: string, district?: string): Promise<GeoJSONFeatureCollection> {
  const params = new URLSearchParams();
  if (village) params.set("village", village);
  if (district) params.set("district", district);
  const qs = params.toString() ? `?${params.toString()}` : "";

  const res = await fetch(`${API_BASE_URL}/documents/integration/gis/parcels${qs}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to get parcels (${res.status})`);
  return res.json();
}

export async function getDocumentParcel(docId: string): Promise<DocumentParcelResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/integration/documents/${docId}/parcel`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Failed to get document parcel (${res.status})`);
  return res.json();
}

export async function lookupLRMS(params: Record<string, string>): Promise<LRMSLookupResponse> {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE_URL}/documents/integration/lrms/lookup?${qs}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`LRMS lookup failed (${res.status})`);
  return res.json();
}

export async function getIntegrationStatus(): Promise<IntegrationStatus> {
  const res = await fetch(`${API_BASE_URL}/documents/integration/status`, {
    method: "GET",
    cache: "no-store",
  });

  if (!res.ok) throw new Error(`Integration status failed (${res.status})`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Authentication & User Management API
// ---------------------------------------------------------------------------

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  role: string;
  full_name?: string | null;
}

export interface UserProfile {
  id: string;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  created_at?: string | null;
  last_login?: string | null;
}

export async function loginUser(username: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Invalid credentials");
  }
  return res.json();
}

export async function listUsers(token?: string): Promise<{ count: number; users: UserProfile[] }> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/auth/users`, {
    method: "GET",
    headers,
    cache: "no-store",
  });

  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

// ---------------------------------------------------------------------------
// Admin Document & Record Mutations
// ---------------------------------------------------------------------------

export async function updateDocumentStatus(
  docId: string,
  status: string,
  errorMessage?: string,
  token?: string
): Promise<{ document_id: string; status: string; message: string }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/documents/${docId}/status`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ status, error_message: errorMessage }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to update document status" }));
    throw new Error(err.detail || "Failed to update status");
  }
  return res.json();
}

export async function deleteDocument(docId: string, token?: string): Promise<{ status: string; document_id: string }> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/documents/${docId}`, {
    method: "DELETE",
    headers,
  });

  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

