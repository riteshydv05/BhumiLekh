"use client";

import React from "react";
import Link from "next/link";
import { useTranslation } from "@/context/AccessibilityContext";
import { Shield, Server, CheckCircle2, Globe2 } from "lucide-react";

export default function Header() {
  const { t } = useTranslation();

  return (
    <header className="bg-white border-b border-gray-200">
      {/* Official Government Tricolor Top Bar Accent */}
      <div className="tricolor-bar" />

      <div className="max-w-7xl mx-auto px-4 py-3 sm:py-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Official Emblem + Department Branding */}
          <Link href="/" className="flex items-center gap-3 sm:gap-4 group focus:outline-none">
            {/* National Emblem Representation with Lion Capital & Satyameva Jayate */}
            <div
              className="w-14 h-14 sm:w-16 sm:h-16 shrink-0 rounded-full border-2 border-amber-700/40 bg-gradient-to-b from-amber-50 to-white flex flex-col items-center justify-center shadow-sm p-1 text-center"
              aria-label="National Emblem of India"
            >
              <svg
                viewBox="0 0 100 100"
                width="38"
                height="38"
                className="w-9 h-9 sm:w-10 sm:h-10 text-amber-800"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
              >
                {/* Ashoka Chakra Motif */}
                <circle cx="50" cy="46" r="38" stroke="#92400E" strokeWidth="2.8" />
                <circle cx="50" cy="46" r="12" fill="#92400E" fillOpacity="0.15" stroke="#92400E" strokeWidth="2" />
                <circle cx="50" cy="46" r="3.5" fill="#92400E" />
                {[...Array(24)].map((_, i) => {
                  const angle = (i * 360) / 24;
                  return (
                    <line
                      key={i}
                      x1="50"
                      y1="46"
                      x2="50"
                      y2="9"
                      stroke="#92400E"
                      strokeWidth="1.5"
                      transform={`rotate(${angle} 50 46)`}
                    />
                  );
                })}
              </svg>
              <span className="text-[7.5px] font-bold tracking-tight text-amber-950 uppercase leading-none mt-0.5">
                सत्यमेव जयते
              </span>
            </div>

            {/* Department Titles Hierarchy */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10.5px] sm:text-xs font-bold tracking-wider text-amber-900 uppercase">
                  भूमि संसाधन विभाग • Department of Land Resources
                </span>
                <span className="text-[10px] bg-amber-100 text-amber-900 border border-amber-300 font-semibold px-1.5 py-0.2 rounded hidden sm:inline">
                  DILRMP Phase-III
                </span>
              </div>

              <h1 className="text-base sm:text-xl font-extrabold text-gray-950 tracking-tight leading-snug">
                {t("header.title")}
              </h1>

              <div className="flex items-center gap-2 text-[11px] text-gray-600 font-medium flex-wrap">
                <span>ग्रामीण विकास मंत्रालय, भारत सरकार</span>
                <span className="text-gray-300">•</span>
                <span className="text-amber-800 font-semibold">National Land Information System (NLIS)</span>
              </div>
            </div>
          </Link>

          {/* Right Side: Operational Server Health & Regional Node */}
          <div className="flex items-center gap-3 self-start lg:self-center">
            <div className="bg-slate-50 border border-slate-200 rounded p-2 text-xs space-y-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 font-bold text-slate-800 text-[11px]">
                  <Server className="w-3 h-3 text-amber-600" />
                  <span>NIC MeghRaj Node:</span>
                  <span className="text-emerald-700 font-mono">UP-LKO-01</span>
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-100 text-emerald-800 border border-emerald-300 px-1.5 py-0.5 rounded font-bold">
                  <CheckCircle2 className="w-2.5 h-2.5" />
                  ONLINE
                </span>
              </div>

              <div className="flex items-center justify-between gap-3 text-[10px] text-slate-500 font-mono border-t border-slate-200 pt-1">
                <span>PostGIS Cadastral: <strong className="text-slate-700">SRID 4326</strong></span>
                <span>AI Pipeline: <strong className="text-slate-700">Paddle+TrOCR</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
