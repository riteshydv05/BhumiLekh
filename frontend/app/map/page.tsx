"use client";

import React from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Breadcrumb from "@/components/layout/Breadcrumb";
import {
  Globe2,
  Layers,
  Satellite,
  BarChart3,
  Shield,
  RefreshCw,
  Map,
  Target,
  Download,
  Zap,
  Navigation2,
  ArrowLeft,
  CheckCircle,
} from "lucide-react";

// Dynamically import Leaflet map (no SSR)
const LandMapClient = dynamic(() => import("@/components/gis/LandMapClient"), {
  ssr: false,
  loading: () => (
    <div className="rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700 shadow-[0_2px_10px_rgba(0,0,0,0.06)] dark:shadow-2xl bg-white dark:bg-slate-900">
      {/* Header skeleton */}
      <div className="bg-gray-50 dark:bg-slate-900 px-4 py-3 flex items-center gap-3 border-b border-gray-200 dark:border-slate-700">
        <div className="w-9 h-9 bg-amber-100 dark:bg-amber-500/30 rounded-xl flex items-center justify-center animate-pulse">
          <Globe2 className="w-5 h-5 text-amber-600 dark:text-amber-500" />
        </div>
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-amber-700 dark:text-amber-400">BhumiLekh GIS</p>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 font-mono">PostGIS · EPSG:4326 · WGS84</p>
        </div>
        <div className="flex-1 h-8 bg-gray-200 dark:bg-slate-700/50 rounded-xl animate-pulse ml-4" />
        <div className="w-20 h-8 bg-gray-200 dark:bg-slate-700/50 rounded-xl animate-pulse" />
      </div>
      {/* Map skeleton */}
      <div className="flex" style={{ height: 620 }}>
        <div className="w-56 bg-gray-50 dark:bg-slate-800/60 border-r border-gray-200 dark:border-slate-700 animate-pulse" />
        <div className="flex-1 bg-gray-100 dark:bg-slate-800/30 flex flex-col items-center justify-center gap-5">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-amber-200 dark:border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
            <div className="absolute inset-2 w-10 h-10 border-4 border-emerald-200 dark:border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" style={{ animationDirection: "reverse", animationDuration: "0.7s" }} />
          </div>
          <div className="text-center space-y-1.5">
            <p className="text-sm font-black text-gray-700 dark:text-slate-200">Initializing GIS Engine</p>
            <p className="text-xs text-gray-400 dark:text-slate-500">Loading Leaflet · Connecting PostGIS · Fetching Parcels</p>
          </div>
        </div>
      </div>
      {/* Status bar skeleton */}
      <div className="bg-gray-50 dark:bg-slate-950 px-4 py-2 flex items-center justify-between border-t border-gray-200 dark:border-slate-800">
        <div className="flex items-center gap-2 text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>PostGIS Connected</span>
        </div>
        <span className="text-[10px] text-gray-400 dark:text-slate-600 font-mono">DILRMP Phase-III · NIC MeghRaj</span>
      </div>
    </div>
  ),
});

// ── Feature cards — same style as homepage cards ─────────────────────────────
const FEATURE_HIGHLIGHTS = [
  {
    icon: Map,        title: "Cadastral Map",
    desc: "PostGIS-backed polygon boundaries color-coded by land classification",
    lightIcon: "text-amber-700 bg-amber-100", darkIcon: "dark:text-amber-400 dark:bg-amber-500/15",
    lightBorder: "hover:border-amber-300", darkBorder: "dark:hover:border-amber-600/50",
  },
  {
    icon: Layers,     title: "Multi-Layer Tiles",
    desc: "Switch between Street, Satellite, and Terrain base layers",
    lightIcon: "text-blue-700 bg-blue-100", darkIcon: "dark:text-blue-400 dark:bg-blue-500/15",
    lightBorder: "hover:border-blue-300", darkBorder: "dark:hover:border-blue-600/50",
  },
  {
    icon: Navigation2,title: "Village-Level Search",
    desc: "Search any village, town, or district — instantly zooms to the location with bounding-box precision",
    lightIcon: "text-emerald-700 bg-emerald-100", darkIcon: "dark:text-emerald-400 dark:bg-emerald-500/15",
    lightBorder: "hover:border-emerald-300", darkBorder: "dark:hover:border-emerald-600/50",
  },
  {
    icon: Target,     title: "Nearby Search",
    desc: "Click any point → find all parcels within a configurable radius via ST_DWithin",
    lightIcon: "text-purple-700 bg-purple-100", darkIcon: "dark:text-purple-400 dark:bg-purple-500/15",
    lightBorder: "hover:border-purple-300", darkBorder: "dark:hover:border-purple-600/50",
  },
  {
    icon: BarChart3,  title: "Analytics Dashboard",
    desc: "District & state-level digitization statistics and land classification breakdown",
    lightIcon: "text-cyan-700 bg-cyan-100", darkIcon: "dark:text-cyan-400 dark:bg-cyan-500/15",
    lightBorder: "hover:border-cyan-300", darkBorder: "dark:hover:border-cyan-600/50",
  },
  {
    icon: Shield,     title: "Conflict Detection",
    desc: "ST_Intersects boundary overlap detection for dispute identification",
    lightIcon: "text-rose-700 bg-rose-100", darkIcon: "dark:text-rose-400 dark:bg-rose-500/15",
    lightBorder: "hover:border-rose-300", darkBorder: "dark:hover:border-rose-600/50",
  },
  {
    icon: Download,   title: "GeoJSON Export",
    desc: "Download filtered parcels as standard GeoJSON for QGIS / ArcGIS",
    lightIcon: "text-slate-700 bg-slate-100", darkIcon: "dark:text-slate-400 dark:bg-slate-500/15",
    lightBorder: "hover:border-slate-300", darkBorder: "dark:hover:border-slate-600/50",
  },
  {
    icon: Zap,        title: "Real-time Parcels",
    desc: "Live PostGIS backend streams land parcel data with instant spatial indexing",
    lightIcon: "text-yellow-700 bg-yellow-100", darkIcon: "dark:text-yellow-400 dark:bg-yellow-500/15",
    lightBorder: "hover:border-yellow-300", darkBorder: "dark:hover:border-yellow-600/50",
  },
];

export default function MapPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Breadcrumb items={[{ label: "Cadastral GIS Map" }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">

        {/* ── Page Header — fixed for light mode ─────────────────────────── */}
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
          <div className="space-y-3">
            {/* Breadcrumb chips */}
            <div className="flex items-center gap-2 flex-wrap">
              <Link href="/" prefetch={true}
                className="flex items-center gap-1.5 text-[10px] font-bold transition group
                  text-gray-500 dark:text-slate-500
                  hover:text-amber-700 dark:hover:text-amber-400">
                <ArrowLeft className="w-3 h-3 group-hover:-translate-x-0.5 transition-transform" />
                Home
              </Link>
              <span className="text-gray-300 dark:text-slate-700">/</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider
                bg-amber-100 dark:bg-amber-500/15
                text-amber-800 dark:text-amber-400
                border border-amber-200 dark:border-amber-500/25">
                GIS Module v2
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full flex items-center gap-1
                text-emerald-700 dark:text-emerald-400
                bg-emerald-100 dark:bg-emerald-500/10
                border border-emerald-200 dark:border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                PostGIS Live
              </span>
            </div>

            {/* Title */}
            <div>
              <h1 className="text-2xl sm:text-3xl font-black uppercase tracking-tight flex items-center gap-2.5
                text-gray-900 dark:text-white">
                <div className="w-9 h-9 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-md shadow-amber-500/25">
                  <Globe2 className="w-5 h-5 text-white" />
                </div>
                Cadastral Land Information System
              </h1>
              <p className="text-xs max-w-2xl leading-relaxed mt-2
                text-gray-500 dark:text-slate-500">
                Interactive GIS map of digitized land parcels from the PostGIS database.
                Parcel boundaries are georeferenced in WGS84 (EPSG:4326). Supports
                village-level search, spatial queries, overlap detection, and GeoJSON export.
              </p>
            </div>
          </div>

          {/* Stat chips */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {[
              { label: "EPSG:4326", icon: "🌐" },
              { label: "PostGIS Backend", icon: "🗄️" },
              { label: "Leaflet Engine", icon: "🗺️" },
              { label: "DILRMP Phase-III", icon: "🏛️" },
            ].map(({ label, icon }) => (
              <span key={label} className="text-[10px] font-semibold px-2.5 py-1.5 rounded-full flex items-center gap-1.5
                bg-white dark:bg-white/5
                border border-gray-200 dark:border-white/10
                text-gray-600 dark:text-slate-400
                shadow-sm dark:shadow-none">
                <span>{icon}</span>
                <span>{label}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Main Map */}
        <LandMapClient />

        {/* ── Feature Cards — homepage-matching style ──────────────────────── */}
        <div>
          <h2 className="text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-1.5
            text-gray-500 dark:text-slate-600">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            GIS Module Capabilities
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc, lightIcon, darkIcon, lightBorder, darkBorder }) => (
              <div key={title}
                className={`p-4 rounded-lg border transition-all duration-200 flex gap-3 items-start
                  bg-white dark:bg-slate-800
                  border-gray-200 dark:border-slate-700
                  shadow-[0_1px_4px_rgba(0,0,0,0.05)] dark:shadow-none
                  hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] dark:hover:shadow-none
                  ${lightBorder} ${darkBorder}`}>
                {/* Colored icon bubble — same as homepage cards */}
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${lightIcon} ${darkIcon}`}>
                  <Icon className="w-4.5 h-4.5" style={{ width: "18px", height: "18px" }} />
                </div>
                <div>
                  <p className="text-xs font-black text-gray-900 dark:text-white">{title}</p>
                  <p className="text-[11px] leading-relaxed mt-0.5 text-gray-500 dark:text-slate-400">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Technical Note — fixed for light mode ───────────────────────── */}
        <div className="p-4 rounded-xl border flex gap-3 text-[11px] leading-relaxed
          bg-white dark:bg-slate-800/60
          border-gray-200 dark:border-slate-700/40
          shadow-[0_1px_4px_rgba(0,0,0,0.04)] dark:shadow-none">
          <Zap className="w-4 h-4 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
          <div className="text-gray-600 dark:text-slate-500">
            <span className="font-bold text-gray-800 dark:text-slate-300">Data Source:</span>{" "}Parcel boundaries are stored in the{" "}
            <span className="font-mono text-gray-700 dark:text-slate-400 bg-gray-100 dark:bg-transparent px-1 rounded">land_records_reference</span>{" "}
            table with a PostGIS{" "}
            <span className="font-mono text-gray-700 dark:text-slate-400 bg-gray-100 dark:bg-transparent px-1 rounded">Geometry(POLYGON, 4326)</span>{" "}column.
            Nearby search uses{" "}
            <span className="font-mono text-gray-700 dark:text-slate-400 bg-gray-100 dark:bg-transparent px-1 rounded">ST_DWithin(geography)</span>{" "}
            for true circular distance queries. Village search uses Nominatim bounding boxes for precise navigation.
            For bulk import from government shapefiles, use{" "}
            <span className="font-mono text-gray-700 dark:text-slate-400 bg-gray-100 dark:bg-transparent px-1 rounded">ogr2ogr</span>{" "}or the{" "}
            <span className="font-mono text-gray-700 dark:text-slate-400 bg-gray-100 dark:bg-transparent px-1 rounded">/scripts/import_shapefiles.py</span>{" "}pipeline.
          </div>
        </div>

      </div>
    </div>
  );
}
