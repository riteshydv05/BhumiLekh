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
  UserCheck,
  Building2,
} from "lucide-react";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी (Hindi)" },
];

const JURISDICTIONS = [
  { id: "all", name: "National DILRMP Portal" },
  { id: "up",  name: "Uttar Pradesh — Bhulekh" },
  { id: "mh",  name: "Maharashtra — Mahabhumi 7/12" },
  { id: "ka",  name: "Karnataka — Bhoomi RTC" },
  { id: "tn",  name: "Tamil Nadu — Patta/Chitta" },
];

export default function TopUtilityBar() {
  const { user, logout } = useAuth();
  const {
    highContrast, toggleHighContrast,
    increaseTextSize, decreaseTextSize, resetAccessibility,
    language, setLanguage, t,
  } = useAccessibility();

  const [currentTime, setCurrentTime] = useState("");
  const [selectedJurisdiction, setSelectedJurisdiction] = useState("up");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) +
        " | " +
        now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }) +
        " IST"
      );
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  /* shared select class */
  const selectCls = "bg-transparent text-[11px] focus:outline-none cursor-pointer text-gray-600 dark:text-slate-300";

  return (
    <div className="w-full text-[11px] py-1 px-3 sm:px-4 border-b
      bg-gray-100 dark:bg-slate-950
      border-gray-200 dark:border-slate-800
      text-gray-600 dark:text-slate-400
      transition-colors duration-250">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">

        {/* Left: Gov identity + clock */}
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          <div className="flex items-center gap-1.5 font-semibold text-amber-800 dark:text-amber-400">
            <span className="text-xs">🇮🇳</span>
            <span>{t("gov.name") || "Government of India"}</span>
          </div>

          <span className="text-gray-300 dark:text-slate-700 hidden sm:inline">|</span>

          {/* Live IST clock */}
          <div className="hidden lg:flex items-center gap-1 font-mono text-gray-500 dark:text-slate-500" title="Indian Standard Time">
            <Clock className="w-3 h-3 text-amber-600 dark:text-amber-500" />
            <span>{currentTime || "Loading IST…"}</span>
          </div>

          <a href="#main-content" className="sr-only focus:not-sr-only focus:bg-amber-600 focus:text-white px-2 py-0.5 rounded text-xs">
            {t("gov.skipContent") || "Skip to main content"}
          </a>
        </div>

        {/* Right: jurisdiction, session, accessibility, language */}
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">

          {/* Jurisdiction */}
          <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded border
            bg-white dark:bg-slate-900
            border-gray-200 dark:border-slate-800">
            <Building2 className="w-3 h-3 text-amber-600 dark:text-amber-400" />
            <select value={selectedJurisdiction} onChange={e => setSelectedJurisdiction(e.target.value)}
              className={selectCls} aria-label="Select State Land Registry Portal">
              {JURISDICTIONS.map(j => (
                <option key={j.id} value={j.id} className="bg-white dark:bg-slate-900">{j.name}</option>
              ))}
            </select>
          </div>

          {/* Auth session */}
          {user ? (
            <div className="flex items-center gap-2 px-2 py-0.5 rounded border
              bg-white dark:bg-slate-900
              border-gray-200 dark:border-slate-800
              text-gray-600 dark:text-slate-300">
              <UserCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              <strong className="text-gray-800 dark:text-white">{user.username}</strong>
              <span className={`text-[9px] px-1 rounded uppercase font-mono font-bold border ${
                user.role === "ADMIN"
                  ? "bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-800"
                  : user.role === "OFFICER"
                  ? "bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-800"
                  : "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800"
              }`}>{user.role}</span>
              {(user.role === "ADMIN" || user.role === "OFFICER") && (
                <Link href="/admin" className="text-[10px] text-amber-600 dark:text-amber-400 hover:underline font-bold">Admin Console</Link>
              )}
              <button onClick={logout} className="text-[10px] text-rose-500 dark:text-rose-400 hover:underline font-semibold ml-1">
                Logout
              </button>
            </div>
          ) : (
            <Link href="/login"
              className="flex items-center gap-1 px-2.5 py-0.5 rounded font-bold text-[11px] transition
                bg-amber-700 dark:bg-amber-600 hover:bg-amber-800 dark:hover:bg-amber-700 text-white">
              <UserCheck className="w-3 h-3" /><span>Login</span>
            </Link>
          )}

          {/* Font scaling */}
          <div className="flex items-center rounded border
            bg-white dark:bg-slate-900
            border-gray-200 dark:border-slate-800"
            role="group" aria-label="Font Size Adjustments">
            {[
              { label: "A-", action: decreaseTextSize, title: "Decrease Font Size" },
              { label: "A",  action: resetAccessibility, title: "Standard Font Size", extra: "border-x border-gray-200 dark:border-slate-800" },
              { label: "A+", action: increaseTextSize, title: "Increase Font Size" },
            ].map(({ label, action, title, extra }) => (
              <button key={label} onClick={action} title={title}
                className={`px-1.5 py-0.5 font-bold transition
                  text-gray-600 dark:text-slate-400
                  hover:bg-gray-100 dark:hover:bg-slate-800
                  hover:text-gray-900 dark:hover:text-white ${extra ?? ""}`}>
                {label}
              </button>
            ))}
          </div>

          {/* High Contrast */}
          <button onClick={toggleHighContrast}
            className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-semibold transition ${
              highContrast
                ? "bg-amber-500 dark:bg-amber-400 text-white dark:text-gray-900 border-amber-600 dark:border-amber-300"
                : "bg-white dark:bg-slate-900 text-gray-600 dark:text-slate-400 border-gray-200 dark:border-slate-800 hover:bg-gray-100 dark:hover:bg-slate-800"
            }`}
            title="Toggle High Contrast">
            <Eye className="w-3 h-3" />
            <span className="hidden xs:inline">{highContrast ? "High Contrast On" : "High Contrast"}</span>
          </button>

          {/* Language */}
          <div className="flex items-center gap-1 px-2 py-0.5 rounded border
            bg-white dark:bg-slate-900
            border-gray-200 dark:border-slate-800">
            <Languages className="w-3 h-3 text-amber-600 dark:text-amber-400" />
            <select value={language} onChange={e => setLanguage(e.target.value)}
              className={selectCls} aria-label="Select Official Language">
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code} className="bg-white dark:bg-slate-900">{l.label}</option>
              ))}
            </select>
          </div>

          {/* Help */}
          <Link href="/help"
            className="flex items-center gap-1 transition
              text-gray-500 dark:text-slate-500
              hover:text-gray-800 dark:hover:text-white"
            title="Help & User Manual">
            <HelpCircle className="w-3 h-3" />
            <span>{t("gov.help") || "Help"}</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
