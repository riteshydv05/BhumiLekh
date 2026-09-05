"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, DUMMY_ACCOUNTS, DummyAccount } from "@/context/AuthContext";
import Breadcrumb from "@/components/layout/Breadcrumb";
import {
  Shield,
  KeyRound,
  User,
  LogIn,
  AlertCircle,
  CheckCircle2,
  Lock,
  ArrowRight,
  Info,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, logout } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please enter both username and password");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const auth = await login(username.trim(), password.trim());
      setSuccess(`Authenticated as ${auth.full_name || auth.username} (${auth.role})`);
      setTimeout(() => {
        if (auth.role === "ADMIN" || auth.role === "OFFICER") {
          router.push("/admin");
        } else {
          router.push("/dashboard");
        }
      }, 700);
    } catch (err: any) {
      setError(err.message || "Invalid credentials. Please verify username and password.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDummy = (acc: DummyAccount) => {
    setUsername(acc.username);
    setPassword(acc.password);
    setError(null);
  };

  return (
    <div className="pb-12">
      <Breadcrumb items={[{ label: "Officer & Citizen Authentication" }]} />

      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 space-y-8">
        {/* Portal Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-amber-100 text-amber-800 rounded-full flex items-center justify-center mx-auto border border-amber-300">
            <Lock className="w-6 h-6" />
          </div>
          <h1 className="text-xl sm:text-2xl font-black text-gray-950 uppercase tracking-tight">
            National Land Records Official Access Portal
          </h1>
          <p className="text-xs text-gray-600 max-w-lg mx-auto">
            Role-Based Authentication & Verification Station for Administrators, Revenue Officers, Patwaris, and Citizens.
          </p>
        </div>

        {/* Already logged in banner */}
        {user && (
          <div className="p-4 bg-emerald-50 border border-emerald-300 rounded text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <p className="font-bold text-emerald-950">
                  Currently Logged in as: {user.full_name || user.username}
                </p>
                <p className="text-emerald-800 text-[11px] font-mono">
                  Role: <strong className="uppercase">{user.role}</strong> | User ID: {user.user_id.substring(0, 8)}...
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => router.push(user.role === "ADMIN" || user.role === "OFFICER" ? "/admin" : "/dashboard")}
                className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold rounded shadow-xs text-xs"
              >
                Go to Protected Console →
              </button>
              <button
                type="button"
                onClick={logout}
                className="px-3 py-1.5 bg-white border border-gray-300 hover:bg-gray-100 text-gray-700 font-semibold rounded text-xs"
              >
                Logout
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          {/* Left: Login Form (7 cols) */}
          <div className="md:col-span-7 gov-card p-6 shadow-sm space-y-4">
            <div className="border-b border-gray-200 pb-3">
              <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center gap-2">
                <LogIn className="w-4 h-4 text-amber-700" />
                <span>Account Credentials Login</span>
              </h2>
              <p className="text-[11px] text-gray-500 mt-0.5">
                Enter your credentials or click any demo profile on the right.
              </p>
            </div>

            {error && (
              <div
                role="alert"
                className="p-3 bg-rose-50 border border-rose-300 text-rose-800 rounded text-xs flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div
                role="alert"
                className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded text-xs flex items-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{success}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-700 font-bold mb-1">
                  Username / Official ID
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-2.5 top-2.5 text-gray-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. admin or officer1"
                    className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded font-mono text-xs focus:ring-1 focus:ring-amber-500 bg-white"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-700 font-bold mb-1">
                  Password
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 absolute left-2.5 top-2.5 text-gray-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded font-mono text-xs focus:ring-1 focus:ring-amber-500 bg-white"
                    required
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-amber-700 hover:bg-amber-800 text-white font-bold rounded uppercase tracking-wider flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
                >
                  <Shield className="w-4 h-4" />
                  <span>{loading ? "Verifying Credentials..." : "Authenticate & Access Portal"}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Right: Dummy Credentials Selector (5 cols) */}
          <div className="md:col-span-5 space-y-3">
            <div className="gov-card p-4 bg-slate-50 border-slate-300 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wide flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-amber-700" />
                  <span>Seeded Demo Accounts</span>
                </h3>
                <span className="text-[10px] bg-amber-200 text-amber-950 font-bold px-1.5 rounded">1-CLICK</span>
              </div>

              <p className="text-[11px] text-gray-600">
                Click any profile to auto-fill the login form:
              </p>

              <div className="space-y-2">
                {DUMMY_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.username}
                    type="button"
                    onClick={() => handleSelectDummy(acc)}
                    className="w-full text-left p-2.5 bg-white border border-gray-200 hover:border-amber-600 rounded transition shadow-2xs group flex flex-col space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-gray-900 text-xs group-hover:text-amber-800">
                        {acc.label}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border uppercase ${acc.badgeColor}`}>
                        {acc.role}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono text-gray-600">
                      <span>ID: <strong className="text-gray-900">{acc.username}</strong></span>
                      <span>Pass: <strong className="text-gray-900">{acc.password}</strong></span>
                    </div>

                    <p className="text-[10px] text-gray-500 leading-tight">
                      {acc.description}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
