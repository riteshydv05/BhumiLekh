"use client";

import React, { useEffect, useRef, useState } from "react";
import { Layers, MapPin, User, LandPlot, AlertCircle, Info } from "lucide-react";

interface ParcelData {
  id: string;
  surveyNumber: string;
  khasraNumber: string;
  village: string;
  tehsil: string;
  district: string;
  ownerName: string;
  areaHectares: number;
  landClass: string;
  coordinates: [number, number][];
}

// Sample prototype cadastral parcels (Pune / Maharashtra demonstration area)
const SAMPLE_PARCELS: ParcelData[] = [
  {
    id: "P-101",
    surveyNumber: "142/1",
    khasraNumber: "451",
    village: "Wagholi",
    tehsil: "Haveli",
    district: "Pune",
    ownerName: "Rameshwar Dnyaneshwar Patil",
    areaHectares: 0.85,
    landClass: "Jirayat (Agricultural)",
    coordinates: [
      [18.578, 73.978],
      [18.581, 73.979],
      [18.580, 73.983],
      [18.577, 73.981],
    ],
  },
  {
    id: "P-102",
    surveyNumber: "142/2",
    khasraNumber: "452",
    village: "Wagholi",
    tehsil: "Haveli",
    district: "Pune",
    ownerName: "Suresh Baburao Deshmukh",
    areaHectares: 1.20,
    landClass: "Bagayat (Irrigated)",
    coordinates: [
      [18.581, 73.979],
      [18.584, 73.980],
      [18.583, 73.984],
      [18.580, 73.983],
    ],
  },
  {
    id: "P-103",
    surveyNumber: "143/A",
    khasraNumber: "453",
    village: "Wagholi",
    tehsil: "Haveli",
    district: "Pune",
    ownerName: "Chandrakant Keshav Jadhav",
    areaHectares: 0.45,
    landClass: "Non-Agricultural (Commercial)",
    coordinates: [
      [18.577, 73.981],
      [18.580, 73.983],
      [18.579, 73.987],
      [18.575, 73.984],
    ],
  },
];

export default function LandMapClient() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const [selectedParcel, setSelectedParcel] = useState<ParcelData | null>(SAMPLE_PARCELS[0]);
  const [mapLoaded, setMapLoaded] = useState(false);

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

      // Initialize map centered at Wagholi, Pune
      const map = L.map(mapContainerRef.current).setView([18.58, 73.982], 15);
      mapInstanceRef.current = map;

      // OpenStreetMap tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      // Render parcel boundary polygons
      SAMPLE_PARCELS.forEach((parcel) => {
        const polygon = L.polygon(parcel.coordinates, {
          color: "#D97706",
          weight: 2,
          fillColor: "#F59E0B",
          fillOpacity: 0.35,
        }).addTo(map);

        polygon.bindTooltip(`Survey No: ${parcel.surveyNumber}<br>${parcel.ownerName}`, {
          sticky: true,
          className: "text-xs font-semibold p-1",
        });

        polygon.on("click", () => {
          setSelectedParcel(parcel);
          polygon.setStyle({ fillColor: "#EA580C", fillOpacity: 0.5 });
        });
      });

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
            <span>Cadastral Boundary Viewer (GIS / PostGIS)</span>
          </span>
          <span className="text-[11px] text-gray-500 font-medium">
            Datum: WGS84 • Provider: OpenStreetMap / LandLens GIS
          </span>
        </div>

        <div className="flex-1 relative">
          <div ref={mapContainerRef} className="w-full h-full" />
        </div>
      </div>

      {/* Selected Parcel Inspector (4 cols) */}
      <div className="lg:col-span-4 flex flex-col h-[650px] bg-white border border-gray-200 rounded p-5 shadow-sm space-y-4">
        <div className="border-b border-gray-200 pb-3">
          <span className="text-[11px] font-semibold text-amber-800 uppercase tracking-wider block">
            Spatial Parcel Metadata
          </span>
          <h2 className="text-base font-bold text-gray-950 mt-0.5">
            Survey No. {selectedParcel?.surveyNumber || "Select a Parcel"}
          </h2>
          <p className="text-xs text-gray-500">
            Parcel ID: {selectedParcel?.id} • Khasra: {selectedParcel?.khasraNumber}
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
                <div className="col-span-2">
                  <span className="text-gray-500 text-[11px]">District:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.district}, Maharashtra</p>
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
                  <p className="font-bold text-gray-900 font-mono">
                    {selectedParcel.areaHectares} Hectares
                  </p>
                  <p className="text-[10px] text-gray-500">
                    (~{(selectedParcel.areaHectares * 2.471).toFixed(2)} Acres)
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 text-[11px]">Classification:</span>
                  <p className="font-semibold text-gray-900">{selectedParcel.landClass}</p>
                </div>
              </div>
            </div>

            {/* Prototype Notice */}
            <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 flex items-start gap-1.5">
              <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <span>
                Demonstration Cadastral Dataset for Wagholi, Pune. PostGIS integration endpoint ready for geo-referenced GeoJSON layer overlays.
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
