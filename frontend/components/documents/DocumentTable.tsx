"use client";

import React from "react";
import Link from "next/link";
import { DocumentItem } from "@/lib/api";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import { useTranslation } from "@/context/AccessibilityContext";
import { Eye, ShieldCheck, FileText, UploadCloud } from "lucide-react";

interface DocumentTableProps {
  documents: DocumentItem[];
  loading?: boolean;
}

export default function DocumentTable({ documents, loading = false }: DocumentTableProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded p-12 text-center text-xs text-gray-500">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-amber-600 border-t-transparent rounded-full mb-3" />
        <p>Loading documents from registry...</p>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded p-12 text-center">
        <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
        <h3 className="text-sm font-bold text-gray-800">{t("table.noDocs")}</h3>
        <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
          {t("table.noDocsDesc")}
        </p>
        <Link
          href="/upload"
          className="inline-flex items-center gap-1.5 mt-4 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold shadow-sm transition"
        >
          <UploadCloud className="w-4 h-4" />
          <span>{t("table.uploadFirst")}</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-xs text-left">
          <thead className="bg-gray-50 text-gray-700 uppercase font-semibold text-[11px] tracking-wider">
            <tr>
              <th scope="col" className="px-4 py-3">
                {t("table.filename")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("table.uploadDate")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("table.formatSize")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("table.language")}
              </th>
              <th scope="col" className="px-4 py-3">
                {t("table.status")}
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                {t("table.actions")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {documents.map((doc) => {
              const formattedDate = doc.created_at
                ? new Date(doc.created_at).toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—";

              const fileSizeKB = doc.file_size
                ? (doc.file_size / 1024).toFixed(0) + " KB"
                : "—";

              return (
                <tr key={doc.id} className="hover:bg-amber-50/40 transition">
                  {/* Filename & ID */}
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <div className="flex items-center gap-2 max-w-xs sm:max-w-sm truncate">
                      <FileText className="w-4 h-4 text-amber-700 shrink-0" />
                      <div className="truncate">
                        <Link
                          href={`/documents/${doc.id}`}
                          className="font-semibold text-gray-900 hover:text-amber-800 hover:underline truncate block"
                          title={doc.filename}
                        >
                          {doc.filename}
                        </Link>
                        <span className="text-[10px] text-gray-400 font-mono block truncate">
                          ID: {doc.id}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* Upload Date */}
                  <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                    {formattedDate}
                  </td>

                  {/* Format & Size */}
                  <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                    <span className="uppercase font-mono text-[11px] font-semibold bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200 mr-1.5">
                      {doc.content_type?.split("/")[1] || "FILE"}
                    </span>
                    <span className="text-gray-500">{fileSizeKB}</span>
                  </td>

                  {/* Language */}
                  <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                    <span className="capitalize font-medium">
                      {doc.detected_language === "hi"
                        ? "Hindi (हिन्दी)"
                        : doc.detected_language === "mr"
                        ? "Marathi (मराठी)"
                        : doc.detected_language === "en"
                        ? "English"
                        : doc.detected_language || "Auto-detecting"}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <DocumentStatusBadge status={doc.status} />
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/documents/${doc.id}`}
                        className="p-1.5 rounded hover:bg-gray-100 text-gray-700 border border-gray-200 inline-flex items-center gap-1 text-[11px] font-medium"
                        title="View Document Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>{t("table.view")}</span>
                      </Link>

                      <Link
                        href={`/verify?documentId=${doc.id}`}
                        className="p-1.5 rounded hover:bg-amber-100 bg-amber-50 text-amber-900 border border-amber-300 inline-flex items-center gap-1 text-[11px] font-semibold"
                        title="Verify Extracted Records"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                        <span>{t("table.verify")}</span>
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
