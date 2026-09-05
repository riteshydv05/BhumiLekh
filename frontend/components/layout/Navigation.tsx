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
  Search,
  BookOpen,
  Bell,
  Lock,
} from "lucide-react";
import { useTranslation } from "@/context/AccessibilityContext";
import { useAuth } from "@/context/AuthContext";

const BASE_NAV_ITEMS = [
  { href: "/", key: "nav.home", defaultLabel: "Home Portal", icon: Home },
  { href: "/dashboard", key: "nav.dashboard", defaultLabel: "System Dashboard", icon: LayoutDashboard },
  { href: "/documents", key: "nav.documents", defaultLabel: "Land Records Repository", icon: FileText },
  { href: "/upload", key: "nav.upload", defaultLabel: "Digitize New Deed", icon: UploadCloud },
  {
    href: "/verify",
    key: "nav.verify",
    defaultLabel: "Audit & Verification",
    icon: ShieldCheck,
    badge: "Audit Queue",
  },
  { href: "/map", key: "nav.map", defaultLabel: "Cadastral Map (GIS)", icon: Map },
];

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = useTranslation();
  const { user, isOfficer } = useAuth();

  const navItems = [
    ...BASE_NAV_ITEMS,
    {
      href: "/admin",
      key: "nav.admin",
      defaultLabel: "Admin Console",
      icon: Lock,
      badge: user?.role ? user.role : "RBAC",
    },
  ];

  return (
    <nav className="bg-gradient-to-r from-amber-700 via-amber-600 to-amber-700 text-white shadow-sm border-b-2 border-amber-800" aria-label="Main Navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-11">
          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-3 py-2 text-xs sm:text-[13px] font-semibold transition rounded-t-sm relative ${
                    isActive
                      ? "bg-amber-900 text-white shadow-inner border-b-2 border-amber-300"
                      : "text-amber-50 hover:bg-amber-800/80 hover:text-white"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
                  <span>{t(item.key) || item.defaultLabel}</span>

                  {item.badge && (
                    <span className="ml-1 text-[9.5px] bg-amber-200 text-amber-950 font-bold px-1.5 py-0.2 rounded-full uppercase tracking-tighter">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Right Action Shortcuts (Desktop) */}
          <div className="hidden lg:flex items-center gap-2">

            <Link
              href="/help"
              className="px-2 py-1 rounded hover:bg-amber-800 text-amber-100 hover:text-white text-xs flex items-center gap-1 transition"
              title="Revenue Guidelines & Helpdesk"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Manual</span>
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden w-full justify-between items-center">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-100 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>{t("nav.menu") || "Official Menu"}</span>
            </span>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-1.5 rounded text-amber-100 hover:text-white hover:bg-amber-800 focus:outline-none"
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
        <div className="md:hidden bg-amber-800 border-t border-amber-900 px-3 pt-2 pb-3 space-y-1">
          {navItems.map((item) => {
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
                className={`flex items-center justify-between px-3 py-2 rounded text-xs font-semibold ${
                  isActive
                    ? "bg-amber-950 text-white font-bold"
                    : "text-amber-100 hover:bg-amber-700 hover:text-white"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  <span>{t(item.key) || item.defaultLabel}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] bg-amber-300 text-amber-950 font-bold px-1.5 py-0.5 rounded-full uppercase">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}


        </div>
      )}
    </nav>
  );
}
