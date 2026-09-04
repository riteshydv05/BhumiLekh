"use client";

import React from "react";
import Link from "next/link";
import { useTranslation } from "@/context/AccessibilityContext";

export default function Header() {
  const { t } = useTranslation();

  return (
    <header className="bg-white border-b border-gray-200">
      {/* Official Saffron Accent Line */}
      <div className="h-1 bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600 w-full" />

      <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Emblem + Branding */}
          <Link href="/" className="flex items-center gap-4 group focus:outline-none">
            {/* Clean Official Emblem Placeholder */}
            <div
              className="w-14 h-14 shrink-0 rounded-full border-2 border-amber-600/60 bg-amber-50 flex items-center justify-center shadow-sm"
              aria-hidden="true"
            >
              <svg
                viewBox="0 0 100 100"
                width="40"
                height="40"
                className="w-10 h-10 text-amber-700"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                {/* Clean Ashok Chakra / Emblem stylistic representation */}
                <circle cx="50" cy="50" r="42" stroke="#B45309" strokeWidth="3" />
                <circle cx="50" cy="50" r="14" fill="#B45309" fillOpacity="0.1" stroke="#B45309" strokeWidth="2.5" />
                <circle cx="50" cy="50" r="4" fill="#B45309" />
                {/* 24 spokes */}
                {[...Array(24)].map((_, i) => {
                  const angle = (i * 360) / 24;
                  return (
                    <line
                      key={i}
                      x1="50"
                      y1="50"
                      x2="50"
                      y2="8"
                      stroke="#B45309"
                      strokeWidth="1.8"
                      transform={`rotate(${angle} 50 50)`}
                    />
                  );
                })}
              </svg>
            </div>

            {/* Department & Portal Titles */}
            <div>
              <p className="text-xs font-semibold tracking-wider text-amber-800 uppercase">
                {t("header.dept")}
              </p>
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight">
                {t("header.title")}
              </h1>
              <p className="text-xs text-gray-600 font-medium">
                {t("header.subtitle")}
              </p>
            </div>
          </Link>

          {/* Quick System Badge */}
          <div className="hidden lg:flex flex-col items-end text-xs text-gray-500">
            <div className="flex items-center gap-2 bg-amber-50 text-amber-900 border border-amber-200 px-3 py-1 rounded">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="font-semibold">{t("header.aiStatus")}</span>
              <span className="text-gray-400">|</span>
              <span className="text-gray-600">{t("header.localPipeline")}</span>
            </div>
            <span className="mt-1 text-[11px]">{t("header.operational")}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
