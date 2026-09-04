"use client";

import React from "react";
import Breadcrumb from "@/components/layout/Breadcrumb";
import { HelpCircle, FileText, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

export default function HelpPage() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Help & User Manual" }]} />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-amber-700" />
            <span>Help Desk & Operating Manual</span>
          </h1>
          <p className="text-xs text-gray-600 mt-1">
            Guidance for citizens and land revenue officers on operating the digitization and validation portal.
          </p>
        </div>

        <div className="space-y-6 text-xs text-gray-700">
          {/* FAQ 1 */}
          <div className="gov-card p-5 space-y-2">
            <h2 className="text-sm font-bold text-gray-900">
              1. What types of land records are supported?
            </h2>
            <p className="leading-relaxed">
              The portal accepts <strong>7/12 extracts (Saat Bara)</strong>, <strong>Khasra</strong>, <strong>Khatauni</strong>, <strong>ROR (Record of Rights)</strong>, and <strong>Mutation Notices (Ferfar/Dakhil Kharij)</strong> in PDF, PNG, JPEG, and TIFF formats up to 50 MB.
            </p>
          </div>

          {/* FAQ 2 */}
          <div className="gov-card p-5 space-y-2">
            <h2 className="text-sm font-bold text-gray-900">
              2. How does Multilingual OCR and Transliteration work?
            </h2>
            <p className="leading-relaxed">
              The platform automatically detects Indic scripts (Hindi, Marathi, Gujarati, etc.) using lightweight language models. Printed text is transcribed via PaddleOCR, and Indic numerals (०-९) are normalized to ASCII digits. Legal names and parcel identifiers are preserved strictly in raw form, while phonetic Roman transliterations are provided alongside.
            </p>
          </div>

          {/* FAQ 3 */}
          <div className="gov-card p-5 space-y-2">
            <h2 className="text-sm font-bold text-gray-900">
              3. What does "Verification Required" mean?
            </h2>
            <p className="leading-relaxed">
              When an extracted field has low confidence (&lt; 0.60) or the machine-learning IsolationForest model flags an anomaly (such as mismatched area sums or suspicious mutation frequencies), the document status is set to <code>VERIFICATION_REQUIRED</code>. A revenue officer must inspect the record in the Verification console to audit and approve the entry.
            </p>
          </div>

          {/* FAQ 4 */}
          <div className="gov-card p-5 space-y-2">
            <h2 className="text-sm font-bold text-gray-900">
              4. Accessibility Features
            </h2>
            <p className="leading-relaxed">
              Use the top utility bar to toggle <strong>High Contrast Mode</strong> (for enhanced text definition and borders) or use the <strong>A- / A / A+</strong> buttons to resize font scales across the application.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
