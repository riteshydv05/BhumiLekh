"use client";

import React from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileCheck,
  Loader2,
} from "lucide-react";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export default function DocumentStatusBadge({ status, className = "" }: StatusBadgeProps) {
  const normStatus = (status || "").toUpperCase();

  switch (normStatus) {
    case "COMPLETED":
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 ${className}`}
          title="Status: Completed"
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" aria-hidden="true" />
          <span>Completed</span>
        </span>
      );

    case "VERIFICATION_REQUIRED":
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300 ${className}`}
          title="Status: Verification Required"
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
          <span>Needs Verification</span>
        </span>
      );

    case "FAILED":
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-300 ${className}`}
          title="Status: Failed"
        >
          <AlertCircle className="w-3.5 h-3.5 text-rose-700" aria-hidden="true" />
          <span>Failed</span>
        </span>
      );

    case "OCR_PROCESSING":
    case "LAYOUT_ANALYSIS":
    case "EXTRACTION":
    case "VALIDATING":
    case "PREPROCESSING":
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300 ${className}`}
          title={`Status: ${normStatus.replace("_", " ")}`}
        >
          <Loader2 className="w-3.5 h-3.5 text-blue-700 animate-spin" aria-hidden="true" />
          <span>{normStatus.replace("_", " ")}</span>
        </span>
      );

    case "QUEUED":
    case "UPLOADED":
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-800 border border-gray-300 ${className}`}
          title={`Status: ${normStatus || "Pending"}`}
        >
          <Clock className="w-3.5 h-3.5 text-gray-600" aria-hidden="true" />
          <span>{normStatus || "Queued"}</span>
        </span>
      );
  }
}
