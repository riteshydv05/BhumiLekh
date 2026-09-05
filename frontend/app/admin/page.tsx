"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth, DUMMY_ACCOUNTS } from "@/context/AuthContext";
import Breadcrumb from "@/components/layout/Breadcrumb";
import {
  getDocuments,
  getDocumentResults,
  updateDocumentStatus,
  deleteDocument,
  updateDocumentField,
  addDocumentField,
  listUsers,
  reprocessDocument,
  DocumentItem,
  DocumentResultItem,
  UserProfile,
} from "@/lib/api";
import {
  Shield,
  KeyRound,
  UserCheck,
  FileText,
  Trash2,
  Edit3,
  Plus,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  Layers,
  Search,
  Lock,
  LogOut,
  Save,
  X,
  Check,
  Eye,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import AdminCharts from "@/components/admin/AdminCharts";

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading, logout, isOfficer, isAdmin } = useAuth();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [usersList, setUsersList] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Active document selection for editing fields
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [docFields, setDocFields] = useState<DocumentResultItem[]>([]);
  const [loadingFields, setLoadingFields] = useState(false);

  // Field Edit Modal / Inline state
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editFieldName, setEditFieldName] = useState("");
  const [editFieldValue, setEditFieldValue] = useState("");
  const [editValidationStatus, setEditValidationStatus] = useState("valid");

  // New Field State
  const [newFieldName, setNewFieldName] = useState("");
  const [newFieldValue, setNewFieldValue] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  // Tab State
  const [activeTab, setActiveTab] = useState<"analytics" | "documents" | "users">("analytics");

  // Load documents and users
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await getDocuments();
      setDocuments(docs || []);
      if (docs && docs.length > 0 && !selectedDocId) {
        setSelectedDocId(docs[0].id);
      }

      // If admin, load registered users
      if (user?.access_token) {
        listUsers(user.access_token)
          .then((res) => setUsersList(res.users || []))
          .catch(() => setUsersList([]));
      }
    } catch (err: any) {
      setError(err.message || "Failed to load database records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && isOfficer) {
      loadData();
    }
  }, [authLoading, isOfficer]);

  // Load fields when a document is selected
  useEffect(() => {
    if (!selectedDocId) return;
    setLoadingFields(true);
    getDocumentResults(selectedDocId)
      .then((res) => {
        setDocFields(res.results || (res as any).fields || []);
      })
      .catch(() => setDocFields([]))
      .finally(() => setLoadingFields(false));
  }, [selectedDocId]);

  const notify = (msg: string) => {
    setSuccessMessage(msg);
    setTimeout(() => setSuccessMessage(null), 3500);
  };

  // 1. Action: Change Document Status in Database
  const handleChangeStatus = async (docId: string, newStatus: string) => {
    try {
      await updateDocumentStatus(docId, newStatus, undefined, user?.access_token);
      setDocuments((prev) =>
        prev.map((d) => (d.id === docId ? { ...d, status: newStatus } : d))
      );
      notify(`Document status changed to ${newStatus} in database.`);
    } catch (err: any) {
      setError(err.message || "Failed to update status");
    }
  };

  // 2. Action: Delete Document from Database
  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Are you sure you want to permanently delete this document and all its extracted results from the database?")) {
      return;
    }
    try {
      await deleteDocument(docId, user?.access_token);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (selectedDocId === docId) {
        setSelectedDocId(null);
        setDocFields([]);
      }
      notify("Document permanently deleted from database.");
    } catch (err: any) {
      setError(err.message || "Failed to delete document");
    }
  };

  // 3. Action: Save Field Edits to Database
  const handleSaveFieldEdit = async (fieldId: string) => {
    if (!selectedDocId) return;
    try {
      await updateDocumentField(
        selectedDocId,
        fieldId,
        {
          field_name: editFieldName,
          field_value: editFieldValue,
          validation_status: editValidationStatus,
          validated: editValidationStatus === "valid",
        }
      );

      setDocFields((prev) =>
        prev.map((f) =>
          f.id === fieldId
            ? {
                ...f,
                field_name: editFieldName,
                field_value: editFieldValue,
                validation_status: editValidationStatus,
                validated: editValidationStatus === "valid",
              }
            : f
        )
      );

      setEditingFieldId(null);
      notify("Field record updated and saved to PostgreSQL database.");
    } catch (err: any) {
      setError(err.message || "Failed to update field");
    }
  };

  // 4. Action: Add New Manual Field to Database
  const handleAddManualField = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDocId || !newFieldName.trim()) return;

    try {
      const added = await addDocumentField(
        selectedDocId,
        {
          field_name: newFieldName.trim(),
          field_value: newFieldValue.trim(),
          data_type: "string",
        }
      );

      setDocFields((prev) => [added, ...prev]);
      setNewFieldName("");
      setNewFieldValue("");
      setShowAddModal(false);
      notify(`New field '${added.field_name}' inserted into database.`);
    } catch (err: any) {
      setError(err.message || "Failed to add field");
    }
  };

  // 5. Action: Reprocess Document
  const handleReprocess = async (docId: string) => {
    try {
      await reprocessDocument(docId, "auto");
      notify("Reprocessing task triggered in Celery worker pool.");
      loadData();
    } catch (err: any) {
      setError(err.message || "Failed to trigger reprocess");
    }
  };

  // Guard: Not logged in
  if (!authLoading && !user) {
    return (
      <div>
        <Breadcrumb items={[{ label: "Admin Console" }]} />
        <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
          <div className="w-14 h-14 bg-amber-100 text-amber-800 rounded-full flex items-center justify-center mx-auto border border-amber-300">
            <Lock className="w-7 h-7" />
          </div>
          <h1 className="text-xl font-black text-gray-900 uppercase tracking-tight">
            Protected Admin Route — Authentication Required
          </h1>
          <p className="text-xs text-gray-600 leading-relaxed">
            This administration console allows modifying document statuses, editing field data in the database, and managing users. You must log in with an Administrator or Officer account to proceed.
          </p>

          <div className="p-4 bg-slate-50 border border-slate-300 rounded text-left space-y-2 text-xs">
            <p className="font-bold text-gray-800">Use Seeded Dummy Credentials:</p>
            <div className="font-mono text-[11px] space-y-1 text-gray-700">
              <p>👑 <strong>Admin:</strong> admin / admin123 (Full control)</p>
              <p>🎖️ <strong>Officer:</strong> officer1 / officer123 (Audit & field edits)</p>
            </div>
          </div>

          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-amber-700 hover:bg-amber-800 text-white rounded font-bold uppercase tracking-wider text-xs shadow-sm transition"
          >
            <KeyRound className="w-4 h-4" />
            <span>Go to Login Page</span>
          </Link>
        </div>
      </div>
    );
  }

  // Guard: Citizen / User role without admin rights
  if (!authLoading && user && !isOfficer) {
    return (
      <div>
        <Breadcrumb items={[{ label: "Admin Console" }]} />
        <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
          <div className="w-14 h-14 bg-rose-100 text-rose-800 rounded-full flex items-center justify-center mx-auto border border-rose-300">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h1 className="text-xl font-black text-gray-900 uppercase tracking-tight">
            Access Restricted: Role Insufficient
          </h1>
          <p className="text-xs text-gray-600 leading-relaxed">
            You are currently logged in as <strong className="font-mono">{user.username}</strong> with role <strong className="font-mono text-rose-700 uppercase">[{user.role}]</strong>. Only users with <strong className="font-mono">ADMIN</strong> or <strong className="font-mono">OFFICER</strong> roles can edit records in this console.
          </p>

          <div className="pt-2 flex justify-center gap-3">
            <button
              onClick={logout}
              className="px-4 py-2 bg-amber-700 hover:bg-amber-800 text-white font-bold rounded text-xs"
            >
              Switch to Admin Account
            </button>
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold rounded text-xs border border-gray-300"
            >
              Return to Public Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const activeDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="pb-12">
      <Breadcrumb items={[{ label: "Admin Console & Database Manager" }]} />

      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 space-y-6">
        {/* Admin Header with Role Pill & Credentials Callout */}
        <div className="bg-slate-900 text-white rounded-md p-4 sm:p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-amber-500">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs bg-amber-500 text-slate-950 font-bold px-2 py-0.5 rounded font-mono uppercase">
                {user?.role} Mode Active
              </span>
              <span className="text-xs text-slate-400">|</span>
              <span className="text-xs text-emerald-400 font-mono flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Database Write Access Enabled
              </span>
            </div>
            <h1 className="text-lg sm:text-xl font-extrabold uppercase tracking-tight">
              Administrative Control Console
            </h1>
            <p className="text-xs text-slate-300">
              Authenticated Operator: <strong className="text-white">{user?.full_name || user?.username}</strong> ({user?.username})
            </p>
          </div>

          {/* Dummy Credentials Reference Banner */}
          <div className="bg-slate-800/90 border border-slate-700 rounded p-3 text-[11px] space-y-1 shrink-0">
            <p className="font-bold text-amber-400 uppercase tracking-wide">Dummy Credentials Reference:</p>
            <div className="font-mono text-slate-300 space-y-0.5">
              <p>Admin: <strong className="text-white">admin</strong> / <strong className="text-white">admin123</strong> (Role: ADMIN)</p>
              <p>Officer: <strong className="text-white">officer1</strong> / <strong className="text-white">officer123</strong> (Role: OFFICER)</p>
              <p>Verifier: <strong className="text-white">verifier1</strong> / <strong className="text-white">verifier123</strong> (Role: VERIFIER)</p>
            </div>
            <button
              onClick={logout}
              className="mt-1 text-[10px] text-rose-400 hover:text-rose-300 font-bold underline flex items-center gap-1"
            >
              <LogOut className="w-3 h-3" /> Logout / Switch Account
            </button>
          </div>
        </div>

        {/* Success/Error Alerts */}
        {successMessage && (
          <div
            role="alert"
            className="p-3 bg-emerald-50 border border-emerald-300 text-emerald-900 rounded text-xs flex items-center gap-2 shadow-xs"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{successMessage}</span>
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="p-3 bg-rose-50 border border-rose-300 text-rose-900 rounded text-xs flex items-center justify-between gap-2 shadow-xs"
          >
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Operational Overview KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="gov-card p-3.5 border-l-4 border-l-amber-600 bg-white shadow-xs">
            <div className="flex items-center justify-between text-gray-500">
              <span className="text-[11px] font-bold uppercase">Total Ingested</span>
              <FileText className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-xl sm:text-2xl font-black text-gray-900 mt-1 font-mono">{documents.length}</p>
            <p className="text-[10px] text-gray-400 mt-0.5">PostgreSQL Records</p>
          </div>

          <div className="gov-card p-3.5 border-l-4 border-l-emerald-600 bg-white shadow-xs">
            <div className="flex items-center justify-between text-gray-500">
              <span className="text-[11px] font-bold uppercase">Auto-Approved</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-xl sm:text-2xl font-black text-gray-900 mt-1 font-mono">
              {documents.filter((d) => d.status === "COMPLETED").length}
            </p>
            <p className="text-[10px] text-emerald-600 font-semibold mt-0.5">&ge; 90% Confidence</p>
          </div>

          <div className="gov-card p-3.5 border-l-4 border-l-amber-500 bg-white shadow-xs">
            <div className="flex items-center justify-between text-gray-500">
              <span className="text-[11px] font-bold uppercase">Audit Queue</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <p className="text-xl sm:text-2xl font-black text-gray-900 mt-1 font-mono">
              {documents.filter((d) => d.status === "VERIFICATION_REQUIRED").length}
            </p>
            <p className="text-[10px] text-amber-700 font-semibold mt-0.5">Pending Tehsildar</p>
          </div>

          <div className="gov-card p-3.5 border-l-4 border-l-purple-600 bg-white shadow-xs">
            <div className="flex items-center justify-between text-gray-500">
              <span className="text-[11px] font-bold uppercase">Active Users</span>
              <UserCheck className="w-4 h-4 text-purple-600" />
            </div>
            <p className="text-xl sm:text-2xl font-black text-gray-900 mt-1 font-mono">
              {usersList.length || 4}
            </p>
            <p className="text-[10px] text-gray-400 mt-0.5">Assigned RBAC Roles</p>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex items-center gap-2 border-b border-gray-200 text-xs font-bold">
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-2 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "analytics"
                ? "border-amber-700 text-amber-800 bg-white rounded-t"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Visual Analytics & Graphs</span>
          </button>

          <button
            onClick={() => setActiveTab("documents")}
            className={`px-4 py-2 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "documents"
                ? "border-amber-700 text-amber-800 bg-white rounded-t"
                : "border-transparent text-gray-600 hover:text-gray-900"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Land Documents & Extracted Fields ({documents.length})</span>
          </button>

          {isAdmin && (
            <button
              onClick={() => setActiveTab("users")}
              className={`px-4 py-2 border-b-2 transition flex items-center gap-1.5 ${
                activeTab === "users"
                  ? "border-amber-700 text-amber-800 bg-white rounded-t"
                  : "border-transparent text-gray-600 hover:text-gray-900"
              }`}
            >
              <UserCheck className="w-4 h-4" />
              <span>Registered Users & Roles ({usersList.length})</span>
            </button>
          )}
        </div>

        {/* Tab 1: Visual Graphs and Analytics */}
        {activeTab === "analytics" && (
          <AdminCharts documents={documents} usersCount={usersList.length} />
        )}

        {/* Tab 2: Land Documents & Field Management */}
        {activeTab === "documents" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Side: Document Registry with Status Controls (5 cols) */}
            <div className="lg:col-span-5 gov-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-gray-200 pb-2">
                <div>
                  <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wide">
                    Database Deeds ({documents.length})
                  </h2>
                  <p className="text-[10px] text-gray-500">Select a document to inspect & edit its fields</p>
                </div>

                <button
                  onClick={loadData}
                  className="p-1 hover:bg-gray-100 rounded text-gray-500"
                  title="Reload from DB"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {loading ? (
                <div className="p-8 text-center text-xs text-gray-500">Loading records from PostgreSQL...</div>
              ) : documents.length === 0 ? (
                <div className="p-8 text-center text-xs text-gray-500">No documents in database. Upload one first.</div>
              ) : (
                <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
                  {documents.map((doc) => {
                    const isSelected = selectedDocId === doc.id;
                    return (
                      <div
                        key={doc.id}
                        className={`p-3 rounded border text-xs transition space-y-2 ${
                          isSelected
                            ? "bg-amber-50/80 border-amber-600 ring-1 ring-amber-500"
                            : "bg-white border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {/* Title & Selection */}
                        <div
                          onClick={() => setSelectedDocId(doc.id)}
                          className="cursor-pointer space-y-0.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-gray-900 truncate block max-w-[220px]" title={doc.filename}>
                              {doc.filename}
                            </span>
                            <span className="text-[9px] font-mono bg-slate-100 px-1 py-0.5 rounded border uppercase font-bold text-slate-700">
                              {doc.status}
                            </span>
                          </div>
                          <p className="text-[10px] text-gray-400 font-mono truncate">ID: {doc.id}</p>
                        </div>

                        {/* Database Status Override Controls */}
                        <div className="pt-2 border-t border-gray-100 flex items-center justify-between gap-1 flex-wrap text-[11px]">
                          <span className="text-gray-500 text-[10px]">Change Status:</span>

                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => handleChangeStatus(doc.id, "COMPLETED")}
                              className="px-1.5 py-0.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-800 rounded font-bold text-[10px]"
                              title="Set status to COMPLETED"
                            >
                              ✓ Verify
                            </button>

                            <button
                              type="button"
                              onClick={() => handleChangeStatus(doc.id, "VERIFICATION_REQUIRED")}
                              className="px-1.5 py-0.5 bg-amber-100 hover:bg-amber-200 text-amber-900 rounded font-bold text-[10px]"
                              title="Flag for Human Audit"
                            >
                              ⚠️ Audit
                            </button>

                            <button
                              type="button"
                              onClick={() => handleChangeStatus(doc.id, "FAILED")}
                              className="px-1.5 py-0.5 bg-rose-100 hover:bg-rose-200 text-rose-800 rounded font-bold text-[10px]"
                              title="Set status to FAILED"
                            >
                              ✕ Fail
                            </button>

                            <button
                              type="button"
                              onClick={() => handleReprocess(doc.id)}
                              className="p-1 text-gray-600 hover:text-amber-800"
                              title="Re-run AI extraction pipeline"
                            >
                              <RotateCw className="w-3 h-3" />
                            </button>

                            {isAdmin && (
                              <button
                                type="button"
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="p-1 text-rose-600 hover:text-rose-800"
                                title="Delete document from DB"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Side: Fields Editor for Selected Document (7 cols) */}
            <div className="lg:col-span-7 gov-card p-4 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-200 pb-3 gap-2">
                <div>
                  <h2 className="text-xs font-bold text-gray-900 uppercase tracking-wide flex items-center gap-1.5">
                    <Edit3 className="w-4 h-4 text-amber-700" />
                    <span>Database Fields & Extracted Attributes</span>
                  </h2>
                  <p className="text-[11px] text-gray-600 truncate max-w-md">
                    Selected Deed: <strong className="text-gray-900 font-mono">{activeDoc?.filename || "None selected"}</strong>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowAddModal(true)}
                    disabled={!selectedDocId}
                    className="px-3 py-1 bg-amber-700 hover:bg-amber-800 text-white rounded text-xs font-bold flex items-center gap-1 shadow-xs disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Manual Field</span>
                  </button>

                  {selectedDocId && (
                    <Link
                      href={`/documents/${selectedDocId}`}
                      className="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded text-xs font-semibold flex items-center gap-1 border border-gray-300"
                      title="View Full Document Page"
                    >
                      <Eye className="w-3 h-3" />
                      <span>View</span>
                    </Link>
                  )}
                </div>
              </div>

              {/* Add Field Inline Form */}
              {showAddModal && (
                <form onSubmit={handleAddManualField} className="p-3 bg-amber-50 border border-amber-300 rounded space-y-2 text-xs">
                  <div className="flex items-center justify-between font-bold text-amber-950 text-xs">
                    <span>Insert New Record Attribute to Database:</span>
                    <button type="button" onClick={() => setShowAddModal(false)} className="text-gray-500 hover:text-black">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div>
                      <label className="block font-semibold text-gray-700 mb-0.5">Field Name / Label</label>
                      <input
                        type="text"
                        value={newFieldName}
                        onChange={(e) => setNewFieldName(e.target.value)}
                        placeholder="e.g. khasra_number, area, owner_name"
                        className="w-full border border-gray-300 rounded px-2 py-1 bg-white font-mono text-xs"
                        required
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-gray-700 mb-0.5">Field Value</label>
                      <input
                        type="text"
                        value={newFieldValue}
                        onChange={(e) => setNewFieldValue(e.target.value)}
                        placeholder="e.g. 123/4 or 2.5 Hectares"
                        className="w-full border border-gray-300 rounded px-2 py-1 bg-white font-mono text-xs"
                        required
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-3 py-1 bg-white border border-gray-300 text-gray-700 rounded font-semibold text-xs"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-3 py-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded font-bold text-xs"
                    >
                      Insert into DB
                    </button>
                  </div>
                </form>
              )}

              {/* Fields Table */}
              {loadingFields ? (
                <div className="p-8 text-center text-xs text-gray-500">Fetching extracted fields from database...</div>
              ) : docFields.length === 0 ? (
                <div className="p-8 text-center text-xs text-gray-500 bg-gray-50 rounded border">
                  No extracted fields found for this document. Use the button above to add a manual attribute.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs text-left gov-table">
                    <thead>
                      <tr>
                        <th>Field Name</th>
                        <th>Current Value (in DB)</th>
                        <th>Validation</th>
                        <th className="text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {docFields.map((f) => {
                        const isEditing = editingFieldId === f.id;
                        return (
                          <tr key={f.id} className="hover:bg-amber-50/40">
                            {/* Field Name */}
                            <td className="font-bold text-gray-900 font-mono whitespace-nowrap">
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={editFieldName}
                                  onChange={(e) => setEditFieldName(e.target.value)}
                                  className="border border-gray-300 rounded px-2 py-0.5 w-32 font-mono text-xs"
                                />
                              ) : (
                                f.field_name
                              )}
                            </td>

                            {/* Field Value */}
                            <td className="font-mono text-gray-800">
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={editFieldValue}
                                  onChange={(e) => setEditFieldValue(e.target.value)}
                                  className="border border-gray-300 rounded px-2 py-0.5 w-full font-mono text-xs"
                                />
                              ) : (
                                <span className="font-semibold text-gray-900">{f.field_value || "—"}</span>
                              )}
                            </td>

                            {/* Status */}
                            <td className="whitespace-nowrap">
                              {isEditing ? (
                                <select
                                  value={editValidationStatus}
                                  onChange={(e) => setEditValidationStatus(e.target.value)}
                                  className="border border-gray-300 rounded px-1.5 py-0.5 text-xs bg-white"
                                >
                                  <option value="valid">valid</option>
                                  <option value="pending">pending</option>
                                  <option value="anomaly">anomaly</option>
                                  <option value="rejected">rejected</option>
                                </select>
                              ) : (
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                                    f.validation_status === "valid" || f.validated
                                      ? "bg-emerald-100 text-emerald-800"
                                      : f.anomaly_flag || f.validation_status === "anomaly"
                                      ? "bg-rose-100 text-rose-800"
                                      : "bg-amber-100 text-amber-800"
                                  }`}
                                >
                                  {f.validation_status || (f.validated ? "valid" : "pending")}
                                </span>
                              )}
                            </td>

                            {/* Actions */}
                            <td className="text-right whitespace-nowrap">
                              {isEditing ? (
                                <div className="flex items-center justify-end gap-1">
                                  <button
                                    type="button"
                                    onClick={() => handleSaveFieldEdit(f.id)}
                                    className="p-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded font-bold"
                                    title="Save to database"
                                  >
                                    <Save className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setEditingFieldId(null)}
                                    className="p-1 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded"
                                    title="Cancel"
                                  >
                                    <X className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingFieldId(f.id);
                                    setEditFieldName(f.field_name);
                                    setEditFieldValue(f.field_value || "");
                                    setEditValidationStatus(f.validation_status || (f.validated ? "valid" : "pending"));
                                  }}
                                  className="p-1 text-amber-700 hover:text-amber-900 border border-gray-200 rounded hover:bg-amber-50"
                                  title="Edit field in database"
                                >
                                  <Edit3 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Users Management Tab (Admin Only) */}
        {activeTab === "users" && (
          <div className="gov-card p-5 space-y-4">
            <div className="border-b border-gray-200 pb-3 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wide">
                  PostgreSQL Users & Role Assignments ({usersList.length})
                </h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  View and manage system administrators, revenue officers, verifiers, and citizens.
                </p>
              </div>

              <span className="text-[11px] bg-purple-100 text-purple-900 border border-purple-300 font-bold px-2 py-0.5 rounded font-mono">
                RBAC Security Level: Active
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-xs text-left gov-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Full Name & Designation</th>
                    <th>Email Address</th>
                    <th>System Role</th>
                    <th>Account Status</th>
                    <th>Registered Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {usersList.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50">
                      <td className="font-bold text-gray-900 font-mono">{u.username}</td>
                      <td className="font-semibold text-gray-800">{u.full_name || "—"}</td>
                      <td className="font-mono text-gray-600">{u.email || "—"}</td>
                      <td>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono border ${
                            u.role === "ADMIN"
                              ? "bg-purple-100 text-purple-900 border-purple-300"
                              : u.role === "OFFICER"
                              ? "bg-blue-100 text-blue-900 border-blue-300"
                              : u.role === "VERIFIER"
                              ? "bg-amber-100 text-amber-900 border-amber-300"
                              : "bg-emerald-100 text-emerald-900 border-emerald-300"
                          }`}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td>
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Active
                        </span>
                      </td>
                      <td className="font-mono text-gray-500">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString("en-IN") : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
