"use client";

import React from "react";
import dynamic from "next/dynamic";
import Breadcrumb from "@/components/layout/Breadcrumb";
import { useTranslation } from "@/context/AccessibilityContext";
import { Map, Loader2 } from "lucide-react";

// Dynamically import Leaflet map component with ssr: false
const LandMapClient = dynamic(() => import("@/components/gis/LandMapClient"), {
  ssr: false,
  loading: () => (
    <div className="h-[650px] bg-white border border-gray-200 rounded flex flex-col items-center justify-center text-xs text-gray-500">
      <Loader2 className="w-8 h-8 text-amber-600 animate-spin mb-2" />
      <p>Loading interactive GIS cadastral map layers...</p>
    </div>
  ),
});

export default function MapPage() {
  const { t } = useTranslation();

  return (
    <div>
      <Breadcrumb items={[{ label: t("nav.map") }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Header */}
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-xl font-bold text-gray-950 uppercase tracking-tight flex items-center gap-2">
            <Map className="w-5 h-5 text-amber-700" />
            <span>{t("services.map.title")}</span>
          </h1>
          <p className="text-xs text-gray-600 mt-0.5">
            {t("services.map.desc")}
          </p>
        </div>

        {/* Map Client */}
        <LandMapClient />
      </div>
    </div>
  );
}
