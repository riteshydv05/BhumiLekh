"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { uploadDocument, getDocumentStatus, DocumentItem } from "@/lib/api";
import { useTranslation } from "@/context/AccessibilityContext";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";

const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/tiff",
];

const MAX_FILE_SIZE_MB = 50;

export default function UploadForm() {
  const { t } = useTranslation();
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentItem | null>(null);
  const [processingStatus, setProcessingStatus] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate selected file
  const validateAndSetFile = (file: File) => {
    setErrorMsg(null);
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      setErrorMsg("Unsupported format. Please upload PDF, JPEG, PNG, or TIFF.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File size exceeds maximum limit of ${MAX_FILE_SIZE_MB}MB.`);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setErrorMsg(null);

    try {
      const doc = await uploadDocument(selectedFile);
      setUploadedDoc(doc);
      setProcessingStatus(doc.status || "QUEUED");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload document to processing queue.");
    } finally {
      setUploading(false);
    }
  };

  // Poll processing status periodically after upload until terminal state
  useEffect(() => {
    if (!uploadedDoc?.id) return;
    const terminalStates = ["COMPLETED", "VERIFICATION_REQUIRED", "FAILED"];
    if (terminalStates.includes(processingStatus || "")) return;

    const interval = setInterval(async () => {
      try {
        const stat = await getDocumentStatus(uploadedDoc.id);
        setProcessingStatus(stat.status);
      } catch (err) {
        console.error("Status poll error:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [uploadedDoc?.id, processingStatus]);

  const handleResetForm = () => {
    setSelectedFile(null);
    setUploadedDoc(null);
    setProcessingStatus(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="bg-white border border-gray-200 rounded p-6 shadow-sm">
      {errorMsg && (
        <div
          role="alert"
          className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-900 rounded text-xs flex items-center gap-2"
        >
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {!uploadedDoc ? (
        <form onSubmit={handleUploadSubmit} className="space-y-5">
          {/* Dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded p-8 text-center cursor-pointer transition ${
              dragActive
                ? "border-amber-600 bg-amber-50/50"
                : "border-gray-300 hover:border-amber-600 bg-gray-50/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleChange}
              accept=".pdf,.jpg,.jpeg,.png,.tiff"
              className="hidden"
              aria-label="Upload land record document file"
            />

            <UploadCloud className="w-12 h-12 mx-auto text-amber-700 mb-2" aria-hidden="true" />

            <p className="text-sm font-semibold text-gray-900">
              {t("upload.dropzone")}{" "}
              <span className="text-amber-700 underline">{t("upload.browse")}</span>
            </p>

            <p className="text-xs text-gray-500 mt-1.5">
              {t("upload.formats")}
            </p>
          </div>

          {/* Selected File Details */}
          {selectedFile && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-gray-900 truncate">
                <FileText className="w-4 h-4 text-amber-700 shrink-0" />
                <span className="font-semibold truncate">{selectedFile.name}</span>
                <span className="text-gray-500 shrink-0">
                  ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                </span>
              </div>
              <button
                type="button"
                onClick={handleResetForm}
                className="text-xs text-rose-700 hover:underline font-semibold"
              >
                Change File
              </button>
            </div>
          )}

          {/* Guidelines Notice */}
          <div className="p-3 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 space-y-1">
            <p className="font-semibold text-gray-900">{t("upload.guidelinesTitle")}</p>
            <ul className="list-disc pl-4 space-y-0.5 text-gray-600">
              <li>{t("upload.guide1")}</li>
              <li>{t("upload.guide2")}</li>
              <li>{t("upload.guide3")}</li>
            </ul>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className={`px-5 py-2.5 rounded text-xs font-semibold uppercase tracking-wider text-white transition flex items-center gap-2 ${
                !selectedFile || uploading
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-amber-600 hover:bg-amber-700 active:bg-amber-800 shadow-sm"
              }`}
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t("upload.uploadingBtn")}</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  <span>{t("upload.submitBtn")}</span>
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        /* Post-Upload State with Live Status Progress */
        <div className="space-y-6">
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-emerald-950">
                {t("upload.successTitle")}
              </h3>
              <p className="text-xs text-emerald-800 mt-0.5">
                File <span className="font-semibold">{uploadedDoc.filename}</span> has been saved to
                MinIO storage and queued for AI pipeline processing.
              </p>
            </div>
          </div>

          {/* Live Pipeline Status Box */}
          <div className="border border-gray-200 rounded p-4 bg-gray-50">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-700">
                {t("table.status")}
              </span>
              <DocumentStatusBadge status={processingStatus || "QUEUED"} />
            </div>

            {/* Visual Step Indicator */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              {[
                { name: "PREPROCESSING", label: "1. Download & Prep" },
                { name: "OCR_PROCESSING", label: "2. PaddleOCR / TrOCR" },
                { name: "EXTRACTION", label: "3. Entity Extraction" },
                { name: "VALIDATING", label: "4. Anomaly Validation" },
              ].map((step, idx) => {
                const isCurrent = (processingStatus || "").includes(step.name);
                const isDone =
                  processingStatus === "COMPLETED" ||
                  processingStatus === "VERIFICATION_REQUIRED";

                return (
                  <div
                    key={idx}
                    className={`p-2.5 rounded border text-center transition ${
                      isCurrent
                        ? "bg-amber-100 border-amber-400 font-bold text-amber-900"
                        : isDone
                        ? "bg-emerald-50 border-emerald-300 text-emerald-900"
                        : "bg-white border-gray-200 text-gray-500"
                    }`}
                  >
                    <p className="font-semibold">{step.label}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Links */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <button
              onClick={handleResetForm}
              className="px-4 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-100 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{t("upload.another")}</span>
            </button>

            <div className="flex items-center gap-3">
              <Link
                href="/documents"
                className="px-4 py-2 text-xs font-semibold text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-100"
              >
                {t("upload.goDocs")}
              </Link>
              <Link
                href={`/documents/${uploadedDoc.id}`}
                className="px-4 py-2 text-xs font-semibold text-white bg-amber-600 rounded hover:bg-amber-700 flex items-center gap-1.5 shadow-sm"
              >
                <span>{t("upload.viewDetails")}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
