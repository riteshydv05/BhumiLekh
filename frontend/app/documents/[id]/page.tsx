"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getDocument,
  getDocumentResults,
  getDocumentFileUrl,
  DocumentItem,
  DocumentResultItem,
} from "@/lib/api";
import Breadcrumb from "@/components/layout/Breadcrumb";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import ConfidenceBadge from "@/components/verification/ConfidenceBadge";
import DocumentViewer from "@/components/documents/DocumentViewer";
import {
  ArrowLeft,
  FileText,
  ShieldCheck,
  AlertTriangle,
  User,
  MapPin,
  LandPlot,
  FileCheck2,
  Calendar,
  Layers,
  AlertCircle,
} from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const docId = params.id as string;

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [results, setResults] = useState<DocumentResultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [docData, resData] = await Promise.all([
          getDocument(docId),
          getDocumentResults(docId).catch(() => ({ document_id: docId, count: 0, results: [] })),
        ]);
        setDocument(docData);
        setResults(resData.results || []);
      } catch (err: any) {
        setError(err.message || "Failed to load document details");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [docId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-12 text-center text-xs text-gray-500">
        <div className="inline-block animate-spin w-8 h-8 border-3 border-amber-600 border-t-transparent rounded-full mb-3" />
        <p>Loading document metadata and extracted records...</p>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="max-w-3xl mx-auto p-8 text-center">
        <AlertCircle className="w-12 h-12 text-rose-600 mx-auto mb-3" />
        <h2 className="text-base font-bold text-gray-900">Document Not Found</h2>
        <p className="text-xs text-gray-600 mt-1">{error || "Could not retrieve document"}</p>
        <Link
          href="/documents"
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-amber-600 text-white rounded text-xs font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Documents</span>
        </Link>
      </div>
    );
  }

  // Group fields into structured government categories
  const fieldMap: Record<string, DocumentResultItem> = {};
  results.forEach((r) => {
    fieldMap[r.field_name] = r;
  });

  const getField = (name: string) => fieldMap[name] || null;

  const fileUrl = getDocumentFileUrl(document.id);

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "My Documents", href: "/documents" },
          { label: document.filename || "Document Details" },
        ]}
      />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header with Title & Action */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Link
                href="/documents"
                className="text-gray-500 hover:text-gray-900 p-1 rounded hover:bg-gray-100"
                title="Back to list"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-lg font-bold text-gray-950 truncate max-w-xl">
                {document.filename}
              </h1>
              <DocumentStatusBadge status={document.status} />
            </div>
            <p className="text-[11px] text-gray-500 font-mono mt-1">
              Document ID: {document.id} • Format: {document.content_type} • Size:{" "}
              {document.file_size ? (document.file_size / 1024).toFixed(1) + " KB" : "—"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/verify?documentId=${document.id}`}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold uppercase tracking-wider rounded flex items-center gap-1.5 shadow-sm transition"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Open Verification Console</span>
            </Link>
          </div>
        </div>

        {/* Split Screen View: Left Preview, Right Extracted Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Document Preview Canvas (5 cols) */}
          <div className="lg:col-span-5 flex flex-col h-[700px]">
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-700 mb-2 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-amber-700" />
              <span>Original Document Scan</span>
            </h2>

            <div className="flex-1 min-h-0">
              <DocumentViewer
                fileUrl={fileUrl}
                contentType={document.content_type}
                filename={document.filename}
              />
            </div>
          </div>

          {/* Right: Extracted Structured Information (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-700 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-amber-700" />
                <span>Extracted Record Data ({results.length} Fields)</span>
              </span>
              <span className="text-[11px] text-gray-500 font-normal">
                Detected Script: {document.detected_language || "Auto-detected"}
              </span>
            </h2>

            {/* Section 1: Land Owner Details */}
            <div className="gov-card p-4">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <User className="w-4 h-4 text-amber-700" />
                <span>1. Land Owner Information</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[11px]">Primary Owner Name</span>
                  <p className="font-semibold text-gray-900 mt-0.5">
                    {getField("OWNER_NAME")?.field_value || "Not available"}
                  </p>
                  {getField("OWNER_NAME")?.transliteration && (
                    <p className="text-[11px] text-gray-500 italic">
                      Transliteration: {getField("OWNER_NAME")?.transliteration}
                    </p>
                  )}
                  {getField("OWNER_NAME") && (
                    <div className="mt-1">
                      <ConfidenceBadge score={getField("OWNER_NAME")?.confidence} />
                    </div>
                  )}
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Father / Husband Name</span>
                  <p className="font-semibold text-gray-900 mt-0.5">
                    {getField("FATHER_NAME")?.field_value || "Not available"}
                  </p>
                  {getField("FATHER_NAME")?.transliteration && (
                    <p className="text-[11px] text-gray-500 italic">
                      Transliteration: {getField("FATHER_NAME")?.transliteration}
                    </p>
                  )}
                  {getField("FATHER_NAME") && (
                    <div className="mt-1">
                      <ConfidenceBadge score={getField("FATHER_NAME")?.confidence} />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Section 2: Land Identifiers & Area */}
            <div className="gov-card p-4">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <LandPlot className="w-4 h-4 text-amber-700" />
                <span>2. Land Identifiers & Area</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[11px]">Survey / Khasra No.</span>
                  <p className="font-mono font-bold text-gray-900 mt-0.5">
                    {getField("SURVEY_NUMBER")?.field_value ||
                      getField("KHASRA_NUMBER")?.field_value ||
                      "Not available"}
                  </p>
                  {(getField("SURVEY_NUMBER") || getField("KHASRA_NUMBER")) && (
                    <div className="mt-1">
                      <ConfidenceBadge
                        score={
                          getField("SURVEY_NUMBER")?.confidence ||
                          getField("KHASRA_NUMBER")?.confidence
                        }
                      />
                    </div>
                  )}
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Khata / Account No.</span>
                  <p className="font-mono font-bold text-gray-900 mt-0.5">
                    {getField("KHATA_NUMBER")?.field_value || "Not available"}
                  </p>
                  {getField("KHATA_NUMBER") && (
                    <div className="mt-1">
                      <ConfidenceBadge score={getField("KHATA_NUMBER")?.confidence} />
                    </div>
                  )}
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Recorded Area</span>
                  <p className="font-bold text-gray-900 mt-0.5">
                    {getField("AREA")?.field_value || "Not available"}
                  </p>
                  {getField("AREA") && (
                    <div className="mt-1">
                      <ConfidenceBadge score={getField("AREA")?.confidence} />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Section 3: Location Details */}
            <div className="gov-card p-4">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-amber-700" />
                <span>3. Location Jurisdiction</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[11px]">Village / Mauza</span>
                  <p className="font-semibold text-gray-900 mt-0.5">
                    {getField("VILLAGE")?.field_value || "Not available"}
                  </p>
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Tehsil / Taluka</span>
                  <p className="font-semibold text-gray-900 mt-0.5">
                    {getField("TEHSIL")?.field_value || "Not available"}
                  </p>
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">District</span>
                  <p className="font-semibold text-gray-900 mt-0.5">
                    {getField("DISTRICT")?.field_value || "Not available"}
                  </p>
                </div>
              </div>
            </div>

            {/* Section 4: Registration & Mutation Details */}
            <div className="gov-card p-4">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <FileCheck2 className="w-4 h-4 text-amber-700" />
                <span>4. Registration & Mutation Details</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[11px]">Registration / Deed No.</span>
                  <p className="font-mono text-gray-900 mt-0.5">
                    {getField("REGISTRATION_NUMBER")?.field_value || "Not available"}
                  </p>
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Mutation No.</span>
                  <p className="font-mono text-gray-900 mt-0.5">
                    {getField("MUTATION_NUMBER")?.field_value || "Not available"}
                  </p>
                </div>

                <div>
                  <span className="text-gray-500 block text-[11px]">Execution Date</span>
                  <p className="font-mono text-gray-900 mt-0.5">
                    {getField("DATE")?.field_value || "Not available"}
                  </p>
                </div>
              </div>
            </div>

            {/* Section 5: Validation & Anomaly Detection */}
            <div className="gov-card p-4 border-l-4 border-l-amber-600">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                <span>5. Validation & Anomaly Verification Signal</span>
              </h3>

              {results.some((r) => r.anomaly_flag) ? (
                <div className="space-y-2">
                  <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold">Anomalies Detected by IsolationForest Validation</p>
                      <ul className="list-disc pl-4 mt-1 space-y-0.5 text-[11px]">
                        {results
                          .filter((r) => r.anomaly_flag && r.anomaly_reason)
                          .map((r, i) => (
                            <li key={i}>{r.anomaly_reason}</li>
                          ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 p-2.5 rounded flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-700" />
                  <span>No numerical or structural anomalies detected. All rule constraints satisfied.</span>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
