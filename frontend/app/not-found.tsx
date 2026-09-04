import React from "react";
import Link from "next/link";
import { AlertCircle, Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6 text-center">
      <div className="gov-card p-8 max-w-md w-full shadow-sm space-y-4">
        <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>

        <h1 className="text-xl font-bold text-gray-900">
          404 — Page Not Found
        </h1>

        <p className="text-xs text-gray-600 leading-relaxed">
          The requested land record portal route does not exist or has been relocated. Please check the URL or return to the main portal.
        </p>

        <div className="pt-2 flex justify-center gap-3">
          <Link
            href="/"
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <Home className="w-4 h-4" />
            <span>Return Home</span>
          </Link>

          <Link
            href="/documents"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded text-xs font-semibold flex items-center gap-1.5 border border-gray-300"
          >
            <span>My Documents</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
