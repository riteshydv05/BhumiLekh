"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { Shield, Mail, Globe } from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";

export default function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="bg-slate-950 text-slate-300 text-xs border-t-4 border-amber-600 mt-auto">
      <div className="tricolor-bar" />

      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">

          {/* Col 1: BhumiLekh Brand (PRIMARY) */}
          <div className="space-y-4 md:col-span-2">
            <div className="flex items-center gap-4">
              <Image
                src="/bhumilekh-logo.jpg"
                alt="BhumiLekh"
                width={64}
                height={64}
                className="rounded-xl object-contain border border-slate-700 bg-white shrink-0"
              />
              <div>
                <h2 className="text-2xl font-black tracking-tight leading-none">
                  <span className="text-green-400">Bhumi</span><span className="text-amber-400">Lekh</span>
                </h2>
                <p className="text-[11px] text-amber-400/80 font-semibold italic mt-0.5">
                  Land Records, Digitized
                </p>
                {/* Secondary: govt attribution — less prominent */}
                <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                  Dept. of Land Resources · Ministry of Rural Development<br />
                  Government of India · DILRMP Phase-III
                </p>
              </div>
            </div>

            <p className="text-slate-400 text-[11px] leading-relaxed max-w-lg">
              BhumiLekh is India's AI-powered National Land Records Modernization, Digitization,
              and Cadastral Mapping Portal — serving citizens and government officials across all states.
            </p>

            {/* Contact — removed Kisan Helpline */}
            <div className="flex items-center gap-3 text-[11px] text-slate-400 flex-wrap">
              <span className="flex items-center gap-1 text-slate-300">
                <Mail className="w-3.5 h-3.5 text-amber-400" />
                <span>support-dilrmp@nic.in</span>
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1 text-slate-300">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                <span>dilrmp.gov.in</span>
              </span>
            </div>
          </div>

          {/* Col 2: Portal Services */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-1.5">
              Portal Services
            </h3>
            <ul className="space-y-1.5 text-[11px]">
              {[
                { href: "/", label: "Home Portal" },
                { href: "/dashboard", label: "My Land Records" },
                { href: "/upload", label: "Digitize New Deed" },
                { href: "/documents", label: "Land Records Repository" },
                { href: "/verify", label: "Verify & Audit" },
                { href: "/map", label: "Cadastral GIS Map" },
              ].map(({ href, label }) => (
                <li key={href}>
                  <Link href={href} className="hover:text-amber-400 transition flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-amber-600 shrink-0" />
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Col 3: Legal & Standards */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-1.5">
              Legal & Standards
            </h3>
            <ul className="space-y-1.5 text-[11px]">
              {[
                { href: "/help", label: "User Manual & Helpdesk" },
                { href: "/privacy", label: "Data Security Policy" },
                { href: "/terms", label: "Terms & Evidence Act" },
                { href: "/contact", label: "Nodal Directorate" },
              ].map(({ href, label }) => (
                <li key={href}>
                  <Link href={href} className="hover:text-amber-400 transition flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-slate-600 shrink-0" />
                    {label}
                  </Link>
                </li>
              ))}
              <li>
                <a href="https://pgportal.gov.in" target="_blank" rel="noopener noreferrer"
                  className="text-amber-400/90 hover:text-amber-300 transition flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-amber-700 shrink-0" />
                  CPGRAMS Grievance Portal ↗
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* State Portals */}
        <div className="border-t border-slate-800/80 mt-6 pt-4 flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-400">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-slate-300 uppercase">Linked State Portals:</span>
            {["UP Bhulekh", "Maharashtra Mahabhumi", "Karnataka Bhoomi", "Tamil Nadu Patta/Chitta", "Gujarat AnyRoR"].map((p, i, arr) => (
              <React.Fragment key={p}>
                <span className="hover:text-amber-400 cursor-pointer transition">{p}</span>
                {i < arr.length - 1 && <span className="text-slate-700">•</span>}
              </React.Fragment>
            ))}
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 px-2 py-1 rounded text-emerald-400 font-mono text-[10px]">
            <Shield className="w-3 h-3" />
            NIC Cloud · Air-Gapped Capable
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="bg-black py-3 px-4 border-t border-slate-900 text-[10px] text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
          <p>
            © {new Date().getFullYear()} <span className="text-slate-300 font-semibold">BhumiLekh</span> · National Land Records Modernization Programme
          </p>
          <p>GIGW 3.0 · WCAG 2.1 AA Compliant · Ministry of Rural Development, Govt. of India</p>
        </div>
      </div>
    </footer>
  );
}
