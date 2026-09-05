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
  Download,
  Printer,
  Filter,
  Shield,
  Activity,
  Layers,
  Search,
  Building,
} from "lucide-react";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [districtFilter, setDistrictFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

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

  // Filtered documents list
  const filteredDocs = documents.filter((doc) => {
    if (statusFilter === "COMPLETED" && doc.status !== "COMPLETED") return false;
    if (statusFilter === "VERIFICATION_REQUIRED" && doc.status !== "VERIFICATION_REQUIRED") return false;
    if (statusFilter === "PROCESSING" && (doc.status === "COMPLETED" || doc.status === "VERIFICATION_REQUIRED" || doc.status === "FAILED")) return false;
    if (statusFilter === "FAILED" && doc.status !== "FAILED") return false;

    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      if (!doc.filename.toLowerCase().includes(q) && !doc.id.toLowerCase().includes(q)) {
        return false;
      }
    }
    return true;
  });

  const recentDocs = [...filteredDocs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleExportCSV = () => {
    const headers = ["Document ID", "Filename", "Status", "Language", "Created At", "File Size (Bytes)"];
    const rows = filteredDocs.map((d) => [
      d.id,
      `"${d.filename.replace(/"/g, '""')}"`,
      d.status,
      d.detected_language || "auto",
      d.created_at,
      d.file_size || 0,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `land_records_registry_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div>
      <Breadcrumb items={[{ label: t("nav.dashboard") }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-gray-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-amber-900 bg-amber-100 border border-amber-300 px-2 py-0.5 rounded uppercase font-mono">
                District Nodal Console • Sadar
              </span>
              <span className="text-xs text-gray-400">•</span>
              <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Registry Sync Active
              </span>
            </div>
            <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight mt-1">
              {t("dash.title")}
            </h1>
            <p className="text-xs text-gray-600">
              National Land Record Modernization Monitoring & Operational Audit Station
            </p>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleExportCSV}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded text-xs font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1.5 transition shadow-xs"
              title="Export filtered records to CSV"
            >
              <Download className="w-3.5 h-3.5 text-gray-600" />
              <span>Export CSV</span>
            </button>

            <button
              onClick={handlePrint}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded text-xs font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1.5 transition shadow-xs"
              title="Print Daily Registry Audit Report"
            >
              <Printer className="w-3.5 h-3.5 text-gray-600" />
              <span>Print Report</span>
            </button>

            <button
              onClick={fetchDocs}
              disabled={loading}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded text-xs font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1.5 transition shadow-xs"
              title={t("dash.refresh")}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
              <span>Refresh</span>
            </button>

            <Link
              href="/upload"
              className="px-4 py-1.5 bg-amber-700 hover:bg-amber-800 text-white rounded text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm transition"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Digitize Deed</span>
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

        {/* Operational Statistics Cards Grid */}
        <section aria-label="System Metrics Summary" className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* Total Documents */}
          <div className="gov-card p-3.5 border-l-4 border-l-blue-600">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-gray-500">{t("dash.totalRecords")}</span>
              <FileText className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-2xl font-black text-gray-900 mt-1.5 font-mono">{totalCount}</p>
            <p className="text-[10px] text-gray-500 mt-0.5">Ingested in Land Vault</p>
          </div>

          {/* Processing */}
          <div className="gov-card p-3.5 border-l-4 border-l-blue-400">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-gray-500">{t("dash.processing")}</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-black text-gray-900 mt-1.5 font-mono">{processingCount}</p>
            <p className="text-[10px] text-gray-500 mt-0.5">Active Celery Workers</p>
          </div>

          {/* Completed */}
          <div className="gov-card p-3.5 border-l-4 border-l-emerald-600">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-gray-500">{t("dash.completed")}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-2xl font-black text-gray-900 mt-1.5 font-mono">{completedCount}</p>
            <p className="text-[10px] text-gray-500 mt-0.5">Digitized & Confirmed</p>
          </div>

          {/* Needs Verification */}
          <div className="gov-card p-3.5 border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-gray-500">{t("dash.auditRequired")}</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-2xl font-black text-gray-900 mt-1.5 font-mono">{verificationCount}</p>
            <p className="text-[10px] text-amber-700 font-semibold mt-0.5">Flagged for Tehsildar</p>
          </div>

          {/* Failed */}
          <div className="gov-card p-3.5 border-l-4 border-l-rose-600 col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase text-gray-500">{t("dash.failed")}</span>
              <AlertCircle className="w-4 h-4 text-rose-600" />
            </div>
            <p className="text-2xl font-black text-gray-900 mt-1.5 font-mono">{failedCount}</p>
            <p className="text-[10px] text-gray-500 mt-0.5">Corrupted / Damaged Scans</p>
          </div>
        </section>

        {/* Filter Toolbar & Status Tabs */}
        <div className="gov-card p-3 bg-slate-50 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            {/* Status Filter Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto text-xs font-semibold">
              <button
                onClick={() => setStatusFilter("ALL")}
                className={`px-3 py-1.5 rounded transition ${
                  statusFilter === "ALL"
                    ? "bg-amber-700 text-white font-bold"
                    : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-100"
                }`}
              >
                All Records ({totalCount})
              </button>
              <button
                onClick={() => setStatusFilter("VERIFICATION_REQUIRED")}
                className={`px-3 py-1.5 rounded transition ${
                  statusFilter === "VERIFICATION_REQUIRED"
                    ? "bg-amber-700 text-white font-bold"
                    : "bg-white text-amber-800 border border-amber-300 hover:bg-amber-50"
                }`}
              >
                ⚠️ Audit Required ({verificationCount})
              </button>
              <button
                onClick={() => setStatusFilter("COMPLETED")}
                className={`px-3 py-1.5 rounded transition ${
                  statusFilter === "COMPLETED"
                    ? "bg-amber-700 text-white font-bold"
                    : "bg-white text-emerald-800 border border-emerald-300 hover:bg-emerald-50"
                }`}
              >
                ✓ Digitized ({completedCount})
              </button>
              <button
                onClick={() => setStatusFilter("PROCESSING")}
                className={`px-3 py-1.5 rounded transition ${
                  statusFilter === "PROCESSING"
                    ? "bg-amber-700 text-white font-bold"
                    : "bg-white text-blue-800 border border-blue-300 hover:bg-blue-50"
                }`}
              >
                ⚙️ In Pipeline ({processingCount})
              </button>
            </div>

            {/* Search within filtered results */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Filter by deed name / UUID..."
                  className="pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-300 rounded focus:ring-1 focus:ring-amber-500 w-48 sm:w-60 font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area: Document Table + Live Operational Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Table (3 cols) */}
          <section aria-labelledby="recent-docs-heading" className="lg:col-span-3 space-y-2">
            <div className="flex items-center justify-between">
              <h2 id="recent-docs-heading" className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                Registry Records ({recentDocs.length} Displayed)
              </h2>

              <Link
                href="/documents"
                className="text-xs font-semibold text-amber-800 hover:underline"
              >
                Open Full Document Archive →
              </Link>
            </div>

            <DocumentTable documents={recentDocs} loading={loading} />
          </section>

          {/* Operational Log & Compliance Feed (1 col) */}
          <aside className="space-y-4">
            {/* System Audit Feed */}
            <div className="gov-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-gray-200 pb-2">
                <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wide flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-amber-700" />
                  <span>Audit Stream (धारा 34)</span>
                </h3>
                <span className="text-[9px] bg-emerald-100 text-emerald-800 font-bold px-1.5 rounded">LIVE</span>
              </div>

              <div className="space-y-2.5 text-[11px]">
                <div className="border-l-2 border-emerald-500 pl-2 space-y-0.5">
                  <p className="font-semibold text-gray-900">Mutation Verified: Khasra 123/4</p>
                  <p className="text-gray-500 font-mono text-[10px]">Chandpur • By RO-4092</p>
                  <span className="text-[9px] text-gray-400">12 mins ago</span>
                </div>

                <div className="border-l-2 border-amber-500 pl-2 space-y-0.5">
                  <p className="font-semibold text-amber-900">Area Mismatch Flagged</p>
                  <p className="text-gray-500 font-mono text-[10px]">Barabanki • 1.2 vs 1.4 Acres</p>
                  <span className="text-[9px] text-gray-400">45 mins ago</span>
                </div>

                <div className="border-l-2 border-blue-500 pl-2 space-y-0.5">
                  <p className="font-semibold text-gray-900">PostGIS Geometry Re-indexed</p>
                  <p className="text-gray-500 font-mono text-[10px]">SRID 4326 Polygon Sync</p>
                  <span className="text-[9px] text-gray-400">1 hour ago</span>
                </div>

                <div className="border-l-2 border-emerald-500 pl-2 space-y-0.5">
                  <p className="font-semibold text-gray-900">Active Learning Snapshot v1.4</p>
                  <p className="text-gray-500 font-mono text-[10px]">+1.2% Devanagari OCR Delta</p>
                  <span className="text-[9px] text-gray-400">3 hours ago</span>
                </div>
              </div>
            </div>

            {/* Quick Links / Department Guidelines */}
            <div className="gov-card p-4 bg-amber-50/50 border-amber-200 space-y-2">
              <h3 className="text-xs font-bold text-amber-950 uppercase tracking-wide flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-amber-800" />
                <span>Legal Compliance Notes</span>
              </h3>
              <p className="text-[11px] text-gray-600 leading-normal">
                All digitized deeds are timestamped and cryptographically hashed with SHA-256 for admissibility under Section 65B of the Indian Evidence Act.
              </p>
              <div className="pt-2 border-t border-amber-200/60">
                <Link
                  href="/help"
                  className="text-xs font-bold text-amber-800 hover:underline flex items-center gap-1"
                >
                  <span>Read Revenue Rulebook</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
