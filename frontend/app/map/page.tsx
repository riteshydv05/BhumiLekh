"use client";

import React from "react";
import dynamic from "next/dynamic";
import Breadcrumb from "@/components/layout/Breadcrumb";
import {
  Globe2,
  Layers,
  Satellite,
  BarChart3,
  Shield,
  RefreshCw,
  Info,
  Map,
  Target,
  Download,
} from "lucide-react";

// Dynamically import Leaflet map component with ssr: false
const LandMapClient = dynamic(() => import("@/components/gis/LandMapClient"), {
  ssr: false,
  loading: () => (
    <div className="rounded-xl overflow-hidden border border-gray-200 shadow-lg">
      <div className="bg-slate-900 px-4 py-3 flex items-center gap-3">
        <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center animate-pulse">
          <Globe2 className="w-5 h-5 text-slate-900" />
        </div>
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-amber-400">BhumiLekh GIS</p>
          <p className="text-[10px] text-slate-400 font-mono">PostGIS · EPSG:4326 · WGS84</p>
        </div>
      </div>
      <div
        className="bg-slate-100 flex flex-col items-center justify-center gap-4"
        style={{ height: 620 }}
      >
        <RefreshCw className="w-10 h-10 text-amber-600 animate-spin" />
        <div className="text-center space-y-1">
          <p className="text-sm font-bold text-gray-700">Loading GIS Engine…</p>
          <p className="text-xs text-gray-400">Initializing Leaflet · Connecting PostGIS · Loading parcels</p>
        </div>
      </div>
    </div>
  ),
});

const FEATURE_HIGHLIGHTS = [
  {
    icon: Map,
    title: "Cadastral Map",
    desc: "PostGIS-backed polygon boundaries color-coded by land classification",
    color: "text-amber-700 bg-amber-50 border-amber-200",
  },
  {
    icon: Layers,
    title: "Multi-Layer Tiles",
    desc: "Switch between Street, Satellite, and Terrain base layers",
    color: "text-blue-700 bg-blue-50 border-blue-200",
  },
  {
    icon: Target,
    title: "Nearby Search",
    desc: "Click any point → find all parcels within a configurable radius via ST_DWithin",
    color: "text-purple-700 bg-purple-50 border-purple-200",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    desc: "District & state-level digitization statistics and land classification breakdown",
    color: "text-emerald-700 bg-emerald-50 border-emerald-200",
  },
  {
    icon: Shield,
    title: "Conflict Detection",
    desc: "ST_Intersects boundary overlap detection for dispute identification",
    color: "text-rose-700 bg-rose-50 border-rose-200",
  },
  {
    icon: Download,
    title: "GeoJSON Export",
    desc: "Download filtered parcels as standard GeoJSON for QGIS / ArcGIS",
    color: "text-slate-700 bg-slate-50 border-slate-200",
  },
];

export default function MapPage() {
  return (
    <div>
      <Breadcrumb items={[{ label: "Cadastral GIS Map" }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 border-b border-gray-200 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded-full uppercase tracking-wider">
                GIS Module v2
              </span>
              <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 border border-emerald-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                PostGIS Live
              </span>
            </div>
            <h1 className="text-2xl font-black text-gray-950 uppercase tracking-tight flex items-center gap-2">
              <Globe2 className="w-6 h-6 text-amber-700" />
              Cadastral Land Information System
            </h1>
            <p className="text-xs text-gray-500 max-w-2xl leading-relaxed">
              Interactive GIS map of digitized land parcels from the PostGIS database.
              Parcel boundaries are georeferenced in WGS84 (EPSG:4326), sourced from the
              LRMS/DILRMP reference layer. Supports spatial queries, overlap detection, and GeoJSON export.
            </p>
          </div>

          {/* Quick stat chips */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {[
              { label: "EPSG:4326", icon: "🌐" },
              { label: "PostGIS Backend", icon: "🗄️" },
              { label: "Leaflet Engine", icon: "🗺️" },
              { label: "DILRMP Phase-III", icon: "🏛️" },
            ].map(({ label, icon }) => (
              <span key={label} className="text-[10px] font-semibold px-2.5 py-1 bg-gray-100 border border-gray-200 rounded-full text-gray-600 flex items-center gap-1">
                <span>{icon}</span>
                <span>{label}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Main Map */}
        <LandMapClient />

        {/* Feature Highlights Grid */}
        <div>
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" />
            GIS Module Capabilities
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {FEATURE_HIGHLIGHTS.map(({ icon: Icon, title, desc, color }) => (
              <div
                key={title}
                className={`p-4 rounded-xl border ${color} flex gap-3 items-start`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-900">{title}</p>
                  <p className="text-[11px] text-gray-500 leading-relaxed mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Technical note */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-600 leading-relaxed flex gap-3">
          <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-800">Data Source:</span> Parcel boundaries are stored in the
            <span className="font-mono text-slate-700"> land_records_reference </span>
            table with a PostGIS <span className="font-mono text-slate-700">Geometry(POLYGON, 4326)</span> column.
            Nearby search uses <span className="font-mono text-slate-700">ST_DWithin(geography)</span> for true
            circular distance queries. For bulk import from government shapefiles, use <span className="font-mono text-slate-700">ogr2ogr</span> or the
            <span className="font-mono text-slate-700"> /scripts/import_shapefiles.py</span> pipeline.
          </div>
        </div>
      </div>
    </div>
  );
}
