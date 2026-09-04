"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getDocuments, DocumentItem } from "@/lib/api";
import Breadcrumb from "@/components/layout/Breadcrumb";
import DocumentTable from "@/components/documents/DocumentTable";
import { useTranslation } from "@/context/AccessibilityContext";
import {
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  UploadCloud,
  RefreshCw,
} from "lucide-react";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  const fetchDocs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDocuments();
      setDocuments(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  // Compute statistics from actual backend document records
  const totalCount = documents.length;
  const completedCount = documents.filter((d) => d.status === "COMPLETED").length;
  const verificationCount = documents.filter(
    (d) => d.status === "VERIFICATION_REQUIRED"
  ).length;
  const failedCount = documents.filter((d) => d.status === "FAILED").length;
  const processingCount = documents.filter(
    (d) =>
      d.status !== "COMPLETED" &&
      d.status !== "VERIFICATION_REQUIRED" &&
      d.status !== "FAILED"
  ).length;

  const recentDocs = [...documents]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(0, 10);

  return (
    <div>
      <Breadcrumb items={[{ label: t("nav.dashboard") }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-200 pb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight">
              {t("dash.title")}
            </h1>
            <p className="text-xs text-gray-600 mt-0.5">
              {t("dash.subtitle")}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchDocs}
              disabled={loading}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded text-xs font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1.5 transition"
              title={t("dash.refresh")}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>{t("dash.refresh")}</span>
            </button>

            <Link
              href="/upload"
              className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm transition"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>{t("dash.upload")}</span>
            </Link>
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded text-xs flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Statistics Cards Grid */}
        <section aria-label="System Metrics Summary" className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* Total Documents */}
          <div className="gov-card p-4 border-l-4 border-l-blue-600">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-gray-500">{t("dash.totalRecords")}</span>
              <FileText className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 font-mono">{totalCount}</p>
            <p className="text-[11px] text-gray-500 mt-1">Uploaded in system</p>
          </div>

          {/* Processing */}
          <div className="gov-card p-4 border-l-4 border-l-blue-400">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-gray-500">{t("dash.processing")}</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 font-mono">{processingCount}</p>
            <p className="text-[11px] text-gray-500 mt-1">Active AI stages</p>
          </div>

          {/* Completed */}
          <div className="gov-card p-4 border-l-4 border-l-emerald-600">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-gray-500">{t("dash.completed")}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 font-mono">{completedCount}</p>
            <p className="text-[11px] text-gray-500 mt-1">Digitized & Validated</p>
          </div>

          {/* Needs Verification */}
          <div className="gov-card p-4 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-gray-500">{t("dash.auditRequired")}</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 font-mono">{verificationCount}</p>
            <p className="text-[11px] text-gray-500 mt-1">Low-conf / Anomalies</p>
          </div>

          {/* Failed */}
          <div className="gov-card p-4 border-l-4 border-l-rose-600 col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-gray-500">{t("dash.failed")}</span>
              <AlertCircle className="w-4 h-4 text-rose-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 font-mono">{failedCount}</p>
            <p className="text-[11px] text-gray-500 mt-1">Errors encountered</p>
          </div>
        </section>

        {/* Recent Documents Table */}
        <section aria-labelledby="recent-docs-heading" className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 id="recent-docs-heading" className="text-sm font-bold text-gray-900 uppercase tracking-wider">
              {t("dash.recentTitle")} ({recentDocs.length})
            </h2>

            <Link
              href="/documents"
              className="text-xs font-semibold text-amber-700 hover:text-amber-800 underline"
            >
              {t("dash.viewAll")}
            </Link>
          </div>

          <DocumentTable documents={recentDocs} loading={loading} />
        </section>
      </div>
    </div>
  );
}
