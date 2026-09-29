"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { loginUser, AuthTokenResponse } from "@/lib/api";

export interface DummyAccount {
  label: string;
  role: string;
  username: string;
  password: string;
  badgeColor: string;
  description: string;
  portal: "citizen" | "government";
}

/** Roles that belong to the Government portal */
export const GOVERNMENT_ROLES = ["ADMIN", "OFFICER", "VERIFIER"] as const;
export type GovernmentRole = (typeof GOVERNMENT_ROLES)[number];

/** All seeded demo accounts — split by portal */
export const CITIZEN_ACCOUNTS: DummyAccount[] = [
  {
    label: "Citizen / Khatedar (Public)",
    role: "USER",
    username: "user1",
    password: "user123",
    badgeColor: "bg-emerald-100 text-emerald-900 border-emerald-300",
    description: "View-only access to public RoR records and cadastral map boundaries.",
    portal: "citizen",
  },
];

export const GOVERNMENT_ACCOUNTS: DummyAccount[] = [
  {
    label: "District Administrator (Tehsildar)",
    role: "ADMIN",
    username: "admin",
    password: "admin123",
    badgeColor: "bg-purple-100 text-purple-900 border-purple-300",
    description: "Full system administration, user management, status overrides, and document deletion.",
    portal: "government",
  },
  {
    label: "Revenue Nodal Officer",
    role: "OFFICER",
    username: "officer1",
    password: "officer123",
    badgeColor: "bg-blue-100 text-blue-900 border-blue-300",
    description: "Field audit approvals, mutation validations, GIS review and document status updates.",
    portal: "government",
  },
  {
    label: "Document Verifier (Patwari)",
    role: "VERIFIER",
    username: "verifier1",
    password: "verifier123",
    badgeColor: "bg-amber-100 text-amber-900 border-amber-300",
    description: "Human-in-the-loop field verification and OCR transcription corrections.",
    portal: "government",
  },
];

/** All accounts combined (legacy compat) */
export const DUMMY_ACCOUNTS: DummyAccount[] = [
  ...CITIZEN_ACCOUNTS,
  ...GOVERNMENT_ACCOUNTS,
];

interface AuthContextType {
  user: AuthTokenResponse | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<AuthTokenResponse>;
  logout: () => void;
  hasRole: (roles: string | string[]) => boolean;
  /** true if user has any government-side role (ADMIN | OFFICER | VERIFIER) */
  isGovernment: boolean;
  /** true if user is a public citizen (USER role) */
  isCitizen: boolean;
  /** true if user is ADMIN */
  isAdmin: boolean;
  /** @deprecated use isGovernment — kept for compat with existing components */
  isOfficer: boolean;
  dummyAccounts: DummyAccount[];
  citizenAccounts: DummyAccount[];
  governmentAccounts: DummyAccount[];
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthTokenResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Load user session on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("bhumilekh_auth");
      if (stored) {
        setUser(JSON.parse(stored));
      }
    } catch {
      // Ignore storage errors
    } finally {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string): Promise<AuthTokenResponse> => {
    const authData = await loginUser(username, password);
    setUser(authData);
    try {
      localStorage.setItem("bhumilekh_auth", JSON.stringify(authData));
    } catch {}
    return authData;
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem("bhumilekh_auth");
    } catch {}
  };

  const hasRole = (roles: string | string[]): boolean => {
    if (!user) return false;
    const roleList = Array.isArray(roles) ? roles : [roles];
    return roleList.includes(user.role);
  };

  const isGovernment = GOVERNMENT_ROLES.includes(user?.role as GovernmentRole);
  const isCitizen = user?.role === "USER";
  const isAdmin = user?.role === "ADMIN";
  // Legacy alias — ADMIN | OFFICER | VERIFIER all get government portal access
  const isOfficer = isGovernment;

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        hasRole,
        isGovernment,
        isCitizen,
        isAdmin,
        isOfficer,
        dummyAccounts: DUMMY_ACCOUNTS,
        citizenAccounts: CITIZEN_ACCOUNTS,
        governmentAccounts: GOVERNMENT_ACCOUNTS,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
