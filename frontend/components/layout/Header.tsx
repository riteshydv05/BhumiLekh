"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { useTranslation } from "@/context/AccessibilityContext";
import { Server, CheckCircle2 } from "lucide-react";

export default function Header() {
  const { t } = useTranslation();

  return (
    <header className="bg-white border-b border-gray-200">
      {/* Official Tricolor Accent */}
      <div className="tricolor-bar" />

      <div className="max-w-7xl mx-auto px-4 py-3 sm:py-3 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">

          {/* Logo + Brand */}
          <Link href="/" className="flex items-center gap-4 group focus:outline-none">
            {/* BhumiLekh Logo */}
            <div className="shrink-0 relative">
              <Image
                src="/bhumilekh-logo.jpg"
                alt="BhumiLekh Logo"
                width={72}
                height={72}
                className="rounded-xl object-contain shadow-sm border border-gray-100"
                priority
              />
            </div>

            {/* Title stack */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] sm:text-[11px] font-bold tracking-wider text-amber-900 uppercase">
                  भूमि संसाधन विभाग • Department of Land Resources
                </span>
                <span className="text-[10px] bg-amber-100 text-amber-900 border border-amber-300 font-semibold px-1.5 py-0.5 rounded hidden sm:inline">
                  DILRMP Phase-III
                </span>
              </div>

              <h1 className="text-xl sm:text-2xl font-black text-gray-950 tracking-tight leading-none flex items-center gap-2">
                <span className="text-green-800">Bhumi</span><span className="text-amber-700">Lekh</span>
                <span className="text-base font-semibold text-gray-500">· भूमिलेख</span>
              </h1>

              <div className="flex items-center gap-2 text-[11px] text-gray-500 font-medium flex-wrap">
                <span>ग्रामीण विकास मंत्रालय, भारत सरकार</span>
                <span className="text-gray-300">•</span>
                <span className="text-amber-800 font-semibold">National Land Information System (NLIS)</span>
              </div>
            </div>
          </Link>

          {/* Right Side: System Health */}
          <div className="flex items-center gap-3 self-start lg:self-center">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs space-y-1">
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
                <span>PostGIS: <strong className="text-slate-700">SRID 4326</strong></span>
                <span>AI: <strong className="text-slate-700">PaddleOCR+TrOCR</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
