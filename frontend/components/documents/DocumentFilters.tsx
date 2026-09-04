"use client";

import React from "react";
import { Search, Filter } from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";

interface DocumentFiltersProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  statusFilter: string;
  onStatusChange: (val: string) => void;
  languageFilter: string;
  onLanguageChange: (val: string) => void;
}

export default function DocumentFilters({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  languageFilter,
  onLanguageChange,
}: DocumentFiltersProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-white border border-gray-200 rounded p-4 shadow-sm mb-4">
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
        {/* Search Input */}
        <div className="sm:col-span-6 relative">
          <label htmlFor="search-input" className="sr-only">
            {t("docs.search")}
          </label>
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            id="search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={t("docs.search")}
            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-300 rounded focus:outline-none focus:border-amber-600"
          />
        </div>

        {/* Status Filter */}
        <div className="sm:col-span-3">
          <label htmlFor="status-select" className="sr-only">
            Filter by processing status
          </label>
          <select
            id="status-select"
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded focus:outline-none focus:border-amber-600 bg-white"
          >
            <option value="ALL">{t("docs.allStatuses")}</option>
            <option value="COMPLETED">{t("dash.completed")}</option>
            <option value="VERIFICATION_REQUIRED">{t("dash.auditRequired")}</option>
            <option value="OCR_PROCESSING">{t("dash.processing")}</option>
            <option value="QUEUED">Queued</option>
            <option value="FAILED">{t("dash.failed")}</option>
          </select>
        </div>

        {/* Language Filter */}
        <div className="sm:col-span-3">
          <label htmlFor="language-select" className="sr-only">
            Filter by detected language
          </label>
          <select
            id="language-select"
            value={languageFilter}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded focus:outline-none focus:border-amber-600 bg-white"
          >
            <option value="ALL">{t("docs.allLanguages")}</option>
            <option value="hi">Hindi (हिन्दी)</option>
            <option value="mr">Marathi (मराठी)</option>
            <option value="en">English</option>
            <option value="gu">Gujarati (ગુજરાતી)</option>
            <option value="bn">Bengali (বাংলা)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
