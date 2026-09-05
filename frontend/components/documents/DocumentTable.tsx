"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DocumentItem } from "@/lib/api";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import { useTranslation } from "@/context/AccessibilityContext";
import {
  Eye,
  ShieldCheck,
  FileText,
  UploadCloud,
  Copy,
  Check,
  MapPin,
  Sparkles,
} from "lucide-react";

interface DocumentTableProps {
  documents: DocumentItem[];
  loading?: boolean;
}

export default function DocumentTable({ documents, loading = false }: DocumentTableProps) {
  const { t } = useTranslation();
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded p-12 text-center text-xs text-gray-500">
        <div className="inline-block animate-spin w-6 h-6 border-2 border-amber-600 border-t-transparent rounded-full mb-3" />
        <p className="font-semibold text-gray-700">Connecting to National Land Records Database...</p>
        <p className="text-[11px] text-gray-400 mt-1">Retrieving indexed deeds and validation audits</p>
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
          className="inline-flex items-center gap-1.5 mt-4 px-4 py-2 bg-amber-700 hover:bg-amber-800 text-white rounded text-xs font-semibold shadow-sm transition"
        >
          <UploadCloud className="w-4 h-4" />
          <span>{t("table.uploadFirst")}</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-xs text-left gov-table">
          <thead>
            <tr>
              <th scope="col">Document Record & ULPIN</th>
              <th scope="col">Revenue Type & State</th>
              <th scope="col">Registered On</th>
              <th scope="col">Format & Size</th>
              <th scope="col">OCR Language</th>
              <th scope="col">Audit Status</th>
              <th scope="col" className="text-right">Actions</th>
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

              // Infer document revenue type
              const docType =
                doc.filename.toLowerCase().includes("7_12") || doc.filename.toLowerCase().includes("satbara")
                  ? "7/12 Extract (सातबारा)"
                  : doc.filename.toLowerCase().includes("khasra") || doc.filename.toLowerCase().includes("khatauni")
                  ? "Khasra-Khatauni (खतौनी)"
                  : doc.filename.toLowerCase().includes("patta")
                  ? "Patta/Chitta (பட்டா)"
                  : "Land Revenue Deed";

              return (
                <tr key={doc.id} className="hover:bg-amber-50/40 transition">
                  {/* Filename & ID */}
                  <td className="font-medium text-gray-900">
                    <div className="flex items-start gap-2 max-w-xs sm:max-w-sm">
                      <FileText className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <Link
                          href={`/documents/${doc.id}`}
                          className="font-bold text-gray-900 hover:text-amber-800 hover:underline truncate block"
                          title={doc.filename}
                        >
                          {doc.filename}
                        </Link>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-[10px] text-gray-500 font-mono">
                            ID: {doc.id.substring(0, 12)}...
                          </span>
                          <button
                            type="button"
                            onClick={() => handleCopyId(doc.id)}
                            className="text-gray-400 hover:text-gray-600"
                            title="Copy Document UUID"
                          >
                            {copiedId === doc.id ? (
                              <Check className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Revenue Type & State */}
                  <td className="whitespace-nowrap">
                    <span className="font-bold text-gray-800 text-[11px] block">{docType}</span>
                    <span className="text-[10px] text-gray-500 font-mono">Tehsil Sadar • UP/MH</span>
                  </td>

                  {/* Upload Date */}
                  <td className="text-gray-600 whitespace-nowrap font-mono text-[11px]">
                    {formattedDate}
                  </td>

                  {/* Format & Size */}
                  <td className="text-gray-600 whitespace-nowrap">
                    <span className="uppercase font-mono text-[10px] font-bold bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded border border-slate-300 mr-1">
                      {doc.content_type?.split("/")[1] || "PDF"}
                    </span>
                    <span className="text-gray-500 font-mono text-[11px]">{fileSizeKB}</span>
                  </td>

                  {/* Language */}
                  <td className="whitespace-nowrap">
                    <span className="capitalize font-semibold text-gray-800">
                      {doc.detected_language === "hi"
                        ? "हिन्दी (Hindi)"
                        : doc.detected_language === "mr"
                        ? "मराठी (Marathi)"
                        : doc.detected_language === "en"
                        ? "English"
                        : doc.detected_language || "Indic Multi"}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="whitespace-nowrap">
                    <DocumentStatusBadge status={doc.status} />
                  </td>

                  {/* Actions */}
                  <td className="text-right whitespace-nowrap">
                    <div className="flex items-center justify-end gap-1.5">
                      <Link
                        href={`/documents/${doc.id}`}
                        className="p-1.5 rounded hover:bg-gray-100 text-gray-700 border border-gray-200 inline-flex items-center gap-1 text-[11px] font-semibold"
                        title="View Document Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View</span>
                      </Link>

                      <Link
                        href={`/verify?documentId=${doc.id}`}
                        className="p-1.5 rounded hover:bg-amber-100 bg-amber-50 text-amber-900 border border-amber-300 inline-flex items-center gap-1 text-[11px] font-bold"
                        title="Verify Extracted Records"
                      >
                        <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                        <span>Verify</span>
                      </Link>

                      <Link
                        href="/map"
                        className="p-1.5 rounded hover:bg-purple-100 bg-purple-50 text-purple-900 border border-purple-200 inline-flex items-center gap-1 text-[11px]"
                        title="Locate on Cadastral Map"
                      >
                        <MapPin className="w-3.5 h-3.5 text-purple-700" />
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
