"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  useAuth,
  CITIZEN_ACCOUNTS,
  GOVERNMENT_ACCOUNTS,
  DummyAccount,
  GOVERNMENT_ROLES,
} from "@/context/AuthContext";
import {
  Shield,
  KeyRound,
  User,
  LogIn,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Landmark,
  Search,
  MapPin,
  Lock,
  ChevronDown,
  Building2,
  Layers,
  ClipboardCheck,
  BadgeCheck,
} from "lucide-react";

type Portal = "citizen" | "government" | null;

export default function LoginPage() {
  const router = useRouter();
  const { login, user, logout, isGovernment } = useAuth();

  const [selectedPortal, setSelectedPortal] = useState<Portal>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSelectPortal = (portal: Portal) => {
    setSelectedPortal(portal);
    setUsername("");
    setPassword("");
    setError(null);
    setSuccess(null);
  };

  const handleSelectDemo = (acc: DummyAccount) => {
    setUsername(acc.username);
    setPassword(acc.password);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please enter both username and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const auth = await login(username.trim(), password.trim());

      // Validate: citizen should not access via government portal
      const isGovRole = GOVERNMENT_ROLES.includes(auth.role as any);
      if (selectedPortal === "citizen" && isGovRole) {
        setError(
          `Account '${auth.username}' has a government role (${auth.role}). Please use the Government Login.`
        );
        logout();
        setLoading(false);
        return;
      }
      if (selectedPortal === "government" && !isGovRole) {
        setError(
          `Account '${auth.username}' is a citizen account. Please use the Citizen Login.`
        );
        logout();
        setLoading(false);
        return;
      }

      setSuccess(`Welcome, ${auth.full_name || auth.username}!`);
      setTimeout(() => {
        router.push(isGovRole ? "/admin" : "/dashboard");
      }, 700);
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please check your username and password.");
    } finally {
      setLoading(false);
    }
  };

  // Already logged-in banner
  const LoggedInBanner = () =>
    user ? (
      <div className="mb-6 p-4 bg-emerald-50 border border-emerald-300 rounded-lg text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <div>
            <p className="font-bold text-emerald-950">
              Currently signed in as {user.full_name || user.username}
            </p>
            <p className="text-emerald-800 text-[11px] font-mono mt-0.5">
              Role: <strong className="uppercase">{user.role}</strong> &nbsp;·&nbsp; Portal:{" "}
              <strong>{isGovernment ? "Government" : "Citizen"}</strong>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => router.push(isGovernment ? "/admin" : "/dashboard")}
            className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold rounded text-xs transition"
          >
            Go to My Portal →
          </button>
          <button
            onClick={logout}
            className="px-3 py-1.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded text-xs"
          >
            Logout
          </button>
        </div>
      </div>
    ) : null;

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12 bg-gradient-to-b from-amber-50/60 to-gray-50">
      <div className="w-full max-w-3xl space-y-6">

        {/* Portal Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-100 border border-amber-300 rounded-full text-xs font-bold text-amber-900 mb-1">
            <Shield className="w-3.5 h-3.5" />
            <span>Authenticated Access Portal</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-gray-950 uppercase tracking-tight">
            BhumiLekh
          </h1>
          <p className="text-sm text-amber-800 font-semibold tracking-wide">भूमिलेख</p>
          <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
            Intelligent Land Record Digitization &amp; Validation System
          </p>
        </div>

        <LoggedInBanner />

        {/* Portal Selection Cards */}
        {!selectedPortal && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Citizen Card */}
            <button
              id="citizen-portal-btn"
              onClick={() => handleSelectPortal("citizen")}
              className="group text-left p-6 bg-white border-2 border-gray-200 hover:border-emerald-500 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-emerald-600 group-hover:text-white transition-all">
                  <User className="w-6 h-6" />
                </div>
                <div className="space-y-1 flex-1">
                  <p className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">
                    Citizen Portal
                  </p>
                  <h2 className="text-lg font-black text-gray-900 leading-tight">
                    Citizen Login
                  </h2>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    Search &amp; view your land records, check ownership details, and view your plot on the GIS map.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-1.5">
                {[
                  { icon: Search, text: "Search by Khasra / Khata / Survey No." },
                  { icon: MapPin, text: "View plot location on cadastral map" },
                  { icon: BadgeCheck, text: "View ownership & mutation details" },
                ].map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-2 text-[11px] text-gray-600">
                    <Icon className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span>{text}</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Public / Khatedar
                </span>
                <ArrowRight className="w-4 h-4 text-emerald-600 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            {/* Government Card */}
            <button
              id="government-portal-btn"
              onClick={() => handleSelectPortal("government")}
              className="group text-left p-6 bg-white border-2 border-gray-200 hover:border-blue-600 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-100 text-blue-700 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-blue-700 group-hover:text-white transition-all">
                  <Landmark className="w-6 h-6" />
                </div>
                <div className="space-y-1 flex-1">
                  <p className="text-[11px] font-bold text-blue-700 uppercase tracking-wider">
                    Government Portal
                  </p>
                  <h2 className="text-lg font-black text-gray-900 leading-tight">
                    Government Login
                  </h2>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    Digitize, verify &amp; manage land records. Dashboard adapts to your assigned role.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-1.5">
                {[
                  { icon: Building2, text: "Upload &amp; OCR digitization pipeline" },
                  { icon: ClipboardCheck, text: "Verify, approve &amp; manage mutations" },
                  { icon: Layers, text: "GIS spatial validation &amp; cadastral maps" },
                ].map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-2 text-[11px] text-gray-600">
                    <Icon className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                    <span dangerouslySetInnerHTML={{ __html: text }} />
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Admin · Officer · Verifier
                </span>
                <ArrowRight className="w-4 h-4 text-blue-600 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>
          </div>
        )}

        {/* Login Form — shown when a portal is selected */}
        {selectedPortal && (
          <div className="bg-white border-2 border-gray-200 rounded-xl shadow-sm overflow-hidden">
            {/* Form Header */}
            <div
              className={`px-6 py-4 flex items-center justify-between ${
                selectedPortal === "citizen"
                  ? "bg-emerald-700 text-white"
                  : "bg-blue-800 text-white"
              }`}
            >
              <div className="flex items-center gap-3">
                {selectedPortal === "citizen" ? (
                  <User className="w-5 h-5" />
                ) : (
                  <Landmark className="w-5 h-5" />
                )}
                <div>
                  <p className="font-black text-sm uppercase tracking-wide">
                    {selectedPortal === "citizen" ? "Citizen Login" : "Government Login"}
                  </p>
                  <p className="text-[11px] opacity-80">
                    {selectedPortal === "citizen"
                      ? "Public · Landowner Access"
                      : "RBAC → Role determined after authentication"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleSelectPortal(null)}
                className="text-xs opacity-70 hover:opacity-100 underline flex items-center gap-1 font-semibold"
              >
                ← Change portal
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-100">
              {/* Left: Form */}
              <div className="p-6 space-y-4">
                {error && (
                  <div
                    role="alert"
                    className="p-3 bg-rose-50 border border-rose-300 text-rose-800 rounded-lg text-xs flex items-center gap-2"
                  >
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {success && (
                  <div
                    role="alert"
                    className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-lg text-xs flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{success}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                  <div>
                    <label className="block text-gray-700 font-bold mb-1.5">
                      {selectedPortal === "citizen" ? "Username / Citizen ID" : "Official ID / Username"}
                    </label>
                    <div className="relative">
                      <User className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
                      <input
                        id="login-username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder={
                          selectedPortal === "citizen" ? "e.g. user1" : "e.g. admin or officer1"
                        }
                        className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg font-mono text-xs focus:ring-2 focus:ring-offset-0 focus:outline-none focus:ring-amber-400 bg-white"
                        required
                        autoComplete="username"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-gray-700 font-bold mb-1.5">Password</label>
                    <div className="relative">
                      <KeyRound className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
                      <input
                        id="login-password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg font-mono text-xs focus:ring-2 focus:ring-offset-0 focus:outline-none focus:ring-amber-400 bg-white"
                        required
                        autoComplete="current-password"
                      />
                    </div>
                  </div>

                  <button
                    id="login-submit-btn"
                    type="submit"
                    disabled={loading}
                    className={`w-full py-2.5 font-bold rounded-lg uppercase tracking-wider flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50 text-white ${
                      selectedPortal === "citizen"
                        ? "bg-emerald-700 hover:bg-emerald-800"
                        : "bg-blue-800 hover:bg-blue-900"
                    }`}
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Verifying…</span>
                      </>
                    ) : (
                      <>
                        <LogIn className="w-4 h-4" />
                        <span>
                          {selectedPortal === "citizen" ? "Access My Records" : "Enter Government Portal"}
                        </span>
                      </>
                    )}
                  </button>
                </form>

                {/* RBAC flow hint for gov */}
                {selectedPortal === "government" && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-[11px] text-blue-900 leading-relaxed">
                    <p className="font-bold mb-1">Role-Based Access:</p>
                    <p className="text-gray-600">
                      After authentication, your dashboard adapts automatically based on your assigned role —{" "}
                      <strong>Admin</strong>, <strong>Revenue Officer</strong>, or <strong>Patwari/Verifier</strong>.
                    </p>
                  </div>
                )}
              </div>

              {/* Right: Demo Accounts */}
              <div className="p-6 space-y-3 bg-gray-50">
                <p className="text-[11px] font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-amber-600" />
                  Demo Credentials
                </p>
                <div className="space-y-2">
                  {(selectedPortal === "citizen" ? CITIZEN_ACCOUNTS : GOVERNMENT_ACCOUNTS).map(
                    (acc) => (
                      <button
                        key={acc.username}
                        type="button"
                        onClick={() => handleSelectDemo(acc)}
                        className="w-full text-left p-3 bg-white border border-gray-200 hover:border-amber-500 rounded-lg transition shadow-xs group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-gray-900 text-xs group-hover:text-amber-800">
                            {acc.label}
                          </span>
                          <span
                            className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${acc.badgeColor}`}
                          >
                            {acc.role}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] font-mono text-gray-500 mb-1">
                          <span>
                            ID: <strong className="text-gray-800">{acc.username}</strong>
                          </span>
                          <span>
                            Pass: <strong className="text-gray-800">{acc.password}</strong>
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-400 leading-tight">{acc.description}</p>
                      </button>
                    )
                  )}
                </div>

                {selectedPortal === "government" && (
                  <div className="pt-2 border-t border-gray-200 text-[10px] text-gray-500 leading-relaxed">
                    <p className="font-semibold text-gray-700 mb-0.5">RBAC Privilege Levels:</p>
                    <p>👑 Admin — All tabs including user management</p>
                    <p>🎖️ Officer — Operations, Land Admin &amp; GIS tabs</p>
                    <p>✅ Verifier — Operations (verification queue) only</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer note */}
        <p className="text-center text-[10px] text-gray-400">
          BhumiLekh · DILRMP · Digital India · Government of India &nbsp;|&nbsp; SIH 2024 Prototype
        </p>
      </div>
    </div>
  );
}
