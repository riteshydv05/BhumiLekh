"use client";

import React from "react";
import Breadcrumb from "@/components/layout/Breadcrumb";
import UploadForm from "@/components/upload/UploadForm";
import { useTranslation } from "@/context/AccessibilityContext";
import { UploadCloud, ShieldCheck, FileText, Info } from "lucide-react";

export default function UploadPage() {
  const { t } = useTranslation();

  return (
    <div>
      <Breadcrumb items={[{ label: t("nav.upload") }]} />

      <div className="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Page Header */}
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-amber-700" />
            <span>{t("upload.title")}</span>
          </h1>
          <p className="text-xs text-gray-600 mt-1">
            {t("upload.subtitle")}
          </p>
        </div>

        {/* Upload Form Component */}
        <UploadForm />

        {/* Technical Notice Banner */}
        <div className="p-4 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 space-y-2">
          <div className="flex items-center gap-1.5 font-bold text-gray-900">
            <Info className="w-4 h-4 text-amber-600" />
            <span>AI Digitization Pipeline Specifications</span>
          </div>
          <p className="text-[11px] text-gray-600 leading-relaxed">
            The submitted document is processed by local open-source models: <strong>PaddleOCR</strong> (PP-OCRv6) for printed Devanagari/English text, <strong>TrOCR</strong> for handwritten notations, <strong>IndicNER</strong> for land entity extraction, and <strong>IsolationForest</strong> for fraud & area anomaly detection. High-conf data is immediately validated, while unreadable regions optionally escalate to Gemini VLM.
          </p>
        </div>
      </div>
    </div>
  );
}
