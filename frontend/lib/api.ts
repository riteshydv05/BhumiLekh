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
  original_text: string | null;
  normalized_text: string | null;
  transliteration: string | null;
  translation: string | null;
  confidence: number | null;
  validated: boolean;
  anomaly_flag: boolean;
  anomaly_reason: string | null;
  created_at?: string;
}

export interface DocumentResultsResponse {
  document_id: string;
  count: number;
  results: DocumentResultItem[];
}

export interface DocumentStatusResponse {
  id: string;
  status: string;
  error_message: string | null;
  ocr_confidence: number | null;
  detected_language: string | null;
  updated_at: string | null;
}

/**
 * Upload a document file to the backend.
 */
export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);

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
 * Get direct streaming URL for the original document file.
 */
export function getDocumentFileUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/file`;
}
