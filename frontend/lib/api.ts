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
