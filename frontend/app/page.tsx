"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileText,
  ShieldCheck,
  Map,
  ArrowRight,
  Cpu,
  CheckCircle2,
  Database,
  Layers,
  Sparkles,
} from "lucide-react";
import { getDocuments, DocumentItem } from "@/lib/api";
import { useTranslation } from "@/context/AccessibilityContext";

export default function HomePage() {
  const [docCount, setDocCount] = useState<number | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    getDocuments()
      .then((docs) => setDocCount(docs.length))
      .catch(() => setDocCount(null));
  }, []);

  return (
    <div className="space-y-8 pb-12">
      {/* Official Government Hero Banner */}
      <section className="bg-white border-b border-gray-200 py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-300 text-amber-900 rounded text-xs font-semibold uppercase tracking-wider">
            <span>{t("hero.tagline")}</span>
          </div>

          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-950 tracking-tight leading-tight">
            {t("hero.title")}
          </h1>

          <p className="text-sm sm:text-base text-gray-600 max-w-3xl mx-auto leading-relaxed">
            {t("hero.desc")}
          </p>

          <div className="pt-2 flex flex-wrap justify-center gap-3">
            <Link
              href="/upload"
              className="px-5 py-2.5 bg-amber-600 hover:bg-amber-700 active:bg-amber-800 text-white rounded text-xs font-bold uppercase tracking-wider transition inline-flex items-center gap-2 shadow-sm"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{t("hero.uploadBtn")}</span>
            </Link>

            <Link
              href="/documents"
              className="px-5 py-2.5 bg-white hover:bg-gray-50 text-gray-800 border border-gray-300 rounded text-xs font-bold uppercase tracking-wider transition inline-flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              <span>{t("hero.docsBtn")}</span>
            </Link>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Quick Services Section */}
        <section aria-labelledby="quick-services-heading">
          <div className="border-b border-gray-200 pb-2 mb-5 flex items-center justify-between">
            <h2 id="quick-services-heading" className="text-base font-bold text-gray-900 uppercase tracking-wider">
              {t("services.title")}
            </h2>
            <span className="text-xs text-gray-500 font-medium">{t("services.subtitle")}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Service 1: Upload */}
            <Link
              href="/upload"
              className="gov-card p-5 hover:border-amber-500 hover:shadow-gov transition group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded bg-amber-100 text-amber-800 flex items-center justify-center mb-3">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 group-hover:text-amber-700">
                  {t("services.upload.title")}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  {t("services.upload.desc")}
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-gray-100 flex items-center text-xs font-semibold text-amber-700">
                <span>{t("services.upload.action")}</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1 transition group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Service 2: My Documents */}
            <Link
              href="/documents"
              className="gov-card p-5 hover:border-amber-500 hover:shadow-gov transition group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded bg-blue-100 text-blue-800 flex items-center justify-center mb-3">
                  <FileText className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 group-hover:text-blue-700">
                  {t("services.docs.title")}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  {t("services.docs.desc")}
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-gray-100 flex items-center text-xs font-semibold text-blue-700">
                <span>{t("services.docs.action")}</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1 transition group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Service 3: Verify Records */}
            <Link
              href="/verify"
              className="gov-card p-5 hover:border-amber-500 hover:shadow-gov transition group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded bg-emerald-100 text-emerald-800 flex items-center justify-center mb-3">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 group-hover:text-emerald-700">
                  {t("services.verify.title")}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  {t("services.verify.desc")}
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-gray-100 flex items-center text-xs font-semibold text-emerald-700">
                <span>{t("services.verify.action")}</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1 transition group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Service 4: View Land Map */}
            <Link
              href="/map"
              className="gov-card p-5 hover:border-amber-500 hover:shadow-gov transition group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded bg-purple-100 text-purple-800 flex items-center justify-center mb-3">
                  <Map className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 group-hover:text-purple-700">
                  {t("services.map.title")}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  {t("services.map.desc")}
                </p>
              </div>
              <div className="mt-4 pt-2 border-t border-gray-100 flex items-center text-xs font-semibold text-purple-700">
                <span>{t("services.map.action")}</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1 transition group-hover:translate-x-1" />
              </div>
            </Link>
          </div>
        </section>

        {/* How It Works (5-stage Flow) */}
        <section aria-labelledby="how-it-works-heading" className="bg-white border border-gray-200 rounded p-6 shadow-sm">
          <div className="border-b border-gray-200 pb-2 mb-6">
            <h2 id="how-it-works-heading" className="text-base font-bold text-gray-900 uppercase tracking-wider">
              {t("flow.title")}
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {t("flow.subtitle")}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {
                step: "1",
                title: t("flow.step1.title"),
                desc: t("flow.step1.desc"),
              },
              {
                step: "2",
                title: t("flow.step2.title"),
                desc: t("flow.step2.desc"),
              },
              {
                step: "3",
                title: t("flow.step3.title"),
                desc: t("flow.step3.desc"),
              },
              {
                step: "4",
                title: t("flow.step4.title"),
                desc: t("flow.step4.desc"),
              },
              {
                step: "5",
                title: t("flow.step5.title"),
                desc: t("flow.step5.desc"),
              },
            ].map((item) => (
              <div key={item.step} className="p-3.5 bg-gray-50 border border-gray-200 rounded flex flex-col justify-between">
                <div>
                  <span className="w-6 h-6 rounded-full bg-amber-600 text-white font-bold text-xs flex items-center justify-center mb-2">
                    {item.step}
                  </span>
                  <h4 className="text-xs font-bold text-gray-900">{item.title}</h4>
                  <p className="text-[11px] text-gray-600 mt-1 leading-normal">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* System Overview & Health Cards */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="gov-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-100 text-amber-800 rounded">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">{t("overview.ai.title")}</p>
                <p className="text-sm font-bold text-gray-900">{t("overview.ai.status")}</p>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3 border-t border-gray-100 pt-2">
              {t("overview.ai.desc")}
            </p>
          </div>

          <div className="gov-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-100 text-blue-800 rounded">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">{t("overview.db.title")}</p>
                <p className="text-sm font-bold text-gray-900">{t("overview.db.status")}</p>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3 border-t border-gray-100 pt-2">
              {t("overview.db.desc")}
            </p>
          </div>

          <div className="gov-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-100 text-emerald-800 rounded">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">{t("overview.records.title")}</p>
                <p className="text-sm font-bold text-gray-900">
                  {docCount !== null ? `${docCount} Records Processed` : t("overview.records.status")}
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3 border-t border-gray-100 pt-2">
              {t("overview.records.desc")}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
