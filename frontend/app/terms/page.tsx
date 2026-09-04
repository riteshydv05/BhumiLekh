"use client";

import React from "react";
import Breadcrumb from "@/components/layout/Breadcrumb";
import { FileCheck } from "lucide-react";

export default function TermsPage() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Terms of Service" }]} />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-amber-700" />
            <span>Terms of Service & Usage Conditions</span>
          </h1>
          <p className="text-xs text-gray-600 mt-1">
            Rules governing prototype operation, automated document digitization, and verification responsibility.
          </p>
        </div>

        <div className="gov-card p-6 space-y-4 text-xs text-gray-700 leading-relaxed">
          <section>
            <h2 className="text-sm font-bold text-gray-900 mb-1">1. Prototype Demonstration Notice</h2>
            <p>
              This portal is an AI-assisted digitization and validation system. While deep learning models (PaddleOCR, TrOCR, IsolationForest) extract and validate records with high fidelity, final legal authority resides with authorized revenue department officers who verify and approve digital records.
            </p>
          </section>

          <section>
            <h2 className="text-sm font-bold text-gray-900 mb-1">2. Permissible Use</h2>
            <p>
              Users agree not to upload malicious payloads, unreadable corrupted files, or documents containing unlawful content. All uploads undergo server-side file type and integrity validation before processing.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
