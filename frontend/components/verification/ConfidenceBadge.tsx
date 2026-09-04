"use client";

import React from "react";

interface ConfidenceBadgeProps {
  score?: number | null;
  className?: string;
}

export default function ConfidenceBadge({ score, className = "" }: ConfidenceBadgeProps) {
  if (score === undefined || score === null) {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 text-gray-600 border border-gray-200 ${className}`}>
        N/A
      </span>
    );
  }

  const num = Number(score);
  let level = "LOW";
  let colorClass = "bg-rose-100 text-rose-800 border-rose-300";

  if (num >= 0.80) {
    level = "HIGH";
    colorClass = "bg-emerald-100 text-emerald-800 border-emerald-300";
  } else if (num >= 0.60) {
    level = "MEDIUM";
    colorClass = "bg-amber-100 text-amber-900 border-amber-300";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold border ${colorClass} ${className}`}
      title={`Confidence: ${level} (${(num * 100).toFixed(1)}%)`}
    >
      <span>{level}</span>
      <span className="font-mono font-normal">{(num).toFixed(2)}</span>
    </span>
  );
}
