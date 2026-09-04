"use client";

import React from "react";
import Link from "next/link";
import { Shield } from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="bg-slate-900 text-slate-300 text-xs border-t-4 border-amber-600 mt-auto">
      {/* Top Footer Section */}
      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Col 1: Portal Overview */}
          <div className="space-y-2 md:col-span-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-amber-500" aria-hidden="true" />
              {t("header.title")}
            </h2>
            <p className="text-slate-400 text-xs leading-relaxed max-w-lg">
              {t("footer.desc")}
            </p>
            <p className="text-[11px] text-amber-400 font-medium">
              {t("footer.tagline")}
            </p>
          </div>

          {/* Col 2: Quick Links */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-700 pb-1">
              {t("footer.services")}
            </h3>
            <ul className="space-y-1.5">
              <li>
                <Link href="/" className="hover:text-amber-400 transition">
                  {t("nav.home")}
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-amber-400 transition">
                  {t("nav.dashboard")}
                </Link>
              </li>
              <li>
                <Link href="/upload" className="hover:text-amber-400 transition">
                  {t("nav.upload")}
                </Link>
              </li>
              <li>
                <Link href="/documents" className="hover:text-amber-400 transition">
                  {t("nav.documents")}
                </Link>
              </li>
              <li>
                <Link href="/verify" className="hover:text-amber-400 transition">
                  {t("nav.verify")}
                </Link>
              </li>
              <li>
                <Link href="/map" className="hover:text-amber-400 transition">
                  {t("nav.map")}
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Legal & Support */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-700 pb-1">
              {t("footer.legal")}
            </h3>
            <ul className="space-y-1.5">
              <li>
                <Link href="/help" className="hover:text-amber-400 transition">
                  User Manual & Helpdesk
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-amber-400 transition">
                  Privacy Policy & Data Security
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-amber-400 transition">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-amber-400 transition">
                  Contact Nodal Officer
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="bg-slate-950 py-3 px-4 border-t border-slate-800 text-[11px] text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
          <p>
            © {new Date().getFullYear()} {t("footer.copyright")}
          </p>
          <p className="text-slate-500">
            Compliant with GIGW (Guidelines for Indian Government Websites) accessibility standards.
          </p>
        </div>
      </div>
    </footer>
  );
}
