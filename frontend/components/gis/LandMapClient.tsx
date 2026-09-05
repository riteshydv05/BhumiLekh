"use client";

import React, { useEffect, useRef, useState } from "react";
import { Layers, MapPin, User, LandPlot, AlertCircle, Info, Database, ExternalLink, Search } from "lucide-react";
import { getGISParcels, GeoJSONFeature, GeoJSONFeatureCollection } from "@/lib/api";

interface SelectedParcel {
  id: string;
  surveyNumber: string;
  khasraNumber: string;
  khataNumber: string;
  plotNumber: string;
  village: string;
  tehsil: string;
  district: string;
  state: string;
  ownerName: string;
  fatherName: string;
  area: string;
  landClass: string;
  lrmsId: string | null;
  dilrmpId: string | null;
  sourceDatabase: string | null;
  registrationNumber: string | null;
}

function featureToParcel(feature: GeoJSONFeature): SelectedParcel {
  const p = feature.properties;
  return {
    id: p.id,
    surveyNumber: p.survey_number || "",
    khasraNumber: p.khasra_number || "",
    khataNumber: p.khata_number || "",
    plotNumber: p.plot_number || "",
    village: p.village || "",
    tehsil: p.tehsil || "",
    district: p.district || "",
    state: p.state || "",
    ownerName: p.owner_name || "",
    fatherName: p.father_name || "",
    area: p.area || "",
    landClass: p.land_classification || "",
    lrmsId: p.lrms_id,
    dilrmpId: p.dilrmp_id,
    sourceDatabase: p.source_database,
    registrationNumber: p.registration_number,
  };
}

export default function LandMapClient() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [selectedParcel, setSelectedParcel] = useState<SelectedParcel | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [parcelCount, setParcelCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [villageFilter, setVillageFilter] = useState<string>("");

  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      if (!mapContainerRef.current || mapInstanceRef.current) return;

      const L = (await import("leaflet")).default;

      // Fix standard leaflet icon path issues in webpack
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (!isMounted) return;

      // Initialize map centered at India
      const map = L.map(mapContainerRef.current).setView([22.5, 79.0], 5);
      mapInstanceRef.current = map;

      // OpenStreetMap tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      // Fetch parcels from PostGIS backend
      try {
        setLoading(true);
        const data: GeoJSONFeatureCollection = await getGISParcels();

        if (!isMounted) return;

        setParcelCount(data.features.length);

        if (data.features.length > 0) {
          const allBounds: [number, number][] = [];

          data.features.forEach((feature) => {
            if (!feature.geometry || feature.geometry.type !== "Polygon") return;

            const coords = (feature.geometry.coordinates[0] as number[][]).map(
              (c) => [c[1], c[0]] as [number, number]
            );

            allBounds.push(...coords);

            const polygon = L.polygon(coords, {
              color: "#D97706",
              weight: 2,
              fillColor: "#F59E0B",
              fillOpacity: 0.35,
            }).addTo(map);

            const p = feature.properties;
            polygon.bindTooltip(
              `<b>Survey: ${p.survey_number || "N/A"}</b><br>${p.owner_name || "Unknown"}<br><i style="font-size:9px;color:#888">LRMS: ${p.lrms_id || "N/A"}</i>`,
              { sticky: true, className: "text-xs font-semibold p-1" }
            );

            polygon.on("click", () => {
              setSelectedParcel(featureToParcel(feature));

              // Reset all polygon styles first
              map.eachLayer((layer: any) => {
                if (layer.setStyle && layer !== polygon) {
                  layer.setStyle({ fillColor: "#F59E0B", fillOpacity: 0.35 });
                }
              });

              polygon.setStyle({ fillColor: "#EA580C", fillOpacity: 0.5 });
            });
          });

          // Fit map to show all parcels
          if (allBounds.length > 0) {
            map.fitBounds(L.latLngBounds(allBounds), { padding: [30, 30], maxZoom: 15 });
          }

          // Select first parcel by default
          if (data.features[0]) {
            setSelectedParcel(featureToParcel(data.features[0]));
          }
        }

        setError(null);
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to load parcels");
        }
      } finally {
        if (isMounted) setLoading(false);
      }

      setMapLoaded(true);
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Map Container (8 cols) */}
      <div className="lg:col-span-8 flex flex-col h-[650px] bg-white border border-gray-300 rounded overflow-hidden shadow-sm">
        <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex items-center justify-between text-xs text-gray-700">
          <span className="font-bold uppercase tracking-wider text-gray-900 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-amber-700" />
            <span>Cadastral Boundary Viewer (PostGIS / LRMS)</span>
          </span>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-emerald-700 font-semibold">
              {parcelCount} parcels loaded
            </span>
            <span className="text-[11px] text-gray-500 font-medium">
              Datum: WGS84 • SRID: 4326
            </span>
          </div>
        </div>

        <div className="flex-1 relative">
          <div ref={mapContainerRef} className="w-full h-full" />
          {loading && (
            <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-[1000]">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-xs text-gray-600">Loading PostGIS parcels...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="absolute bottom-3 left-3 right-3 bg-red-50 border border-red-200 rounded p-2 text-[11px] text-red-700 z-[1000] flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Selected Parcel Inspector (4 cols) */}
      <div className="lg:col-span-4 flex flex-col h-[650px] bg-white border border-gray-200 rounded p-5 shadow-sm space-y-4 overflow-y-auto">
        <div className="border-b border-gray-200 pb-3">
          <span className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider block">
            Spatial Parcel Metadata
          </span>
          <h2 className="text-base font-bold text-gray-950 mt-0.5">
            Survey No. {selectedParcel?.surveyNumber || "Select a Parcel"}
          </h2>
          <p className="text-xs text-gray-500">
            Parcel ID: {selectedParcel?.id?.substring(0, 8) || "—"} • Khasra: {selectedParcel?.khasraNumber || "—"}
          </p>
        </div>

        {selectedParcel ? (
          <div className="space-y-4 text-xs overflow-y-auto pr-1">
            {/* Owner Details */}
            <div className="p-3 bg-gray-50 border border-gray-200 rounded space-y-1">
              <span className="text-[11px] font-bold text-gray-500 uppercase flex items-center gap-1">
                <User className="w-3.5 h-3.5 text-amber-700" />
                <span>Primary Recorded Owner</span>
              </span>
              <p className="font-bold text-gray-900 text-sm">{selectedParcel.ownerName}</p>
              {selectedParcel.fatherName && (
                <p className="text-[11px] text-gray-500">Father: {selectedParcel.fatherName}</p>
              )}
            </div>

            {/* Jurisdiction Details */}
            <div className="p-3 bg-gray-50 border border-gray-200 rounded space-y-2">
              <span className="text-[11px] font-bold text-gray-500 uppercase flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-amber-700" />
                <span>Jurisdiction Hierarchy</span>
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 text-[11px]">Village:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.village}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">Tehsil:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.tehsil}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">District:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.district}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">State:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.state}</p>
                </div>
              </div>
            </div>

            {/* Land Specs */}
            <div className="p-3 bg-gray-50 border border-gray-200 rounded space-y-2">
              <span className="text-[11px] font-bold text-gray-500 uppercase flex items-center gap-1">
                <LandPlot className="w-3.5 h-3.5 text-amber-700" />
                <span>Area & Land Use</span>
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 text-[11px]">Survey Area:</span>
                  <p className="font-bold text-gray-900 font-mono">{selectedParcel.area}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">Classification:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.landClass}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">Khata No.:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.khataNumber || "—"}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">Plot No.:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.plotNumber || "—"}</p>
                </div>
              </div>
            </div>

            {/* Integration IDs */}
            <div className="p-3 bg-violet-50/50 border border-violet-100 rounded space-y-2">
              <span className="text-[11px] font-bold text-violet-800 uppercase flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-violet-700" />
                <span>LRMS / DILRMP Integration</span>
              </span>
              <div className="grid grid-cols-1 gap-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">LRMS ID:</span>
                  <span className="font-mono text-violet-800 font-semibold">{selectedParcel.lrmsId || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">DILRMP ID:</span>
                  <span className="font-mono text-violet-800 font-semibold">{selectedParcel.dilrmpId || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Reg. No.:</span>
                  <span className="font-mono text-gray-800 font-semibold text-[10px]">{selectedParcel.registrationNumber || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Source:</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold">
                    {selectedParcel.sourceDatabase === "synthetic_prototype" ? "Synthetic Prototype" : selectedParcel.sourceDatabase}
                  </span>
                </div>
              </div>
            </div>

            {/* Prototype Notice */}
            <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 flex items-start gap-1.5">
              <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <span>
                <strong>LRMS Prototype Data.</strong> PostGIS-backed synthetic cadastral data. Integration interfaces are ready for authorized government LRMS/DILRMP/GIS API connections.
              </span>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-gray-500">
            <MapPin className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p>Click on any highlighted parcel polygon on the map to inspect ownership details.</p>
          </div>
        )}
      </div>
    </div>
  );
}
