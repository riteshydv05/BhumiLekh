"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { getDocuments, DocumentItem } from "@/lib/api";
import Breadcrumb from "@/components/layout/Breadcrumb";
import DocumentFilters from "@/components/documents/DocumentFilters";
import DocumentTable from "@/components/documents/DocumentTable";
import { useTranslation } from "@/context/AccessibilityContext";
import { UploadCloud, RefreshCw, AlertCircle } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  // Filters state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [languageFilter, setLanguageFilter] = useState("ALL");

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDocuments();
      setDocuments(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load document records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Filter and search
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Search
      const matchesSearch =
        !searchQuery.trim() ||
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.id.toLowerCase().includes(searchQuery.toLowerCase());

      // Status
      const matchesStatus =
        statusFilter === "ALL" ||
        (doc.status || "").toUpperCase() === statusFilter.toUpperCase();

      // Language
      const matchesLanguage =
        languageFilter === "ALL" ||
        (doc.detected_language || "").toLowerCase() === languageFilter.toLowerCase();

      return matchesSearch && matchesStatus && matchesLanguage;
    });
  }, [documents, searchQuery, statusFilter, languageFilter]);

  return (
    <div>
      <Breadcrumb items={[{ label: t("nav.documents") }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-5">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-gray-200 pb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight">
              {t("docs.title")}
            </h1>
            <p className="text-xs text-gray-600 mt-0.5">
              {t("docs.subtitle")}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadDocuments}
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
              <span>{t("nav.upload")}</span>
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

        {/* Filter Controls */}
        <DocumentFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          languageFilter={languageFilter}
          onLanguageChange={setLanguageFilter}
        />

        {/* Results Info */}
        <div className="flex items-center justify-between text-xs text-gray-500 px-1">
          <span>
            {t("docs.showing")} <strong className="text-gray-900">{filteredDocuments.length}</strong> {t("docs.of")}{" "}
            <strong>{documents.length}</strong> {t("docs.records")}
          </span>
          {(searchQuery || statusFilter !== "ALL" || languageFilter !== "ALL") && (
            <button
              onClick={() => {
                setSearchQuery("");
                setStatusFilter("ALL");
                setLanguageFilter("ALL");
              }}
              className="text-amber-700 hover:underline font-semibold"
            >
              {t("docs.clearFilters")}
            </button>
          )}
        </div>

        {/* Documents Table */}
        <DocumentTable documents={filteredDocuments} loading={loading} />
      </div>
    </div>
  );
}
