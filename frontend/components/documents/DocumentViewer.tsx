"use client";

import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCw, Maximize2 } from "lucide-react";

interface DocumentViewerProps {
  fileUrl: string;
  contentType: string;
  filename: string;
  bboxes?: Array<{
    text?: string;
    bbox: number[];
    confidence?: number;
  }>;
}

export default function DocumentViewer({
  fileUrl,
  contentType,
  filename,
  bboxes = [],
}: DocumentViewerProps) {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);

  const isPdf = contentType === "application/pdf" || filename.toLowerCase().endsWith(".pdf");

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 250));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);
  const handleReset = () => {
    setZoom(100);
    setRotation(0);
  };

  return (
    <div className="flex flex-col h-full bg-gray-100 border border-gray-300 rounded overflow-hidden">
      {/* Control Bar */}
      <div className="bg-white px-3 py-2 border-b border-gray-200 flex items-center justify-between text-xs text-gray-700">
        <span className="font-semibold truncate max-w-xs text-gray-900" title={filename}>
          {filename}
        </span>

        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-gray-100 text-gray-600 border border-gray-200"
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="px-2 py-0.5 text-[11px] font-mono font-medium">{zoom}%</span>
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-gray-100 text-gray-600 border border-gray-200"
            title="Zoom In"
            aria-label="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleRotate}
            className="p-1 rounded hover:bg-gray-100 text-gray-600 border border-gray-200 ml-1"
            title="Rotate 90°"
            aria-label="Rotate 90 Degrees"
          >
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-1 rounded hover:bg-gray-100 text-gray-600 border border-gray-200"
            title="Reset Zoom"
            aria-label="Reset Zoom and Rotation"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Viewer Canvas */}
      <div className="flex-1 overflow-auto p-4 flex items-center justify-center min-h-[420px]">
        {isPdf ? (
          <iframe
            src={`${fileUrl}#toolbar=1&navpanes=0`}
            title={filename}
            className="w-full h-full min-h-[500px] border-0 bg-white shadow-sm"
          />
        ) : (
          <div
            className="relative transition-transform duration-200 inline-block shadow-sm"
            style={{
              transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
              transformOrigin: "center center",
            }}
          >
            <img
              src={fileUrl}
              alt={filename}
              className="max-w-full max-h-[600px] object-contain rounded bg-white"
            />

            {/* Optional Overlay Bounding Boxes Architecture */}
            {bboxes.length > 0 && (
              <div className="absolute inset-0 pointer-events-none">
                {bboxes.map((b, idx) => (
                  <div
                    key={idx}
                    style={{
                      position: "absolute",
                      left: `${b.bbox[0]}px`,
                      top: `${b.bbox[1]}px`,
                      width: `${b.bbox[2] - b.bbox[0]}px`,
                      height: `${b.bbox[3] - b.bbox[1]}px`,
                    }}
                    className="border-2 border-amber-500 bg-amber-500/10 pointer-events-auto hover:bg-amber-500/25 transition"
                    title={b.text ? `${b.text} (${((b.confidence || 1) * 100).toFixed(0)}%)` : undefined}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
