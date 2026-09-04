"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  Home,
  LayoutDashboard,
  Map,
  Menu,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";

const NAV_ITEMS = [
  { href: "/", key: "nav.home", defaultLabel: "Home", icon: Home },
  { href: "/dashboard", key: "nav.dashboard", defaultLabel: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", key: "nav.documents", defaultLabel: "My Documents", icon: FileText },
  { href: "/upload", key: "nav.upload", defaultLabel: "Upload Document", icon: UploadCloud },
  { href: "/verify", key: "nav.verify", defaultLabel: "Verification", icon: ShieldCheck },
  { href: "/map", key: "nav.map", defaultLabel: "Land Map (GIS)", icon: Map },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = useTranslation();

  return (
    <nav className="bg-amber-600 text-white shadow-sm border-b-2 border-amber-700" aria-label="Main Navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-11">
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium transition rounded-t-sm ${
                    isActive
                      ? "bg-amber-800 text-white font-semibold shadow-inner border-b-2 border-amber-300"
                      : "text-amber-50 hover:bg-amber-700 hover:text-white"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <span>{t(item.key) || item.defaultLabel}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden w-full justify-between items-center">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-100">
              {t("nav.menu") || "Navigation Menu"}
            </span>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-1.5 rounded text-amber-100 hover:text-white hover:bg-amber-700 focus:outline-none"
              aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Collapsible Drawer */}
      {mobileOpen && (
        <div className="md:hidden bg-amber-700 border-t border-amber-800 px-3 pt-2 pb-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-medium ${
                  isActive
                    ? "bg-amber-900 text-white font-bold"
                    : "text-amber-100 hover:bg-amber-600 hover:text-white"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="w-4 h-4" aria-hidden="true" />
                <span>{t(item.key) || item.defaultLabel}</span>
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
}
