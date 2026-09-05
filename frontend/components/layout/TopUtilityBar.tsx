"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAccessibility } from "@/context/AccessibilityContext";
import { useAuth } from "@/context/AuthContext";
import {
  Eye,
  HelpCircle,
  Languages,
  Clock,
  PhoneCall,
  UserCheck,
  Building2,
} from "lucide-react";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी (Hindi)" },
];

const JURISDICTIONS = [
  { id: "all", name: "National DILRMP Portal" },
  { id: "up", name: "Uttar Pradesh — Bhulekh" },
  { id: "mh", name: "Maharashtra — Mahabhumi 7/12" },
  { id: "ka", name: "Karnataka — Bhoomi RTC" },
  { id: "tn", name: "Tamil Nadu — Patta/Chitta" },
];

export default function TopUtilityBar() {
  const { user, logout } = useAuth();
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

  const [currentTime, setCurrentTime] = useState<string>("");
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>("up");

  // Keep a running live IST clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const formatted = now.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }) + " | " + now.toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }) + " IST";
      setCurrentTime(formatted);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full bg-slate-950 text-slate-200 text-[11px] py-1 px-3 sm:px-4 border-b border-slate-800">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        {/* Left: Official Republic of India Identity & Live Clock */}
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          <div className="flex items-center gap-1.5 font-semibold text-amber-400">
            <span className="text-xs">🇮🇳</span>
            <span>{t("gov.name")}</span>
          </div>

          <span className="text-slate-700 hidden sm:inline">|</span>

          {/* Live Indian Standard Time */}
          <div className="hidden lg:flex items-center gap-1 text-slate-400 font-mono" title="Indian Standard Time">
            <Clock className="w-3 h-3 text-amber-500" />
            <span>{currentTime || "Loading IST..."}</span>
          </div>

          <span className="text-slate-700 hidden md:inline">|</span>

          {/* Citizen Helpline */}
          <div className="hidden md:flex items-center gap-1 text-slate-300">
            <PhoneCall className="w-3 h-3 text-emerald-400" />
            <span>Kisan Helpline: <strong className="text-white font-mono">1800-180-1551</strong> (Toll-Free)</span>
          </div>

          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:bg-amber-600 focus:text-white px-2 py-0.5 rounded text-xs"
          >
            {t("gov.skipContent")}
          </a>
        </div>

        {/* Right: Jurisdiction, Session, Accessibility & Language */}
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          {/* Jurisdiction Selector */}
          <div className="hidden sm:flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            <Building2 className="w-3 h-3 text-amber-400" />
            <select
              value={selectedJurisdiction}
              onChange={(e) => setSelectedJurisdiction(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] focus:outline-none cursor-pointer"
              aria-label="Select State Land Registry Portal"
            >
              {JURISDICTIONS.map((j) => (
                <option key={j.id} value={j.id} className="bg-slate-900 text-white">
                  {j.name}
                </option>
              ))}
            </select>
          </div>

          {/* Real Authentication Session Pill / Login Button */}
          {user ? (
            <div className="flex items-center gap-2 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
              <UserCheck className="w-3 h-3 text-emerald-400" />
              <span>
                <strong className="text-white">{user.username}</strong>
              </span>
              <span className={`text-[9px] px-1 rounded uppercase font-mono font-bold border ${
                user.role === "ADMIN"
                  ? "bg-purple-950 text-purple-300 border-purple-800"
                  : user.role === "OFFICER"
                  ? "bg-blue-950 text-blue-300 border-blue-800"
                  : "bg-emerald-950 text-emerald-300 border-emerald-800"
              }`}>
                {user.role}
              </span>

              {(user.role === "ADMIN" || user.role === "OFFICER") && (
                <Link
                  href="/admin"
                  className="text-[10px] text-amber-400 hover:text-amber-300 font-bold underline"
                  title="Open Admin Console"
                >
                  Admin Console
                </Link>
              )}

              <button
                type="button"
                onClick={logout}
                className="text-[10px] text-rose-400 hover:text-rose-300 font-semibold ml-1"
                title="Sign out of current account"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1 bg-amber-700 hover:bg-amber-800 text-white px-2.5 py-0.5 rounded font-bold text-[11px] shadow-2xs transition"
              title="Sign in with official credentials"
            >
              <UserCheck className="w-3 h-3" />
              <span>Login</span>
            </Link>
          )}

          {/* Font Scaling Controls */}
          <div
            className="flex items-center border border-slate-800 rounded bg-slate-900"
            role="group"
            aria-label="Font Size Adjustments"
          >
            <button
              onClick={decreaseTextSize}
              className="px-1.5 py-0.5 hover:bg-slate-800 transition font-bold text-slate-300 hover:text-white"
              title="Decrease Font Size"
              aria-label="Decrease Font Size (A-)"
            >
              A-
            </button>
            <button
              onClick={resetAccessibility}
              className="px-1.5 py-0.5 hover:bg-slate-800 transition font-bold text-slate-300 hover:text-white border-x border-slate-800"
              title="Standard Font Size"
              aria-label="Standard Font Size (A)"
            >
              A
            </button>
            <button
              onClick={increaseTextSize}
              className="px-1.5 py-0.5 hover:bg-slate-800 transition font-bold text-slate-300 hover:text-white"
              title="Increase Font Size"
              aria-label="Increase Font Size (A+)"
            >
              A+
            </button>
          </div>

          {/* High Contrast Mode Toggle */}
          <button
            onClick={toggleHighContrast}
            className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-semibold transition ${
              highContrast
                ? "bg-amber-400 text-black border-amber-300"
                : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800 hover:text-white"
            }`}
            title="Toggle High Contrast Light Mode"
            aria-label={`High Contrast Mode ${highContrast ? "Enabled" : "Disabled"}`}
          >
            <Eye className="w-3 h-3" aria-hidden="true" />
            <span className="hidden xs:inline">{highContrast ? t("gov.highContrastOn") : t("gov.highContrast")}</span>
          </button>

          {/* Language Selector */}
          <div className="flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            <Languages className="w-3 h-3 text-amber-400" aria-hidden="true" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] focus:outline-none cursor-pointer"
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
            className="flex items-center gap-1 text-slate-300 hover:text-white transition"
            title="Help & User Manual"
          >
            <HelpCircle className="w-3 h-3 text-slate-400" aria-hidden="true" />
            <span>{t("gov.help")}</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
