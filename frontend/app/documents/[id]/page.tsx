"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getDocument,
  getDocumentResults,
  getDocumentStatus,
  getDocumentFileUrl,
  reprocessDocument,
  translateDocument,
  getDocumentValidation,
  getDocumentVerification,
  getDocumentDuplicates,
  DocumentItem,
  DocumentResultItem,
  ValidationResponse,
  VerificationResponse,
  DuplicateResponse,
  LearningStatsResponse,
  getLearningStats,
  triggerLearningCycle,
  getDocumentParcel,
  DocumentParcelResponse,
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
  Languages,
  RotateCw,
  Globe,
  Sparkles,
  Database,
  Copy,
  Gauge,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Brain,
  TrendingUp,
  Zap,
  MapPinned,
} from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const docId = params.id as string;

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [results, setResults] = useState<DocumentResultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [validationData, setValidationData] = useState<ValidationResponse | null>(null);
  const [verificationData, setVerificationData] = useState<VerificationResponse | null>(null);
  const [duplicateData, setDuplicateData] = useState<DuplicateResponse | null>(null);
  const [learningData, setLearningData] = useState<LearningStatsResponse | null>(null);
  const [isLearning, setIsLearning] = useState<boolean>(false);
  const [learningResult, setLearningResult] = useState<string | null>(null);
  const [documentParcel, setDocumentParcel] = useState<DocumentParcelResponse | null>(null);

  const [selectedOcrLang, setSelectedOcrLang] = useState<string>("auto");
  const [selectedTargetLang, setSelectedTargetLang] = useState<string>("en");
  const [isReprocessing, setIsReprocessing] = useState<boolean>(false);
  const [isTranslating, setIsTranslating] = useState<boolean>(false);

  useEffect(() => {
    if (!docId) return;

    let isMounted = true;

    const fetchData = async (isInitial = false) => {
      if (isInitial) setLoading(true);
      try {
        const [docData, resData] = await Promise.all([
          getDocument(docId),
          getDocumentResults(docId).catch(() => ({ document_id: docId, count: 0, results: [], fields: [] } as any)),
        ]);
        if (!isMounted) return;
        setDocument(docData);
        setResults(resData.results || (resData as any).fields || []);
        if (docData.detected_language && docData.detected_language !== "unknown") {
          setSelectedOcrLang(docData.detected_language);
        }
        // Fetch validation, verification, and duplicate data (non-blocking)
        if (docData.status === "COMPLETED" || docData.status === "VERIFICATION_REQUIRED") {
          Promise.all([
            getDocumentValidation(docId).catch(() => null),
            getDocumentVerification(docId).catch(() => null),
            getDocumentDuplicates(docId).catch(() => null),
            getLearningStats().catch(() => null),
            getDocumentParcel(docId).catch(() => null),
          ]).then(([valData, verData, dupData, learnData, parcelData]) => {
            if (!isMounted) return;
            if (valData) setValidationData(valData);
            if (verData) setVerificationData(verData);
            if (dupData) setDuplicateData(dupData);
            if (learnData) setLearningData(learnData);
            if (parcelData) setDocumentParcel(parcelData);
          });
        }
        setError(null);
      } catch (err: any) {
        if (!isMounted) return;
        if (isInitial) {
          setError(err.message || "Failed to load document details");
        }
      } finally {
        if (isMounted && isInitial) {
          setLoading(false);
        }
      }
    };

    fetchData(true);

    // Poll while document is in non-terminal processing states
    const terminalStates = ["COMPLETED", "VERIFICATION_REQUIRED", "FAILED"];
    const interval = setInterval(async () => {
      if (!isMounted) return;
      if (document && terminalStates.includes(document.status) && !isReprocessing) {
        return;
      }
      await fetchData(false);
    }, 2500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [docId, document?.status, isReprocessing]);

  const handleReprocess = async () => {
    if (!docId) return;
    setIsReprocessing(true);
    try {
      await reprocessDocument(docId, selectedOcrLang);
      // Poll for status completion
      let status = "PROCESSING";
      for (let i = 0; i < 20; i++) {
        await new Promise((r) => setTimeout(r, 1200));
        const st = await getDocumentStatus(docId);
        status = st.status;
        if (["COMPLETED", "VERIFICATION_REQUIRED", "FAILED"].includes(status)) break;
      }
      const [updatedDoc, updatedRes] = await Promise.all([
        getDocument(docId),
        getDocumentResults(docId),
      ]);
      setDocument(updatedDoc);
      setResults(updatedRes.results || updatedRes.fields || []);
    } catch (err: any) {
      alert("Failed to reprocess document: " + (err.message || err));
    } finally {
      setIsReprocessing(false);
    }
  };

  const handleTranslate = async () => {
    if (!docId) return;
    setIsTranslating(true);
    try {
      const res = await translateDocument(docId, selectedTargetLang);
      setResults(res.fields || []);
    } catch (err: any) {
      alert("Failed to translate fields: " + (err.message || err));
    } finally {
      setIsTranslating(false);
    }
  };

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
          className="inline-block mt-4 px-4 py-2 bg-gray-900 text-white text-xs font-bold rounded"
        >
          Back to Documents
        </Link>
      </div>
    );
  }

  // Group fields dynamically by data_type or canonical_key
  const categorizeFields = (fields: DocumentResultItem[]) => {
    const people = fields.filter(
      (f) =>
        f.data_type === "person" ||
        ["owner_name", "father_name", "mother_name", "purchaser", "seller", "grantee"].some((k) =>
          (f.canonical_key || f.field_name).toLowerCase().includes(k)
        )
    );

    const identifiers = fields.filter(
      (f) =>
        !people.includes(f) &&
        (f.data_type === "identifier" ||
          ["survey_number", "khasra_number", "khata_number", "plot_number", "patta_number", "deed_number", "registration_number", "mutation_number"].some((k) =>
            (f.canonical_key || f.field_name).toLowerCase().includes(k)
          ))
    );

    const location = fields.filter(
      (f) =>
        !people.includes(f) &&
        !identifiers.includes(f) &&
        (f.data_type === "address" ||
          ["village", "tehsil", "district", "state", "block", "sub_division"].some((k) =>
            (f.canonical_key || f.field_name).toLowerCase().includes(k)
          ))
    );

    const financialAndArea = fields.filter(
      (f) =>
        !people.includes(f) &&
        !identifiers.includes(f) &&
        !location.includes(f) &&
        (f.data_type === "currency" ||
          f.data_type === "area" ||
          ["area", "stamp_duty", "consideration_amount", "tax", "assessment"].some((k) =>
            (f.canonical_key || f.field_name).toLowerCase().includes(k)
          ))
    );

    const dates = fields.filter(
      (f) =>
        !people.includes(f) &&
        !identifiers.includes(f) &&
        !location.includes(f) &&
        !financialAndArea.includes(f) &&
        (f.data_type === "date" ||
          (f.canonical_key || f.field_name).toLowerCase().includes("date"))
    );

    const other = fields.filter(
      (f) =>
        !people.includes(f) &&
        !identifiers.includes(f) &&
        !location.includes(f) &&
        !financialAndArea.includes(f) &&
        !dates.includes(f)
    );

    const categories = [];
    if (people.length > 0)
      categories.push({ label: "People & Ownership", icon: <User className="w-4 h-4 text-blue-600" />, fields: people });
    if (identifiers.length > 0)
      categories.push({ label: "Parcel & Registration Identifiers", icon: <LandPlot className="w-4 h-4 text-purple-600" />, fields: identifiers });
    if (location.length > 0)
      categories.push({ label: "Location & Administrative Divisions", icon: <MapPin className="w-4 h-4 text-green-600" />, fields: location });
    if (financialAndArea.length > 0)
      categories.push({ label: "Area & Financial Details", icon: <FileCheck2 className="w-4 h-4 text-emerald-600" />, fields: financialAndArea });
    if (dates.length > 0)
      categories.push({ label: "Dates & Timestamps", icon: <Calendar className="w-4 h-4 text-yellow-600" />, fields: dates });
    if (other.length > 0)
      categories.push({ label: "Other Extracted Fields", icon: <Layers className="w-4 h-4 text-gray-600" />, fields: other });

    // Fallback if categorization leaves empty list
    if (categories.length === 0 && fields.length > 0) {
      categories.push({ label: "Extracted Record Fields", icon: <Layers className="w-4 h-4 text-amber-600" />, fields });
    }

    return categories;
  };

  const categories = categorizeFields(results);

  const fileUrl = getDocumentFileUrl(document.id);

  const documentType = (document as any).document_type || "Unknown";

  const getScriptDisplayName = (code?: string | null) => {
    if (!code || code === "unknown") return "Auto-detected";
    const lower = code.toLowerCase();
    const map: Record<string, string> = {
      mr: "Marathi (मराठी)",
      hi: "Hindi (हिंदी)",
      en: "English",
      gu: "Gujarati (ગુજરાતી)",
      ta: "Tamil (தமிழ்)",
      te: "Telugu (తెలుగు)",
      kn: "Kannada (ಕನ್ನಡ)",
      ml: "Malayalam (മലയാളം)",
      pa: "Punjabi (ਪੰਜਾਬੀ)",
      bn: "Bengali (বাংলা)",
    };
    return map[lower] || code;
  };

  const getExtractionMethodLabel = (method?: string | null) => {
    if (!method) return "";
    const labels: Record<string, string> = {
      key_value_extraction: "Key-Value",
      ner: "NER",
      table_extraction: "Table",
      handwriting_ocr: "Handwriting",
      vlm: "VLM",
      manual: "Manual",
    };
    return labels[method] || method;
  };

  const getDataTypeColor = (dt?: string | null) => {
    const colors: Record<string, string> = {
      person: "bg-blue-50 text-blue-700 border-blue-200",
      identifier: "bg-purple-50 text-purple-700 border-purple-200",
      address: "bg-green-50 text-green-700 border-green-200",
      date: "bg-yellow-50 text-yellow-700 border-yellow-200",
      currency: "bg-emerald-50 text-emerald-700 border-emerald-200",
      area: "bg-orange-50 text-orange-700 border-orange-200",
      integer: "bg-gray-50 text-gray-600 border-gray-200",
      decimal: "bg-gray-50 text-gray-600 border-gray-200",
      string: "bg-gray-50 text-gray-500 border-gray-200",
    };
    return colors[dt || "string"] || colors.string;
  };

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
              {documentType !== "Unknown" && (
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                  {documentType}
                </span>
              )}
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
          <div className="lg:col-span-5 flex flex-col h-[750px]">
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

          {/* Right: Dynamic Extracted Information (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-700 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-amber-700" />
                <span>Extracted Record Data ({results.length} Fields)</span>
              </span>
              <span className="text-[11px] text-gray-500 font-normal">
                Detected Script: {getScriptDisplayName(document.detected_language)}
              </span>
            </h2>

            {/* Language Selection & Translation Control Bar */}
            <div className="gov-card p-3 bg-gradient-to-r from-amber-50/80 via-white to-amber-50/80 border border-amber-200/80 shadow-xs rounded-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1 text-amber-900 font-bold">
                  <Languages className="w-4 h-4 text-amber-700" />
                  <span>OCR Language:</span>
                </div>
                
                <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded border border-gray-300">
                  <select
                    value={selectedOcrLang}
                    onChange={(e) => setSelectedOcrLang(e.target.value)}
                    className="text-xs bg-transparent font-medium text-gray-900 focus:outline-none cursor-pointer"
                  >
                    <option value="auto">Auto-Detect</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="mr">Marathi (मराठी)</option>
                    <option value="te">Telugu (తెలుగు)</option>
                    <option value="kn">Kannada (ಕನ್ನಡ)</option>
                    <option value="gu">Gujarati (ગુજરાતી)</option>
                    <option value="ml">Malayalam (മലയാളം)</option>
                    <option value="bn">Bengali (বাংলা)</option>
                    <option value="pa">Punjabi (ਪੰਜਾਬੀ)</option>
                    <option value="en">English</option>
                  </select>
                  <button
                    onClick={handleReprocess}
                    disabled={isReprocessing}
                    className="px-2.5 py-0.5 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-[11px] font-bold rounded flex items-center gap-1 shadow-xs transition"
                    title="Re-run OCR with chosen language"
                  >
                    <RotateCw className={`w-3 h-3 ${isReprocessing ? "animate-spin" : ""}`} />
                    <span>{isReprocessing ? "Processing..." : "Re-run OCR"}</span>
                  </button>
                </div>
              </div>

              {/* Translate Section */}
              <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded border border-gray-300">
                <Globe className="w-3.5 h-3.5 text-blue-600" />
                <span className="text-[11px] text-gray-500 font-medium">Translate To:</span>
                <select
                  value={selectedTargetLang}
                  onChange={(e) => setSelectedTargetLang(e.target.value)}
                  className="text-xs bg-transparent font-medium text-gray-900 focus:outline-none cursor-pointer"
                >
                  <option value="en">English</option>
                  <option value="hi">Hindi (हिंदी)</option>
                  <option value="mr">Marathi (मराठी)</option>
                  <option value="ta">Tamil (தமிழ்)</option>
                  <option value="te">Telugu (తెలుగు)</option>
                  <option value="kn">Kannada (ಕನ್ನಡ)</option>
                  <option value="gu">Gujarati (ગુજરાતી)</option>
                  <option value="bn">Bengali (বাংলা)</option>
                  <option value="ml">Malayalam (മലയാളം)</option>
                </select>
                <button
                  onClick={handleTranslate}
                  disabled={isTranslating}
                  className="px-2.5 py-0.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-[11px] font-bold rounded flex items-center gap-1 shadow-xs transition"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>{isTranslating ? "Translating..." : "Translate"}</span>
                </button>
              </div>
            </div>

            {results.length === 0 && (
              <div className="gov-card p-6 text-center text-gray-500 text-sm">
                <AlertCircle className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                <p>No fields extracted yet. Document may still be processing or selected OCR language needs adjustment.</p>
              </div>
            )}

            {/* Dynamic field categories */}
            {categories.map((cat, catIdx) => (
              <div key={catIdx} className="gov-card p-4">
                <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                  {cat.icon}
                  <span>{catIdx + 1}. {cat.label}</span>
                  <span className="ml-auto text-[10px] text-gray-400 font-normal lowercase">
                    {cat.fields.length} field{cat.fields.length !== 1 ? "s" : ""}
                  </span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {cat.fields.map((f) => (
                    <div key={f.id} className="group p-2.5 rounded bg-gray-50/60 border border-gray-100 hover:border-amber-200 transition">
                      <span className="text-gray-500 block text-[11px] flex items-center gap-1 font-medium">
                        {f.field_name}
                        {f.canonical_key && (
                          <span className="text-[9px] text-gray-400 font-mono" title={`Canonical: ${f.canonical_key}`}>
                            [{f.canonical_key}]
                          </span>
                        )}
                      </span>
                      <p className="font-semibold text-gray-900 mt-0.5 break-words">
                        {f.field_value || f.original_text || "—"}
                      </p>
                      {f.translation && f.translation !== f.field_value && f.translation !== f.original_text && (
                        <p className="text-[11px] text-blue-700 font-medium mt-1 flex items-start gap-1 bg-blue-50/70 p-1.5 rounded border border-blue-100">
                          <span className="text-[9px] bg-blue-600 text-white px-1 py-0.5 rounded font-bold uppercase shrink-0">Translated</span>
                          <span className="break-words">{f.translation}</span>
                        </p>
                      )}
                      {f.transliteration && f.transliteration !== f.field_value && (
                        <p className="text-[10px] text-gray-500 italic mt-0.5">
                          Phonetic: {f.transliteration}
                        </p>
                      )}
                      <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                        {f.confidence != null && (
                          <ConfidenceBadge score={f.confidence} />
                        )}
                        {f.data_type && f.data_type !== "string" && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded border ${getDataTypeColor(f.data_type)}`}>
                            {f.data_type}
                          </span>
                        )}
                        {f.extraction_method && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-white text-gray-500 border border-gray-200">
                            {getExtractionMethodLabel(f.extraction_method)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {/* Validation & Anomaly Detection */}
            <div className="gov-card p-4 border-l-4 border-l-amber-600">
              <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                <span>Validation & Anomaly Verification Signal</span>
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

            {/* Confidence Scoring Dashboard */}
            {validationData && (
              <div className="gov-card p-4 border-l-4 border-l-indigo-600">
                <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                  <Gauge className="w-4 h-4 text-indigo-700" />
                  <span>Confidence Scoring Dashboard</span>
                  {validationData.overall_confidence_category && (
                    <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded border ${
                      validationData.overall_confidence_category === "HIGH"
                        ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                        : validationData.overall_confidence_category === "MEDIUM"
                        ? "bg-amber-50 text-amber-800 border-amber-300"
                        : validationData.overall_confidence_category === "LOW"
                        ? "bg-orange-50 text-orange-800 border-orange-300"
                        : "bg-rose-50 text-rose-800 border-rose-300"
                    }`}>
                      Overall: {validationData.overall_confidence_category}
                      {validationData.overall_confidence != null && ` (${(validationData.overall_confidence * 100).toFixed(0)}%)`}
                    </span>
                  )}
                </h3>

                <div className="grid grid-cols-4 gap-2 mb-3">
                  <div className="text-center p-2 bg-emerald-50 rounded border border-emerald-200">
                    <p className="text-lg font-bold text-emerald-700">{validationData.high_count}</p>
                    <p className="text-[9px] font-bold text-emerald-600 uppercase">High ≥85%</p>
                  </div>
                  <div className="text-center p-2 bg-amber-50 rounded border border-amber-200">
                    <p className="text-lg font-bold text-amber-700">{validationData.medium_count}</p>
                    <p className="text-[9px] font-bold text-amber-600 uppercase">Medium 60-84%</p>
                  </div>
                  <div className="text-center p-2 bg-orange-50 rounded border border-orange-200">
                    <p className="text-lg font-bold text-orange-700">{validationData.low_count}</p>
                    <p className="text-[9px] font-bold text-orange-600 uppercase">Low 30-59%</p>
                  </div>
                  <div className="text-center p-2 bg-rose-50 rounded border border-rose-200">
                    <p className="text-lg font-bold text-rose-700">{validationData.uncertain_count}</p>
                    <p className="text-[9px] font-bold text-rose-600 uppercase">Uncertain &lt;30%</p>
                  </div>
                </div>

                {validationData.flagged_fields.length > 0 && (
                  <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900">
                    <p className="font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {validationData.flagged_fields.length} field{validationData.flagged_fields.length !== 1 ? "s" : ""} flagged for review
                    </p>
                    <p className="text-[10px] mt-1 text-amber-700">
                      {validationData.flagged_fields.join(", ")}
                    </p>
                  </div>
                )}

                {validationData.requires_human_review && (
                  <p className="mt-2 text-[11px] text-rose-700 bg-rose-50 border border-rose-200 p-2 rounded flex items-center gap-1.5 font-medium">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>Human review required due to low confidence or validation issues.</span>
                  </p>
                )}
              </div>
            )}

            {/* Cross-Database Verification */}
            {verificationData && (
              <div className="gov-card p-4 border-l-4 border-l-blue-600">
                <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-blue-700" />
                  <span>Cross-Database Verification</span>
                  {documentParcel && documentParcel.status === "MATCHED" && (
                    <a
                      href={`/map?parcel=${documentParcel.parcel?.id}`}
                      className="ml-2 text-[9px] px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded font-semibold hover:bg-emerald-200 flex items-center gap-1 transition"
                    >
                      <MapPinned className="w-3 h-3" />
                      View on Map
                    </a>
                  )}
                  <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded border ${
                    verificationData.overall_status === "VERIFIED"
                      ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                      : verificationData.overall_status === "PARTIALLY_VERIFIED"
                      ? "bg-blue-50 text-blue-800 border-blue-300"
                      : verificationData.overall_status === "MISMATCH_DETECTED"
                      ? "bg-rose-50 text-rose-800 border-rose-300"
                      : verificationData.overall_status === "NOT_FOUND"
                      ? "bg-gray-100 text-gray-600 border-gray-300"
                      : "bg-gray-50 text-gray-500 border-gray-200"
                  }`}>
                    {verificationData.overall_status.replace(/_/g, " ")}
                  </span>
                </h3>

                <div className="grid grid-cols-4 gap-2 mb-3 text-center">
                  <div className="p-1.5 bg-emerald-50 rounded border border-emerald-200">
                    <p className="text-sm font-bold text-emerald-700">{verificationData.match_count}</p>
                    <p className="text-[8px] font-bold text-emerald-600 uppercase">Match</p>
                  </div>
                  <div className="p-1.5 bg-rose-50 rounded border border-rose-200">
                    <p className="text-sm font-bold text-rose-700">{verificationData.mismatch_count}</p>
                    <p className="text-[8px] font-bold text-rose-600 uppercase">Mismatch</p>
                  </div>
                  <div className="p-1.5 bg-gray-50 rounded border border-gray-200">
                    <p className="text-sm font-bold text-gray-600">{verificationData.not_found_count}</p>
                    <p className="text-[8px] font-bold text-gray-500 uppercase">Not Found</p>
                  </div>
                  <div className="p-1.5 bg-gray-50 rounded border border-gray-200">
                    <p className="text-sm font-bold text-gray-400">{verificationData.not_verifiable_count}</p>
                    <p className="text-[8px] font-bold text-gray-400 uppercase">N/A</p>
                  </div>
                </div>

                {verificationData.field_verifications.length > 0 && (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {verificationData.field_verifications
                      .filter((fv) => fv.status !== "NOT_VERIFIABLE")
                      .map((fv, idx) => (
                      <div key={idx} className="flex items-center justify-between text-[11px] p-1.5 rounded bg-gray-50/80 border border-gray-100">
                        <span className="text-gray-700 font-medium truncate max-w-[140px]" title={fv.field_name}>
                          {fv.canonical_key || fv.field_name}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {fv.status === "MATCH" && (
                            <span className="flex items-center gap-0.5 text-emerald-700">
                              <CheckCircle2 className="w-3 h-3" />
                              <span className="text-[9px] font-bold">MATCH</span>
                            </span>
                          )}
                          {fv.status === "MISMATCH" && (
                            <span className="flex items-center gap-0.5 text-rose-700" title={`Reference: ${fv.reference_value}`}>
                              <XCircle className="w-3 h-3" />
                              <span className="text-[9px] font-bold">MISMATCH</span>
                            </span>
                          )}
                          {fv.status === "NOT_FOUND" && (
                            <span className="flex items-center gap-0.5 text-gray-500">
                              <HelpCircle className="w-3 h-3" />
                              <span className="text-[9px]">NOT FOUND</span>
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {verificationData.reference_record_id && (
                  <p className="mt-2 text-[10px] text-gray-400 font-mono">
                    Reference ID: {verificationData.reference_record_id}
                  </p>
                )}
              </div>
            )}

            {/* Duplicate Detection */}
            {duplicateData && (duplicateData.has_file_duplicate || duplicateData.has_content_duplicate) && (
              <div className="gov-card p-4 border-l-4 border-l-rose-600">
                <h3 className="text-xs font-bold text-gray-900 uppercase border-b border-gray-100 pb-2 mb-3 flex items-center gap-1.5">
                  <Copy className="w-4 h-4 text-rose-700" />
                  <span>Duplicate Detection Warning</span>
                  <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-300">
                    {duplicateData.duplicate_count} duplicate{duplicateData.duplicate_count !== 1 ? "s" : ""} found
                  </span>
                </h3>

                <div className="space-y-2">
                  {duplicateData.duplicates.map((dup, idx) => (
                    <div key={idx} className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-rose-900 truncate max-w-[250px]">{dup.filename}</span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          dup.match_type === "file_hash"
                            ? "bg-rose-700 text-white"
                            : "bg-amber-600 text-white"
                        }`}>
                          {dup.match_type === "file_hash" ? "IDENTICAL FILE" : "CONTENT MATCH"}
                        </span>
                      </div>
                      {dup.matched_fields.length > 0 && (
                        <p className="text-[10px] text-rose-700 mt-1">
                          Matched: {dup.matched_fields.join(", ")}
                          {dup.similarity_score < 1 && ` (${(dup.similarity_score * 100).toFixed(0)}% similarity)`}
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {duplicateData.file_hash && (
                  <p className="mt-2 text-[10px] text-gray-400 font-mono">
                    SHA-256: {duplicateData.file_hash.substring(0, 16)}...
                  </p>
                )}
              </div>
            )}

            {/* No duplicates - clean message */}
            {duplicateData && !duplicateData.has_file_duplicate && !duplicateData.has_content_duplicate && (
              <div className="text-[11px] text-emerald-700 bg-emerald-50/50 border border-emerald-100 p-2 rounded flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>No duplicate documents detected. File hash: <span className="font-mono text-[9px]">{duplicateData.file_hash?.substring(0, 16)}...</span></span>
              </div>
            )}

            {/* AI Learning Insights Panel */}
            {learningData && (
              <div className="gov-card p-4 border-l-4 border-l-violet-600">
                <h3 className="text-xs font-bold text-violet-900 flex items-center gap-1.5 mb-3">
                  <Brain className="w-3.5 h-3.5" />
                  Continuous AI Learning
                </h3>

                {/* Active Model Version */}
                <div className="bg-violet-50/70 border border-violet-100 rounded p-2.5 mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-semibold text-violet-800">Active Model</span>
                    {learningData.active_version ? (
                      <span className="text-[9px] px-1.5 py-0.5 bg-violet-200 text-violet-800 rounded font-mono">
                        v{learningData.active_version.version}
                      </span>
                    ) : (
                      <span className="text-[9px] px-1.5 py-0.5 bg-gray-200 text-gray-600 rounded">
                        No model trained
                      </span>
                    )}
                  </div>
                  {learningData.active_version && (
                    <div className="grid grid-cols-2 gap-1.5">
                      <div className="text-[10px]">
                        <span className="text-gray-500">Accuracy: </span>
                        <span className="font-semibold text-violet-700">
                          {learningData.active_version.accuracy_after != null
                            ? `${(learningData.active_version.accuracy_after * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="text-[10px]">
                        <span className="text-gray-500">Improvement: </span>
                        <span className={`font-semibold ${
                          (learningData.active_version.improvement_delta || 0) > 0
                            ? 'text-emerald-600'
                            : 'text-gray-500'
                        }`}>
                          {learningData.active_version.improvement_delta != null
                            ? `${(learningData.active_version.improvement_delta > 0 ? '+' : '')}${(learningData.active_version.improvement_delta * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Training Dataset Stats */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="bg-white border rounded p-2 text-center">
                    <div className="text-sm font-bold text-violet-700">{learningData.total_training_samples}</div>
                    <div className="text-[9px] text-gray-500">Total Samples</div>
                  </div>
                  <div className="bg-white border rounded p-2 text-center">
                    <div className="text-sm font-bold text-amber-600">{learningData.unused_samples}</div>
                    <div className="text-[9px] text-gray-500">Unused</div>
                  </div>
                  <div className="bg-white border rounded p-2 text-center">
                    <div className="text-sm font-bold text-blue-600">
                      {learningData.correction_type_breakdown?.value_correction || 0}
                    </div>
                    <div className="text-[9px] text-gray-500">Corrections</div>
                  </div>
                </div>

                {/* Learned Patterns Summary */}
                {learningData.patterns_summary && (
                  <div className="mb-3">
                    <div className="text-[10px] font-semibold text-gray-700 mb-1">Learned Patterns</div>
                    <div className="grid grid-cols-2 gap-1">
                      <div className="text-[10px] flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-violet-500" />
                        <span className="text-gray-600">{learningData.patterns_summary.label_mappings_count} label mappings</span>
                      </div>
                      <div className="text-[10px] flex items-center gap-1">
                        <Zap className="w-3 h-3 text-amber-500" />
                        <span className="text-gray-600">{learningData.patterns_summary.ocr_corrections_count} OCR corrections</span>
                      </div>
                      <div className="text-[10px] flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-blue-500" />
                        <span className="text-gray-600">{learningData.patterns_summary.confidence_adjustments_count} confidence adjustments</span>
                      </div>
                      <div className="text-[10px] flex items-center gap-1">
                        <Database className="w-3 h-3 text-emerald-500" />
                        <span className="text-gray-600">{learningData.patterns_summary.doctype_patterns_count} doc-type patterns</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Frequently Corrected Fields */}
                {learningData.frequently_corrected_fields && learningData.frequently_corrected_fields.length > 0 && (
                  <div className="mb-3">
                    <div className="text-[10px] font-semibold text-gray-700 mb-1">Frequently Corrected Fields</div>
                    <div className="space-y-0.5">
                      {learningData.frequently_corrected_fields.slice(0, 5).map((f, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[10px]">
                          <span className="text-gray-600 truncate">{f.field_name}</span>
                          <span className="text-red-600 font-semibold">{f.correction_count}x corrected</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Learning Ready Status */}
                <div className={`text-[10px] p-2 rounded flex items-center justify-between ${
                  learningData.ready_to_learn
                    ? 'bg-amber-50 border border-amber-200 text-amber-800'
                    : 'bg-gray-50 border border-gray-200 text-gray-600'
                }`}>
                  <span>
                    {learningData.ready_to_learn
                      ? `${learningData.unused_samples} new samples ready (threshold: ${learningData.retrain_threshold})`
                      : `${learningData.unused_samples}/${learningData.retrain_threshold} samples until next learning`}
                  </span>
                  <button
                    onClick={async () => {
                      setIsLearning(true);
                      setLearningResult(null);
                      try {
                        const result = await triggerLearningCycle();
                        setLearningResult(
                          result.status === 'deployed'
                            ? `v${result.version} deployed! Accuracy: ${((result.accuracy_after || 0) * 100).toFixed(1)}% (+${((result.improvement_delta || 0) * 100).toFixed(1)}%)`
                            : result.status === 'skipped'
                            ? result.reason || 'Not enough data'
                            : result.status === 'rejected'
                            ? `Rejected: accuracy would decrease`
                            : `Error: ${result.error || 'Unknown'}`
                        );
                        const stats = await getLearningStats().catch(() => null);
                        if (stats) setLearningData(stats);
                      } catch (e: any) {
                        setLearningResult(`Error: ${e.message}`);
                      } finally {
                        setIsLearning(false);
                      }
                    }}
                    disabled={isLearning}
                    className="px-2 py-1 bg-violet-600 text-white rounded text-[9px] font-semibold hover:bg-violet-700 disabled:opacity-50 flex items-center gap-1"
                  >
                    <Brain className="w-3 h-3" />
                    {isLearning ? 'Learning...' : 'Train AI'}
                  </button>
                </div>

                {/* Learning Result */}
                {learningResult && (
                  <div className={`mt-2 text-[10px] p-1.5 rounded ${
                    learningResult.startsWith('v') || learningResult.startsWith('V')
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}>
                    {learningResult}
                  </div>
                )}

                {/* Version History (last 3) */}
                {learningData.version_history && learningData.version_history.length > 0 && (
                  <div className="mt-3">
                    <div className="text-[10px] font-semibold text-gray-700 mb-1">Version History</div>
                    <div className="space-y-1">
                      {learningData.version_history.slice(0, 3).map((v, idx) => (
                        <div key={idx} className={`text-[9px] p-1.5 rounded border flex items-center justify-between ${
                          v.deployed ? 'bg-violet-50 border-violet-200' : 'bg-gray-50 border-gray-200'
                        }`}>
                          <span className="font-mono">v{v.version}</span>
                          <span className="text-gray-500">{v.training_samples_count} samples</span>
                          <span className={v.deployed ? 'text-violet-700 font-semibold' : 'text-gray-400'}>
                            {v.deployed ? '● Active' : '○ Inactive'}
                          </span>
                          <span className={`font-semibold ${
                            (v.improvement_delta || 0) > 0 ? 'text-emerald-600' : 'text-gray-500'
                          }`}>
                            {v.improvement_delta != null
                              ? `${(v.improvement_delta > 0 ? '+' : '')}${(v.improvement_delta * 100).toFixed(1)}%`
                              : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

