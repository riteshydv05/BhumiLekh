"use client";

import React from "react";
import Link from "next/link";
import { useAccessibility } from "@/context/AccessibilityContext";
import { Eye, HelpCircle, Languages } from "lucide-react";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी (Hindi)" },
  { code: "mr", label: "मराठी (Marathi)" },
  { code: "gu", label: "ગુજરાતી (Gujarati)" },
  { code: "bn", label: "বাংলা (Bengali)" },
  { code: "pa", label: "ਪੰਜਾਬੀ (Punjabi)" },
  { code: "te", label: "తెలుగు (Telugu)" },
  { code: "ta", label: "தமிழ் (Tamil)" },
  { code: "kn", label: "ಕನ್ನಡ (Kannada)" },
  { code: "ml", label: "മലയാളം (Malayalam)" },
  { code: "or", label: "ଓଡ଼ିଆ (Odia)" },
  { code: "as", label: "অসমীয়া (Assamese)" },
  { code: "ur", label: "اردو (Urdu)" },
];

export default function TopUtilityBar() {
  const {
    highContrast,
    toggleHighContrast,
    increaseTextSize,
    decreaseTextSize,
    resetAccessibility,
    language,
    setLanguage,
    t,
  } = useAccessibility();

  return (
    <div className="w-full bg-slate-900 text-slate-100 text-xs py-1.5 px-4 border-b border-slate-700">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        {/* Left: Government Portal Tagline & Skip to content */}
        <div className="flex items-center gap-4">
          <span className="font-semibold text-gov-yellow">
            {t("gov.name")}
          </span>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:bg-gov-saffron focus:text-white px-2 py-0.5 rounded"
          >
            {t("gov.skipContent")}
          </a>
        </div>

        {/* Right: Accessibility Controls & Language */}
        <div className="flex items-center gap-3">
          {/* Text Size Scaling Controls */}
          <div
            className="flex items-center border border-slate-700 rounded bg-slate-800"
            role="group"
            aria-label="Font Size Adjustments"
          >
            <button
              onClick={decreaseTextSize}
              className="px-2 py-0.5 hover:bg-slate-700 transition font-bold"
              title="Decrease Font Size"
              aria-label="Decrease Font Size (A-)"
            >
              A-
            </button>
            <button
              onClick={resetAccessibility}
              className="px-2 py-0.5 hover:bg-slate-700 transition font-bold border-x border-slate-700"
              title="Standard Font Size"
              aria-label="Standard Font Size (A)"
            >
              A
            </button>
            <button
              onClick={increaseTextSize}
              className="px-2 py-0.5 hover:bg-slate-700 transition font-bold"
              title="Increase Font Size"
              aria-label="Increase Font Size (A+)"
            >
              A+
            </button>
          </div>

          {/* High Contrast Mode Toggle */}
          <button
            onClick={toggleHighContrast}
            className={`flex items-center gap-1 px-2.5 py-0.5 rounded border text-xs font-semibold transition ${
              highContrast
                ? "bg-amber-400 text-black border-amber-300"
                : "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700"
            }`}
            title="Toggle High Contrast Light Mode"
            aria-label={`High Contrast Mode ${highContrast ? "Enabled" : "Disabled"}`}
          >
            <Eye className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{highContrast ? t("gov.highContrastOn") : t("gov.highContrast")}</span>
          </button>

          {/* Language Selector */}
          <div className="flex items-center gap-1.5 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            <Languages className="w-3.5 h-3.5 text-slate-300" aria-hidden="true" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent text-slate-100 text-xs focus:outline-none cursor-pointer"
              aria-label="Select Official Language"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-slate-900 text-white">
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* Help Link */}
          <Link
            href="/help"
            className="flex items-center gap-1 text-slate-300 hover:text-white transition ml-1"
            title="Help & User Manual"
          >
            <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t("gov.help")}</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
