"use client";

import React from "react";
import Breadcrumb from "@/components/layout/Breadcrumb";
import { Shield } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Privacy Policy" }]} />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <Shield className="w-5 h-5 text-amber-700" />
            <span>Privacy Policy & Data Security</span>
          </h1>
          <p className="text-xs text-gray-600 mt-1">
            Data governance, citizen record confidentiality, and document storage principles.
          </p>
        </div>

        <div className="gov-card p-6 space-y-4 text-xs text-gray-700 leading-relaxed">
          <section>
            <h2 className="text-sm font-bold text-gray-900 mb-1">1. Offline-First Processing Principle</h2>
            <p>
              Uploaded land record documents are stored in private MinIO object storage buckets and processed primarily by on-premise/local AI pipelines (PaddleOCR, TrOCR, LayoutLMv3, and IndicNER). Documents are never transmitted to external third parties unless hosted fallbacks are explicitly enabled by an authorized administrator.
            </p>
          </section>

          <section>
            <h2 className="text-sm font-bold text-gray-900 mb-1">2. Confidentiality of Ownership Records</h2>
            <p>
              Extracted landowner identities, khasra survey numbers, and transaction dates are restricted according to national digital governance policies. All API tokens and storage keys are managed through isolated environment configurations.
            </p>
          </section>

          <section>
            <h2 className="text-sm font-bold text-gray-900 mb-1">3. Audit Logging</h2>
            <p>
              Modifications and verification approvals performed by revenue officers are logged with UTC timestamps and user identifiers to ensure immutable accountability for land parcel entries.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
