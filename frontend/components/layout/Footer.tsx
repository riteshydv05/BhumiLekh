"use client";

import React from "react";
import Link from "next/link";
import { Shield, PhoneCall, Mail, Building, Globe, CheckCircle2 } from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="bg-slate-950 text-slate-300 text-xs border-t-4 border-amber-600 mt-auto">
      {/* Official Saffron-White-Green Tricolor Accent Line */}
      <div className="tricolor-bar" />

      {/* Main Footer Body */}
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Col 1: Portal Authority & Emblem */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border border-amber-500/50 bg-amber-950/40 flex items-center justify-center text-amber-400 font-bold text-base shrink-0">
                🏛️
              </div>
              <div>
                <h2 className="text-sm font-extrabold text-white uppercase tracking-wider">
                  भूमि संसाधन विभाग • Department of Land Resources
                </h2>
                <p className="text-[11px] text-amber-400 font-medium">
                  ग्रामीण विकास मंत्रालय, भारत सरकार • Ministry of Rural Development, Govt. of India
                </p>
              </div>
            </div>

            <p className="text-slate-400 text-xs leading-relaxed max-w-lg">
              BhumiLekh (भूमिलेख) is the National Land Records Modernization, Digitization, and Cadastral Mapping Portal built under the Digital India Land Records Modernization Programme (DILRMP).
            </p>

            <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1 flex-wrap">
              <span className="flex items-center gap-1 text-slate-300">
                <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
                <span>Toll-Free: <strong>1800-180-1551</strong></span>
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1 text-slate-300">
                <Mail className="w-3.5 h-3.5 text-amber-400" />
                <span>support-dilrmp@nic.in</span>
              </span>
            </div>
          </div>

          {/* Col 2: Services & Consoles */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-1.5 flex items-center gap-1.5">
              <span>पोर्टल सेवाएं • Services</span>
            </h3>
            <ul className="space-y-1.5 text-[11px]">
              <li>
                <Link href="/" className="hover:text-amber-400 transition">
                  {t("nav.home")} (मुख्य पृष्ठ)
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-amber-400 transition">
                  {t("nav.dashboard")} (प्रशासनिक डैशबोर्ड)
                </Link>
              </li>
              <li>
                <Link href="/upload" className="hover:text-amber-400 transition">
                  {t("nav.upload")} (अभिलेख डिजिटलीकरण)
                </Link>
              </li>
              <li>
                <Link href="/documents" className="hover:text-amber-400 transition">
                  {t("nav.documents")} (भू-अभिलेख संग्रह)
                </Link>
              </li>
              <li>
                <Link href="/verify" className="hover:text-amber-400 transition">
                  {t("nav.verify")} (सत्यापन एवं ऑडिट)
                </Link>
              </li>
              <li>
                <Link href="/map" className="hover:text-amber-400 transition">
                  {t("nav.map")} (भू-मानचित्र GIS)
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Compliance & External Standards */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-1.5">
              कानूनी एवं नीतियां • Compliance
            </h3>
            <ul className="space-y-1.5 text-[11px]">
              <li>
                <Link href="/help" className="hover:text-amber-400 transition">
                  User Manual & Helpdesk (उपयोगकर्ता पुस्तिका)
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-amber-400 transition">
                  Data Security & Sovereignty Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-amber-400 transition">
                  Terms of Service & Evidence Act S.65B
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-amber-400 transition">
                  Nodal Technical Directorate
                </Link>
              </li>
              <li>
                <a
                  href="https://pgportal.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-400/90 hover:text-amber-300 transition"
                >
                  CPGRAMS Public Grievance Portal ↗
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* State Revenue Portals Strip */}
        <div className="border-t border-slate-800/80 mt-6 pt-4 flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-400">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-slate-300 uppercase">Linked State Portals:</span>
            <span className="hover:text-white cursor-pointer">UP Bhulekh</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer">Maharashtra Mahabhumi (7/12)</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer">Karnataka Bhoomi</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer">Tamil Nadu Patta/Chitta</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer">Gujarat AnyRoR</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="bg-slate-900 border border-slate-700 px-2 py-0.5 rounded text-emerald-400 font-mono">
              NIC Cloud Hosted • 100% Air-Gapped Capable
            </span>
          </div>
        </div>
      </div>

      {/* Bottom Mandatory Government Disclaimer */}
      <div className="bg-black py-3 px-4 border-t border-slate-900 text-[10.5px] text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
          <p>
            © {new Date().getFullYear()} Ministry of Rural Development, Government of India. Developed under National Land Records Modernization Programme.
          </p>
          <p className="text-slate-400">
            Website Content Managed by Department of Land Resources • Compliant with GIGW 3.0 & WCAG 2.1 AA.
          </p>
        </div>
      </div>
    </footer>
  );
}
