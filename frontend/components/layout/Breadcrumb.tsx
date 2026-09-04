"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export default function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav
      className="bg-gray-100 border-b border-gray-200 py-2 px-4 text-xs text-gray-600"
      aria-label="Breadcrumb"
    >
      <div className="max-w-7xl mx-auto flex items-center space-x-1.5 flex-wrap">
        <Link
          href="/"
          className="flex items-center text-gray-700 hover:text-amber-800 transition"
          title="Home"
        >
          <Home className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
          <span>Home</span>
        </Link>

        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;

          return (
            <React.Fragment key={idx}>
              <ChevronRight className="w-3.5 h-3.5 text-gray-400 shrink-0" aria-hidden="true" />
              {isLast || !item.href ? (
                <span className="font-semibold text-gray-900 truncate max-w-xs" aria-current="page">
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-gray-700 hover:text-amber-800 transition truncate max-w-xs"
                >
                  {item.label}
                </Link>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </nav>
  );
}
