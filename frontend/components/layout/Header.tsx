"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { useTranslation } from "@/context/AccessibilityContext";
import { Server, CheckCircle2 } from "lucide-react";

export default function Header() {
  const { t } = useTranslation();

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-slate-800 transition-colors duration-250">
      <div className="tricolor-bar" />
      <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">

          {/* Brand */}
          <Link href="/" prefetch={true} className="flex items-center gap-4 focus:outline-none group">
            <div className="shrink-0">
              <Image
                src="/bhumilekh-logo.jpg"
                alt="BhumiLekh Logo"
                width={68}
                height={68}
                className="rounded-xl object-contain shadow-sm border border-gray-200 dark:border-slate-700"
                priority
              />
            </div>
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] sm:text-[11px] font-bold tracking-wider uppercase
                  text-amber-800 dark:text-amber-400">
                  भूमि संसाधन विभाग • Department of Land Resources
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold hidden sm:inline
                  bg-amber-100 dark:bg-amber-500/15
                  text-amber-900 dark:text-amber-300
                  border border-amber-300 dark:border-amber-500/30">
                  DILRMP Phase-III
                </span>
              </div>
              <div className="text-xl sm:text-2xl font-black tracking-tight leading-none flex items-center gap-2">
                <span className="text-green-800 dark:text-emerald-400">Bhumi</span>
                <span className="text-amber-700 dark:text-amber-400">Lekh</span>
                <span className="text-base font-semibold text-gray-400 dark:text-slate-600">· भूमिलेख</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] flex-wrap
                text-gray-500 dark:text-slate-500">
                <span>ग्रामीण विकास मंत्रालय, भारत सरकार</span>
                <span className="text-gray-300 dark:text-slate-700">•</span>
                <span className="font-semibold text-amber-800 dark:text-amber-600/80">
                  National Land Information System (NLIS)
                </span>
              </div>
            </div>
          </Link>

          {/* System health */}
          <div className="self-start lg:self-center">
            <div className="rounded-lg p-2.5 text-xs space-y-1.5 border
              bg-gray-50 dark:bg-slate-800
              border-gray-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 font-bold text-[11px]
                  text-gray-700 dark:text-slate-300">
                  <Server className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                  NIC MeghRaj Node:
                  <span className="text-emerald-700 dark:text-emerald-400 font-mono">UP-LKO-01</span>
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded
                  bg-emerald-100 dark:bg-emerald-500/15
                  text-emerald-800 dark:text-emerald-400
                  border border-emerald-300 dark:border-emerald-500/25">
                  <CheckCircle2 className="w-2.5 h-2.5" />ONLINE
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 text-[10px] font-mono border-t pt-1.5
                text-gray-400 dark:text-slate-600 border-gray-200 dark:border-slate-700">
                <span>PostGIS: <strong className="text-gray-600 dark:text-slate-400">SRID 4326</strong></span>
                <span>AI: <strong className="text-gray-600 dark:text-slate-400">PaddleOCR+TrOCR</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
